import itertools
import math
import random
from functools import lru_cache

import pytest

from app.algorithms import dp


def brute_edit(a, b, transpositions=False):
    @lru_cache(maxsize=None)
    def go(i, j):
        if i == 0:
            return j
        if j == 0:
            return i
        best = min(go(i - 1, j) + 1, go(i, j - 1) + 1, go(i - 1, j - 1) + (a[i - 1] != b[j - 1]))
        if transpositions and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
            best = min(best, go(i - 2, j - 2) + 1)
        return best

    return go(len(a), len(b))


def rand_word(rng, n, alphabet="abc"):
    return "".join(rng.choice(alphabet) for _ in range(n))


def test_edit_distance_known_values():
    assert dp.edit_distance("kitten", "sitting")["distance"] == 3
    assert dp.edit_distance("ca", "ac")["distance"] == 2
    assert dp.edit_distance("ca", "ac", "DAMERAU")["distance"] == 1
    assert dp.edit_distance("", "abc")["distance"] == 3


def test_edit_distance_variants_match_recursive_oracle():
    rng = random.Random(1)
    for _ in range(200):
        a, b = rand_word(rng, rng.randint(0, 7)), rand_word(rng, rng.randint(0, 7))
        assert dp.edit_distance(a, b)["distance"] == brute_edit(a, b)
        assert dp.levenshtein_distance(a, b) == brute_edit(a, b)
        assert dp.edit_distance(a, b, "DAMERAU")["distance"] == brute_edit(a, b, True)
        assert dp.osa_distance(a, b) == brute_edit(a, b, True)


def test_levenshtein_band_early_exit_never_underestimates():
    rng = random.Random(2)
    for _ in range(300):
        a, b = rand_word(rng, rng.randint(0, 9)), rand_word(rng, rng.randint(0, 9))
        for budget in (0, 1, 2, 3):
            true = brute_edit(a, b)
            banded = dp.levenshtein_distance(a, b, max_distance=budget)
            assert banded == true if true <= budget else banded > budget
            true_osa = brute_edit(a, b, True)
            banded_osa = dp.osa_distance(a, b, max_distance=budget)
            assert banded_osa == true_osa if true_osa <= budget else banded_osa > budget


def test_edit_traceback_replays_to_target():
    rng = random.Random(3)
    for variant in ("LEVENSHTEIN", "DAMERAU"):
        for _ in range(100):
            a, b = rand_word(rng, rng.randint(0, 6)), rand_word(rng, rng.randint(0, 6))
            result = dp.edit_distance(a, b, variant)
            produced = "".join(op["b"] for op in result["operations"])
            consumed = "".join(op["a"] for op in result["operations"])
            assert produced == b and consumed == a
            cost = sum(0 if op["op"] == "match" else 1 for op in result["operations"])
            assert cost == result["distance"]


def test_weighted_edit_distance_prefers_cheap_operations():
    # substitution costs 5 > insert + delete, so the optimum deletes then inserts
    result = dp.edit_distance("a", "b", "WEIGHTED", insert_cost=1, delete_cost=1, substitute_cost=5)
    assert result["distance"] == 2
    assert sorted(op["op"] for op in result["operations"]) == ["delete", "insert"]


def test_needleman_wunsch_and_smith_waterman():
    nw = dp.needleman_wunsch("GATTACA", "GCATGCU", match=1, mismatch=-1, gap=-1)
    assert nw["score"] == 0
    assert nw["aligned_a"].replace("-", "") == "GATTACA" and nw["aligned_b"].replace("-", "") == "GCATGCU"
    sw = dp.smith_waterman("TGTTACGG", "GGTTGACTA", match=3, mismatch=-3, gap=-2)
    assert sw["score"] == 13
    assert sw["aligned_a"] == "GTT-AC" and sw["aligned_b"] == "GTTGAC"


def test_alignment_score_matches_aligned_strings():
    rng = random.Random(4)
    for _ in range(100):
        a, b = rand_word(rng, rng.randint(1, 8), "ACGT"), rand_word(rng, rng.randint(1, 8), "ACGT")
        r = dp.needleman_wunsch(a, b, 2, -1, -2)
        score = sum(-2 if x == "-" or y == "-" else (2 if x == y else -1) for x, y in zip(r["aligned_a"], r["aligned_b"]))
        assert score == r["score"]


def test_matrix_chain_clrs_example():
    result = dp.matrix_chain_order([30, 35, 15, 5, 10, 20, 25])
    assert result["min_cost"] == 15125
    assert result["parenthesization"] == "((A1 x (A2 x A3)) x ((A4 x A5) x A6))"
    assert result["left_to_right_cost"] >= result["min_cost"]


def brute_bst_cost(freqs):
    @lru_cache(maxsize=None)
    def go(i, j, depth):
        if i > j:
            return 0
        return min(freqs[r] * depth + go(i, r - 1, depth + 1) + go(r + 1, j, depth + 1) for r in range(i, j + 1))

    return go(0, len(freqs) - 1, 1)


