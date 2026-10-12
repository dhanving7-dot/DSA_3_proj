import itertools
import random
from collections import Counter

import pytest

from app.algorithms.dinic import dinic_max_flow
from app.algorithms.dp import bitmask_assignment
from app.algorithms.edmonds_karp import edmonds_karp_max_flow
from app.algorithms.flow_analysis import konig_vertex_cover, min_cut, project_selection
from app.algorithms.ford_fulkerson import ford_fulkerson_max_flow
from app.algorithms.graph import BipartiteGraph, FlowNetwork
from app.algorithms.hopcroft_karp import hopcroft_karp_max_matching
from app.algorithms.heap import MinHeap
from app.algorithms.matching_engine import (
    AllocationConfigError,
    EngineConstraints,
    LabInput,
    StudentInput,
    department_quota,
    run_allocation,
)
from app.algorithms.min_cost_flow import CostFlowNetwork, min_cost_max_flow


def random_network(rng, n, density=0.3, max_cap=9):
    arcs = [(u, v, rng.randint(1, max_cap)) for u in range(n) for v in range(n) if u != v and rng.random() < density]
    return arcs


def build(n, arcs):
    net = FlowNetwork(n)
    for u, v, c in arcs:
        net.add_edge(u, v, c)
    return net


def test_heap_pops_in_sorted_order():
    rng = random.Random(1)
    heap = MinHeap()
    values = [rng.randint(-100, 100) for _ in range(500)]
    for i, v in enumerate(values):
        heap.push(v, i)
    popped = [heap.pop()[0] for _ in range(len(values))]
    assert popped == sorted(values)
    with pytest.raises(IndexError):
        heap.pop()


def test_ford_fulkerson_and_min_cut_agree_with_dinic_on_general_networks():
    rng = random.Random(2)
    for _ in range(40):
        n = rng.randint(2, 9)
        arcs = random_network(rng, n)
        ff_net, dinic_net, ek_net = build(n, arcs), build(n, arcs), build(n, arcs)
        ff, _ = ford_fulkerson_max_flow(ff_net, 0, n - 1)
        dinic, _ = dinic_max_flow(dinic_net, 0, n - 1)
        ek, _ = edmonds_karp_max_flow(ek_net, 0, n - 1)
        assert ff == dinic == ek
        cut = min_cut(dinic_net, 0)
        assert cut["cut_capacity"] == dinic  # max-flow min-cut theorem
        assert 0 in cut["source_side"] and (n - 1) not in cut["source_side"]
        # brute-force minimum s-t cut over every partition
        best = min(
            sum(c for u, v, c in arcs if (mask >> u) & 1 and not (mask >> v) & 1)
            for mask in range(1 << n)
            if mask & 1 and not (mask >> (n - 1)) & 1
        )
        assert best == dinic


def test_konig_cover_has_matching_size_and_covers_every_edge():
    rng = random.Random(3)
    for _ in range(80):
        nl, nr = rng.randint(1, 8), rng.randint(1, 8)
        edges = [(u, v) for u in range(nl) for v in range(nr) if rng.random() < 0.35]
        g = BipartiteGraph(nl, nr)
        for u, v in edges:
            g.add_edge(u, v)
        matching = hopcroft_karp_max_matching(g)
        cover = konig_vertex_cover(g, matching.matched_pairs)
        assert cover["size"] == matching.match_size
        left, right = set(cover["left"]), set(cover["right"])
        assert all(u in left or v in right for u, v in edges)


def test_min_cost_flow_is_maximum_and_optimal():
    rng = random.Random(4)
    for _ in range(60):
        nl, nr = rng.randint(1, 6), rng.randint(1, 6)
        scores = [[rng.randint(1, 9) if rng.random() < 0.5 else None for _ in range(nr)] for _ in range(nl)]
        s, t = 0, 1 + nl + nr
        net = CostFlowNetwork(t + 1)
        for u in range(nl):
            net.add_edge(s, 1 + u, 1, 0)
        for v in range(nr):
            net.add_edge(1 + nl + v, t, 1, 0)
        for u in range(nl):
            for v in range(nr):
                if scores[u][v] is not None:
                    net.add_edge(1 + u, 1 + nl + v, 1, 10 - scores[u][v])
        flow, cost, _ = min_cost_max_flow(net, s, t)
        oracle = bitmask_assignment(scores)
        assert flow == oracle["matched"]
        assert 10 * flow - cost == oracle["total_score"]


def test_min_cost_flow_rejects_negative_costs():
    with pytest.raises(ValueError):
        CostFlowNetwork(2).add_edge(0, 1, 1, -1)


def test_project_selection_matches_brute_force():
    rng = random.Random(5)
    for _ in range(60):
        p, t = rng.randint(1, 6), rng.randint(1, 6)
        profits = [rng.randint(0, 20) for _ in range(p)]
        costs = [rng.randint(0, 20) for _ in range(t)]
        requires = [(i, j) for i in range(p) for j in range(t) if rng.random() < 0.3]
        best = 0
        for mask in range(1 << p):
            tools = {j for i, j in requires if (mask >> i) & 1}
            best = max(best, sum(profits[i] for i in range(p) if (mask >> i) & 1) - sum(costs[j] for j in tools))
        result = project_selection(profits, costs, requires)
        assert result["max_profit"] == best
        chosen = set(result["projects"])
        assert all(j in result["tools"] for i, j in requires if i in chosen)


