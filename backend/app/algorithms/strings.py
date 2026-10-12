"""Module 2 - String algorithms, all hand-built.

Every search routine counts its character comparisons so the Concept Lab and
the entity search endpoint can show *why* the linear-time algorithms beat
the naive O(n*m) scan, not just that they return the same positions.

Conventions used throughout this module:
  * positions are 0-based start indices of each occurrence (overlaps included)
  * an empty pattern, or a pattern longer than the text, has no occurrences

Contents
  naive_search            O(n*m)
  prefix_function / kmp   O(n + m)            Knuth-Morris-Pratt
  z_function / z_search   O(n + m)
  rabin_karp              O(n + m) expected   double polynomial hashing,
                                              moduli are random primes found
                                              with Miller-Rabin (Module 6)
  AhoCorasick             O(n + sum|P| + z)   multi-pattern trie + failure links
  suffix_array            O(n log^2 n)        prefix doubling
  lcp_kasai               O(n)
  suffix_array_search     O(m log n)
"""
from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Sequence

from app.algorithms.randomized import random_prime


@dataclass
class SearchResult:
    algorithm: str
    positions: list[int]
    comparisons: int
    execution_time_ms: float = 0.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "positions": self.positions,
            "occurrences": len(self.positions),
            "comparisons": self.comparisons,
            "execution_time_ms": self.execution_time_ms,
            **self.extra,
        }


def _trivial(text: Sequence, pattern: Sequence) -> bool:
    return len(pattern) == 0 or len(pattern) > len(text)


# --------------------------------------------------------------------------- naive


def naive_search(text: str, pattern: str) -> SearchResult:
    start = time.perf_counter()
    positions: list[int] = []
    comparisons = 0
    if not _trivial(text, pattern):
        n, m = len(text), len(pattern)
        for i in range(n - m + 1):
            j = 0
            while j < m:
                comparisons += 1
                if text[i + j] != pattern[j]:
                    break
                j += 1
            if j == m:
                positions.append(i)
    return SearchResult("NAIVE", positions, comparisons, (time.perf_counter() - start) * 1000)


# --------------------------------------------------------------------------- KMP


def prefix_function(pattern: Sequence) -> tuple[list[int], int]:
    """pi[i] = length of the longest proper prefix of pattern[:i+1] that is also its suffix.

    Returns (pi, comparisons). Amortised O(m): `k` rises by at most one per
    step and every fallback strictly decreases it.
    """
    m = len(pattern)
    pi = [0] * m
    comparisons = 0
    k = 0
    for i in range(1, m):
        while True:
            comparisons += 1
            if pattern[i] == pattern[k]:
                k += 1
                break
            if k == 0:
                break
            k = pi[k - 1]  # fall back to the next-longest border
        pi[i] = k
    return pi, comparisons


def kmp_search(text: str, pattern: str) -> SearchResult:
    start = time.perf_counter()
    if _trivial(text, pattern):
        pi = prefix_function(pattern)[0] if pattern else []
        return SearchResult("KMP", [], 0, (time.perf_counter() - start) * 1000, {"failure_function": pi})

    pi, comparisons = prefix_function(pattern)
    preprocessing = comparisons
    positions: list[int] = []
    m = len(pattern)
    k = 0  # number of pattern characters currently matched
    for i, ch in enumerate(text):
        while True:
            comparisons += 1
            if ch == pattern[k]:
                k += 1
                break
            if k == 0:
                break
            k = pi[k - 1]
        if k == m:
            positions.append(i - m + 1)
            k = pi[k - 1]
    return SearchResult(
        "KMP",
        positions,
        comparisons,
        (time.perf_counter() - start) * 1000,
        {"failure_function": pi, "preprocessing_comparisons": preprocessing},
    )


# --------------------------------------------------------------------------- Z


