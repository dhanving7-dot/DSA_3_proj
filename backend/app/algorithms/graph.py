"""Core graph data structures shared by every matching / max-flow algorithm.

Two representations are used deliberately, mirroring the two ways the course
treats bipartite matching:

* :class:`BipartiteGraph` - a plain adjacency-list bipartite graph used by
  Kuhn's algorithm and Hopcroft-Karp. Laboratory *capacity* is handled by
  expanding each laboratory into ``capacity`` distinct "slot" vertices on the
  right side before the algorithm ever runs - this is the standard reduction
  from many-to-one bipartite b-matching to plain 1-to-1 bipartite matching.

* :class:`FlowNetwork` - a residual-graph adjacency list (edges stored as
  mutable objects with a paired reverse edge) used by Edmonds-Karp and
  Dinic. Laboratory capacity is expressed directly as edge capacity, which is
  the more natural way to model capacities in the max-flow formulation and is
  what makes the flow formulation strictly more general than the simple
  matching formulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BipartiteGraph:
    """Adjacency list bipartite graph, left = students, right = lab-slots."""

    num_left: int
    num_right: int
    adjacency: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.adjacency:
            self.adjacency = [[] for _ in range(self.num_left)]

    @property
    def num_edges(self) -> int:
        return sum(len(neighbors) for neighbors in self.adjacency)

    @property
    def num_vertices(self) -> int:
        return self.num_left + self.num_right

    def add_edge(self, left: int, right: int) -> None:
        self.adjacency[left].append(right)


@dataclass
class Edge:
    to: int
    capacity: int
    flow: int = 0
    reverse_index: int = -1

    @property
    def residual(self) -> int:
        return self.capacity - self.flow


class FlowNetwork:
    """Directed graph with edge capacities, stored as adjacency of Edge objects.

    Every added edge (u -> v, cap) is paired with an implicit reverse edge
    (v -> u, cap=0) so augmenting paths can "cancel" flow, which is required
    for Ford-Fulkerson-style algorithms to reach a true maximum flow.
    """

    def __init__(self, num_nodes: int) -> None:
        self.num_nodes = num_nodes
        self.graph: list[list[Edge]] = [[] for _ in range(num_nodes)]

    @property
    def num_edges(self) -> int:
        # only count forward edges (every forward edge has one paired reverse edge)
        return sum(1 for adj in self.graph for e in adj if e.capacity > 0)

    def add_edge(self, u: int, v: int, capacity: int) -> None:
        forward = Edge(to=v, capacity=capacity)
        backward = Edge(to=u, capacity=0)
        self.graph[u].append(forward)
        self.graph[v].append(backward)
        forward.reverse_index = len(self.graph[v]) - 1
        backward.reverse_index = len(self.graph[u]) - 1

    def reverse_edge(self, u: int, edge: Edge) -> Edge:
        return self.graph[edge.to][edge.reverse_index]
