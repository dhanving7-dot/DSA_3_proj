"""Concept Lab: run any hand-built algorithm on input of the user's choosing.

These endpoints never touch allocation data (except /dp/obst with
from_lab_data, which reads preference counts). They exist so each concept
can be explored interactively - tables, traces and side-by-side comparisons
come straight from the implementations in app.algorithms.
"""
from __future__ import annotations

import math
import random
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.algorithms import approximation, dp, parallel, randomized, strings
from app.algorithms.catalog import ATLAS, MODULES, REDUCTIONS
from app.algorithms.dinic import dinic_max_flow
from app.algorithms.edmonds_karp import edmonds_karp_max_flow
from app.algorithms.flow_analysis import konig_vertex_cover, min_cut, project_selection
from app.algorithms.graph import BipartiteGraph, FlowNetwork
from app.algorithms.hopcroft_karp import hopcroft_karp_max_matching
from app.algorithms.min_cost_flow import CostFlowNetwork, min_cost_max_flow
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.laboratory import Laboratory
from app.models.student import StudentPreference
from app.models.user import User
from app.schemas.concepts import (
    AhoCorasickRequest,
    AlignmentRequest,
    EditDistanceRequest,
    HamiltonianRequest,
    HashingRequest,
    KnapsackRequest,
    MatrixChainRequest,
    MinCostRequest,
    OptimalBSTRequest,
    PatternSearchRequest,
    PrimalityRequest,
    ProjectSelectionRequest,
    QuicksortRequest,
    RandomBipartiteRequest,
    ReservoirRequest,
    ScanRequest,
    SetCoverRequest,
    SuffixArrayRequest,
    TSPRequest,
    TreeRequest,
    VertexCoverRequest,
)

router = APIRouter(prefix="/concepts", tags=["concepts"], dependencies=[Depends(get_current_user)])


@router.get("/atlas")
def atlas():
    return {"modules": MODULES, "algorithms": ATLAS, "reductions": REDUCTIONS}


# --------------------------------------------------------------------------- strings


@router.post("/strings/search")
def pattern_search(payload: PatternSearchRequest):
    runs = [
        strings.naive_search(payload.text, payload.pattern),
        strings.kmp_search(payload.text, payload.pattern),
        strings.z_search(payload.text, payload.pattern),
        strings.rabin_karp(payload.text, payload.pattern, payload.seed),
    ]
    start = time.perf_counter()
    sa = strings.suffix_array(payload.text)
    build_ms = (time.perf_counter() - start) * 1000
    sa_run = strings.suffix_array_search(payload.text, payload.pattern, sa)
    sa_run.extra["build_time_ms"] = build_ms
    runs.append(sa_run)

    reference = runs[0].positions
    return {
        "text_length": len(payload.text),
        "pattern_length": len(payload.pattern),
        "positions": reference,
        "all_agree": all(r.positions == reference for r in runs),
        "naive_worst_case": (len(payload.text) - len(payload.pattern) + 1) * len(payload.pattern)
        if len(payload.pattern) <= len(payload.text)
        else 0,
        "runs": [r.to_dict() for r in runs],
    }


@router.post("/strings/aho-corasick")
def aho_corasick(payload: AhoCorasickRequest):
    start = time.perf_counter()
    automaton = strings.AhoCorasick(payload.patterns)
    matches = automaton.search(payload.text)
    elapsed_ms = (time.perf_counter() - start) * 1000
    # one KMP per pattern, to show what the single automaton pass replaces
    separate = [strings.kmp_search(payload.text, p) for p in payload.patterns]
    return {
        "patterns": payload.patterns,
        "matches": [{"position": pos, "pattern": payload.patterns[idx]} for pos, idx in matches],
        "trie_nodes": automaton.num_nodes,
        "nodes": automaton.describe(),
        "execution_time_ms": elapsed_ms,
        "separate_kmp_comparisons": sum(r.comparisons for r in separate),
        "separate_kmp_occurrences": sum(len(r.positions) for r in separate),
    }


