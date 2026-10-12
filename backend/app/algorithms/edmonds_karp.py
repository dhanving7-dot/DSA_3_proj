"""Edmonds-Karp algorithm: Ford-Fulkerson using BFS to pick the *shortest*
(fewest-edges) augmenting path in the residual graph on every iteration.

Used here as the max-flow formulation of bipartite matching: source -> each
student (capacity 1) -> each eligible lab (capacity 1 per edge) -> sink
(capacity = lab capacity). The value of the maximum flow equals the size of
the maximum matching (integrality of flow guarantees an integral, 0/1
solution on the student edges).

Time complexity:  O(V * E^2)
Space complexity: O(V + E)
"""
from __future__ import annotations

import time
from collections import deque

from app.algorithms.graph import FlowNetwork
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent


def _bfs_find_path(network: FlowNetwork, source: int, sink: int) -> list[tuple[int, int]] | None:
    """Returns list of (node, edge_index_in_that_node's_adjacency) forming source->sink path, or None."""
    parent_edge: list[tuple[int, int] | None] = [None] * network.num_nodes
    visited = [False] * network.num_nodes
    visited[source] = True
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == sink:
            break
        for idx, edge in enumerate(network.graph[u]):
            if not visited[edge.to] and edge.residual > 0:
                visited[edge.to] = True
                parent_edge[edge.to] = (u, idx)
                queue.append(edge.to)
    if not visited[sink]:
        return None
    path: list[tuple[int, int]] = []
    node = sink
    while node != source:
        u, idx = parent_edge[node]
        path.append((u, idx))
        node = u
    path.reverse()
    return path


def edmonds_karp_max_flow(
    network: FlowNetwork, source: int, sink: int, algorithm_label: str = "EDMONDS_KARP"
) -> tuple[int, MatchingResult]:
    steps: list[AlgorithmStep] = []
    step_no = 0
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

    max_flow = 0
    start = time.perf_counter()

    while True:
        emit(StepEvent.SEARCHING_AUGMENTING_PATH, "BFS search for shortest augmenting path in residual graph.")
        path = _bfs_find_path(network, source, sink)
        if path is None:
            emit(StepEvent.NO_PATH_FOUND, "No augmenting path remains from source to sink.")
            break

        bottleneck = min(network.graph[u][idx].residual for u, idx in path)
        for u, idx in path:
            edge = network.graph[u][idx]
            edge.flow += bottleneck
            reverse = network.reverse_edge(u, edge)
            reverse.flow -= bottleneck

        max_flow += bottleneck
        augmenting_paths_found += 1
        emit(
            StepEvent.AUGMENTING_PATH_FOUND,
            f"Augmenting path #{augmenting_paths_found} found with bottleneck capacity {bottleneck}.",
            {"path": [u for u, _ in path] + [sink], "bottleneck": bottleneck},
        )
        emit(StepEvent.MATCH_UPDATED, f"Flow increased by {bottleneck}; total flow now {max_flow}.", {"flow": max_flow})

    elapsed_ms = (time.perf_counter() - start) * 1000

    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Maximum flow reached: {max_flow} units (== size of maximum matching).",
        {"max_flow": max_flow},
    )

    result = MatchingResult(
        algorithm=algorithm_label,
        matched_pairs=[],  # filled in by matching_engine after interpreting flow-carrying edges
        unmatched_left=[],
        unmatched_right=[],
        vertices=network.num_nodes,
        edges=network.num_edges,
        iterations=augmenting_paths_found,
        augmenting_paths_found=augmenting_paths_found,
        execution_time_ms=elapsed_ms,
        time_complexity="O(V * E^2)",
        space_complexity="O(V + E)",
        steps=steps,
    )
    return max_flow, result
