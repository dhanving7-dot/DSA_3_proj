"""Static algorithm metadata used by the playground / explanation panels.

Kept separate from the algorithm implementations themselves so the UI can
fetch "what is this algorithm" copy without running anything.
"""
from __future__ import annotations

ALGORITHM_INFO: dict[str, dict] = {
    "KUHN": {
        "name": "Kuhn's Algorithm",
        "category": "Bipartite Matching",
        "description": (
            "Repeatedly searches for an augmenting path from each unmatched left "
            "vertex using DFS over alternating unmatched/matched edges. Simple to "
            "reason about, and optimal for small-to-medium graphs."
        ),
        "time_complexity": "O(V * E)",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build bipartite graph from eligible student-lab edges",
            "For each unmatched student, run DFS to find an augmenting path",
            "If found, flip matched/unmatched edges along the path",
            "Repeat for all students",
            "Maximum matching reached when no more augmenting paths exist",
        ],
    },
    "HOPCROFT_KARP": {
        "name": "Hopcroft-Karp Algorithm",
        "category": "Bipartite Matching",
        "description": (
            "Improves on Kuhn's algorithm by finding a maximal set of "
            "vertex-disjoint shortest augmenting paths per phase (BFS layering + "
            "restricted DFS), reducing the number of phases to O(sqrt(V))."
        ),
        "time_complexity": "O(E * sqrt(V))",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build bipartite graph from eligible student-lab edges",
            "BFS: compute shortest-augmenting-path layers from all free students",
            "DFS: greedily find vertex-disjoint augmenting paths restricted to those layers",
            "Flip matched/unmatched edges along every path found this phase",
            "Repeat phases until BFS finds no augmenting path",
            "Maximum matching reached",
        ],
    },
    "EDMONDS_KARP": {
        "name": "Edmonds-Karp Algorithm",
        "category": "Maximum Flow",
        "description": (
            "Ford-Fulkerson specialised to always augment along the shortest "
            "(fewest-edge) path found via BFS on the residual graph. Models "
            "matching as flow: source -> students -> labs -> sink, with lab "
            "capacity expressed directly as edge capacity."
        ),
        "time_complexity": "O(V * E^2)",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build flow network: source -> students -> eligible labs -> sink",
            "BFS for the shortest augmenting path in the residual graph",
            "Compute the bottleneck capacity along that path",
            "Push flow equal to the bottleneck, update residual capacities",
            "Repeat until no augmenting path remains",
            "Maximum flow == size of maximum matching",
        ],
    },
    "DINIC": {
        "name": "Dinic's Algorithm",
        "category": "Maximum Flow",
        "description": (
            "Organises augmentation into phases: BFS builds a level graph, then a "
            "single DFS pass (with current-arc pointers) saturates a blocking flow "
            "restricted to edges that advance exactly one level. Matches "
            "Hopcroft-Karp's O(E*sqrt(V)) bound on unit-capacity bipartite graphs."
        ),
        "time_complexity": "O(V^2 * E) general, O(E*sqrt(V)) on unit-capacity bipartite graphs",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build flow network: source -> students -> eligible labs -> sink",
            "BFS: assign levels to all reachable nodes from the source",
            "DFS with current-arc optimisation: push blocking flow along level-respecting edges",
            "Repeat DFS until the blocking flow is saturated for this level graph",
            "Rebuild levels and repeat until sink is unreachable",
            "Maximum flow == size of maximum matching",
        ],
    },
    "FORD_FULKERSON": {
        "name": "Ford-Fulkerson Method (DFS)",
        "category": "Maximum Flow",
        "description": (
            "The generic augmenting-path method: any s->t path with spare residual capacity "
            "may be used, here found with DFS. Correct by the max-flow min-cut theorem, but "
            "its running time depends on the flow value - Edmonds-Karp (BFS) and Dinic "
            "(level graphs) are the refinements that remove that dependence."
        ),
        "time_complexity": "O(E * |f*|)",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build flow network: source -> students -> eligible labs -> sink",
            "DFS for any augmenting path in the residual graph",
            "Push the bottleneck capacity along it; reverse edges let later paths undo choices",
            "Repeat until the sink is unreachable",
            "The reachable set is the source side of a minimum cut; max flow == maximum matching",
        ],
    },
    "MIN_COST_FLOW": {
        "name": "Min-Cost Max-Flow (Successive Shortest Paths)",
        "category": "Weighted Matching / Flow",
        "description": (
            "Every student->lab edge costs (best score - score). Successive shortest paths "
            "augment along the cheapest residual path (Dijkstra on reduced costs with "
            "Johnson potentials), so the result is a *maximum* matching that also has the "
            "largest possible total preference/skill/priority score - the assignment problem."
        ),
        "time_complexity": "O(F * E log V)",
        "space_complexity": "O(V + E)",
        "steps": [
            "Build the flow network, attaching a cost to every student->lab edge",
            "Dijkstra over reduced costs c(u,v) + h(u) - h(v) >= 0 finds the cheapest s->t path",
            "Update potentials h with the new distances so reduced costs stay non-negative",
            "Augment along the path; reverse edges carry negative cost for later re-routing",
            "Stop when the sink is unreachable: flow is maximum and its cost is minimum",
        ],
    },
}