def z_function(s: Sequence) -> tuple[list[int], int]:
    """z[i] = length of the longest common prefix of s and s[i:]; z[0] = len(s).

    Maintains the rightmost match window [l, r); positions inside it reuse
    earlier answers, so every comparison either extends r or ends a scan,
    giving O(n) total.
    """
    n = len(s)
    z = [0] * n
    if n == 0:
        return z, 0
    z[0] = n
    comparisons = 0
    l = r = 0
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])
        while i + z[i] < n:
            comparisons += 1
            if s[z[i]] != s[i + z[i]]:
                break
            z[i] += 1
        if i + z[i] > r:
            l, r = i, i + z[i]
    return z, comparisons


_SENTINEL = object()  # compares unequal to every character, so no separator char is needed


def z_search(text: str, pattern: str) -> SearchResult:
    start = time.perf_counter()
    if _trivial(text, pattern):
        return SearchResult("Z_FUNCTION", [], 0, (time.perf_counter() - start) * 1000, {"z_array": []})
    m = len(pattern)
    combined: list = [*pattern, _SENTINEL, *text]
    z, comparisons = z_function(combined)
    positions = [i - m - 1 for i in range(m + 1, len(combined)) if z[i] >= m]
    return SearchResult(
        "Z_FUNCTION",
        positions,
        comparisons,
        (time.perf_counter() - start) * 1000,
        # z over "pattern $ text" - the sentinel slot is reported as 0 for display
        {"z_array": [0 if i == m else v for i, v in enumerate(z)]},
    )


# --------------------------------------------------------------------------- Rabin-Karp


def rabin_karp(text: str, pattern: str, seed: int | None = None) -> SearchResult:
    """Double-hash Rabin-Karp.

    Two independent (base, prime) pairs are drawn at random; the primes are
    31-bit and generated by a Las Vegas loop around Miller-Rabin. A window is
    only verified character-by-character when *both* rolling hashes agree,
    which makes spurious verifications vanishingly rare - the run reports how
    many happened so the effect of double hashing is observable.
    """
    start = time.perf_counter()
    rng = random.Random(seed)
    p1, _ = random_prime(31, rng)
    p2, _ = random_prime(31, rng)
    while p2 == p1:
        p2, _ = random_prime(31, rng)
    b1 = rng.randrange(257, p1 - 1)
    b2 = rng.randrange(257, p2 - 1)
    params = {"moduli": [p1, p2], "bases": [b1, b2]}

    if _trivial(text, pattern):
        return SearchResult("RABIN_KARP", [], 0, (time.perf_counter() - start) * 1000, {**params, "hash_hits": 0, "spurious_hits": 0})

    n, m = len(text), len(pattern)
    hp1 = hp2 = ht1 = ht2 = 0
    for i in range(m):
        hp1 = (hp1 * b1 + ord(pattern[i])) % p1
        hp2 = (hp2 * b2 + ord(pattern[i])) % p2
        ht1 = (ht1 * b1 + ord(text[i])) % p1
        ht2 = (ht2 * b2 + ord(text[i])) % p2
    # b^(m-1) mod p, used to remove the outgoing character
    pow1 = pow2 = 1
    for _ in range(m - 1):
        pow1 = (pow1 * b1) % p1
        pow2 = (pow2 * b2) % p2

    positions: list[int] = []
    comparisons = 0
    hash_hits = 0
    spurious = 0
    for i in range(n - m + 1):
        if ht1 == hp1 and ht2 == hp2:
            hash_hits += 1
            j = 0
            while j < m:
                comparisons += 1
                if text[i + j] != pattern[j]:
                    break
                j += 1
            if j == m:
                positions.append(i)
            else:
                spurious += 1
        if i + m < n:
            ht1 = ((ht1 - ord(text[i]) * pow1) * b1 + ord(text[i + m])) % p1
            ht2 = ((ht2 - ord(text[i]) * pow2) * b2 + ord(text[i + m])) % p2

    return SearchResult(
        "RABIN_KARP",
        positions,
        comparisons,
        (time.perf_counter() - start) * 1000,
        {**params, "hash_hits": hash_hits, "spurious_hits": spurious, "windows_hashed": n - m + 1},
    )


