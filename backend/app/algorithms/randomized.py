"""Module 6 - Randomised algorithms, hand-built.

Las Vegas  = always correct, running time is the random variable
             (random_prime, randomized_quicksort, reservoir_sample)
Monte Carlo = bounded running time, answer correct with high probability
             (miller_rabin with random witnesses, Monte Carlo risk estimation
              in app.services.insights_service)

Contents
  mod_pow                    square-and-multiply, O(log e) multiplications
  fermat_test                fooled by Carmichael numbers (561, 1105, ...)
  miller_rabin               error <= 4^-k for k random witnesses
  is_prime_deterministic     fixed witness set, exact for n < 3.3 * 10^24
  random_prime               Las Vegas prime generation
  UniversalHash              Carter-Wegman family ((a*x + b) mod p) mod m
  reservoir_sample           Algorithm R, uniform k-sample of a stream
  randomized_quicksort       expected O(n log n) on *every* input
  deterministic_quicksort    first-element pivot, O(n^2) on sorted input
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, TypeVar

T = TypeVar("T")

# deterministic Miller-Rabin is exact for every n < 3,317,044,064,679,887,385,961,981 with these bases
_DETERMINISTIC_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
KNOWN_CARMICHAEL = (561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341, 41041, 46657, 52633, 62745, 63973)


def mod_pow(base: int, exponent: int, modulus: int) -> int:
    if modulus == 1:
        return 0
    result = 1
    base %= modulus
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        exponent >>= 1
    return result


def _decompose(n: int) -> tuple[int, int]:
    """n - 1 = 2^s * d with d odd."""
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return s, d


def fermat_test(n: int, bases: Iterable[int]) -> dict:
    """a^(n-1) == 1 (mod n) for every base coprime to n. Carmichael numbers pass this for all such bases."""
    if n < 4:
        return {"n": n, "probably_prime": n in (2, 3), "witnesses": []}
    results = []
    verdict = True
    for a in bases:
        a = a % n
        if a < 2:
            continue
        g = _gcd(a, n)
        value = mod_pow(a, n - 1, n)
        passes = value == 1
        results.append({"a": a, "a_pow_n_minus_1": value, "coprime": g == 1, "passes": passes})
        if g == 1 and not passes:
            verdict = False
    return {"n": n, "probably_prime": verdict, "witnesses": results}


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _miller_rabin_round(n: int, a: int, s: int, d: int) -> tuple[bool, list[int]]:
    """True if `a` does NOT witness compositeness. Also returns the squaring chain for display."""
    x = mod_pow(a, d, n)
    chain = [x]
    if x == 1 or x == n - 1:
        return True, chain
    for _ in range(s - 1):
        x = (x * x) % n
        chain.append(x)
        if x == n - 1:
            return True, chain
    return False, chain


def miller_rabin(n: int, rounds: int = 8, rng: random.Random | None = None, trace: bool = False):
    """Monte Carlo primality test. A composite survives one random round with probability <= 1/4."""
    if n < 2:
        return (False, []) if trace else False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if n in small_primes:
        return (True, []) if trace else True
    if any(n % p == 0 for p in small_primes):
        return (False, [{"a": None, "chain": [], "verdict": "divisible by a small prime"}]) if trace else False

    rng = rng or random.Random()
    s, d = _decompose(n)
    steps: list[dict] = []
    for _ in range(rounds):
        a = rng.randrange(2, n - 1)
        ok, chain = _miller_rabin_round(n, a, s, d)
        steps.append({"a": a, "chain": chain, "verdict": "consistent with prime" if ok else "witness: composite"})
        if not ok:
            return (False, steps) if trace else False
    return (True, steps) if trace else True


def is_prime_deterministic(n: int) -> bool:
    if n < 2:
        return False
    for p in _DETERMINISTIC_BASES:
        if n % p == 0:
            return n == p
    s, d = _decompose(n)
    return all(_miller_rabin_round(n, a, s, d)[0] for a in _DETERMINISTIC_BASES)


def trial_division(n: int, limit: int = 2_000_000) -> bool | None:
    """Ground truth for small n; None if sqrt(n) exceeds `limit` (too slow to be useful)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if i > limit:
            return None
        if n % i == 0:
            return False
        i += 2
    return True


