import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.algorithms.complexity import ALGORITHM_INFO
from app.algorithms.dinic import dinic_max_flow
from app.algorithms.edmonds_karp import edmonds_karp_max_flow
from app.algorithms.ford_fulkerson import ford_fulkerson_max_flow
from app.algorithms.graph import BipartiteGraph, FlowNetwork
from app.algorithms.hopcroft_karp import hopcroft_karp_max_matching
from app.algorithms.kuhn import kuhn_max_matching
from app.algorithms.matching_engine import AllocationConfigError
from app.algorithms.min_cost_flow import CostFlowNetwork, min_cost_max_flow
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.allocation import CompareAlgorithmsRequest, RunMatchingRequest
from app.services import allocation_service
from app.ws.manager import manager, replay_steps

router = APIRouter(prefix="/matching", tags=["matching"])


def _generate_random_bipartite(num_left: int, num_right: int, edge_probability: float, seed: int | None):
    rng = random.Random(seed)
    edges = [
        (u, v)
        for u in range(num_left)
        for v in range(num_right)
        if rng.random() < edge_probability
    ]
    return edges


@router.get("/algorithms")
def list_algorithms(_: User = Depends(get_current_user)):
    return ALGORITHM_INFO


def _playground_edge_costs(edges: list[tuple[int, int]], seed: int | None) -> list[int]:
    """Deterministic per-edge costs (1-9) for the min-cost flow playground, derived from the seed."""
    rng = random.Random(None if seed is None else seed * 7919 + 17)
    return [rng.randint(1, 9) for _ in edges]


@router.post("/run")
async def run_playground_matching(payload: RunMatchingRequest, channel: str | None = None, _: User = Depends(get_current_user)):
    edges = _generate_random_bipartite(payload.num_left, payload.num_right, payload.edge_probability, payload.seed)
    algorithm = payload.algorithm.value
    edge_costs: list[int] | None = None
    total_cost: int | None = None

    if algorithm in ("KUHN", "HOPCROFT_KARP"):
        graph = BipartiteGraph(num_left=payload.num_left, num_right=payload.num_right)
        for u, v in edges:
            graph.add_edge(u, v)
        trace = kuhn_max_matching(graph) if algorithm == "KUHN" else hopcroft_karp_max_matching(graph)
        max_value = trace.match_size
    else:
        source = 0
        left_offset = 1
        right_offset = left_offset + payload.num_left
        sink = right_offset + payload.num_right
        if algorithm == "MIN_COST_FLOW":
            edge_costs = _playground_edge_costs(edges, payload.seed)
            network = CostFlowNetwork(sink + 1)
            for u in range(payload.num_left):
                network.add_edge(source, left_offset + u, 1, 0)
            for v in range(payload.num_right):
                network.add_edge(right_offset + v, sink, 1, 0)
            for (u, v), cost in zip(edges, edge_costs):
                network.add_edge(left_offset + u, right_offset + v, 1, cost)
            max_value, total_cost, trace = min_cost_max_flow(network, source, sink)
        else:
            network = FlowNetwork(num_nodes=sink + 1)
            for u in range(payload.num_left):
                network.add_edge(source, left_offset + u, 1)
            for v in range(payload.num_right):
                network.add_edge(right_offset + v, sink, 1)
            for u, v in edges:
                network.add_edge(left_offset + u, right_offset + v, 1)
            if algorithm == "EDMONDS_KARP":
                max_value, trace = edmonds_karp_max_flow(network, source, sink)
            elif algorithm == "FORD_FULKERSON":
                max_value, trace = ford_fulkerson_max_flow(network, source, sink)
            else:
                max_value, trace = dinic_max_flow(network, source, sink)

        # recover which left->right edges carry flow, so the playground can highlight the matching
        matched = []
        for u in range(payload.num_left):
            for edge in network.graph[left_offset + u]:
                if right_offset <= edge.to < sink and edge.flow > 0:
                    matched.append((u, edge.to - right_offset))
        trace.matched_pairs = matched
        matched_left = {u for u, _ in matched}
        matched_right = {v for _, v in matched}
        trace.unmatched_left = [u for u in range(payload.num_left) if u not in matched_left]
        trace.unmatched_right = [v for v in range(payload.num_right) if v not in matched_right]

    if channel:
        await manager.broadcast(channel, {"type": "RUN_STARTED", "algorithm": algorithm})
        await replay_steps(channel, [step.to_dict() for step in trace.steps])
        await manager.broadcast(channel, {"type": "ALGORITHM_COMPLETE", "match_size": max_value})

    return {
        "input_edges": edges,
        "num_left": payload.num_left,
        "num_right": payload.num_right,
        "edge_costs": edge_costs,
        "total_cost": total_cost,
        "result": trace.to_dict(),
    }


@router.post("/compare")
def compare_algorithms(
    payload: CompareAlgorithmsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comparisons = []
    for algorithm in payload.algorithms:
        try:
            result, _, _ = allocation_service.compute_engine_result(
                db, algorithm.value, payload.config, payload.student_ids, payload.lab_ids
            )
        except AllocationConfigError as exc:
            comparisons.append({"algorithm": algorithm.value, "skipped_reason": str(exc)})
            continue
        run = allocation_service.persist_allocation_run(db, algorithm.value, payload.config, result, current_user.id)
        comparisons.append(
            {
                "algorithm": algorithm.value,
                "run_id": run.id,
                "matched_count": run.matched_count,
                "unmatched_count": run.unmatched_count,
                "execution_time_ms": run.execution_time_ms,
                "preference_satisfaction": run.preference_satisfaction,
                "capacity_utilization": run.capacity_utilization,
                "vertices": run.metrics.vertices if run.metrics else None,
                "edges": run.metrics.edges if run.metrics else None,
                "iterations": run.metrics.iterations if run.metrics else None,
                "time_complexity": run.metrics.time_complexity if run.metrics else None,
                "total_score": result.total_score,
            }
        )
    return {"comparisons": comparisons}