# --------------------------------------------------------------------------- Aho-Corasick


class AhoCorasick:
    """Multi-pattern matcher: a trie of all patterns plus BFS-built failure links.

    fail[v]   -> node for the longest proper suffix of v's string that is also a trie path
    dict_link -> nearest node along the failure chain that ends a pattern
                 (so reporting all matches at a position costs O(matches), not O(depth))
    """

    def __init__(self, patterns: Sequence[str]) -> None:
        self.patterns = list(patterns)
        self.children: list[dict[str, int]] = [{}]
        self.fail: list[int] = [0]
        self.ends: list[list[int]] = [[]]  # pattern indices ending exactly at this node
        self.dict_link: list[int] = [-1]

        for idx, pattern in enumerate(self.patterns):
            if not pattern:
                continue
            node = 0
            for ch in pattern:
                nxt = self.children[node].get(ch)
                if nxt is None:
                    nxt = len(self.children)
                    self.children[node][ch] = nxt
                    self.children.append({})
                    self.fail.append(0)
                    self.ends.append([])
                    self.dict_link.append(-1)
                node = nxt
            self.ends[node].append(idx)

        queue: deque[int] = deque()
        for child in self.children[0].values():
            queue.append(child)  # depth-1 nodes fail to the root
        while queue:
            node = queue.popleft()
            for ch, child in self.children[node].items():
                f = self.fail[node]
                while f and ch not in self.children[f]:
                    f = self.fail[f]
                candidate = self.children[f].get(ch, 0)
                self.fail[child] = candidate if candidate != child else 0
                target = self.fail[child]
                self.dict_link[child] = target if self.ends[target] else self.dict_link[target]
                queue.append(child)

    @property
    def num_nodes(self) -> int:
        return len(self.children)

    def search(self, text: str) -> list[tuple[int, int]]:
        """Returns (start_position, pattern_index) for every occurrence, in text order."""
        matches: list[tuple[int, int]] = []
        node = 0
        for i, ch in enumerate(text):
            while node and ch not in self.children[node]:
                node = self.fail[node]
            node = self.children[node].get(ch, 0)
            out = node
            while out > 0:
                for idx in self.ends[out]:
                    matches.append((i - len(self.patterns[idx]) + 1, idx))
                out = self.dict_link[out]
        matches.sort()
        return matches

    def found_set(self, text: str) -> set[int]:
        return {idx for _, idx in self.search(text)}

    def describe(self) -> list[dict]:
        """Node table for visualisation: string spelled by each node, its failure target, outputs."""
        labels = [""] * self.num_nodes
        queue: deque[int] = deque([0])
        while queue:
            node = queue.popleft()
            for ch, child in self.children[node].items():
                labels[child] = labels[node] + ch
                queue.append(child)
        return [
            {
                "node": v,
                "label": labels[v],
                "fail": self.fail[v],
                "fail_label": labels[self.fail[v]],
                "outputs": [self.patterns[i] for i in self.ends[v]],
            }
            for v in range(self.num_nodes)
        ]


# --------------------------------------------------------------------------- suffix structures


def suffix_array(s: str) -> list[int]:
    """Prefix-doubling construction: sort suffixes by their first 2^k characters.

    Each round sorts by the pair (rank[i], rank[i+k]) - O(n log n) per round,
    O(log n) rounds -> the practical O(n log^2 n) bound. (SA-IS reaches O(n)
    by induced sorting; this is the version taught for implementation.)
    """
    n = len(s)
    if n == 0:
        return []
    sa = list(range(n))
    rank = [ord(c) for c in s]
    k = 1
    while True:
        key = lambda i: (rank[i], rank[i + k] if i + k < n else -1)  # noqa: E731
        sa.sort(key=key)
        new_rank = [0] * n
        for idx in range(1, n):
            new_rank[sa[idx]] = new_rank[sa[idx - 1]] + (key(sa[idx]) != key(sa[idx - 1]))
        rank = new_rank
        if rank[sa[-1]] == n - 1 or k >= n:
            break
        k *= 2
    return sa


