"""Kuhn's algorithm for Maximum Bipartite Matching.
For every left vertex (student) we attempt to find an augmenting path to an
unmatched right vertex (lab slot) via DFS, following unmatched edges out and
matched edges back ("alternating path"). If such a path exists we flip every
edge along it, growing the matching by exactly one pair.

Repeating this for every left vertex once yields a maximum matching.

Time complexity:  O(V * E)   (V = |L|+|R| vertices, one DFS of O(E) per left vertex)
Space complexity: O(V + E)
"""
from __future__ import annotations

import time

from app.algorithms.graph import BipartiteGraph
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent


def kuhn_max_matching(graph: BipartiteGraph) -> MatchingResult:
    match_right: list[int] = [-1] * graph.num_right
    match_left: list[int] = [-1] * graph.num_left

    steps: list[AlgorithmStep] = []
    step_no = 0
    augmenting_paths_found = 0
    dfs_calls = 0

    def emit(event: StepEvent, description: str, data: dict | None = None) -> None:
        nonlocal step_no
        step_no += 1
        steps.append(AlgorithmStep(step_no, event, description, data or {}))

    emit(
        StepEvent.GRAPH_CREATED,
        f"Built bipartite graph with {graph.num_left} students and {graph.num_right} lab slots.",
        {"num_left": graph.num_left, "num_right": graph.num_right, "num_edges": graph.num_edges},
    )

    def try_kuhn(left: int, visited: list[bool]) -> bool:
        nonlocal dfs_calls
        dfs_calls += 1
        for right in graph.adjacency[left]:
            if visited[right]:
                continue
            visited[right] = True
            if match_right[right] == -1 or try_kuhn(match_right[right], visited):
                match_right[right] = left
                match_left[left] = right
                return True
        return False

    start = time.perf_counter()

    for left in range(graph.num_left):
        emit(
            StepEvent.SEARCHING_AUGMENTING_PATH,
            f"Searching augmenting path from student #{left} via DFS.",
            {"left": left},
        )
        visited = [False] * graph.num_right
        found = try_kuhn(left, visited)
        if found:
            augmenting_paths_found += 1
            emit(
                StepEvent.MATCH_UPDATED,
                f"Augmenting path found for student #{left} -> lab-slot #{match_left[left]}.",
                {"left": left, "right": match_left[left]},
            )
        else:
            emit(
                StepEvent.NO_PATH_FOUND,
                f"No augmenting path exists for student #{left}; remains unmatched.",
                {"left": left},
            )

    elapsed_ms = (time.perf_counter() - start) * 1000

    matched_pairs = [(left, right) for left, right in enumerate(match_left) if right != -1]
    unmatched_left = [left for left, right in enumerate(match_left) if right == -1]
    unmatched_right = [right for right, left in enumerate(match_right) if left == -1]

    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Maximum matching reached: {len(matched_pairs)} pairs matched.",
        {"match_size": len(matched_pairs)},
    )

    return MatchingResult(
        algorithm="KUHN",
        matched_pairs=matched_pairs,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
        vertices=graph.num_vertices,
        edges=graph.num_edges,
        iterations=dfs_calls,
        augmenting_paths_found=augmenting_paths_found,
        execution_time_ms=elapsed_ms,
        time_complexity="O(V * E)",
        space_complexity="O(V + E)",
        steps=steps,
    )
