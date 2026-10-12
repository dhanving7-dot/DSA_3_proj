"""Allocation insights: the course's advanced algorithms applied to the *real* student/lab data.

Every number returned here is computed on demand from the database by the
same eligibility rules the allocation engine uses - nothing is cached or
estimated except where the method is explicitly Monte Carlo.

  bottleneck_analysis   min cut of the max-flow network -> Hall violator set, König cover   (Module 4)
  set_cover_analysis    fewest labs that keep every placeable student placeable           (Module 5)
  skill_supply          SOS DP over lab skill requirements                                 (Module 3)
  optimality_gap        Hopcroft-Karp vs min-cost max-flow on identical input             (Module 4)
  monte_carlo_outages   random lab outages, expected placements with a confidence interval (Module 6)
  audit_sample          reservoir sample of a run's allocations                            (Module 6)
"""
from __future__ import annotations

import math
import random
import time

from sqlalchemy.orm import Session

from app.algorithms.approximation import exact_set_cover, greedy_set_cover, harmonic
from app.algorithms.dinic import dinic_max_flow
from app.algorithms.dp import sos_superset_sums
from app.algorithms.flow_analysis import residual_reachable
from app.algorithms.graph import FlowNetwork
from app.algorithms.matching_engine import (
    ALL_ALGORITHMS,
    MATCHING_ALGORITHMS,
    LabInput,
    StudentInput,
    build_eligible_edges,
    build_flow_layout,
    run_allocation,
)
from app.algorithms.randomized import reservoir_sample
from app.models.allocation import Allocation, AllocationRun
from app.models.laboratory import Laboratory
from app.models.student import Student
from app.schemas.constraint import AllocationConfig
from app.services import analytics_service
from app.services.allocation_service import load_labs, load_students, to_engine_constraints


def _resolve_config(db: Session, run_id: int | None) -> tuple[AllocationConfig, int | None]:
    """Config of the requested run, else of the latest run, else the defaults."""
    run = db.get(AllocationRun, run_id) if run_id else analytics_service.get_latest_run(db)
    if run and run.config_snapshot:
        return AllocationConfig(**run.config_snapshot), run.id
    return AllocationConfig(), None


def _names(db: Session) -> tuple[dict[int, str], dict[int, str]]:
    students = {sid: f"{name} ({roll})" for sid, name, roll in db.query(Student.id, Student.full_name, Student.roll_number)}
    labs = {lid: name for lid, name in db.query(Laboratory.id, Laboratory.name)}
    return students, labs


def _load(db: Session, run_id: int | None):
    config, used_run = _resolve_config(db, run_id)
    students = load_students(db)
    labs = load_labs(db)
    constraints = to_engine_constraints(config)
    return config, used_run, students, labs, constraints


# --------------------------------------------------------------------------- bottleneck / min cut


