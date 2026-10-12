from app.algorithms.graph import BipartiteGraph
from app.algorithms.kuhn import kuhn_max_matching


def make_graph(num_left, num_right, edges):
    g = BipartiteGraph(num_left=num_left, num_right=num_right)
    for u, v in edges:
        g.add_edge(u, v)
    return g


def test_simple_perfect_matching():
    g = make_graph(3, 3, [(0, 0), (1, 1), (2, 2)])
    result = kuhn_max_matching(g)
    assert result.match_size == 3
    assert result.unmatched_left == []


def test_no_edges_no_matches():
    g = make_graph(3, 3, [])
    result = kuhn_max_matching(g)
    assert result.match_size == 0
    assert set(result.unmatched_left) == {0, 1, 2}


def test_more_left_than_right():
    # classic textbook example requiring augmenting-path reassignment
    g = make_graph(4, 2, [(0, 0), (1, 0), (2, 1), (3, 1)])
    result = kuhn_max_matching(g)
    assert result.match_size == 2


def test_augmenting_path_reassignment():
    # 0-{0,1}, 1-{0}, 2-{1}: greedy first-come could strand vertex 1 or 2
    # without augmenting path re-routing; max matching size is 3.
    g = make_graph(3, 2, [(0, 0), (0, 1), (1, 0), (2, 1)])
    result = kuhn_max_matching(g)
    assert result.match_size == 2  # only 2 right vertices exist -> bound by min(|L|,|R|)...
    # actually verify true maximum: with 3 left, 2 right, max possible is 2
    assert len(result.matched_pairs) == 2


def test_disconnected_graph_component():
    g = make_graph(4, 4, [(0, 0), (1, 1)])  # vertices 2,3 fully isolated
    result = kuhn_max_matching(g)
    assert result.match_size == 2
    assert 2 in result.unmatched_left and 3 in result.unmatched_left


def test_steps_are_recorded():
    g = make_graph(2, 2, [(0, 0), (1, 1)])
    result = kuhn_max_matching(g)
    assert result.steps[0].event.value == "GRAPH_CREATED"
    assert result.steps[-1].event.value == "ALGORITHM_COMPLETE"
    assert result.time_complexity == "O(V * E)"
