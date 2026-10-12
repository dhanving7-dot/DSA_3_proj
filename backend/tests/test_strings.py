import random

import pytest

from app.algorithms.strings import (
    AhoCorasick,
    SEARCH_ALGORITHMS,
    kmp_search,
    lcp_kasai,
    naive_search,
    prefix_function,
    rabin_karp,
    suffix_array,
    suffix_array_search,
    suffix_structure_summary,
    z_function,
    z_search,
)


def occurrences(text, pattern):
    """Ground truth independent of every implementation under test."""
    if not pattern or len(pattern) > len(text):
        return []
    return [i for i in range(len(text) - len(pattern) + 1) if text.startswith(pattern, i)]


def random_string(rng, n, alphabet="ab"):
    return "".join(rng.choice(alphabet) for _ in range(n))


@pytest.mark.parametrize("name", list(SEARCH_ALGORITHMS))
def test_every_search_algorithm_matches_ground_truth(name):
    rng = random.Random(1234)
    fn = SEARCH_ALGORITHMS[name]
    for _ in range(300):
        text = random_string(rng, rng.randint(0, 40), rng.choice(["ab", "abc", "a"]))
        pattern = random_string(rng, rng.randint(1, 5), "ab")
        assert fn(text, pattern).positions == occurrences(text, pattern), (name, text, pattern)


def test_overlapping_occurrences_are_all_reported():
    for fn in SEARCH_ALGORITHMS.values():
        assert fn("aaaaa", "aa").positions == [0, 1, 2, 3]
        assert fn("abababa", "aba").positions == [0, 2, 4]


def test_empty_and_oversized_patterns_have_no_matches():
    for fn in SEARCH_ALGORITHMS.values():
        assert fn("abc", "").positions == []
        assert fn("ab", "abc").positions == []
        assert fn("", "a").positions == []


def test_prefix_function_matches_definition():
    rng = random.Random(5)
    for _ in range(200):
        s = random_string(rng, rng.randint(1, 20))
        pi, _ = prefix_function(s)
        for i in range(len(s)):
            sub = s[: i + 1]
            expected = max((k for k in range(i + 1) if sub[:k] == sub[i + 1 - k:]), default=0)
            assert pi[i] == expected


def test_kmp_failure_function_example():
    assert prefix_function("abacabab")[0] == [0, 0, 1, 0, 1, 2, 3, 2]


def test_z_function_matches_definition():
    rng = random.Random(6)
    for _ in range(200):
        s = random_string(rng, rng.randint(1, 20))
        z, _ = z_function(s)
        assert z[0] == len(s)
        for i in range(1, len(s)):
            k = 0
            while i + k < len(s) and s[k] == s[i + k]:
                k += 1
            assert z[i] == k


def test_linear_algorithms_beat_naive_on_adversarial_input():
    text, pattern = "a" * 2000, "a" * 50 + "b"
    naive = naive_search(text, pattern).comparisons
    assert kmp_search(text, pattern).comparisons < naive / 10
    assert z_search(text, pattern).comparisons < naive / 10


def test_rabin_karp_uses_two_prime_moduli_and_is_deterministic_per_seed():
    first = rabin_karp("the quick brown fox", "o", seed=3)
    second = rabin_karp("the quick brown fox", "o", seed=3)
    assert first.positions == second.positions == [12, 17]
    assert first.extra["moduli"] == second.extra["moduli"]
    p1, p2 = first.extra["moduli"]
    assert p1 != p2 and p1.bit_length() == 31 and p2.bit_length() == 31
    assert first.extra["hash_hits"] == len(first.positions) + first.extra["spurious_hits"]


def test_aho_corasick_matches_per_pattern_search():
    rng = random.Random(9)
    for _ in range(200):
        text = random_string(rng, rng.randint(0, 50), "abc")
        patterns = [random_string(rng, rng.randint(1, 4), "abc") for _ in range(rng.randint(1, 6))]
        expected = sorted((pos, idx) for idx, p in enumerate(patterns) for pos in occurrences(text, p))
        assert AhoCorasick(patterns).search(text) == expected


def test_aho_corasick_classic_example_with_nested_patterns():
    ac = AhoCorasick(["he", "she", "his", "hers"])
    found = {(pos, ["he", "she", "his", "hers"][idx]) for pos, idx in ac.search("ushers")}
    assert found == {(1, "she"), (2, "he"), (2, "hers")}


def test_suffix_array_and_lcp_match_brute_force():
    rng = random.Random(10)
    for _ in range(200):
        s = random_string(rng, rng.randint(1, 30), rng.choice(["ab", "abc", "a"]))
        sa = suffix_array(s)
        assert sa == sorted(range(len(s)), key=lambda i: s[i:])
        lcp = lcp_kasai(s, sa)
        for i in range(1, len(s)):
            a, b = s[sa[i - 1]:], s[sa[i]:]
            k = 0
            while k < min(len(a), len(b)) and a[k] == b[k]:
                k += 1
            assert lcp[i] == k


def test_suffix_summary_counts_distinct_substrings():
    rng = random.Random(11)
    for _ in range(100):
        s = random_string(rng, rng.randint(1, 15), "abc")
        summary = suffix_structure_summary(s)
        distinct = {s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)}
        assert summary["distinct_substrings"] == len(distinct)
        repeat = summary["longest_repeated_substring"]
        if repeat:
            assert len(occurrences(s, repeat)) >= 2
        longest = max((len(t) for t in distinct if len(occurrences(s, t)) >= 2), default=0)
        assert len(repeat) == longest


def test_banana():
    summary = suffix_structure_summary("banana")
    assert summary["suffix_array"] == [5, 3, 1, 0, 4, 2]
    assert summary["lcp"] == [0, 1, 3, 0, 0, 2]
    assert summary["longest_repeated_substring"] == "ana"
    assert suffix_array_search("banana", "an").positions == [1, 3]
