"""Module 4 - What a finished max flow *proves*: min cuts, König covers, project selection.

After any max-flow algorithm stops, the set S of nodes still reachable from
the source in the residual graph is the source side of a minimum cut. Every
edge from S to T is saturated and their capacities sum to exactly the max
flow - the max-flow min-cut theorem, checked numerically here.

For bipartite matching the same residual search yields

* König's theorem   - a minimum vertex cover of size |maximum matching|
* Hall's condition  - a set of students whose combined eligible-lab
                      capacity is smaller than the set itself (the
                      certificate for why some students *cannot* be placed)
"""
from __future__ import annotations

from collections import deque

from app.algorithms.dinic import dinic_max_flow
from app.algorithms.graph import BipartiteGraph, FlowNetwork


def residual_reachable(network: FlowNetwork, source: int) -> list[bool]:
    seen = [False] * network.num_nodes
    seen[source] = True
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for edge in network.graph[u]:
            if edge.residual > 0 and not seen[edge.to]:
                seen[edge.to] = True
                queue.append(edge.to)
    return seen


def min_cut(network: FlowNetwork, source: int) -> dict:
    """Call after max flow has been computed on `network`."""
    side = residual_reachable(network, source)
    cut_edges = []
    capacity = 0
    for u in range(network.num_nodes):
        if not side[u]:
            continue
        for edge in network.graph[u]:
            if edge.capacity > 0 and not side[edge.to]:
                cut_edges.append((u, edge.to, edge.capacity))
                capacity += edge.capacity
    return {
        "source_side": [v for v in range(network.num_nodes) if side[v]],
        "cut_edges": cut_edges,
        "cut_capacity": capacity,
    }


def konig_vertex_cover(graph: BipartiteGraph, matched_pairs: list[tuple[int, int]]) -> dict:
    """Minimum vertex cover of a bipartite graph from a maximum matching.

    Z = vertices reachable from unmatched left vertices along alternating paths
    (unmatched edge left->right, matched edge right->left). Then
    cover = (L \\ Z) u (R n Z), and |cover| == |matching|.
    """
    match_left = [-1] * graph.num_left
    match_right = [-1] * graph.num_right
    for left, right in matched_pairs:
        match_left[left] = right
        match_right[right] = left

    z_left = [False] * graph.num_left
    z_right = [False] * graph.num_right
    queue = deque(u for u in range(graph.num_left) if match_left[u] == -1)
    for u in queue:
        z_left[u] = True
    while queue:
        u = queue.popleft()
        for v in graph.adjacency[u]:
            if z_right[v] or match_left[u] == v:
                continue
            z_right[v] = True
            w = match_right[v]
            if w != -1 and not z_left[w]:
                z_left[w] = True
                queue.append(w)

    cover_left = [u for u in range(graph.num_left) if not z_left[u]]
    cover_right = [v for v in range(graph.num_right) if z_right[v]]
    return {"left": cover_left, "right": cover_right, "size": len(cover_left) + len(cover_right)}


def project_selection(profits: list[int], costs: list[int], requires: list[tuple[int, int]]) -> dict:
    """Choose projects (profit p_i) that each need tools (cost c_j) to maximise profit - costs.

    Reduction: source -> project (cap p_i), tool -> sink (cap c_j), project -> tool (cap inf).
    A finite cut can never separate a chosen project from a tool it needs, and
    best profit = sum(p_i) - min cut. Chosen sets are the source side of the cut.
    """
    num_projects, num_tools = len(profits), len(costs)
    source = 0
    project_offset = 1
    tool_offset = project_offset + num_projects
    sink = tool_offset + num_tools
    big = sum(profits) + sum(costs) + 1  # acts as infinity: larger than any finite cut
    network = FlowNetwork(sink + 1)
    for i, p in enumerate(profits):
        network.add_edge(source, project_offset + i, p)
    for j, c in enumerate(costs):
        network.add_edge(tool_offset + j, sink, c)
    for i, j in requires:
        network.add_edge(project_offset + i, tool_offset + j, big)

    flow, _ = dinic_max_flow(network, source, sink)
    side = residual_reachable(network, source)
    chosen_projects = [i for i in range(num_projects) if side[project_offset + i]]
    chosen_tools = [j for j in range(num_tools) if side[tool_offset + j]]
    return {
        "max_profit": sum(profits) - flow,
        "min_cut": flow,
        "projects": chosen_projects,
        "tools": chosen_tools,
    }
