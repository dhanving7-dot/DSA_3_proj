"""Hopcroft-Karp algorithm for Maximum Bipartite Matching.

Improves on Kuhn's algorithm by finding a *maximal set of vertex-disjoint
shortest augmenting paths* in each phase (BFS to compute layers + DFS
restricted to those layers), instead of one augmenting path at a time.

There are at most O(sqrt(V)) phases, and each phase costs O(E), giving:

Time complexity:  O(E * sqrt(V))
Space complexity: O(V + E)
"""
from __future__ import annotations

import time
from collections import deque

from app.algorithms.graph import BipartiteGraph
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent

INF = float("inf")
NIL = -1


def hopcroft_karp_max_matching(graph: BipartiteGraph) -> MatchingResult:
    match_left = [NIL] * graph.num_left
    match_right = [NIL] * graph.num_right
    dist = [0] * graph.num_left

    steps: list[AlgorithmStep] = []
    step_no = 0
    phase_no = 0
    augmenting_paths_found = 0
    bfs_dfs_ops = 0

    def emit(event: StepEvent, description: str, data: dict | None = None) -> None:
        nonlocal step_no
        step_no += 1
        steps.append(AlgorithmStep(step_no, event, description, data or {}))

    emit(
        StepEvent.GRAPH_CREATED,
        f"Built bipartite graph with {graph.num_left} students and {graph.num_right} lab slots.",
        {"num_left": graph.num_left, "num_right": graph.num_right, "num_edges": graph.num_edges},
    )

    def bfs() -> bool:
        nonlocal bfs_dfs_ops
        queue: deque[int] = deque()
        for u in range(graph.num_left):
            if match_left[u] == NIL:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = INF
        dist_nil = INF
        while queue:
            u = queue.popleft()
            bfs_dfs_ops += 1
            if dist[u] < dist_nil:
                for v in graph.adjacency[u]:
                    matched_u = match_right[v]
                    if matched_u == NIL:
                        dist_nil = dist[u] + 1
                    elif dist[matched_u] == INF:
                        dist[matched_u] = dist[u] + 1
                        queue.append(matched_u)
        return dist_nil != INF

    def dfs(u: int) -> bool:
        nonlocal bfs_dfs_ops
        bfs_dfs_ops += 1
        for v in graph.adjacency[u]:
            matched_u = match_right[v]
            if matched_u == NIL or (dist[matched_u] == dist[u] + 1 and dfs(matched_u)):
                match_right[v] = u
                match_left[u] = v
                return True
        dist[u] = INF
        return False

    start = time.perf_counter()

    while bfs():
        phase_no += 1
        emit(
            StepEvent.PHASE_START,
            f"Phase {phase_no}: BFS layering complete, searching vertex-disjoint shortest augmenting paths.",
            {"phase": phase_no},
        )
        for u in range(graph.num_left):
            if match_left[u] == NIL:
                emit(
                    StepEvent.SEARCHING_AUGMENTING_PATH,
                    f"Phase {phase_no}: DFS augmenting attempt from student #{u}.",
                    {"phase": phase_no, "left": u},
                )
                if dfs(u):
                    augmenting_paths_found += 1
                    emit(
                        StepEvent.MATCH_UPDATED,
                        f"Phase {phase_no}: augmenting path found, student #{u} -> lab-slot #{match_left[u]}.",
                        {"phase": phase_no, "left": u, "right": match_left[u]},
                    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    matched_pairs = [(u, v) for u, v in enumerate(match_left) if v != NIL]
    unmatched_left = [u for u, v in enumerate(match_left) if v == NIL]
    unmatched_right = [v for v, u in enumerate(match_right) if u == NIL]

    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Maximum matching reached after {phase_no} phases: {len(matched_pairs)} pairs matched.",
        {"match_size": len(matched_pairs), "phases": phase_no},
    )

    return MatchingResult(
        algorithm="HOPCROFT_KARP",
        matched_pairs=matched_pairs,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
        vertices=graph.num_vertices,
        edges=graph.num_edges,
        iterations=bfs_dfs_ops,
        augmenting_paths_found=augmenting_paths_found,
        execution_time_ms=elapsed_ms,
        time_complexity="O(E * sqrt(V))",
        space_complexity="O(V + E)",
        steps=steps,
    )