def test_optimal_bst_knuth_equals_cubic_and_brute_force():
    rng = random.Random(5)
    for _ in range(80):
        n = rng.randint(1, 8)
        freqs = tuple(rng.randint(0, 20) for _ in range(n))
        keys = list(range(n))
        cubic = dp.optimal_bst(keys, list(freqs), knuth=False)
        knuth = dp.optimal_bst(keys, list(freqs), knuth=True)
        assert cubic["cost"] == knuth["cost"] == brute_bst_cost(freqs)
        assert knuth["root_evaluations"] <= cubic["root_evaluations"]


def tsp_brute(dist):
    n = len(dist)
    return min(
        sum(dist[t[i]][t[i + 1]] for i in range(n))
        for t in ((0, *p, 0) for p in itertools.permutations(range(1, n)))
    )


def test_held_karp_matches_permutations():
    rng = random.Random(6)
    for _ in range(20):
        n = rng.randint(2, 7)
        pts = [(rng.randint(0, 50), rng.randint(0, 50)) for _ in range(n)]
        dist = [[math.dist(p, q) for q in pts] for p in pts]
        result = dp.held_karp_tsp(dist)
        assert result["cost"] == pytest.approx(tsp_brute(dist))
        tour = result["tour"]
        assert tour[0] == tour[-1] == 0 and sorted(tour[:-1]) == list(range(n))
        assert sum(dist[tour[i]][tour[i + 1]] for i in range(n)) == pytest.approx(result["cost"])


def test_hamiltonian_path_matches_permutations():
    rng = random.Random(7)
    for _ in range(60):
        n = rng.randint(1, 7)
        adj = [[] for _ in range(n)]
        edges = set()
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.4:
                    adj[u].append(v)
                    adj[v].append(u)
                    edges.add((u, v))
        exists = any(all((min(p[i], p[i + 1]), max(p[i], p[i + 1])) in edges for i in range(n - 1)) for p in itertools.permutations(range(n)))
        result = dp.hamiltonian_path(n, adj)
        assert result["exists"] == exists
        if exists:
            path = result["path"]
            assert sorted(path) == list(range(n))
            assert all((min(path[i], path[i + 1]), max(path[i], path[i + 1])) in edges for i in range(n - 1))


def test_tree_dp_against_bfs_and_brute_force():
    rng = random.Random(8)
    for _ in range(60):
        n = rng.randint(1, 11)
        edges = [(rng.randrange(v), v) for v in range(1, n)]
        result = dp.tree_dp(n, edges)
        all_dist = [dp.bfs_distances(n, edges, v) for v in range(n)]
        assert result["diameter"] == max(max(row) for row in all_dist)
        assert result["sum_of_distances"] == [sum(row) for row in all_dist]
        best_mis = 0
        for mask in range(1 << n):
            if all(not ((mask >> u) & 1 and (mask >> v) & 1) for u, v in edges):
                best_mis = max(best_mis, bin(mask).count("1"))
        assert result["max_independent_set"] == best_mis
        assert result["centroids"] and len(result["centroids"]) <= 2


def test_sos_superset_and_subset_sums():
    rng = random.Random(9)
    for k in range(0, 7):
        f = [rng.randint(0, 9) for _ in range(1 << k)]
        sup = dp.sos_superset_sums(f, k)
        sub = dp.sos_subset_sums(f, k)
        for mask in range(1 << k):
            assert sup[mask] == sum(f[s] for s in range(1 << k) if s & mask == mask)
            assert sub[mask] == sum(f[s] for s in range(1 << k) if s & mask == s)


def test_knapsack_and_subset_sum_against_brute_force():
    rng = random.Random(10)
    for _ in range(80):
        n = rng.randint(1, 9)
        w = [rng.randint(1, 15) for _ in range(n)]
        v = [rng.randint(1, 30) for _ in range(n)]
        cap = rng.randint(0, 40)
        best = max(
            sum(v[i] for i in range(n) if (m >> i) & 1)
            for m in range(1 << n)
            if sum(w[i] for i in range(n) if (m >> i) & 1) <= cap
        )
        result = dp.knapsack_01(w, v, cap)
        assert result["value"] == best
        assert sum(w[i] for i in result["items"]) <= cap and sum(v[i] for i in result["items"]) == best

        target = rng.randint(0, 40)
        possible = any(sum(w[i] for i in range(n) if (m >> i) & 1) == target for m in range(1 << n))
        ss = dp.subset_sum(w, target)
        assert ss["possible"] == possible
        if possible:
            assert sum(ss["subset"]) == target


def test_bitmask_assignment_matches_permutation_search():
    rng = random.Random(11)
    for _ in range(60):
        rows, cols = rng.randint(1, 5), rng.randint(1, 5)
        scores = [[rng.randint(1, 9) if rng.random() < 0.6 else None for _ in range(cols)] for _ in range(rows)]
        best = (0, 0)
        for assignment in itertools.product(range(-1, cols), repeat=rows):
            used = [c for c in assignment if c != -1]
            if len(used) != len(set(used)) or any(c != -1 and scores[r][c] is None for r, c in enumerate(assignment)):
                continue
            best = max(best, (len(used), sum(scores[r][c] for r, c in enumerate(assignment) if c != -1)))
        result = dp.bitmask_assignment(scores)
        assert (result["matched"], result["total_score"]) == best
