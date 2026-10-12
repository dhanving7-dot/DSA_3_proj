"""AI layer: natural-language -> structured constraints, and explanations
generated strictly from real backend facts.

Design principle (per project spec): the AI NEVER invents allocation
results or statistics. It only:
  1. Parses free text into a structured `AllocationConfig` + filters, which
     is then handed to the real deterministic matching engine.
  2. Reads real rows out of the database (allocations, runs, metrics) and
     turns them into natural-language explanations / answers.

The parser below is a transparent, rule-based NLP pipeline (keyword +
alias matching, no network calls) so it always works offline and
deterministically in this environment. It is intentionally isolated behind
`parse_command`, so a real LLM call (e.g. the Claude API, guarded by
`settings.ANTHROPIC_API_KEY`) could be dropped in later purely to improve
*parsing quality* - it would still hand the same structured config to the
same unmodified matching engine, preserving the "AI enhances, never
replaces, the algorithm" contract.

String algorithms used by the parser (Module 2 / Module 3 of the course):
  * every department alias and algorithm keyword is found in ONE pass over
    the command with an Aho-Corasick automaton, instead of one substring scan
    per keyword;
  * when no exact keyword is present, words are compared against the
    vocabulary with Damerau-Levenshtein (OSA) edit distance, so typos such as
    "mechanicl" or "hopcroft-krap" still resolve - and the note says so.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.algorithms.dp import osa_distance
from app.algorithms.strings import AhoCorasick

from app.models.allocation import Allocation, AllocationRun, AllocationStatus
from app.models.laboratory import Laboratory
from app.models.student import Student
from app.schemas.ai import AIExplainResponse, ParsedConstraints
from app.schemas.constraint import AllocationConfig
from app.services import analytics_service

DEPARTMENT_ALIASES: dict[str, list[str]] = {
    "CSE": ["computer science", "cse", "cs "],
    "ECE": ["electronics and communication", "electronics", "ece"],
    "EEE": ["electrical and electronics", "eee"],
    "MECH": ["mechanical", "mech"],
    "CIVIL": ["civil"],
    "IT": ["information technology", " it "],
    "AIML": ["artificial intelligence", "ai and ml", "aiml", "ai/ml"],
}

YEAR_WORDS = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2,
    "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "final": 4,
}

ALGORITHM_KEYWORDS = {
    "min cost": "MIN_COST_FLOW",
    "min-cost": "MIN_COST_FLOW",
    "mincost": "MIN_COST_FLOW",
    "minimum cost": "MIN_COST_FLOW",
    "cost flow": "MIN_COST_FLOW",
    "successive shortest": "MIN_COST_FLOW",
    "hungarian": "MIN_COST_FLOW",  # the Hungarian method solves the *weighted* assignment problem
    "assignment problem": "MIN_COST_FLOW",
    "ford-fulkerson": "FORD_FULKERSON",
    "ford fulkerson": "FORD_FULKERSON",
    "fulkerson": "FORD_FULKERSON",
    "kuhn": "KUHN",
    "hopcroft": "HOPCROFT_KARP",
    "hopcroft-karp": "HOPCROFT_KARP",
    "edmonds": "EDMONDS_KARP",
    "edmonds-karp": "EDMONDS_KARP",
    "max flow": "EDMONDS_KARP",
    "maximum flow": "EDMONDS_KARP",
    "dinic": "DINIC",
}


# single words that may be typo-corrected, mapped to what they mean (multi-word and very short
# aliases are deliberately excluded: fuzzy-matching "it" or "cs" would fire on ordinary words)
FUZZY_DEPARTMENT_WORDS = {
    "electronics": "ECE",
    "electrical": "EEE",
    "mechanical": "MECH",
    "civil": "CIVIL",
    "computer": "CSE",
    "information": "IT",
    "artificial": "AIML",
    "intelligence": "AIML",
}
FUZZY_ALGORITHM_WORDS = {
    "hopcroft": "HOPCROFT_KARP",
    "edmonds": "EDMONDS_KARP",
    "dinic": "DINIC",
    "dinics": "DINIC",
    "fulkerson": "FORD_FULKERSON",
    "hungarian": "MIN_COST_FLOW",
}

_DEPARTMENT_PATTERNS = [alias for aliases in DEPARTMENT_ALIASES.values() for alias in aliases]
_DEPARTMENT_MATCHER = AhoCorasick(_DEPARTMENT_PATTERNS)
_ALGORITHM_PATTERNS = list(ALGORITHM_KEYWORDS)
_ALGORITHM_MATCHER = AhoCorasick(_ALGORITHM_PATTERNS)


def _found_keywords(matcher: AhoCorasick, patterns: list[str], text_lower: str) -> set[str]:
    return {patterns[idx] for idx in matcher.found_set(text_lower)}


def _fuzzy_lookup(text_lower: str, vocabulary: dict[str, str]) -> tuple[str, str, str, int] | None:
    """Closest (word, vocabulary word, meaning, distance) within the typo budget, or None.

    Budget: 1 edit for words up to 7 letters, 2 for longer ones; words shorter
    than 5 letters are never corrected. Exact matches are handled by the
    Aho-Corasick pass, so distance 0 is skipped here.
    """
    best: tuple[str, str, str, int] | None = None
    for word in re.findall(r"[a-z]+", text_lower):
        if len(word) < 5:
            continue
        for target, meaning in vocabulary.items():
            if abs(len(word) - len(target)) > 2:
                continue
            budget = 1 if len(target) <= 7 else 2
            distance = osa_distance(word, target)
            if 0 < distance <= budget and (best is None or distance < best[3]):
                best = (word, target, meaning, distance)
    return best


def _extract_department(text_lower: str, notes: list[str] | None = None) -> str | None:
    found = _found_keywords(_DEPARTMENT_MATCHER, _DEPARTMENT_PATTERNS, text_lower)
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias in found:
                return dept
    fuzzy = _fuzzy_lookup(text_lower, FUZZY_DEPARTMENT_WORDS)
    if fuzzy:
        word, target, dept, distance = fuzzy
        if notes is not None:
            notes.append(f"Typo-corrected '{word}' -> '{target}' (edit distance {distance}).")
        return dept
    return None


def _extract_year(text_lower: str) -> int | None:
    match = re.search(r"\b(year\s*[1-4])\b", text_lower)
    if match:
        return int(re.sub(r"\D", "", match.group(1)))
    for word, year in YEAR_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b\s*year", text_lower) or re.search(
            rf"\byear\b\s*{re.escape(word)}", text_lower
        ):
            return year
    return None


def _extract_algorithm(text_lower: str, notes: list[str] | None = None) -> str:
    found = _found_keywords(_ALGORITHM_MATCHER, _ALGORITHM_PATTERNS, text_lower)
    for keyword, algo in ALGORITHM_KEYWORDS.items():
        if keyword in found:
            return algo
    fuzzy = _fuzzy_lookup(text_lower, FUZZY_ALGORITHM_WORDS)
    if fuzzy:
        word, target, algo, distance = fuzzy
        if notes is not None:
            notes.append(f"Typo-corrected '{word}' -> '{target}' (edit distance {distance}).")
        return algo
    return "HOPCROFT_KARP"


def _extract_lab_filters(text_lower: str, db: Session) -> list[str]:
    labs = db.query(Laboratory).all()
    matched: list[str] = []
    for lab in labs:
        name_lower = lab.name.lower()
        # the lab code's prefix (e.g. "AI" from "AI-LAB-01", "DBMS" from "DBMS-LAB-01")
        # is the human-recognizable acronym administrators actually type/say,
        # so it gets a precise whole-word match even when short (2-6 chars).
        code_prefix = lab.code.split("-")[0].lower()
        code_match = len(code_prefix) >= 2 and re.search(rf"\b{re.escape(code_prefix)}\b", text_lower)
        # full-word tokens from the lab name itself (skip generic "lab"/"laboratory");
        # require >=4 chars here since short name-tokens are too likely to collide
        # with ordinary English words.
        tokens = [t for t in re.split(r"[\s\-]+", name_lower) if t not in ("lab", "laboratory", "")]
        name_match = any(len(tok) >= 4 and tok in text_lower for tok in tokens)
        if code_match or name_match:
            matched.append(lab.name)
    return matched


def parse_command(text: str, db: Session) -> ParsedConstraints:
    text_lower = text.lower()
    notes: list[str] = []

    department = _extract_department(text_lower, notes)
    if department:
        notes.append(f"Interpreted department filter: {department}")

    year = _extract_year(text_lower)
    if year:
        notes.append(f"Interpreted year filter: year {year}")

    algorithm = _extract_algorithm(text_lower, notes)
    notes.append(f"Selected algorithm: {algorithm}")

    lab_filters = _extract_lab_filters(text_lower, db)
    if lab_filters:
        notes.append(f"Interpreted target laboratories: {', '.join(lab_filters)}")

    config = AllocationConfig()

    prioritize_pref = any(
        phrase in text_lower
        for phrase in ["prioritiz", "first preference", "top preference", "favor their preference"]
    )
    if prioritize_pref:
        config.preference_weight = 0.7
        config.skill_weight = 0.2
        config.priority_weight = 0.1
        notes.append("Increased preference_weight to 0.7 because the request emphasised student preference.")

    if "only" in text_lower and any(phrase in text_lower for phrase in ["their preference", "preferred lab", "preferences"]):
        config.require_preference = True
        notes.append("Set require_preference=True: only labs a student explicitly ranked are eligible.")

    if department and ("only" in text_lower or "same department" in text_lower):
        config.same_department_only = True
        notes.append("Set same_department_only=True based on department-restrictive phrasing.")

    if any(phrase in text_lower for phrase in ["fair", "fairness", "balanced across departments"]):
        config.max_share_per_department = 0.6
        notes.append("Applied a fairness cap: max_share_per_department=0.6")
        if algorithm in ("KUHN", "HOPCROFT_KARP"):
            notes.append(
                f"Switched {algorithm} -> DINIC: per-department quotas inside each lab are a laminar "
                "constraint that plain bipartite matching cannot express, but a flow network can."
            )
            algorithm = "DINIC"

    return ParsedConstraints(
        algorithm=algorithm,
        config=config,
        department_filter=department,
        year_filter=year,
        lab_name_filters=lab_filters,
        notes=notes,
    )


def resolve_filters_to_ids(
    db: Session, department: str | None, year: int | None, lab_names: list[str]
) -> tuple[list[int] | None, list[int] | None]:
    student_query = db.query(Student.id)
    if department:
        student_query = student_query.filter(Student.department == department)
    if year:
        student_query = student_query.filter(Student.year == year)
    student_ids = [row[0] for row in student_query.all()] if (department or year) else None

    lab_ids: list[int] | None = None
    if lab_names:
        lab_ids = [row[0] for row in db.query(Laboratory.id).filter(Laboratory.name.in_(lab_names)).all()]

    return student_ids, lab_ids


def explain_assignment(db: Session, allocation: Allocation) -> AIExplainResponse:
    student = db.get(Student, allocation.student_id)
    lab = db.get(Laboratory, allocation.lab_id) if allocation.lab_id else None
    run = db.get(AllocationRun, allocation.run_id)

    facts = {
        "student_department": student.department if student else None,
        "student_year": student.year if student else None,
        "student_cgpa": student.cgpa if student else None,
        "preference_rank": allocation.preference_rank,
        "match_score": allocation.match_score,
        "eligibility_reason": allocation.eligibility_reason,
        "algorithm": allocation.algorithm.value,
        "run_id": allocation.run_id,
    }

    if allocation.status == AllocationStatus.MATCHED and lab:
        utilization = analytics_service.get_lab_utilization(db, run.id if run else None)
        lab_util = next((u for u in utilization if u["lab_id"] == lab.id), None)
        facts["lab_name"] = lab.name
        facts["lab_capacity"] = lab.capacity
        facts["lab_utilization"] = lab_util["utilization"] if lab_util else None

        rank_clause = (
            f"This was the student's #{allocation.preference_rank} ranked preference. "
            if allocation.preference_rank
            else "This lab was not in the student's stated preference list, but was the best-scoring eligible option. "
        )
        explanation = (
            f"Student #{student.id} ({student.department}, year {student.year}) was assigned to "
            f"'{lab.name}' by the {allocation.algorithm.value} algorithm in run #{allocation.run_id}. "
            f"{rank_clause}"
            f"Eligibility was determined by: {allocation.eligibility_reason}. "
            f"Final match score: {allocation.match_score:.3f} "
            f"(weighted combination of preference rank, skill fit and priority score). "
            f"Laboratory '{lab.name}' has capacity {lab.capacity} and is currently at "
            f"{(lab_util['utilization'] * 100 if lab_util else 0):.0f}% utilization for this run."
        )
    else:
        explanation = (
            f"Student #{student.id if student else allocation.student_id} was NOT matched in run "
            f"#{allocation.run_id} ({allocation.algorithm.value}). Reason recorded by the allocation "
            f"engine: {allocation.eligibility_reason}."
        )

    return AIExplainResponse(
        student_id=allocation.student_id,
        lab_id=allocation.lab_id,
        status=allocation.status.value,
        explanation=explanation,
        facts=facts,
    )


def answer_analytics_question(db: Session, question: str, run_id: int | None = None) -> tuple[str, dict]:
    text_lower = question.lower()
    run = db.get(AllocationRun, run_id) if run_id else analytics_service.get_latest_run(db)

    if not run:
        return "No allocation run has been executed yet, so there is no data to analyse.", {}

    if any(phrase in text_lower for phrase in ["unmatched", "not matched", "didn't get", "why"]) and (
        "unmatched" in text_lower or "not matched" in text_lower
    ):
        unmatched = (
            db.query(Allocation)
            .filter(Allocation.run_id == run.id, Allocation.status == AllocationStatus.UNMATCHED)
            .all()
        )
        reason_counts: dict[str, int] = {}
        for a in unmatched:
            key = a.eligibility_reason.split(" (lab")[0].split(";")[0].strip()
            reason_counts[key] = reason_counts.get(key, 0) + 1
        breakdown = ", ".join(f"{count} student(s): {reason}" for reason, count in reason_counts.items())
        answer = (
            f"In run #{run.id} ({run.algorithm.value}), {run.unmatched_count} of {run.total_students} "
            f"students were unmatched. Breakdown of recorded reasons -> {breakdown or 'no unmatched students'}."
        )
        return answer, {"run_id": run.id, "unmatched_count": run.unmatched_count, "reasons": reason_counts}

    if "utiliz" in text_lower or "capacity" in text_lower:
        util = analytics_service.get_lab_utilization(db, run.id)
        answer = "Lab utilization for run #{}: ".format(run.id) + "; ".join(
            f"{u['lab_name']} {u['allocated']}/{u['capacity']} ({u['utilization']*100:.0f}%)" for u in util
        )
        return answer, {"run_id": run.id, "lab_utilization": util}

    if "fast" in text_lower or "performance" in text_lower or "complexity" in text_lower:
        perf = analytics_service.get_algorithm_performance(db)
        answer = "Recorded algorithm performance (most recent first): " + "; ".join(
            f"{p['algorithm']} on run #{p['run_id']} took {p['execution_time_ms']:.3f}ms "
            f"for {p['vertices']} vertices / {p['edges']} edges"
            for p in perf
        )
        return answer, {"algorithm_performance": perf}

    overview = analytics_service.get_overview(db)
    answer = (
        f"Latest run #{run.id} used {run.algorithm.value}: {run.matched_count} matched, "
        f"{run.unmatched_count} unmatched out of {run.total_students} students "
        f"({overview['matching_percentage']*100:.1f}% matched), "
        f"capacity utilization {overview['capacity_utilization']*100:.1f}%, "
        f"preference satisfaction {overview['preference_satisfaction']*100:.1f}%."
    )
    return answer, overview


def detect_conflicts(db: Session) -> list[dict]:
    conflicts: list[dict] = []

    zero_capacity_active = db.query(Laboratory).filter(Laboratory.capacity <= 0).all()
    for lab in zero_capacity_active:
        conflicts.append(
            {
                "type": "ZERO_CAPACITY",
                "severity": "high",
                "message": f"Laboratory '{lab.name}' has capacity {lab.capacity} and can accept no students.",
                "lab_id": lab.id,
            }
        )

    labs_without_slots = [lab for lab in db.query(Laboratory).all() if lab.time_slots and not any(t.is_available for t in lab.time_slots)]
    for lab in labs_without_slots:
        conflicts.append(
            {
                "type": "NO_AVAILABLE_SLOT",
                "severity": "medium",
                "message": f"Laboratory '{lab.name}' has time slots defined but none are marked available.",
                "lab_id": lab.id,
            }
        )

    from sqlalchemy import func as sa_func

    dept_demand = dict(db.query(Student.department, sa_func.count(Student.id)).group_by(Student.department).all())
    dept_supply: dict[str, int] = {}
    for lab in db.query(Laboratory).all():
        dept_supply[lab.department] = dept_supply.get(lab.department, 0) + lab.capacity
    for dept, demand in dept_demand.items():
        supply = dept_supply.get(dept, 0)
        if supply < demand:
            conflicts.append(
                {
                    "type": "DEPARTMENT_UNDERSUPPLY",
                    "severity": "medium",
                    "message": (
                        f"Department '{dept}' has {demand} students but only {supply} same-department lab "
                        f"seats available; cross-department eligibility or added capacity may be required."
                    ),
                    "department": dept,
                }
            )

    return conflicts


def generate_report(db: Session, run_id: int | None = None) -> str:
    run = db.get(AllocationRun, run_id) if run_id else analytics_service.get_latest_run(db)
    if not run:
        return "No allocation run has been executed yet."

    util = analytics_service.get_lab_utilization(db, run.id)
    dept = analytics_service.get_department_allocation(db, run.id)

    lines = [
        f"# Allocation Report - Run #{run.id}",
        "",
        f"- Algorithm: {run.algorithm.value}",
        f"- Students: {run.total_students} total, {run.matched_count} matched, {run.unmatched_count} unmatched",
        f"- Execution time: {run.execution_time_ms:.3f} ms",
        f"- Preference satisfaction: {run.preference_satisfaction * 100:.1f}%",
        f"- Capacity utilization: {run.capacity_utilization * 100:.1f}%",
        "",
        "## Laboratory Utilization",
    ]
    for u in util:
        lines.append(f"- {u['lab_name']} ({u['department']}): {u['allocated']}/{u['capacity']} ({u['utilization']*100:.0f}%)")

    lines.append("")
    lines.append("## Department Breakdown")
    for d in dept:
        lines.append(f"- {d['department']}: {d['matched']} matched / {d['total_students']} total")

    conflicts = detect_conflicts(db)
    if conflicts:
        lines.append("")
        lines.append("## Detected Conflicts")
        for c in conflicts:
            lines.append(f"- [{c['severity'].upper()}] {c['message']}")

    return "\n".join(lines)