@router.post("/strings/suffix-array")
def suffix_structures(payload: SuffixArrayRequest):
    return strings.suffix_structure_summary(payload.text)


# --------------------------------------------------------------------------- dynamic programming


@router.post("/dp/edit-distance")
def edit_distance(payload: EditDistanceRequest):
    return dp.edit_distance(
        payload.a, payload.b, payload.variant, payload.insert_cost, payload.delete_cost, payload.substitute_cost
    )


@router.post("/dp/alignment")
def alignment(payload: AlignmentRequest):
    if payload.mode == "GLOBAL":
        return dp.needleman_wunsch(payload.a, payload.b, payload.match, payload.mismatch, payload.gap)
    return dp.smith_waterman(payload.a, payload.b, payload.match, payload.mismatch, payload.gap)


@router.post("/dp/matrix-chain")
def matrix_chain(payload: MatrixChainRequest):
    return dp.matrix_chain_order(payload.dims)


@router.post("/dp/obst")
def obst(payload: OptimalBSTRequest, db: Session = Depends(get_db)):
    if payload.from_lab_data:
        counts = dict(db.query(StudentPreference.lab_id, func.count(StudentPreference.id)).group_by(StudentPreference.lab_id).all())
        labs = sorted(db.query(Laboratory).all(), key=lambda lab: lab.code)[:15]
        keys = [lab.code for lab in labs]
        freqs = [counts.get(lab.id, 0) for lab in labs]
    else:
        if len(payload.keys) != len(payload.freqs):
            raise HTTPException(status_code=422, detail="keys and freqs must have the same length")
        if len(set(payload.keys)) != len(payload.keys):
            raise HTTPException(status_code=422, detail="keys must be distinct")
        if any(f < 0 for f in payload.freqs):
            raise HTTPException(status_code=422, detail="frequencies must be non-negative")
        pairs = sorted(zip(payload.keys, payload.freqs))  # a BST needs its keys in sorted order
        keys = [k for k, _ in pairs]
        freqs = [f for _, f in pairs]
    if not keys:
        raise HTTPException(status_code=422, detail="at least one key is required")
    cubic = dp.optimal_bst(keys, freqs, knuth=False)
    knuth = dp.optimal_bst(keys, freqs, knuth=True)
    # a balanced tree for contrast: cost of the median-split BST that ignores frequencies
    def balanced_cost(lo: int, hi: int, depth: int) -> int:
        if lo > hi:
            return 0
        mid = (lo + hi) // 2
        return freqs[mid] * depth + balanced_cost(lo, mid - 1, depth + 1) + balanced_cost(mid + 1, hi, depth + 1)

    return {
        "keys": keys,
        "freqs": freqs,
        "cost": knuth["cost"],
        "tree": knuth["tree"],
        "cubic_root_evaluations": cubic["root_evaluations"],
        "knuth_root_evaluations": knuth["root_evaluations"],
        "costs_agree": cubic["cost"] == knuth["cost"],
        "balanced_tree_cost": balanced_cost(0, len(keys) - 1, 1),
    }


def _random_points(n: int, seed: int | None) -> tuple[list[list[int]], list[list[float]]]:
    rng = random.Random(seed)
    points = [[rng.randint(0, 100), rng.randint(0, 100)] for _ in range(n)]
    dist = [[round(math.dist(p, q), 2) for q in points] for p in points]
    return points, dist


@router.post("/dp/tsp")
def tsp(payload: TSPRequest):
    points, dist = _random_points(payload.num_cities, payload.seed)
    start = time.perf_counter()
    exact = dp.held_karp_tsp(dist)
    exact_ms = (time.perf_counter() - start) * 1000
    nn = approximation.tsp_nearest_neighbour(dist)
    mst = approximation.tsp_mst_2approx(dist)
    opt = exact["cost"]
    return {
        "points": points,
        "held_karp": {**exact, "cost": round(opt, 2), "time_ms": exact_ms},
        "nearest_neighbour": {**nn, "cost": round(nn["cost"], 2), "ratio": round(nn["cost"] / opt, 4) if opt else 1.0},
        "mst_2approx": {
            **mst,
            "cost": round(mst["cost"], 2),
            "mst_weight": round(mst["mst_weight"], 2),
            "ratio": round(mst["cost"] / opt, 4) if opt else 1.0,
        },
    }


