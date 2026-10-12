"""Domain-aware orchestration layer on top of the four graph algorithms.

This module is deliberately decoupled from SQLAlchemy: it accepts plain
dataclasses (StudentInput / LabInput / EngineConstraints) so the algorithms
and the eligibility/scoring logic can be unit-tested without a database at
all. `app.services.allocation_service` is the only place that converts ORM
rows into these inputs.

Pipeline:
  1. Determine eligibility for every (student, lab) pair given skills,
     department rules, lab status and preference-only constraints.
  2. Score every eligible edge (preference rank, skill fit, priority/fairness).
  3. Build the appropriate graph representation for the requested algorithm
     and run it (Kuhn/Hopcroft-Karp -> BipartiteGraph with lab-capacity
     "slot" expansion; Ford-Fulkerson/Edmonds-Karp/Dinic -> a source/sink
     FlowNetwork; min-cost flow -> the same network with edge costs).
  4. Translate the raw matching/flow result back into student<->lab
     assignments with explainable reasons and aggregate statistics.

Fairness caps (at most a share of a lab's seats per department) are a
*laminar* capacity constraint: department quotas nested inside each lab's
total. Plain bipartite matching cannot express that, the flow formulation
can - each (lab, department) pair gets a gadget node whose edge into the
lab carries the quota. This is exactly why the flow formulation is the more
general one, so the matching-only algorithms reject a fairness cap rather
than silently ignoring it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.algorithms.dinic import dinic_max_flow
from app.algorithms.edmonds_karp import edmonds_karp_max_flow
from app.algorithms.ford_fulkerson import ford_fulkerson_max_flow
from app.algorithms.graph import BipartiteGraph, FlowNetwork
from app.algorithms.hopcroft_karp import hopcroft_karp_max_matching
from app.algorithms.kuhn import kuhn_max_matching
from app.algorithms.min_cost_flow import CostFlowNetwork, min_cost_max_flow
from app.algorithms.parallel import blelloch_exclusive_scan
from app.algorithms.result import MatchingResult

MATCHING_ALGORITHMS = ("KUHN", "HOPCROFT_KARP")
FLOW_ALGORITHMS = ("FORD_FULKERSON", "EDMONDS_KARP", "DINIC")
COST_FLOW_ALGORITHMS = ("MIN_COST_FLOW",)
ALL_ALGORITHMS = MATCHING_ALGORITHMS + FLOW_ALGORITHMS + COST_FLOW_ALGORITHMS

# match scores are rounded to 4 decimals, so this scale turns them into exact integer costs
COST_SCALE = 10_000


class AllocationConfigError(ValueError):
    """A configuration the requested algorithm cannot honour (surfaced to API callers as HTTP 400)."""


@dataclass
class StudentInput:
    id: int
    department: str
    year: int
    cgpa: float
    priority_score: float
    skills: dict[str, int] = field(default_factory=dict)  # skill_name -> proficiency (1-5)
    preferences: dict[int, int] = field(default_factory=dict)  # lab_id -> rank (1 = best)


@dataclass
class LabRequiredSkill:
    skill_name: str
    min_proficiency: int
    required: bool


@dataclass
class LabInput:
    id: int
    department: str
    capacity: int
    is_active: bool
    required_skills: list[LabRequiredSkill] = field(default_factory=list)
    has_available_slot: bool = True  # scheduling/availability constraint


@dataclass
class EngineConstraints:
    same_department_only: bool = False
    require_preference: bool = False
    min_preference_score: float = 0.3
    preference_weight: float = 0.5
    skill_weight: float = 0.3
    priority_weight: float = 0.2
    max_share_per_department: float | None = None  # fairness: cap fraction of a lab's capacity per department


@dataclass
class EligibleEdge:
    student_id: int
    lab_id: int
    score: float
    preference_rank: int | None
    reason: str


@dataclass
class AssignmentResult:
    student_id: int
    lab_id: int | None
    preference_rank: int | None
    match_score: float
    eligibility_reason: str
    status: str  # MATCHED | UNMATCHED


@dataclass
class EngineResult:
    algorithm: str
    assignments: list[AssignmentResult]
    matched_count: int
    unmatched_count: int
    total_students: int
    total_labs: int
    total_edges: int
    preference_satisfaction: float
    capacity_utilization: float
    algorithm_trace: MatchingResult
    total_score: float = 0.0  # sum of match scores over matched students (what min-cost flow maximises)


def _skill_fit(student: StudentInput, lab: LabInput) -> tuple[bool, float, str]:
    if not lab.required_skills:
        return True, 1.0, "no specific skill requirements"
    satisfied = 0
    total_required = 0
    missing: list[str] = []
    for req in lab.required_skills:
        if not req.required:
            continue
        total_required += 1
        proficiency = student.skills.get(req.skill_name, 0)
        if proficiency >= req.min_proficiency:
            satisfied += 1
        else:
            missing.append(req.skill_name)
    if total_required == 0:
        return True, 1.0, "no mandatory skill requirements"
    if missing:
        return False, 0.0, f"missing required skill(s): {', '.join(missing)}"
    fit_ratio = satisfied / total_required
    return True, fit_ratio, f"satisfies {satisfied}/{total_required} required skills"


def _best_rejection_reason(student: StudentInput, labs: list[LabInput], constraints: EngineConstraints) -> str:
    """Picks the most informative reason a student has zero eligible edges.

    Skill mismatches are reported before department/preference mismatches
    since they are usually the more actionable piece of feedback for the
    AI explanation panel and for administrators tuning constraints.
    """
    if not labs:
        return "no laboratories are currently registered in the system"

    fallback_reason = "no eligible laboratory found for this student under current constraints"
    for lab in labs:
        if not (lab.is_active and lab.has_available_slot and lab.capacity > 0):
            continue
        if constraints.same_department_only and student.department != lab.department:
            continue
        eligible, _, skill_reason = _skill_fit(student, lab)
        if not eligible:
            return f"{skill_reason} (lab {lab.id})"
        if constraints.require_preference and student.preferences.get(lab.id) is None:
            fallback_reason = "not eligible: lab requires a stated preference, none of student's preferences matched any active lab"
    return fallback_reason


def build_eligible_edges(
    students: list[StudentInput], labs: list[LabInput], constraints: EngineConstraints
) -> list[EligibleEdge]:
    edges: list[EligibleEdge] = []
    active_labs = [lab for lab in labs if lab.is_active and lab.has_available_slot and lab.capacity > 0]

    for student in students:
        for lab in active_labs:
            if constraints.same_department_only and student.department != lab.department:
                continue

            pref_rank = student.preferences.get(lab.id)
            if constraints.require_preference and pref_rank is None:
                continue

            eligible, skill_score, skill_reason = _skill_fit(student, lab)
            if not eligible:
                continue

            if pref_rank is not None:
                max_rank = max(len(student.preferences), 1)
                preference_score = 1.0 - (pref_rank - 1) / max(max_rank, 1)
                pref_reason = f"ranked #{pref_rank} preference"
            else:
                preference_score = constraints.min_preference_score
                pref_reason = "not in stated preferences (baseline score applied)"

            priority_score = min(max(student.priority_score, 0.0), 1.0)

            score = (
                constraints.preference_weight * preference_score
                + constraints.skill_weight * skill_score
                + constraints.priority_weight * priority_score
            )

            dept_reason = (
                "same department as lab"
                if student.department == lab.department
                else f"cross-department ({student.department} -> {lab.department})"
            )
            reason = f"{pref_reason}; {skill_reason}; {dept_reason}"

            edges.append(
                EligibleEdge(
                    student_id=student.id,
                    lab_id=lab.id,
                    score=round(score, 4),
                    preference_rank=pref_rank,
                    reason=reason,
                )
            )
    return edges


def _group_edges_by_student(edges: list[EligibleEdge]) -> dict[int, list[EligibleEdge]]:
    """Per-student edge lists, best score first (the order augmenting-path searches try them in)."""
    grouped: dict[int, list[EligibleEdge]] = {}
    for edge in edges:
        grouped.setdefault(edge.student_id, []).append(edge)
    for student_edges in grouped.values():
        student_edges.sort(key=lambda e: e.score, reverse=True)
    return grouped


def _run_kuhn_or_hk(
    students: list[StudentInput],
    labs: list[LabInput],
    edges: list[EligibleEdge],
    algorithm: str,
) -> tuple[list[tuple[int, int]], MatchingResult, dict[int, int]]:
    """Returns (matched (student_idx, lab_idx) pairs, trace, slot_to_lab_idx map)."""
    student_index = {s.id: i for i, s in enumerate(students)}
    lab_index = {lab.id: i for i, lab in enumerate(labs)}

    # expand each lab into `capacity` slot-vertices on the right side; lab j's slots start at the
    # exclusive prefix sum of the capacities before it (computed with the work-efficient Blelloch scan)
    capacities = [lab.capacity for lab in labs]
    slot_offsets = blelloch_exclusive_scan(capacities).result
    slot_counter = sum(capacities)
    slot_to_lab_idx: dict[int, int] = {}
    for lab_idx, lab in enumerate(labs):
        for slot in range(slot_offsets[lab_idx], slot_offsets[lab_idx] + lab.capacity):
            slot_to_lab_idx[slot] = lab_idx

    graph = BipartiteGraph(num_left=len(students), num_right=slot_counter)
    for sid, student_edges in _group_edges_by_student(edges).items():
        left = student_index[sid]
        for edge in student_edges:
            lab_idx = lab_index[edge.lab_id]
            base_slot = slot_offsets[lab_idx]
            for slot in range(base_slot, base_slot + labs[lab_idx].capacity):
                graph.add_edge(left, slot)

    if algorithm == "KUHN":
        trace = kuhn_max_matching(graph)
    else:
        trace = hopcroft_karp_max_matching(graph)

    matched_pairs = [(left, slot_to_lab_idx[right]) for left, right in trace.matched_pairs]
    return matched_pairs, trace, slot_to_lab_idx


def department_quota(capacity: int, share: float) -> int:
    """Seats one department may take in a lab under a fairness cap (at least one, never above capacity)."""
    return min(capacity, max(1, math.floor(share * capacity)))


@dataclass
class FlowLayout:
    """Node numbering and arcs of the flow formulation, shared by plain and min-cost flow.

    source(0) -> student nodes -> [ (lab, department) quota gadgets ] -> lab nodes -> sink
    Gadget nodes only exist when a fairness cap is active; they are numbered after the sink.
    """

    num_nodes: int
    source: int
    sink: int
    student_offset: int
    node_to_lab: dict[int, int]
    # (u, v, capacity, edge) - `edge` is the EligibleEdge for student arcs, None otherwise
    arcs: list[tuple[int, int, int, EligibleEdge | None]]


def build_flow_layout(
    students: list[StudentInput], labs: list[LabInput], edges: list[EligibleEdge], share: float | None
) -> FlowLayout:
    student_index = {s.id: i for i, s in enumerate(students)}
    lab_index = {lab.id: i for i, lab in enumerate(labs)}
    department_of = {s.id: s.department for s in students}

    source = 0
    student_offset = 1
    lab_offset = student_offset + len(students)
    sink = lab_offset + len(labs)
    next_node = sink + 1

    arcs: list[tuple[int, int, int, EligibleEdge | None]] = []
    for i in range(len(students)):
        arcs.append((source, student_offset + i, 1, None))
    for j, lab in enumerate(labs):
        arcs.append((lab_offset + j, sink, lab.capacity, None))

    node_to_lab = {lab_offset + j: j for j in range(len(labs))}
    gadgets: dict[tuple[int, str], int] = {}
    for sid, student_edges in _group_edges_by_student(edges).items():
        s_node = student_offset + student_index[sid]
        for edge in student_edges:
            l_idx = lab_index[edge.lab_id]
            if share is None:
                target = lab_offset + l_idx
            else:
                key = (l_idx, department_of[sid])
                if key not in gadgets:
                    gadgets[key] = next_node
                    node_to_lab[next_node] = l_idx
                    next_node += 1
                target = gadgets[key]
            arcs.append((s_node, target, 1, edge))
    for (l_idx, _department), node in gadgets.items():
        arcs.append((node, lab_offset + l_idx, department_quota(labs[l_idx].capacity, share), None))

    return FlowLayout(next_node, source, sink, student_offset, node_to_lab, arcs)


def _extract_flow_pairs(graph_adjacency, layout: FlowLayout, num_students: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for i in range(num_students):
        for edge in graph_adjacency[layout.student_offset + i]:
            if edge.flow > 0 and edge.to in layout.node_to_lab:
                pairs.append((i, layout.node_to_lab[edge.to]))
                break
    return pairs


def _run_flow_algorithm(
    students: list[StudentInput],
    labs: list[LabInput],
    edges: list[EligibleEdge],
    algorithm: str,
    share: float | None,
) -> tuple[list[tuple[int, int]], MatchingResult]:
    layout = build_flow_layout(students, labs, edges, share)
    network = FlowNetwork(num_nodes=layout.num_nodes)
    for u, v, capacity, _edge in layout.arcs:
        network.add_edge(u, v, capacity)

    if algorithm == "EDMONDS_KARP":
        _, trace = edmonds_karp_max_flow(network, layout.source, layout.sink, "EDMONDS_KARP")
    elif algorithm == "FORD_FULKERSON":
        _, trace = ford_fulkerson_max_flow(network, layout.source, layout.sink)
    else:
        _, trace = dinic_max_flow(network, layout.source, layout.sink)

    return _extract_flow_pairs(network.graph, layout, len(students)), trace


def _run_min_cost_flow(
    students: list[StudentInput],
    labs: list[LabInput],
    edges: list[EligibleEdge],
    share: float | None,
) -> tuple[list[tuple[int, int]], MatchingResult]:
    """Cheapest maximum flow where a student->lab arc costs (best score - score): among all maximum
    matchings this picks one with the largest total match score."""
    layout = build_flow_layout(students, labs, edges, share)
    best_score = max(e.score for e in edges)
    network = CostFlowNetwork(layout.num_nodes)
    for u, v, capacity, edge in layout.arcs:
        cost = round((best_score - edge.score) * COST_SCALE) if edge is not None else 0
        network.add_edge(u, v, capacity, cost)
    _, _, trace = min_cost_max_flow(network, layout.source, layout.sink)
    return _extract_flow_pairs(network.graph, layout, len(students)), trace


def run_allocation(
    students: list[StudentInput],
    labs: list[LabInput],
    constraints: EngineConstraints,
    algorithm: str,
) -> EngineResult:
    if algorithm not in ALL_ALGORITHMS:
        raise AllocationConfigError(f"Unknown algorithm: {algorithm}")
    share = constraints.max_share_per_department
    if share is not None:
        if not 0 < share <= 1:
            raise AllocationConfigError("max_share_per_department must be in (0, 1]")
        if algorithm in MATCHING_ALGORITHMS:
            raise AllocationConfigError(
                f"{algorithm} solves plain bipartite matching, which cannot express a per-department "
                "fairness cap (department quotas nested inside each lab's capacity form a laminar "
                "constraint). Use a flow formulation - FORD_FULKERSON, EDMONDS_KARP, DINIC or "
                "MIN_COST_FLOW - which models each quota as a gadget node."
            )

    edges = build_eligible_edges(students, labs, constraints)

    if not students or not labs or not edges:
        assignments = [
            AssignmentResult(
                student_id=s.id,
                lab_id=None,
                preference_rank=None,
                match_score=0.0,
                eligibility_reason=_best_rejection_reason(s, labs, constraints),
                status="UNMATCHED",
            )
            for s in students
        ]
        empty_trace = MatchingResult(
            algorithm=algorithm,
            matched_pairs=[],
            unmatched_left=list(range(len(students))),
            unmatched_right=list(range(len(labs))),
            vertices=len(students) + len(labs),
            edges=0,
            iterations=0,
            augmenting_paths_found=0,
            execution_time_ms=0.0,
            time_complexity="N/A",
            space_complexity="N/A",
            steps=[],
        )
        return EngineResult(
            algorithm=algorithm,
            assignments=assignments,
            matched_count=0,
            unmatched_count=len(students),
            total_students=len(students),
            total_labs=len(labs),
            total_edges=0,
            preference_satisfaction=0.0,
            capacity_utilization=0.0,
            algorithm_trace=empty_trace,
        )

    edge_lookup = {(e.student_id, e.lab_id): e for e in edges}

    if algorithm in MATCHING_ALGORITHMS:
        matched_idx_pairs, trace, _ = _run_kuhn_or_hk(students, labs, edges, algorithm)
    elif algorithm in FLOW_ALGORITHMS:
        matched_idx_pairs, trace = _run_flow_algorithm(students, labs, edges, algorithm, share)
    else:
        matched_idx_pairs, trace = _run_min_cost_flow(students, labs, edges, share)
    students_with_edges = {e.student_id for e in edges}

    matched_student_ids: dict[int, int] = {}  # student_id -> lab_id
    for s_idx, l_idx in matched_idx_pairs:
        matched_student_ids[students[s_idx].id] = labs[l_idx].id

    assignments: list[AssignmentResult] = []
    preference_hits = 0
    total_score = 0.0
    for student in students:
        lab_id = matched_student_ids.get(student.id)
        if lab_id is not None:
            edge = edge_lookup[(student.id, lab_id)]
            assignments.append(
                AssignmentResult(
                    student_id=student.id,
                    lab_id=lab_id,
                    preference_rank=edge.preference_rank,
                    match_score=edge.score,
                    eligibility_reason=edge.reason,
                    status="MATCHED",
                )
            )
            total_score += edge.score
            if edge.preference_rank is not None:
                preference_hits += 1
        else:
            if student.id in students_with_edges:
                quota_clause = " or department quota" if share is not None else ""
                reason = (
                    f"eligible for one or more labs, but capacity{quota_clause} was exhausted: "
                    "no augmenting path reaches a free seat, so no larger matching includes this student"
                )
            else:
                reason = _best_rejection_reason(student, labs, constraints)
            assignments.append(
                AssignmentResult(
                    student_id=student.id,
                    lab_id=None,
                    preference_rank=None,
                    match_score=0.0,
                    eligibility_reason=reason,
                    status="UNMATCHED",
                )
            )

    matched_count = len(matched_student_ids)
    unmatched_count = len(students) - matched_count
    total_capacity = sum(l.capacity for l in labs)
    capacity_utilization = round(matched_count / total_capacity, 4) if total_capacity else 0.0
    preference_satisfaction = round(preference_hits / matched_count, 4) if matched_count else 0.0

    return EngineResult(
        algorithm=algorithm,
        assignments=assignments,
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        total_students=len(students),
        total_labs=len(labs),
        total_edges=len(edges),
        preference_satisfaction=preference_satisfaction,
        capacity_utilization=capacity_utilization,
        algorithm_trace=trace,
        total_score=round(total_score, 4),
    )
