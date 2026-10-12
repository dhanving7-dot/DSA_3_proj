import random

from app.algorithms.dinic import dinic_max_flow
from app.algorithms.edmonds_karp import edmonds_karp_max_flow
from app.algorithms.graph import BipartiteGraph, FlowNetwork
from app.algorithms.kuhn import kuhn_max_matching


def bipartite_to_flow_network(num_left, num_right, edges, right_capacity=1):
    source = 0
    left_offset = 1
    right_offset = left_offset + num_left
    sink = right_offset + num_right
    network = FlowNetwork(num_nodes=sink + 1)
    for u in range(num_left):
        network.add_edge(source, left_offset + u, 1)
    for v in range(num_right):
        network.add_edge(right_offset + v, sink, right_capacity)
    for u, v in edges:
        network.add_edge(left_offset + u, right_offset + v, 1)
    return network, source, sink


def test_edmonds_karp_matches_kuhn_on_random_graphs():
    random.seed(7)
    for _ in range(15):
        num_left = random.randint(1, 10)
        num_right = random.randint(1, 10)
        edges = [
            (u, v)
            for u in range(num_left)
            for v in range(num_right)
            if random.random() < 0.4
        ]
        g = BipartiteGraph(num_left=num_left, num_right=num_right)
        for u, v in edges:
            g.add_edge(u, v)
        kuhn_result = kuhn_max_matching(g)

        network, source, sink = bipartite_to_flow_network(num_left, num_right, edges)
        max_flow, _ = edmonds_karp_max_flow(network, source, sink)
        assert max_flow == kuhn_result.match_size


def test_dinic_matches_edmonds_karp():
    random.seed(11)
    for _ in range(15):
        num_left = random.randint(1, 10)
        num_right = random.randint(1, 10)
        edges = [
            (u, v)
            for u in range(num_left)
            for v in range(num_right)
            if random.random() < 0.4
        ]
        net1, s1, t1 = bipartite_to_flow_network(num_left, num_right, edges)
        net2, s2, t2 = bipartite_to_flow_network(num_left, num_right, edges)
        flow1, _ = edmonds_karp_max_flow(net1, s1, t1)
        flow2, _ = dinic_max_flow(net2, s2, t2)
        assert flow1 == flow2


def test_capacity_greater_than_one_on_right_side():
    # 3 students all preferring the same single lab with capacity 2
    edges = [(0, 0), (1, 0), (2, 0)]
    network, source, sink = bipartite_to_flow_network(3, 1, edges, right_capacity=2)
    max_flow, trace = edmonds_karp_max_flow(network, source, sink)
    assert max_flow == 2  # only 2 of 3 students can be matched
    assert trace.algorithm == "EDMONDS_KARP"


def test_zero_capacity_lab_yields_zero_flow():
    network, source, sink = bipartite_to_flow_network(2, 1, [(0, 0), (1, 0)], right_capacity=0)
    max_flow, _ = edmonds_karp_max_flow(network, source, sink)
    assert max_flow == 0


def test_no_edges_yields_zero_flow():
    network, source, sink = bipartite_to_flow_network(3, 3, [])
    max_flow, _ = dinic_max_flow(network, source, sink)
    assert max_flow == 0


def test_disconnected_source_sink():
    network = FlowNetwork(num_nodes=4)
    network.add_edge(0, 1, 5)
    network.add_edge(2, 3, 5)
    max_flow, trace = edmonds_karp_max_flow(network, 0, 3)
    assert max_flow == 0
    assert trace.augmenting_paths_found == 0