def bottleneck_analysis(db: Session, run_id: int | None = None) -> dict:
    config, used_run, students, labs, constraints = _load(db, run_id)
    _, lab_names = _names(db)
    edges = build_eligible_edges(students, labs, constraints)
    share = constraints.max_share_per_department

    layout = build_flow_layout(students, labs, edges, share)
    network = FlowNetwork(layout.num_nodes)
    for u, v, capacity, _ in layout.arcs:
        network.add_edge(u, v, capacity)
    start = time.perf_counter()
    max_flow, _ = dinic_max_flow(network, layout.source, layout.sink)
    side = residual_reachable(network, layout.source)
    elapsed_ms = (time.perf_counter() - start) * 1000

    n = len(students)
    lab_offset = layout.student_offset + n
    lab_node = {lab_offset + j: j for j in range(len(labs))}

    hall_students = [i for i in range(n) if side[layout.student_offset + i]]
    hall_set = set(hall_students)
    neighbours: dict[int, set[int]] = {}
    for u, v, _, edge in layout.arcs:
        if edge is not None and (u - layout.student_offset) in hall_set:
            neighbours.setdefault(layout.node_to_lab[v], set()).add(u - layout.student_offset)

    cut_capacity = 0
    students_cut = 0
    bottleneck_labs = []
    binding_quotas = []
    for u in range(network.num_nodes):
        if not side[u]:
            continue
        for e in network.graph[u]:
            if e.capacity <= 0 or side[e.to]:
                continue
            cut_capacity += e.capacity
            if u == layout.source:
                students_cut += 1
            elif e.to == layout.sink and u in lab_node:
                lab = labs[lab_node[u]]
                bottleneck_labs.append(
                    {
                        "lab_id": lab.id,
                        "lab_name": lab_names.get(lab.id, f"Lab #{lab.id}"),
                        "capacity": lab.capacity,
                        "students_competing": len(neighbours.get(lab_node[u], ())),
                    }
                )
            else:  # gadget -> lab edge: a department quota that is binding
                lab = labs[layout.node_to_lab[u]]
                department = next(
                    (students[a - layout.student_offset].department for a, b, _, ed in layout.arcs if ed is not None and b == u),
                    "?",
                )
                binding_quotas.append(
                    {"lab_id": lab.id, "lab_name": lab_names.get(lab.id, f"Lab #{lab.id}"), "department": department, "quota": e.capacity}
                )

    blocking_capacity = cut_capacity - students_cut
    by_department: dict[str, int] = {}
    for i in hall_students:
        by_department[students[i].department] = by_department.get(students[i].department, 0) + 1
    with_edges = {e.student_id for e in edges}
    no_edges = sum(1 for i in hall_students if students[i].id not in with_edges)
    spare_labs = [
        {"lab_id": labs[j].id, "lab_name": lab_names.get(labs[j].id, f"Lab #{labs[j].id}")}
        for node, j in lab_node.items()
        if not side[node] and labs[j].is_active and labs[j].capacity > 0
    ]

    return {
        "config": config.model_dump(),
        "config_from_run": used_run,
        "total_students": n,
        "max_flow": max_flow,
        "unmatched": n - max_flow,
        "min_cut_capacity": cut_capacity,
        "max_flow_equals_min_cut": cut_capacity == max_flow,
        "hall": {
            "violator_size": len(hall_students),
            "reachable_capacity": blocking_capacity,
            "deficiency": len(hall_students) - blocking_capacity,
            "students_with_no_eligible_lab": no_edges,
            "by_department": dict(sorted(by_department.items(), key=lambda kv: -kv[1])),
        },
        "konig": {
            "students_in_cover": students_cut,
            "lab_seats_in_cover": blocking_capacity,
            "min_vertex_cover": students_cut + blocking_capacity,
            "max_matching": max_flow,
        },
        "bottleneck_labs": sorted(bottleneck_labs, key=lambda b: -b["students_competing"]),
        "binding_quotas": binding_quotas,
        "labs_outside_bottleneck": spare_labs,
        "execution_time_ms": elapsed_ms,
    }


# --------------------------------------------------------------------------- set cover


def set_cover_analysis(db: Session, run_id: int | None = None) -> dict:
    config, used_run, students, labs, constraints = _load(db, run_id)
    _, lab_names = _names(db)
    edges = build_eligible_edges(students, labs, constraints)
    student_bit = {s.id: i for i, s in enumerate(students)}
    candidate_labs = sorted({e.lab_id for e in edges})
    masks = []
    for lab_id in candidate_labs:
        mask = 0
        for e in edges:
            if e.lab_id == lab_id:
                mask |= 1 << student_bit[e.student_id]
        masks.append(mask)
    universe = 0
    for m in masks:
        universe |= m
    universe_size = bin(universe).count("1")

    start = time.perf_counter()
    greedy = greedy_set_cover(universe, masks)
    greedy_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    exact = exact_set_cover(universe, masks) if len(masks) <= 20 else None
    exact_ms = (time.perf_counter() - start) * 1000

    def describe(indices: list[int]) -> list[dict]:
        return [
            {"lab_id": candidate_labs[i], "lab_name": lab_names.get(candidate_labs[i], f"Lab #{candidate_labs[i]}"), "covers": bin(masks[i]).count("1")}
            for i in indices
        ]

    essential = []
    for i, m in enumerate(masks):
        others = 0
        for j, other in enumerate(masks):
            if j != i:
                others |= other
        only_here = bin(m & ~others).count("1")
        if only_here:
            essential.append({**describe([i])[0], "students_only_eligible_here": only_here})

    greedy_size = len(greedy["chosen"])
    exact_size = exact["size"] if exact else None
    return {
        "config": config.model_dump(),
        "config_from_run": used_run,
        "placeable_students": universe_size,
        "students_with_no_eligible_lab": len(students) - universe_size,
        "candidate_labs": len(masks),
        "greedy": {"labs": describe(greedy["chosen"]), "new_students_per_pick": greedy["gains"], "size": greedy_size, "time_ms": greedy_ms},
        "exact": {"labs": describe(exact["chosen"]), "size": exact_size, "subsets_evaluated": exact["subsets_evaluated"], "time_ms": exact_ms} if exact else None,
        "approximation_ratio": round(greedy_size / exact_size, 4) if exact_size else None,
        "harmonic_bound": round(harmonic(max(universe_size, 1)), 4),
        "essential_labs": essential,
    }


# --------------------------------------------------------------------------- SOS DP skill supply


