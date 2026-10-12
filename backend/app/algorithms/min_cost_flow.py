"""Min-cost max-flow via Successive Shortest Paths with Johnson potentials.

Plain max-flow (Edmonds-Karp, Dinic) maximises *how many* students are
placed but is indifferent to *which* maximum matching it returns. Giving
every student->lab edge a cost of (best_score - score) and asking for the
cheapest maximum flow selects, among all maximum matchings, one with the
largest total match score - the "assignment problem" generalisation of
bipartite matching.

SSP repeatedly augments along a cheapest residual s->t path. Residual
reverse edges carry negative cost, so Dijkstra is run on *reduced* costs
c'(u,v) = c(u,v) + h(u) - h(v) >= 0, where the potentials h are the previous
round's shortest distances. Initial costs are non-negative, so h = 0 is a
valid start (Bellman-Ford would be needed otherwise).

Time complexity:  O(F * E log V)   (F = max flow value, one Dijkstra per unit of flow)
Space complexity: O(V + E)
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.algorithms.heap import MinHeap
from app.algorithms.result import AlgorithmStep, MatchingResult, StepEvent

INF = float("inf")


@dataclass
class CostEdge:
    to: int
    capacity: int
    cost: int
    flow: int = 0
    reverse_index: int = -1

    @property
    def residual(self) -> int:
        return self.capacity - self.flow


class CostFlowNetwork:
    def __init__(self, num_nodes: int) -> None:
        self.num_nodes = num_nodes
        self.graph: list[list[CostEdge]] = [[] for _ in range(num_nodes)]

    @property
    def num_edges(self) -> int:
        return sum(1 for adj in self.graph for e in adj if e.capacity > 0)

    def add_edge(self, u: int, v: int, capacity: int, cost: int) -> None:
        if cost < 0:
            raise ValueError("SSP with zero initial potentials requires non-negative edge costs")
        forward = CostEdge(to=v, capacity=capacity, cost=cost)
        backward = CostEdge(to=u, capacity=0, cost=-cost)
        self.graph[u].append(forward)
        self.graph[v].append(backward)
        forward.reverse_index = len(self.graph[v]) - 1
        backward.reverse_index = len(self.graph[u]) - 1


def min_cost_max_flow(network: CostFlowNetwork, source: int, sink: int) -> tuple[int, int, MatchingResult]:
    """Returns (max_flow, min_cost, trace)."""
    n = network.num_nodes
    potential = [0] * n
    steps: list[AlgorithmStep] = []
    step_no = 0
    augmentations = 0
    relaxations = 0

    def emit(event: StepEvent, description: str, data: dict | None = None) -> None:
        nonlocal step_no
        step_no += 1
        steps.append(AlgorithmStep(step_no, event, description, data or {}))

    emit(
        StepEvent.GRAPH_CREATED,
        f"Built cost-flow network with {n} nodes; student->lab edges cost (best score - score).",
        {"num_nodes": n, "num_edges": network.num_edges},
    )

    flow = 0
    cost = 0
    start = time.perf_counter()
    while True:
        emit(StepEvent.SEARCHING_AUGMENTING_PATH, "Dijkstra on reduced costs for the cheapest augmenting path.")
        dist = [INF] * n
        prev_node = [-1] * n
        prev_edge = [-1] * n
        dist[source] = 0
        heap = MinHeap()
        heap.push(0, source)
        while len(heap):
            d, u = heap.pop()
            if d > dist[u]:
                continue  # stale entry (lazy deletion)
            for idx, edge in enumerate(network.graph[u]):
                if edge.residual <= 0:
                    continue
                nd = d + edge.cost + potential[u] - potential[edge.to]
                relaxations += 1
                if nd < dist[edge.to]:
                    dist[edge.to] = nd
                    prev_node[edge.to] = u
                    prev_edge[edge.to] = idx
                    heap.push(nd, edge.to)

        if dist[sink] == INF:
            emit(StepEvent.NO_PATH_FOUND, "Sink unreachable in the residual graph: flow is maximum and cost is minimum.")
            break

        for v in range(n):
            if dist[v] < INF:
                potential[v] += dist[v]

        bottleneck = INF
        v = sink
        while v != source:
            edge = network.graph[prev_node[v]][prev_edge[v]]
            bottleneck = min(bottleneck, edge.residual)
            v = prev_node[v]

        path_cost = 0
        v = sink
        while v != source:
            u = prev_node[v]
            edge = network.graph[u][prev_edge[v]]
            edge.flow += bottleneck
            network.graph[v][edge.reverse_index].flow -= bottleneck
            path_cost += edge.cost
            v = u

        flow += bottleneck
        cost += bottleneck * path_cost
        augmentations += 1
        emit(
            StepEvent.AUGMENTING_PATH_FOUND,
            f"Augmentation #{augmentations}: pushed {bottleneck} unit(s) along a path of cost {path_cost}.",
            {"pushed": bottleneck, "path_cost": path_cost},
        )
        emit(StepEvent.MATCH_UPDATED, f"Flow {flow}, total cost {cost}.", {"flow": flow, "cost": cost})

    elapsed_ms = (time.perf_counter() - start) * 1000
    emit(
        StepEvent.ALGORITHM_COMPLETE,
        f"Min-cost max-flow reached: flow {flow} with total cost {cost} after {augmentations} shortest-path augmentations.",
        {"max_flow": flow, "min_cost": cost},
    )
    trace = MatchingResult(
        algorithm="MIN_COST_FLOW",
        matched_pairs=[],
        unmatched_left=[],
        unmatched_right=[],
        vertices=n,
        edges=network.num_edges,
        iterations=relaxations,
        augmenting_paths_found=augmentations,
        execution_time_ms=elapsed_ms,
        time_complexity="O(F * E log V)",
        space_complexity="O(V + E)",
        steps=steps,
    )
    return flow, cost, trace