def random_prime(bits: int, rng: random.Random | None = None) -> tuple[int, int]:
    """Las Vegas: draw random odd `bits`-bit numbers until one is prime. Returns (prime, attempts).

    By the prime number theorem about 1 in (bits * ln 2 / 2) odd candidates is
    prime, so the expected number of attempts is O(bits).
    """
    if bits < 3:
        raise ValueError("bits must be >= 3")
    rng = rng or random.Random()
    attempts = 0
    while True:
        attempts += 1
        candidate = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime_deterministic(candidate):
            return candidate, attempts


@dataclass
class UniversalHash:
    """h_{a,b}(x) = ((a*x + b) mod p) mod m, with p prime > every key.

    For any fixed x != y, Pr[h(x) == h(y)] <= 1/m over the random choice of
    (a, b) - the guarantee holds for *every* input, including adversarial ones.
    """

    p: int
    m: int
    a: int
    b: int

    @classmethod
    def random(cls, m: int, max_key: int, rng: random.Random) -> "UniversalHash":
        p = max_key + 1
        while not is_prime_deterministic(p):
            p += 1
        return cls(p=p, m=m, a=rng.randrange(1, p), b=rng.randrange(0, p))

    def __call__(self, x: int) -> int:
        return ((self.a * x + self.b) % self.p) % self.m


def reservoir_sample(stream: Iterable[T], k: int, rng: random.Random | None = None) -> tuple[list[T], int]:
    """Algorithm R. Returns (sample, items_seen).

    Invariant: after seeing i items each one is in the reservoir with
    probability k/i. Item i+1 enters with probability k/(i+1) and evicts a
    uniformly random slot, which keeps every earlier item at
    (k/i) * (1 - 1/(i+1)) = k/(i+1).
    """
    rng = rng or random.Random()
    reservoir: list[T] = []
    seen = 0
    for item in stream:
        seen += 1
        if len(reservoir) < k:
            reservoir.append(item)
        else:
            j = rng.randrange(seen)  # uniform in [0, seen)
            if j < k:
                reservoir[j] = item
    return reservoir, seen


def _partition(arr: list, lo: int, hi: int, pivot_index: int) -> tuple[int, int]:
    """Lomuto partition of arr[lo..hi] around arr[pivot_index]. Returns (final pivot index, comparisons)."""
    arr[pivot_index], arr[hi] = arr[hi], arr[pivot_index]
    pivot = arr[hi]
    store = lo
    for i in range(lo, hi):
        if arr[i] < pivot:
            arr[i], arr[store] = arr[store], arr[i]
            store += 1
    arr[store], arr[hi] = arr[hi], arr[store]
    return store, hi - lo


def _quicksort(values: list, choose_pivot) -> tuple[list, int, int]:
    """Iterative quicksort (explicit stack, so sorted inputs cannot overflow Python's recursion limit).

    Returns (sorted copy, comparisons, max stack depth).
    """
    arr = list(values)
    comparisons = 0
    max_depth = 0
    stack: list[tuple[int, int, int]] = [(0, len(arr) - 1, 1)]
    while stack:
        lo, hi, depth = stack.pop()
        if lo >= hi:
            continue
        max_depth = max(max_depth, depth)
        p, c = _partition(arr, lo, hi, choose_pivot(lo, hi))
        comparisons += c
        stack.append((lo, p - 1, depth + 1))
        stack.append((p + 1, hi, depth + 1))
    return arr, comparisons, max_depth


def randomized_quicksort(values: list, rng: random.Random | None = None) -> tuple[list, int, int]:
    rng = rng or random.Random()
    return _quicksort(values, lambda lo, hi: rng.randint(lo, hi))


def deterministic_quicksort(values: list) -> tuple[list, int, int]:
    return _quicksort(values, lambda lo, hi: lo)