# --------------------------------------------------------------------------- engine integration


def student(i, dept="CSE", prefs=None, priority=0.5):
    return StudentInput(id=i, department=dept, year=2, cgpa=8.0, priority_score=priority, skills={}, preferences=prefs or {})


def lab(i, cap, dept="CSE"):
    return LabInput(id=i, department=dept, capacity=cap, is_active=True, required_skills=[])


ALL = ["KUHN", "HOPCROFT_KARP", "FORD_FULKERSON", "EDMONDS_KARP", "DINIC", "MIN_COST_FLOW"]


def random_instance(rng):
    labs = [lab(100 + j, rng.randint(0, 3), rng.choice(["CSE", "ECE"])) for j in range(rng.randint(1, 4))]
    students = []
    for i in range(rng.randint(1, 9)):
        ranked = rng.sample([l.id for l in labs], rng.randint(0, len(labs)))
        students.append(student(i + 1, rng.choice(["CSE", "ECE", "MECH"]), {lid: r + 1 for r, lid in enumerate(ranked)}, rng.random()))
    constraints = EngineConstraints(require_preference=rng.random() < 0.5)
    return students, labs, constraints


def test_all_six_algorithms_agree_on_matching_size_and_min_cost_flow_maximises_score():
    rng = random.Random(6)
    for _ in range(80):
        students, labs, constraints = random_instance(rng)
        results = {a: run_allocation(students, labs, constraints, a) for a in ALL}
        sizes = {r.matched_count for r in results.values()}
        assert len(sizes) == 1
        best = results["MIN_COST_FLOW"].total_score
        assert all(best >= r.total_score - 1e-9 for r in results.values())
        for r in results.values():  # capacities are respected
            per_lab = Counter(a.lab_id for a in r.assignments if a.status == "MATCHED")
            assert all(per_lab[l.id] <= l.capacity for l in labs)


def test_min_cost_flow_engine_matches_bitmask_oracle():
    rng = random.Random(7)
    for _ in range(40):
        students, labs, constraints = random_instance(rng)
        result = run_allocation(students, labs, constraints, "MIN_COST_FLOW")
        # oracle: expand labs into seats and run exact bitmask DP on the engine's own edge scores
        from app.algorithms.matching_engine import build_eligible_edges

        edges = {(e.student_id, e.lab_id): e.score for e in build_eligible_edges(students, labs, constraints)}
        seats = [l.id for l in labs for _ in range(l.capacity)]
        if len(seats) > 12:
            continue
        matrix = [[edges.get((s.id, lid)) for lid in seats] for s in students]
        oracle = bitmask_assignment(matrix) if seats else {"matched": 0, "total_score": 0}
        assert result.matched_count == oracle["matched"]
        assert result.total_score == pytest.approx(oracle["total_score"], abs=1e-6)


@pytest.mark.parametrize("algorithm", ["FORD_FULKERSON", "EDMONDS_KARP", "DINIC", "MIN_COST_FLOW"])
def test_fairness_cap_is_enforced_by_flow_algorithms(algorithm):
    labs = [lab(1, 10)]
    students = [student(i, "CSE" if i <= 8 else "ECE", {1: 1}) for i in range(1, 11)]
    constraints = EngineConstraints(max_share_per_department=0.4)
    result = run_allocation(students, labs, constraints, algorithm)
    dept = {s.id: s.department for s in students}
    per_dept = Counter(dept[a.student_id] for a in result.assignments if a.status == "MATCHED")
    assert per_dept["CSE"] == 4  # quota = floor(0.4 * 10)
    assert per_dept["ECE"] == 2
    unmatched_reasons = {a.eligibility_reason for a in result.assignments if a.status == "UNMATCHED"}
    assert all("department quota" in r for r in unmatched_reasons)


@pytest.mark.parametrize("algorithm", ["KUHN", "HOPCROFT_KARP"])
def test_fairness_cap_is_rejected_by_plain_matching(algorithm):
    with pytest.raises(AllocationConfigError):
        run_allocation([student(1)], [lab(1, 1)], EngineConstraints(max_share_per_department=0.5), algorithm)


def test_fairness_cap_property_on_random_instances():
    rng = random.Random(8)
    for _ in range(60):
        students, labs, constraints = random_instance(rng)
        constraints.max_share_per_department = rng.choice([0.3, 0.5, 0.8])
        dept = {s.id: s.department for s in students}
        sizes = set()
        for algorithm in ["FORD_FULKERSON", "EDMONDS_KARP", "DINIC", "MIN_COST_FLOW"]:
            result = run_allocation(students, labs, constraints, algorithm)
            sizes.add(result.matched_count)
            counts = Counter((a.lab_id, dept[a.student_id]) for a in result.assignments if a.status == "MATCHED")
            caps = {l.id: l.capacity for l in labs}
            for (lab_id, _), c in counts.items():
                assert c <= department_quota(caps[lab_id], constraints.max_share_per_department)
        assert len(sizes) == 1


def test_unknown_algorithm_and_bad_share_raise_config_errors():
    with pytest.raises(AllocationConfigError):
        run_allocation([student(1)], [lab(1, 1)], EngineConstraints(), "SIMPLEX")
    with pytest.raises(AllocationConfigError):
        run_allocation([student(1)], [lab(1, 1)], EngineConstraints(max_share_per_department=1.5), "DINIC")