def skill_supply(db: Session, max_items: int = 16) -> dict:
    labs = [lab for lab in load_labs(db) if lab.is_active]
    students = load_students(db)
    _, lab_names = _names(db)

    frequency: dict[tuple[str, int], int] = {}
    for lab in labs:
        for req in lab.required_skills:
            if req.required:
                key = (req.skill_name, req.min_proficiency)
                frequency[key] = frequency.get(key, 0) + 1
    items = sorted(frequency, key=lambda key: (-frequency[key], key))[:max_items]
    k = len(items)
    bit = {item: i for i, item in enumerate(items)}

    def qualification_mask(student: StudentInput) -> int:
        mask = 0
        for i, (skill, level) in enumerate(items):
            if student.skills.get(skill, 0) >= level:
                mask |= 1 << i
        return mask

    start = time.perf_counter()
    f = [0] * (1 << k)
    for s in students:
        f[qualification_mask(s)] += 1
    g = sos_superset_sums(f, k)
    sos_ms = (time.perf_counter() - start) * 1000

    per_lab = []
    brute_ops = 0
    for lab in labs:
        reqs = [(r.skill_name, r.min_proficiency) for r in lab.required_skills if r.required]
        tracked = all(r in bit for r in reqs)
        mask = sum(1 << bit[r] for r in reqs if r in bit)
        brute = 0
        for s in students:  # independent brute-force check of the SOS answer
            brute_ops += len(reqs)
            if all(s.skills.get(name, 0) >= level for name, level in reqs):
                brute += 1
        per_lab.append(
            {
                "lab_id": lab.id,
                "lab_name": lab_names.get(lab.id, f"Lab #{lab.id}"),
                "capacity": lab.capacity,
                "requirements": [f"{name} >= {level}" for name, level in reqs],
                "qualified_sos": g[mask] if tracked else None,
                "qualified_bruteforce": brute,
            }
        )

    pair_matrix = [[g[(1 << i) | (1 << j)] for j in range(k)] for i in range(k)]
    return {
        "items": [f"{name} >= {level}" for name, level in items],
        "k": k,
        "masks": 1 << k,
        "sos_operations": k * (1 << k),
        "sos_time_ms": sos_ms,
        "bruteforce_operations": brute_ops,
        "students": len(students),
        "per_lab": per_lab,
        "pair_matrix": pair_matrix,
        "qualified_for_none": f[0],
    }


# --------------------------------------------------------------------------- optimality gap


def _summarise(result, label: str) -> dict:
    ranks: dict[str, int] = {}
    for a in result.assignments:
        if a.status != "MATCHED":
            continue
        key = f"#{a.preference_rank}" if a.preference_rank else "unranked"
        ranks[key] = ranks.get(key, 0) + 1
    return {
        "algorithm": label,
        "matched": result.matched_count,
        "total_score": result.total_score,
        "average_score": round(result.total_score / result.matched_count, 4) if result.matched_count else 0.0,
        "preference_satisfaction": result.preference_satisfaction,
        "rank_distribution": dict(sorted(ranks.items(), key=lambda kv: (kv[0] == "unranked", kv[0]))),
        "execution_time_ms": result.algorithm_trace.execution_time_ms,
    }


def optimality_gap(db: Session, run_id: int | None = None) -> dict:
    """Every algorithm on identical input. All reach the same maximum cardinality (they solve the
    same max-flow problem), but only min-cost flow is guaranteed to maximise the total score -
    the others return whichever maximum matching their search order happens to find."""
    config, used_run, students, labs, constraints = _load(db, run_id)
    fair = constraints.max_share_per_department is not None
    algorithms = [a for a in ALL_ALGORITHMS if not (fair and a in MATCHING_ALGORITHMS)]
    results = {a: run_allocation(students, labs, constraints, a) for a in algorithms}
    optimal = results["MIN_COST_FLOW"]
    optimal_map = {a.student_id: a.lab_id for a in optimal.assignments}
    rows = []
    for algorithm, result in results.items():
        summary = _summarise(result, algorithm)
        summary["gap_to_optimal"] = round(optimal.total_score - result.total_score, 4)
        summary["students_placed_differently"] = sum(1 for a in result.assignments if optimal_map.get(a.student_id) != a.lab_id)
        rows.append(summary)
    return {
        "config": config.model_dump(),
        "config_from_run": used_run,
        "skipped": [a for a in ALL_ALGORITHMS if a not in algorithms],
        "algorithms": rows,
        "optimal_total_score": optimal.total_score,
        "same_cardinality": len({r.matched_count for r in results.values()}) == 1,
    }


# --------------------------------------------------------------------------- Monte Carlo outages