@router.post("/dp/hamiltonian")
def hamiltonian(payload: HamiltonianRequest):
    rng = random.Random(payload.seed)
    edges = [(u, v) for u in range(payload.num_vertices) for v in range(u + 1, payload.num_vertices) if rng.random() < payload.edge_probability]
    adjacency: list[list[int]] = [[] for _ in range(payload.num_vertices)]
    for u, v in edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    start = time.perf_counter()
    result = dp.hamiltonian_path(payload.num_vertices, adjacency)
    return {"num_vertices": payload.num_vertices, "edges": edges, **result, "states": 1 << payload.num_vertices, "time_ms": (time.perf_counter() - start) * 1000}


@router.post("/dp/tree")
def tree(payload: TreeRequest):
    rng = random.Random(payload.seed)
    edges = [(rng.randrange(v), v) for v in range(1, payload.num_nodes)]  # random recursive tree
    result = dp.tree_dp(payload.num_nodes, edges)
    oracle_ok = all(
        sum(dp.bfs_distances(payload.num_nodes, edges, v)) == result["sum_of_distances"][v] for v in range(payload.num_nodes)
    )
    return {"num_nodes": payload.num_nodes, "edges": edges, **result, "rerooting_matches_bfs": oracle_ok}


# --------------------------------------------------------------------------- flow


def _random_bipartite(num_left: int, num_right: int, p: float, seed: int | None) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    return [(u, v) for u in range(num_left) for v in range(num_right) if rng.random() < p]


@router.post("/flow/min-cut")
def flow_min_cut(payload: RandomBipartiteRequest):
    edges = _random_bipartite(payload.num_left, payload.num_right, payload.edge_probability, payload.seed)
    source, left0 = 0, 1
    right0 = left0 + payload.num_left
    sink = right0 + payload.num_right
    network = FlowNetwork(sink + 1)
    for u in range(payload.num_left):
        network.add_edge(source, left0 + u, 1)
    for v in range(payload.num_right):
        network.add_edge(right0 + v, sink, 1)
    for u, v in edges:
        network.add_edge(left0 + u, right0 + v, 1)
    max_flow, _ = dinic_max_flow(network, source, sink)
    cut = min_cut(network, source)

    def label(node: int) -> str:
        if node == source:
            return "s"
        if node == sink:
            return "t"
        if node < right0:
            return f"S{node - left0}"
        return f"L{node - right0}"

    graph = BipartiteGraph(payload.num_left, payload.num_right)
    for u, v in edges:
        graph.add_edge(u, v)
    matching = hopcroft_karp_max_matching(graph)
    cover = konig_vertex_cover(graph, matching.matched_pairs)
    approx = approximation.vertex_cover_2approx([(u, payload.num_left + v) for u, v in edges])
    return {
        "num_left": payload.num_left,
        "num_right": payload.num_right,
        "edges": edges,
        "max_flow": max_flow,
        "cut_capacity": cut["cut_capacity"],
        "cut_edges": [{"from": label(u), "to": label(v), "capacity": c} for u, v, c in cut["cut_edges"]],
        "source_side": [label(v) for v in cut["source_side"]],
        "matching": matching.matched_pairs,
        "konig_cover": {"students": cover["left"], "labs": cover["right"], "size": cover["size"]},
        "approx_cover_size": approx["size"],
    }