def lcp_kasai(s: str, sa: list[int]) -> list[int]:
    """lcp[i] = longest common prefix of suffixes sa[i-1] and sa[i]; lcp[0] = 0.

    Kasai's observation: moving from suffix i to i+1 drops at most one
    character of the previous LCP, so the pointer `h` only decreases by one
    per step and the whole pass is O(n).
    """
    n = len(s)
    lcp = [0] * n
    if n == 0:
        return lcp
    rank = [0] * n
    for i, pos in enumerate(sa):
        rank[pos] = i
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h > 0:
                h -= 1
        else:
            h = 0
    return lcp


def _compare_prefix(text: str, start: int, pattern: str) -> tuple[int, int]:
    """Compares text[start:start+m] against pattern. Returns (-1|0|1, comparisons)."""
    comparisons = 0
    m = len(pattern)
    for j in range(m):
        if start + j >= len(text):
            return -1, comparisons  # suffix shorter than pattern and equal so far -> smaller
        comparisons += 1
        a, b = text[start + j], pattern[j]
        if a != b:
            return (-1 if a < b else 1), comparisons
    return 0, comparisons


def suffix_array_search(text: str, pattern: str, sa: list[int] | None = None) -> SearchResult:
    """Two binary searches over the suffix array bracket every suffix that starts with `pattern`."""
    start = time.perf_counter()
    if _trivial(text, pattern):
        return SearchResult("SUFFIX_ARRAY", [], 0, (time.perf_counter() - start) * 1000)
    sa = sa if sa is not None else suffix_array(text)
    comparisons = 0

    lo, hi = 0, len(sa)
    while lo < hi:  # first suffix >= pattern
        mid = (lo + hi) // 2
        cmp, c = _compare_prefix(text, sa[mid], pattern)
        comparisons += c
        if cmp < 0:
            lo = mid + 1
        else:
            hi = mid
    first = lo

    hi = len(sa)
    while lo < hi:  # first suffix whose prefix > pattern
        mid = (lo + hi) // 2
        cmp, c = _compare_prefix(text, sa[mid], pattern)
        comparisons += c
        if cmp <= 0:
            lo = mid + 1
        else:
            hi = mid
    positions = sorted(sa[first:lo])
    return SearchResult(
        "SUFFIX_ARRAY", positions, comparisons, (time.perf_counter() - start) * 1000, {"sa_range": [first, lo]}
    )


def suffix_structure_summary(s: str) -> dict:
    sa = suffix_array(s)
    lcp = lcp_kasai(s, sa)
    n = len(s)
    best = max(range(n), key=lambda i: lcp[i], default=0)
    longest_repeat = s[sa[best]: sa[best] + lcp[best]] if n and lcp[best] > 0 else ""
    return {
        "suffix_array": sa,
        "lcp": lcp,
        "suffixes": [s[i:] for i in sa],
        "longest_repeated_substring": longest_repeat,
        # every distinct substring is a prefix of exactly one suffix, minus prefixes shared with the previous suffix
        "distinct_substrings": n * (n + 1) // 2 - sum(lcp),
    }


SEARCH_ALGORITHMS = {
    "NAIVE": naive_search,
    "KMP": kmp_search,
    "Z_FUNCTION": z_search,
    "RABIN_KARP": rabin_karp,
    "SUFFIX_ARRAY": suffix_array_search,
}


def find_all(text: str, pattern: str, algorithm: str = "KMP") -> SearchResult:
    try:
        fn = SEARCH_ALGORITHMS[algorithm]
    except KeyError as exc:
        raise ValueError(f"Unknown string algorithm: {algorithm}") from exc
    return fn(text, pattern)
