"""Dinic's algorithm: max flow via repeated blocking flows on a BFS level graph.

Each phase (1) runs a BFS from the source to assign levels, then (2) uses a
DFS with the classic "current arc" pointer optimisation to saturate a
blocking flow restricted to edges that advance exactly one level. There are
at most O(V) phases and each blocking flow costs O(V*E), giving the general
bound below - but on unit-capacity bipartite-matching networks (our case)
this specialises to O(E * sqrt(V)), matching Hopcroft-Karp exactly, which is
why the two are presented side-by-side in the algorithm playground.

Time complexity:  O(V^2 * E)  (O(E * sqrt(V)) on unit-capacity bipartite graphs)
Space complexity: O(V + E)
"""
from __future__ import annotations

import time
from collections import deque

from app.algorithms.graph import FlowNetwork
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent

INF = float("inf")


def dinic_max_flow(network: FlowNetwork, source: int, sink: int) -> tuple[int, MatchingResult]:
    steps: list[AlgorithmStep] = []
    step_no = 0
    phase_no = 0
    augmenting_paths_found = 0

    def emit(event: StepEvent, description: str, data: dict | None = None) -> None:
        nonlocal step_no
        step_no += 1
        steps.append(AlgorithmStep(step_no, event, description, data or {}))

    emit(
        StepEvent.GRAPH_CREATED,
        f"Built flow network with {network.num_nodes} nodes (source, students, labs, sink).",
        {"num_nodes": network.num_nodes, "num_edges": network.num_edges},
    )

    level = [-1] * network.num_nodes
    it = [0] * network.num_nodes

    def bfs_levels() -> bool:
        nonlocal level
        level = [-1] * network.num_nodes
        level[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for edge in network.graph[u]:
                if edge.residual > 0 and level[edge.to] == -1:
                    level[edge.to] = level[u] + 1
                    queue.append(edge.to)
        return level[sink] != -1

    def dfs_blocking_flow(u: int, pushed: float) -> float:
        if u == sink:
            return pushed
        while it[u] < len(network.graph[u]):
            edge = network.graph[u][it[u]]
            if level[edge.to] == level[u] + 1 and edge.residual > 0:
                bottleneck = dfs_blocking_flow(edge.to, min(pushed, edge.residual))
                if bottleneck > 0:
                    edge.flow += bottleneck
                    reverse = network.reverse_edge(u, edge)
                    reverse.flow -= bottleneck
                    return bottleneck
            it[u] += 1
        return 0

    max_flow = 0
    start = time.perf_counter()

    while bfs_levels():
        phase_no += 1
        it = [0] * network.num_nodes
        emit(
            StepEvent.PHASE_START,
            f"Phase {phase_no}: BFS level graph built (sink at level {level[sink]}).",
            {"phase": phase_no, "sink_level": level[sink]},
        )
        while True:
            emit(
                StepEvent.SEARCHING_AUGMENTING_PATH,
                f"Phase {phase_no}: DFS searching blocking-flow augmenting path.",
                {"phase": phase_no},
            )
            pushed = dfs_blocking_flow(source, INF)
            if pushed == 0:
                emit(StepEvent.NO_PATH_FOUND, f"Phase {phase_no}: blocking flow saturated, no more paths at this level.")
                break
            max_flow += pushed
            augmenting_paths_found += 1
            emit(
                StepEvent.AUGMENTING_PATH_FOUND,
                f"Phase {phase_no}: augmenting path #{augmenting_paths_found} pushed {pushed} unit(s) of flow.",
                {"phase": phase_no, "pushed": pushed},
            )
            emit(StepEvent.MATCH_UPDATED, f"Total flow now {max_flow}.", {"flow": max_flow})

    elapsed_ms = (time.perf_counter() - start) * 1000

    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Maximum flow reached after {phase_no} phases: {max_flow} units (== size of maximum matching).",
        {"max_flow": max_flow, "phases": phase_no},
    )

    result = MatchingResult(
        algorithm="DINIC",
        matched_pairs=[],
        unmatched_left=[],
        unmatched_right=[],
        vertices=network.num_nodes,
        edges=network.num_edges,
        iterations=augmenting_paths_found,
        augmenting_paths_found=augmenting_paths_found,
        execution_time_ms=elapsed_ms,
        time_complexity="O(V^2 * E), O(E*sqrt(V)) on unit-capacity bipartite graphs",
        space_complexity="O(V + E)",
        steps=steps,
    )
    return max_flow, result