@router.post("/flow/min-cost")
def flow_min_cost(payload: MinCostRequest):
    rng = random.Random(payload.seed)
    edges = _random_bipartite(payload.num_left, payload.num_right, payload.edge_probability, payload.seed)
    scores = {e: rng.randint(1, 9) for e in edges}  # higher = better fit
    source, left0 = 0, 1
    right0 = left0 + payload.num_left
    sink = right0 + payload.num_right

    cost_net = CostFlowNetwork(sink + 1)
    plain_net = FlowNetwork(sink + 1)
    for u in range(payload.num_left):
        cost_net.add_edge(source, left0 + u, 1, 0)
        plain_net.add_edge(source, left0 + u, 1)
    for v in range(payload.num_right):
        cost_net.add_edge(right0 + v, sink, 1, 0)
        plain_net.add_edge(right0 + v, sink, 1)
    for (u, v) in edges:
        cost_net.add_edge(left0 + u, right0 + v, 1, 10 - scores[(u, v)])  # cost = 10 - score >= 1
        plain_net.add_edge(left0 + u, right0 + v, 1)

    flow, cost, trace = min_cost_max_flow(cost_net, source, sink)
    plain_flow, _ = edmonds_karp_max_flow(plain_net, source, sink)

    def pairs(net) -> list[tuple[int, int]]:
        out = []
        for u in range(payload.num_left):
            for e in net.graph[left0 + u]:
                if right0 <= e.to < sink and e.flow > 0:
                    out.append((u, e.to - right0))
        return out

    mcmf_pairs, ek_pairs = pairs(cost_net), pairs(plain_net)
    matrix = [[scores.get((u, v)) for v in range(payload.num_right)] for u in range(payload.num_left)]
    oracle = dp.bitmask_assignment(matrix)
    return {
        "num_left": payload.num_left,
        "num_right": payload.num_right,
        "edges": [{"student": u, "lab": v, "score": scores[(u, v)]} for u, v in edges],
        "min_cost_flow": {
            "flow": flow,
            "total_score": sum(scores[p] for p in mcmf_pairs),
            "pairs": mcmf_pairs,
            "augmentations": trace.augmenting_paths_found,
            "steps": [s.to_dict() for s in trace.steps],
        },
        "edmonds_karp": {"flow": plain_flow, "total_score": sum(scores[p] for p in ek_pairs), "pairs": ek_pairs},
        "bitmask_dp_oracle": {"matched": oracle["matched"], "total_score": oracle["total_score"]},
        "optimal_verified": oracle["matched"] == flow and oracle["total_score"] == sum(scores[p] for p in mcmf_pairs),
        "total_cost": cost,
    }


@router.post("/flow/project-selection")
def flow_project_selection(payload: ProjectSelectionRequest):
    for p, t in payload.requires:
        if not (0 <= p < len(payload.profits) and 0 <= t < len(payload.costs)):
            raise HTTPException(status_code=422, detail=f"requirement ({p}, {t}) refers to a missing project or tool")
    result = project_selection(payload.profits, payload.costs, payload.requires)
    # brute force over project subsets as an oracle (projects <= 10)
    best = 0
    n = len(payload.profits)
    for mask in range(1 << n):
        tools = {t for p, t in payload.requires if (mask >> p) & 1}
        value = sum(payload.profits[p] for p in range(n) if (mask >> p) & 1) - sum(payload.costs[t] for t in tools)
        best = max(best, value)
    return {**result, "bruteforce_best": best, "verified": best == result["max_profit"]}


# --------------------------------------------------------------------------- NP & approximation


@router.post("/np/vertex-cover")
def np_vertex_cover(payload: VertexCoverRequest):
    rng = random.Random(payload.seed)
    edges = [(u, v) for u in range(payload.num_vertices) for v in range(u + 1, payload.num_vertices) if rng.random() < payload.edge_probability]
    approx = approximation.vertex_cover_2approx(edges)
    start = time.perf_counter()
    exact = approximation.vertex_cover_exact(payload.num_vertices, edges)
    exact_ms = (time.perf_counter() - start) * 1000
    return {
        "num_vertices": payload.num_vertices,
        "edges": edges,
        "approx": approx,
        "exact": {**exact, "time_ms": exact_ms},
        "ratio": round(approx["size"] / exact["size"], 4) if exact["size"] else 1.0,
    }


