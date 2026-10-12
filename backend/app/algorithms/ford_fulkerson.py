"""Ford-Fulkerson method with DFS path selection - the generic form that
Edmonds-Karp (BFS) and Dinic (level graphs) refine.

Any augmenting path works; correctness follows from the max-flow min-cut
theorem (no augmenting path <=> the reachable set defines a cut of equal
capacity). With integer capacities each augmentation adds at least one unit,
so it terminates after at most |f*| augmentations - but unlike Edmonds-Karp
there is no bound independent of the capacities.

Time complexity:  O(E * |f*|)
Space complexity: O(V + E)
"""
from __future__ import annotations

import time

from app.algorithms.graph import FlowNetwork
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent


def _dfs_find_path(network: FlowNetwork, source: int, sink: int) -> tuple[list[tuple[int, int]] | None, int]:
    """Iterative DFS. Returns ((node, edge_index) path or None, nodes_visited)."""
    parent: list[tuple[int, int] | None] = [None] * network.num_nodes
    visited = [False] * network.num_nodes
    visited[source] = True
    stack = [source]
    explored = 0
    while stack:
        u = stack.pop()
        explored += 1
        if u == sink:
            break
        for idx, edge in enumerate(network.graph[u]):
            if not visited[edge.to] and edge.residual > 0:
                visited[edge.to] = True
                parent[edge.to] = (u, idx)
                stack.append(edge.to)
    if not visited[sink]:
        return None, explored
    path: list[tuple[int, int]] = []
    node = sink
    while node != source:
        u, idx = parent[node]
        path.append((u, idx))
        node = u
    path.reverse()
    return path, explored


def ford_fulkerson_max_flow(network: FlowNetwork, source: int, sink: int) -> tuple[int, MatchingResult]:
    steps: list[AlgorithmStep] = []
    step_no = 0
    augmenting_paths_found = 0
    explored_total = 0

    def emit(event: StepEvent, description: str, data: dict | None = None) -> None:
        nonlocal step_no
        step_no += 1
        steps.append(AlgorithmStep(step_no, event, description, data or {}))

    emit(
        StepEvent.GRAPH_CREATED,
        f"Built flow network with {network.num_nodes} nodes (source, students, labs, sink).",
        {"num_nodes": network.num_nodes, "num_edges": network.num_edges},
    )

    max_flow = 0
    start = time.perf_counter()
    while True:
        emit(StepEvent.SEARCHING_AUGMENTING_PATH, "DFS for any augmenting path in the residual graph.")
        path, explored = _dfs_find_path(network, source, sink)
        explored_total += explored
        if path is None:
            emit(StepEvent.NO_PATH_FOUND, "No augmenting path remains: the reachable set now defines a minimum cut.")
            break
        bottleneck = min(network.graph[u][idx].residual for u, idx in path)
        for u, idx in path:
            edge = network.graph[u][idx]
            edge.flow += bottleneck
            network.reverse_edge(u, edge).flow -= bottleneck
        max_flow += bottleneck
        augmenting_paths_found += 1
        emit(
            StepEvent.AUGMENTING_PATH_FOUND,
            f"Augmenting path #{augmenting_paths_found} ({len(path)} edges) pushed {bottleneck} unit(s).",
            {"path_length": len(path), "pushed": bottleneck},
        )
        emit(StepEvent.MATCH_UPDATED, f"Total flow now {max_flow}.", {"flow": max_flow})

    elapsed_ms = (time.perf_counter() - start) * 1000
    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Maximum flow reached: {max_flow} units (== size of maximum matching).",
        {"max_flow": max_flow},
    )
    result = MatchingResult(
        algorithm="FORD_FULKERSON",
        matched_pairs=[],
        unmatched_left=[],
        unmatched_right=[],
        vertices=network.num_nodes,
        edges=network.num_edges,
        iterations=explored_total,
        augmenting_paths_found=augmenting_paths_found,
        execution_time_ms=elapsed_ms,
        time_complexity="O(E * |f*|)",
        space_complexity="O(V + E)",
        steps=steps,
    )
    return max_flow, result
