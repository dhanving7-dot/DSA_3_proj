import itertools
import math
import random

from app.algorithms import approximation, parallel, randomized
from app.algorithms.dp import held_karp_tsp, knapsack_01


def test_vertex_cover_approximation_within_factor_two():
    rng = random.Random(1)
    for _ in range(80):
        n = rng.randint(1, 10)
        edges = [(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < 0.35]
        approx = approximation.vertex_cover_2approx(edges)
        exact = approximation.vertex_cover_exact(n, edges)
        for cover in (set(approx["cover"]), set(exact["cover"])):
            assert all(u in cover or v in cover for u, v in edges)
        brute = min((len(c) for k in range(n + 1) for c in itertools.combinations(range(n), k) if all(u in c or v in c for u, v in edges)))
        assert exact["size"] == brute
        assert exact["size"] <= approx["size"] <= 2 * exact["size"]


def test_set_cover_greedy_and_exact():
    rng = random.Random(2)
    for _ in range(60):
        universe_size, k = rng.randint(1, 12), rng.randint(1, 8)
        sets = [sum(1 << e for e in rng.sample(range(universe_size), rng.randint(1, universe_size))) for _ in range(k)]
        universe = 0
        for s in sets:
            universe |= s
        greedy = approximation.greedy_set_cover(universe, sets)
        exact = approximation.exact_set_cover(universe, sets)
        union = 0
        for i in greedy["chosen"]:
            union |= sets[i]
        assert union == universe and greedy["fully_covered"]
        brute = min(r for r in range(1, k + 1) for combo in itertools.combinations(range(k), r) if _union(sets, combo) == universe)
        assert exact["size"] == brute
        assert len(greedy["chosen"]) <= brute * approximation.harmonic(bin(universe).count("1")) + 1e-9


def _union(sets, combo):
    out = 0
    for i in combo:
        out |= sets[i]
    return out


def test_knapsack_fptas_guarantee():
    rng = random.Random(3)
    for _ in range(80):
        n = rng.randint(1, 10)
        w = [rng.randint(1, 30) for _ in range(n)]
        v = [rng.randint(1, 100) for _ in range(n)]
        cap = rng.randint(0, 80)
        eps = rng.choice([0.1, 0.3, 0.5])
        opt = knapsack_01(w, v, cap)["value"]
        fptas = approximation.knapsack_fptas(w, v, cap, eps)
        assert sum(w[i] for i in fptas["items"]) <= cap
        assert fptas["value"] == sum(v[i] for i in fptas["items"])
        assert fptas["value"] >= (1 - eps) * opt - 1e-9


def test_metric_tsp_approximations():
    rng = random.Random(4)
    for _ in range(20):
        n = rng.randint(3, 8)
        pts = [(rng.randint(0, 100), rng.randint(0, 100)) for _ in range(n)]
        dist = [[math.dist(p, q) for q in pts] for p in pts]
        opt = held_karp_tsp(dist)["cost"]
        mst = approximation.tsp_mst_2approx(dist)
        nn = approximation.tsp_nearest_neighbour(dist)
        for tour in (mst["tour"], nn["tour"]):
            assert tour[0] == tour[-1] == 0 and sorted(tour[:-1]) == list(range(n))
        assert opt - 1e-9 <= mst["cost"] <= 2 * opt + 1e-9
        assert mst["mst_weight"] <= opt + 1e-9
        assert nn["cost"] >= opt - 1e-9


def test_primality_tests_against_trial_division():
    rng = random.Random(5)
    for n in range(0, 5000):
        truth = randomized.trial_division(n)
        assert randomized.is_prime_deterministic(n) == truth
        assert randomized.miller_rabin(n, 8, rng) == truth


def test_carmichael_numbers_fool_fermat_but_not_miller_rabin():
    for n in randomized.KNOWN_CARMICHAEL:
        fermat = randomized.fermat_test(n, [2, 3, 5, 7, 11, 13])
        assert fermat["probably_prime"] is True  # every coprime base passes
        assert randomized.is_prime_deterministic(n) is False
        assert randomized.miller_rabin(n, 10, random.Random(n)) is False


def test_large_known_primes_and_random_prime():
    assert randomized.is_prime_deterministic(2**61 - 1)
    assert not randomized.is_prime_deterministic(2**61 + 1)
    assert randomized.mod_pow(3, 10**18, 10**9 + 7) == pow(3, 10**18, 10**9 + 7)
    rng = random.Random(6)
    for bits in (8, 16, 31, 48):
        p, attempts = randomized.random_prime(bits, rng)
        assert p.bit_length() == bits and attempts >= 1
        assert randomized.trial_division(p) in (True, None)


def test_reservoir_sampling_is_uniform_and_handles_short_streams():
    sample, seen = randomized.reservoir_sample(range(3), 10, random.Random(0))
    assert sample == [0, 1, 2] and seen == 3
    rng = random.Random(7)
    counts = [0] * 20
    trials = 20000
    for _ in range(trials):
        s, _ = randomized.reservoir_sample(range(20), 5, rng)
        assert len(s) == len(set(s)) == 5
        for x in s:
            counts[x] += 1
    expected = trials * 5 / 20
    assert all(abs(c - expected) < 0.06 * expected for c in counts)


def test_quicksorts_sort_and_show_worst_case():
    rng = random.Random(8)
    for _ in range(50):
        data = [rng.randint(0, 20) for _ in range(rng.randint(0, 60))]
        assert randomized.randomized_quicksort(data, rng)[0] == sorted(data)
        assert randomized.deterministic_quicksort(data)[0] == sorted(data)
    n = 1500  # deep enough to break a recursive implementation
    _, comparisons, depth = randomized.deterministic_quicksort(list(range(n)))
    assert comparisons == n * (n - 1) // 2 and depth == n - 1
    _, rand_comparisons, _ = randomized.randomized_quicksort(list(range(n)), random.Random(1))
    assert rand_comparisons < 4 * n * math.log(n)


def test_universal_hash_stays_in_range():
    rng = random.Random(9)
    h = randomized.UniversalHash.random(17, 10_000, rng)
    assert randomized.is_prime_deterministic(h.p) and h.p > 10_000
    assert all(0 <= h(x) < 17 for x in range(0, 10_000, 7))


def test_blelloch_scan_matches_sequential_with_logarithmic_span():
    rng = random.Random(10)
    for n in list(range(0, 20)) + [31, 32, 33, 64]:
        values = [rng.randint(0, 50) for _ in range(n)]
        trace = parallel.blelloch_exclusive_scan(values)
        assert trace.result == parallel.sequential_exclusive_scan(values)
        if n > 1:
            size = 1 << (n - 1).bit_length()
            assert trace.work == 2 * (size - 1)
            assert trace.span == 2 * int(math.log2(size))


def test_parallel_reduce_and_brent_bound():
    values = list(range(1, 17))
    trace = parallel.parallel_reduce(values)
    assert trace.result == sum(values)
    assert trace.work == 15 and trace.span == 4
    assert trace.brent_bound(1) == 15 + 4
    assert trace.brent_bound(4) == 15 / 4 + 4
    assert parallel.parallel_reduce([7]).result == 7
    assert parallel.parallel_reduce([]).result == 0