@router.post("/np/set-cover")
def np_set_cover(payload: SetCoverRequest):
    rng = random.Random(payload.seed)
    sets = []
    for _ in range(payload.num_sets):
        size = rng.randint(1, max(1, payload.universe_size // 3))
        members = rng.sample(range(payload.universe_size), size)
        sets.append(sum(1 << m for m in members))
    universe = 0
    for s in sets:
        universe |= s
    greedy = approximation.greedy_set_cover(universe, sets)
    exact = approximation.exact_set_cover(universe, sets)
    covered = bin(universe).count("1")

    def members(mask: int) -> list[int]:
        return [i for i in range(payload.universe_size) if (mask >> i) & 1]

    return {
        "universe_size": payload.universe_size,
        "coverable_elements": covered,
        "sets": [members(s) for s in sets],
        "greedy": greedy,
        "exact": exact,
        "ratio": round(len(greedy["chosen"]) / exact["size"], 4) if exact["size"] else 1.0,
        "harmonic_bound": round(approximation.harmonic(max(covered, 1)), 4),
    }


@router.post("/np/knapsack")
def np_knapsack(payload: KnapsackRequest):
    if len(payload.weights) != len(payload.values):
        raise HTTPException(status_code=422, detail="weights and values must have the same length")
    return approximation.knapsack_compare(payload.weights, payload.values, payload.capacity, payload.epsilon)


# --------------------------------------------------------------------------- randomised & parallel


def _korselt_carmichael(n: int) -> bool | None:
    """Korselt: composite, square-free, and (p - 1) | (n - 1) for every prime p | n. None if n is too big to factor."""
    if n > 10**12:
        return None
    if n < 3:
        return False
    factors = []
    m, p = n, 2
    while p * p <= m:
        if m % p == 0:
            count = 0
            while m % p == 0:
                m //= p
                count += 1
            if count > 1:
                return False
            factors.append(p)
        p += 1
    if m > 1:
        factors.append(m)
    if len(factors) < 2:
        return False
    return all((n - 1) % (q - 1) == 0 for q in factors)


@router.post("/random/primality")
def random_primality(payload: PrimalityRequest):
    n = int(payload.n)
    rng = random.Random(payload.seed)
    mr, mr_trace = randomized.miller_rabin(n, payload.rounds, rng, trace=True)
    fermat = randomized.fermat_test(n, [2, 3, 5, 7, 11, 13])
    truth = randomized.trial_division(n)
    return {
        "n": str(n),
        "miller_rabin": {"probably_prime": mr, "rounds": [{**r, "chain": [str(x) for x in r["chain"]], "a": None if r["a"] is None else str(r["a"])} for r in mr_trace]},
        "error_bound": f"4^-{payload.rounds}" if mr else "0 (a witness proves compositeness)",
        "fermat": {**fermat, "n": str(n), "witnesses": [{**w, "a_pow_n_minus_1": str(w["a_pow_n_minus_1"])} for w in fermat["witnesses"]]},
        "deterministic": randomized.is_prime_deterministic(n),
        # the fixed witness set {2..41} is proven exact below this bound; above it the answer is still Monte Carlo
        "deterministic_is_exact": n < 3_317_044_064_679_887_385_961_981,
        "trial_division": truth,
        "carmichael": _korselt_carmichael(n),
        "known_carmichael_numbers": list(randomized.KNOWN_CARMICHAEL[:8]),
    }


@router.post("/random/quicksort")
def random_quicksort(payload: QuicksortRequest):
    rng = random.Random(payload.seed)
    n = payload.n
    if payload.input_kind == "sorted":
        data = list(range(n))
    elif payload.input_kind == "reversed":
        data = list(range(n, 0, -1))
    elif payload.input_kind == "few_unique":
        data = [rng.randint(0, 4) for _ in range(n)]
    else:
        data = [rng.randint(0, 10 * n) for _ in range(n)]

    det_out, det_cmp, det_depth = randomized.deterministic_quicksort(data)
    expected_sorted = sorted(data)
    sorted_correctly = det_out == expected_sorted
    rand_runs = []
    for t in range(payload.trials):
        out, cmp, depth = randomized.randomized_quicksort(data, random.Random((payload.seed or 0) * 1000 + t))
        sorted_correctly = sorted_correctly and out == expected_sorted
        rand_runs.append({"comparisons": cmp, "max_depth": depth})
    mean = sum(r["comparisons"] for r in rand_runs) / len(rand_runs)
    return {
        "n": n,
        "input_kind": payload.input_kind,
        "deterministic": {"comparisons": det_cmp, "max_depth": det_depth},
        "randomized": {"runs": rand_runs, "mean_comparisons": round(mean, 1)},
        "n_log2_n": round(n * math.log2(n), 1) if n > 1 else 0,
        "expected_randomized": round(2 * n * math.log(n), 1) if n > 1 else 0,  # ~ 2 n ln n
        "worst_case": n * (n - 1) // 2,
        "sorted_correctly": sorted_correctly,
    }


@router.post("/random/reservoir")
def random_reservoir(payload: ReservoirRequest):
    rng = random.Random(payload.seed)
    k = min(payload.k, payload.stream_size)
    counts = [0] * payload.stream_size
    for _ in range(payload.trials):
        sample, _ = randomized.reservoir_sample(range(payload.stream_size), k, rng)
        for item in sample:
            counts[item] += 1
    expected = payload.trials * k / payload.stream_size
    chi_square = sum((c - expected) ** 2 / expected for c in counts) if expected else 0.0
    one_sample, _ = randomized.reservoir_sample(range(payload.stream_size), k, random.Random(payload.seed))
    return {
        "stream_size": payload.stream_size,
        "k": k,
        "trials": payload.trials,
        "expected_per_item": round(expected, 3),
        "counts": counts,
        "min_count": min(counts),
        "max_count": max(counts),
        "chi_square": round(chi_square, 3),
        "degrees_of_freedom": payload.stream_size - 1,
        "example_sample": sorted(one_sample),
    }


@router.post("/random/hashing")
def random_hashing(payload: HashingRequest):
    rng = random.Random(payload.seed)
    m = payload.table_size
    # adversarial keys for h(x) = x mod m: every key is a multiple of m
    keys = [m * (i + 1) for i in range(payload.num_keys)]
    universal = randomized.UniversalHash.random(m, max(keys), rng)

    def load(hash_fn) -> list[int]:
        buckets = [0] * m
        for key in keys:
            buckets[hash_fn(key)] += 1
        return buckets

    def collisions(buckets: list[int]) -> int:
        return sum(b * (b - 1) // 2 for b in buckets)

    fixed = load(lambda x: x % m)
    uni = load(universal)
    pairs = payload.num_keys * (payload.num_keys - 1) // 2
    return {
        "keys": payload.num_keys,
        "table_size": m,
        "key_pattern": f"multiples of {m}",
        "universal_params": {"p": universal.p, "a": universal.a, "b": universal.b},
        "fixed_mod": {"max_bucket": max(fixed), "colliding_pairs": collisions(fixed), "non_empty_buckets": sum(1 for b in fixed if b)},
        "universal": {"max_bucket": max(uni), "colliding_pairs": collisions(uni), "non_empty_buckets": sum(1 for b in uni if b), "buckets": uni},
        "expected_colliding_pairs_bound": round(pairs / m, 1),
    }


@router.post("/parallel/scan")
def parallel_scan(payload: ScanRequest):
    scan = parallel.blelloch_exclusive_scan(payload.values)
    reduce = parallel.parallel_reduce(payload.values)
    return {
        "values": payload.values,
        "scan": scan.to_dict(payload.processors),
        "reduce": reduce.to_dict(payload.processors),
        "sequential_scan": parallel.sequential_exclusive_scan(payload.values),
        "scan_correct": scan.result == parallel.sequential_exclusive_scan(payload.values),
    }
