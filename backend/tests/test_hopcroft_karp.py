import random

from app.algorithms.graph import BipartiteGraph
from app.algorithms.hopcroft_karp import hopcroft_karp_max_matching
from app.algorithms.kuhn import kuhn_max_matching


def make_graph(num_left, num_right, edges):
    g = BipartiteGraph(num_left=num_left, num_right=num_right)
    for u, v in edges:
        g.add_edge(u, v)
    return g


def test_matches_kuhn_result_size_on_random_graphs():
    random.seed(42)
    for _ in range(20):
        num_left = random.randint(1, 12)
        num_right = random.randint(1, 12)
        edges = [
            (u, v)
            for u in range(num_left)
            for v in range(num_right)
            if random.random() < 0.35
        ]
        g1 = make_graph(num_left, num_right, edges)
        g2 = make_graph(num_left, num_right, edges)
        kuhn_result = kuhn_max_matching(g1)
        hk_result = hopcroft_karp_max_matching(g2)
        assert kuhn_result.match_size == hk_result.match_size


def test_perfect_matching():
    g = make_graph(4, 4, [(0, 0), (1, 1), (2, 2), (3, 3)])
    result = hopcroft_karp_max_matching(g)
    assert result.match_size == 4
    assert result.unmatched_left == []
    assert result.unmatched_right == []


def test_empty_graph():
    g = make_graph(0, 0, [])
    result = hopcroft_karp_max_matching(g)
    assert result.match_size == 0


def test_phases_recorded_in_steps():
    g = make_graph(3, 3, [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)])
    result = hopcroft_karp_max_matching(g)
    phase_events = [s for s in result.steps if s.event.value == "PHASE_START"]
    assert len(phase_events) >= 1
    assert result.time_complexity == "O(E * sqrt(V))"


def test_no_right_vertices():
    g = make_graph(5, 0, [])
    result = hopcroft_karp_max_matching(g)
    assert result.match_size == 0
    assert result.unmatched_left == [0, 1, 2, 3, 4]