def monte_carlo_outages(
    db: Session, trials: int, outage_probability: float, seed: int | None, algorithm: str, run_id: int | None = None
) -> dict:
    """Each trial knocks every active lab out independently with probability p and re-runs the engine.

    Monte Carlo: fixed running time (trials x one allocation), approximate answer.
    The sample mean converges at rate 1/sqrt(trials) - the 95% interval below is
    mean +/- 1.96 * s / sqrt(trials) (normal approximation).
    """
    config, used_run, students, labs, constraints = _load(db, run_id)
    if constraints.max_share_per_department is not None and algorithm in MATCHING_ALGORITHMS:
        algorithm = "DINIC"
    student_names, lab_names = _names(db)
    rng = random.Random(seed)
    active = [lab for lab in labs if lab.is_active]

    start = time.perf_counter()
    baseline_result = run_allocation(students, labs, constraints, algorithm)
    baseline = baseline_result.matched_count
    placed_today = {a.student_id for a in baseline_result.assignments if a.status == "MATCHED"}
    samples: list[int] = []
    unmatched_counts: dict[int, int] = {s.id: 0 for s in students}
    lab_down_sum: dict[int, list[int]] = {lab.id: [0, 0] for lab in active}  # [sum matched when down, trials down]
    for _ in range(trials):
        down = {lab.id for lab in active if rng.random() < outage_probability}
        trial_labs: list[LabInput] = [lab for lab in labs if lab.id not in down]
        result = run_allocation(students, trial_labs, constraints, algorithm)
        samples.append(result.matched_count)
        for a in result.assignments:
            if a.status != "MATCHED":
                unmatched_counts[a.student_id] += 1
        for lab_id in down:
            lab_down_sum[lab_id][0] += result.matched_count
            lab_down_sum[lab_id][1] += 1
    elapsed_ms = (time.perf_counter() - start) * 1000

    mean = sum(samples) / trials
    variance = sum((x - mean) ** 2 for x in samples) / (trials - 1) if trials > 1 else 0.0
    std = math.sqrt(variance)
    half_width = 1.96 * std / math.sqrt(trials)

    histogram: dict[int, int] = {}
    for x in samples:
        histogram[x] = histogram.get(x, 0) + 1

    # only students placed today can be put at risk by an outage; the rest are unplaced in every trial
    at_risk = sorted(
        (
            {"student_id": sid, "student": student_names.get(sid, f"Student #{sid}"), "p_unmatched": round(c / trials, 4)}
            for sid, c in unmatched_counts.items()
            if c and sid in placed_today
        ),
        key=lambda r: (-r["p_unmatched"], r["student_id"]),
    )[:12]
    students_ever_displaced = sum(1 for sid, c in unmatched_counts.items() if c and sid in placed_today)
    criticality = sorted(
        (
            {
                "lab_id": lab_id,
                "lab_name": lab_names.get(lab_id, f"Lab #{lab_id}"),
                "trials_down": cnt,
                "expected_matched_when_down": round(total / cnt, 2),
                "loss_vs_baseline": round(baseline - total / cnt, 2),
            }
            for lab_id, (total, cnt) in lab_down_sum.items()
            if cnt
        ),
        key=lambda r: -r["loss_vs_baseline"],
    )
    return {
        "config_from_run": used_run,
        "algorithm": algorithm,
        "trials": trials,
        "outage_probability": outage_probability,
        "seed": seed,
        "baseline_matched": baseline,
        "mean_matched": round(mean, 3),
        "std_matched": round(std, 3),
        "ci95": [round(mean - half_width, 3), round(mean + half_width, 3)],
        "min_matched": min(samples),
        "max_matched": max(samples),
        "histogram": [{"matched": k, "trials": v} for k, v in sorted(histogram.items())],
        "at_risk_students": at_risk,
        "students_ever_displaced": students_ever_displaced,
        "never_placeable": len(students) - baseline,
        "lab_criticality": criticality,
        "execution_time_ms": elapsed_ms,
    }


# --------------------------------------------------------------------------- reservoir audit sample


def audit_sample(db: Session, run_id: int | None, k: int, seed: int | None) -> dict:
    run = db.get(AllocationRun, run_id) if run_id else analytics_service.get_latest_run(db)
    if not run:
        return {"run_id": None, "sample": [], "items_seen": 0, "k": k, "inclusion_probability": 0.0}
    student_names, lab_names = _names(db)
    stream = db.query(Allocation).filter(Allocation.run_id == run.id).order_by(Allocation.id).yield_per(64)
    sample, seen = reservoir_sample(stream, k, random.Random(seed))
    rows = [
        {
            "allocation_id": a.id,
            "student_id": a.student_id,
            "student": student_names.get(a.student_id, f"Student #{a.student_id}"),
            "lab": lab_names.get(a.lab_id) if a.lab_id else None,
            "status": a.status.value,
            "preference_rank": a.preference_rank,
            "match_score": a.match_score,
            "reason": a.eligibility_reason,
        }
        for a in sorted(sample, key=lambda a: a.id)
    ]
    return {
        "run_id": run.id,
        "k": k,
        "items_seen": seen,
        "inclusion_probability": round(min(1.0, k / seen), 4) if seen else 0.0,
        "sample": rows,
    }
