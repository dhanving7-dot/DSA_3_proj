package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.function.IntBinaryOperator;
import java.util.random.RandomGenerator;

/**
 * Module 6 - Randomised algorithms, hand-built.
 *
 * <p>Las Vegas = always correct, running time is the random variable (random prime, randomised
 * quicksort, reservoir sampling). Monte Carlo = bounded running time, answer correct with high
 * probability (Miller-Rabin with random witnesses).
 *
 * <p>All arithmetic is on {@code long}, so inputs are limited to n &lt; 2^63 (Python's version
 * accepted arbitrary-precision integers).
 */
public final class Randomized {
    /** Deterministic Miller-Rabin is exact for every n &lt; 3.3 * 10^24 with these bases (so for every long). */
    private static final long[] DETERMINISTIC_BASES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41};
    private static final long[] SMALL_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37};
    public static final long[] KNOWN_CARMICHAEL = {
            561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341, 41041, 46657, 52633, 62745, 63973};

    private Randomized() {}

    /** a + b (mod m) for 0 &lt;= a, b &lt; m, without overflowing for any positive long m. */
    private static long addMod(long a, long b, long m) {
        return a >= m - b ? a - (m - b) : a + b;
    }

    /** a * b (mod m): direct when the product fits in a long, otherwise double-and-add. */
    static long mulMod(long a, long b, long m) {
        a %= m;
        b %= m;
        if (a < 3_037_000_499L && b < 3_037_000_499L) {
            return a * b % m;
        }
        long result = 0;
        while (b > 0) {
            if ((b & 1) == 1) {
                result = addMod(result, a, m);
            }
            a = addMod(a, a, m);
            b >>= 1;
        }
        return result;
    }

    /** Square-and-multiply, O(log e) multiplications. */
    public static long modPow(long base, long exponent, long modulus) {
        if (modulus == 1) {
            return 0;
        }
        long result = 1;
        base = Math.floorMod(base, modulus);
        while (exponent > 0) {
            if ((exponent & 1) == 1) {
                result = mulMod(result, base, modulus);
            }
            base = mulMod(base, base, modulus);
            exponent >>= 1;
        }
        return result;
    }

    /** n - 1 = 2^s * d with d odd; returns {s, d}. */
    private static long[] decompose(long n) {
        long d = n - 1;
        long s = 0;
        while (d % 2 == 0) {
            d /= 2;
            s++;
        }
        return new long[] {s, d};
    }

    static long gcd(long a, long b) {
        while (b != 0) {
            long t = a % b;
            a = b;
            b = t;
        }
        return a;
    }

    public record FermatWitness(long a, long aPowNMinus1, boolean coprime, boolean passes) {}

    public record FermatResult(long n, boolean probablyPrime, List<FermatWitness> witnesses) {}

    /** a^(n-1) == 1 (mod n) for every base coprime to n. Carmichael numbers pass this for all such bases. */
    public static FermatResult fermatTest(long n, long[] bases) {
        if (n < 4) {
            return new FermatResult(n, n == 2 || n == 3, List.of());
        }
        List<FermatWitness> results = new ArrayList<>();
        boolean verdict = true;
        for (long base : bases) {
            long a = base % n;
            if (a < 2) {
                continue;
            }
            long g = gcd(a, n);
            long value = modPow(a, n - 1, n);
            boolean passes = value == 1;
            results.add(new FermatWitness(a, value, g == 1, passes));
            if (g == 1 && !passes) {
                verdict = false;
            }
        }
        return new FermatResult(n, verdict, results);
    }

    private record RoundOutcome(boolean consistentWithPrime, List<Long> chain) {}

    /** consistentWithPrime is true if {@code a} does NOT witness compositeness; chain is the squaring sequence. */
    private static RoundOutcome millerRabinRound(long n, long a, long s, long d) {
        long x = modPow(a, d, n);
        List<Long> chain = new ArrayList<>();
        chain.add(x);
        if (x == 1 || x == n - 1) {
            return new RoundOutcome(true, chain);
        }
        for (long r = 0; r < s - 1; r++) {
            x = mulMod(x, x, n);
            chain.add(x);
            if (x == n - 1) {
                return new RoundOutcome(true, chain);
            }
        }
        return new RoundOutcome(false, chain);
    }

    /** @param a null when the verdict came from small-prime trial division */
    public record MillerRabinStep(Long a, List<Long> chain, String verdict) {}

    public record MillerRabinTrace(boolean probablyPrime, List<MillerRabinStep> steps) {}

    public static boolean millerRabin(long n, int rounds, RandomGenerator rng) {
        return millerRabinTrace(n, rounds, rng).probablyPrime();
    }

    /** Monte Carlo primality test. A composite survives one random round with probability &lt;= 1/4. */
    public static MillerRabinTrace millerRabinTrace(long n, int rounds, RandomGenerator rng) {
        if (n < 2) {
            return new MillerRabinTrace(false, List.of());
        }
        for (long p : SMALL_PRIMES) {
            if (n == p) {
                return new MillerRabinTrace(true, List.of());
            }
        }
        for (long p : SMALL_PRIMES) {
            if (n % p == 0) {
                return new MillerRabinTrace(false,
                        List.of(new MillerRabinStep(null, List.of(), "divisible by a small prime")));
            }
        }
        if (rng == null) {
            rng = new Random();
        }
        long[] sd = decompose(n);
        List<MillerRabinStep> steps = new ArrayList<>();
        for (int r = 0; r < rounds; r++) {
            long a = rng.nextLong(2, n - 1); // uniform in [2, n - 2]
            RoundOutcome outcome = millerRabinRound(n, a, sd[0], sd[1]);
            boolean ok = outcome.consistentWithPrime();
            steps.add(new MillerRabinStep(a, outcome.chain(), ok ? "consistent with prime" : "witness: composite"));
            if (!ok) {
                return new MillerRabinTrace(false, steps);
            }
        }
        return new MillerRabinTrace(true, steps);
    }

    public static boolean isPrimeDeterministic(long n) {
        if (n < 2) {
            return false;
        }
        for (long p : DETERMINISTIC_BASES) {
            if (n % p == 0) {
                return n == p;
            }
        }
        long[] sd = decompose(n);
        for (long a : DETERMINISTIC_BASES) {
            if (!millerRabinRound(n, a, sd[0], sd[1]).consistentWithPrime()) {
                return false;
            }
        }
        return true;
    }

    public static Boolean trialDivision(long n) {
        return trialDivision(n, 2_000_000L);
    }

    /** Ground truth for small n; null if sqrt(n) exceeds {@code limit} (too slow to be useful). */
    public static Boolean trialDivision(long n, long limit) {
        if (n < 2) {
            return false;
        }
        if (n < 4) {
            return true;
        }
        if (n % 2 == 0) {
            return false;
        }
        for (long i = 3; i * i <= n; i += 2) {
            if (i > limit) {
                return null;
            }
            if (n % i == 0) {
                return false;
            }
        }
        return true;
    }

    public record RandomPrime(long prime, int attempts) {}

    /**
     * Las Vegas: draw random odd {@code bits}-bit numbers until one is prime. By the prime number
     * theorem about 1 in (bits * ln 2 / 2) odd candidates is prime, so the expected number of
     * attempts is O(bits).
     */
    public static RandomPrime randomPrime(int bits, RandomGenerator rng) {
        if (bits < 3 || bits > 62) {
            throw new IllegalArgumentException("bits must be in [3, 62]");
        }
        if (rng == null) {
            rng = new Random();
        }
        int attempts = 0;
        while (true) {
            attempts++;
            long candidate = (rng.nextLong() >>> (64 - bits)) | (1L << (bits - 1)) | 1L;
            if (isPrimeDeterministic(candidate)) {
                return new RandomPrime(candidate, attempts);
            }
        }
    }

    /**
     * h_{a,b}(x) = ((a*x + b) mod p) mod m, with p prime &gt; every key. For any fixed x != y,
     * Pr[h(x) == h(y)] &lt;= 1/m over the random choice of (a, b) - for every input, including
     * adversarial ones.
     */
    public record UniversalHash(long p, long m, long a, long b) {
        public static UniversalHash random(long m, long maxKey, RandomGenerator rng) {
            long p = maxKey + 1;
            while (!isPrimeDeterministic(p)) {
                p++;
            }
            return new UniversalHash(p, m, rng.nextLong(1, p), rng.nextLong(0, p));
        }

        public long apply(long x) {
            return addMod(mulMod(a, Math.floorMod(x, p), p), b, p) % m;
        }
    }

    public record Reservoir<T>(List<T> sample, int seen) {}

    /**
     * Algorithm R. Invariant: after seeing i items each one is in the reservoir with probability
     * k/i. Item i+1 enters with probability k/(i+1) and evicts a uniformly random slot, which keeps
     * every earlier item at (k/i) * (1 - 1/(i+1)) = k/(i+1).
     */
    public static <T> Reservoir<T> reservoirSample(Iterable<T> stream, int k, RandomGenerator rng) {
        if (rng == null) {
            rng = new Random();
        }
        List<T> reservoir = new ArrayList<>();
        int seen = 0;
        for (T item : stream) {
            seen++;
            if (reservoir.size() < k) {
                reservoir.add(item);
            } else {
                int j = rng.nextInt(seen); // uniform in [0, seen)
                if (j < k) {
                    reservoir.set(j, item);
                }
            }
        }
        return new Reservoir<>(reservoir, seen);
    }

    public record SortResult(int[] sorted, long comparisons, int maxDepth) {}

    /** Lomuto partition of arr[lo..hi] around arr[pivotIndex]; returns the final pivot index. */
    private static int partition(int[] arr, int lo, int hi, int pivotIndex) {
        swap(arr, pivotIndex, hi);
        int pivot = arr[hi];
        int store = lo;
        for (int i = lo; i < hi; i++) {
            if (arr[i] < pivot) {
                swap(arr, i, store);
                store++;
            }
        }
        swap(arr, store, hi);
        return store;
    }

    private static void swap(int[] arr, int i, int j) {
        int t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
    }

    /** Iterative quicksort (explicit stack, so sorted inputs cannot overflow the call stack). */
    private static SortResult quicksort(int[] values, IntBinaryOperator choosePivot) {
        int[] arr = Arrays.copyOf(values, values.length);
        long comparisons = 0;
        int maxDepth = 0;
        ArrayDeque<int[]> stack = new ArrayDeque<>();
        stack.push(new int[] {0, arr.length - 1, 1});
        while (!stack.isEmpty()) {
            int[] frame = stack.pop();
            int lo = frame[0];
            int hi = frame[1];
            int depth = frame[2];
            if (lo >= hi) {
                continue;
            }
            maxDepth = Math.max(maxDepth, depth);
            int p = partition(arr, lo, hi, choosePivot.applyAsInt(lo, hi));
            comparisons += hi - lo;
            stack.push(new int[] {lo, p - 1, depth + 1});
            stack.push(new int[] {p + 1, hi, depth + 1});
        }
        return new SortResult(arr, comparisons, maxDepth);
    }

    /** Expected O(n log n) on <em>every</em> input. */
    public static SortResult randomizedQuicksort(int[] values, RandomGenerator rng) {
        RandomGenerator r = rng != null ? rng : new Random();
        return quicksort(values, (lo, hi) -> r.nextInt(lo, hi + 1));
    }

    /** First-element pivot: O(n^2) on sorted input. */
    public static SortResult deterministicQuicksort(int[] values) {
        return quicksort(values, (lo, hi) -> lo);
    }
}
