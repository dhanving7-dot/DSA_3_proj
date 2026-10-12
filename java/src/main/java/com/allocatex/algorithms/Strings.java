package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.function.BiFunction;

/**
 * Module 2 - String algorithms, all hand-built.
 *
 * <p>Every search routine counts its character comparisons so callers can show <em>why</em> the
 * linear-time algorithms beat the naive O(n*m) scan, not just that they return the same positions.
 *
 * <p>Conventions: positions are 0-based start indices of each occurrence (overlaps included); an
 * empty pattern, or a pattern longer than the text, has no occurrences.
 *
 * <ul>
 *   <li>naive search - O(n*m)</li>
 *   <li>prefix function / KMP - O(n + m)</li>
 *   <li>Z-function / Z search - O(n + m)</li>
 *   <li>Rabin-Karp - O(n + m) expected; double polynomial hashing, moduli are random primes found
 *       with Miller-Rabin</li>
 *   <li>{@link AhoCorasick} - O(n + sum|P| + z)</li>
 *   <li>suffix array - O(n log^2 n) prefix doubling; LCP (Kasai) - O(n); suffix array search -
 *       O(m log n)</li>
 * </ul>
 */
public final class Strings {
    private Strings() {}

    public record SearchResult(String algorithm, List<Integer> positions, long comparisons, double executionTimeMs,
                               Map<String, Object> extra) {
        public int occurrences() {
            return positions.size();
        }
    }

    private static boolean trivial(int textLength, int patternLength) {
        return patternLength == 0 || patternLength > textLength;
    }

    private static double msSince(long startNanos) {
        return (System.nanoTime() - startNanos) / 1e6;
    }

    // ------------------------------------------------------------------ naive

    public static SearchResult naiveSearch(String text, String pattern) {
        long start = System.nanoTime();
        List<Integer> positions = new ArrayList<>();
        long comparisons = 0;
        if (!trivial(text.length(), pattern.length())) {
            int n = text.length();
            int m = pattern.length();
            for (int i = 0; i <= n - m; i++) {
                int j = 0;
                while (j < m) {
                    comparisons++;
                    if (text.charAt(i + j) != pattern.charAt(j)) {
                        break;
                    }
                    j++;
                }
                if (j == m) {
                    positions.add(i);
                }
            }
        }
        return new SearchResult("NAIVE", positions, comparisons, msSince(start), Map.of());
    }

    // ------------------------------------------------------------------ KMP

    public record PrefixFunction(int[] pi, long comparisons) {}

    /**
     * pi[i] = length of the longest proper prefix of pattern[0..i] that is also its suffix.
     * Amortised O(m): {@code k} rises by at most one per step and every fallback strictly decreases it.
     */
    public static PrefixFunction prefixFunction(String pattern) {
        int m = pattern.length();
        int[] pi = new int[m];
        long comparisons = 0;
        int k = 0;
        for (int i = 1; i < m; i++) {
            while (true) {
                comparisons++;
                if (pattern.charAt(i) == pattern.charAt(k)) {
                    k++;
                    break;
                }
                if (k == 0) {
                    break;
                }
                k = pi[k - 1]; // fall back to the next-longest border
            }
            pi[i] = k;
        }
        return new PrefixFunction(pi, comparisons);
    }

    public static SearchResult kmpSearch(String text, String pattern) {
        long start = System.nanoTime();
        if (trivial(text.length(), pattern.length())) {
            int[] pi = prefixFunction(pattern).pi();
            return new SearchResult("KMP", List.of(), 0, msSince(start), Map.of("failure_function", pi));
        }

        PrefixFunction pf = prefixFunction(pattern);
        int[] pi = pf.pi();
        long comparisons = pf.comparisons();
        long preprocessing = comparisons;
        List<Integer> positions = new ArrayList<>();
        int m = pattern.length();
        int k = 0; // number of pattern characters currently matched
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            while (true) {
                comparisons++;
                if (ch == pattern.charAt(k)) {
                    k++;
                    break;
                }
                if (k == 0) {
                    break;
                }
                k = pi[k - 1];
            }
            if (k == m) {
                positions.add(i - m + 1);
                k = pi[k - 1];
            }
        }
        Map<String, Object> extra = new LinkedHashMap<>();
        extra.put("failure_function", pi);
        extra.put("preprocessing_comparisons", preprocessing);
        return new SearchResult("KMP", positions, comparisons, msSince(start), extra);
    }

    // ------------------------------------------------------------------ Z

    public record ZFunction(int[] z, long comparisons) {}

    public static ZFunction zFunction(String s) {
        return zFunction(s.chars().toArray());
    }

    /**
     * z[i] = length of the longest common prefix of s and s[i..]; z[0] = len(s).
     *
     * <p>Maintains the rightmost match window [l, r); positions inside it reuse earlier answers, so
     * every comparison either extends r or ends a scan, giving O(n) total.
     */
    public static ZFunction zFunction(int[] s) {
        int n = s.length;
        int[] z = new int[n];
        if (n == 0) {
            return new ZFunction(z, 0);
        }
        z[0] = n;
        long comparisons = 0;
        int l = 0;
        int r = 0;
        for (int i = 1; i < n; i++) {
            if (i < r) {
                z[i] = Math.min(r - i, z[i - l]);
            }
            while (i + z[i] < n) {
                comparisons++;
                if (s[z[i]] != s[i + z[i]]) {
                    break;
                }
                z[i]++;
            }
            if (i + z[i] > r) {
                l = i;
                r = i + z[i];
            }
        }
        return new ZFunction(z, comparisons);
    }

    /** Compares unequal to every character, so no separator char is needed. */
    private static final int SENTINEL = -1;

    public static SearchResult zSearch(String text, String pattern) {
        long start = System.nanoTime();
        if (trivial(text.length(), pattern.length())) {
            return new SearchResult("Z_FUNCTION", List.of(), 0, msSince(start), Map.of("z_array", new int[0]));
        }
        int m = pattern.length();
        int[] combined = new int[m + 1 + text.length()];
        for (int i = 0; i < m; i++) {
            combined[i] = pattern.charAt(i);
        }
        combined[m] = SENTINEL;
        for (int i = 0; i < text.length(); i++) {
            combined[m + 1 + i] = text.charAt(i);
        }
        ZFunction zf = zFunction(combined);
        int[] z = zf.z();
        List<Integer> positions = new ArrayList<>();
        for (int i = m + 1; i < combined.length; i++) {
            if (z[i] >= m) {
                positions.add(i - m - 1);
            }
        }
        // z over "pattern $ text" - the sentinel slot is reported as 0 for display
        int[] display = z.clone();
        display[m] = 0;
        return new SearchResult("Z_FUNCTION", positions, zf.comparisons(), msSince(start), Map.of("z_array", display));
    }

    // ------------------------------------------------------------------ Rabin-Karp

    public static SearchResult rabinKarp(String text, String pattern) {
        return rabinKarp(text, pattern, null);
    }

    /**
     * Double-hash Rabin-Karp.
     *
     * <p>Two independent (base, prime) pairs are drawn at random; the primes are 31-bit and generated
     * by a Las Vegas loop around Miller-Rabin. A window is only verified character-by-character when
     * <em>both</em> rolling hashes agree, which makes spurious verifications vanishingly rare - the
     * run reports how many happened so the effect of double hashing is observable.
     */
    public static SearchResult rabinKarp(String text, String pattern, Long seed) {
        long start = System.nanoTime();
        Random rng = seed != null ? new Random(seed) : new Random();
        long p1 = Randomized.randomPrime(31, rng).prime();
        long p2 = Randomized.randomPrime(31, rng).prime();
        while (p2 == p1) {
            p2 = Randomized.randomPrime(31, rng).prime();
        }
        long b1 = rng.nextLong(257, p1 - 1);
        long b2 = rng.nextLong(257, p2 - 1);
        Map<String, Object> extra = new LinkedHashMap<>();
        extra.put("moduli", List.of(p1, p2));
        extra.put("bases", List.of(b1, b2));

        if (trivial(text.length(), pattern.length())) {
            extra.put("hash_hits", 0);
            extra.put("spurious_hits", 0);
            return new SearchResult("RABIN_KARP", List.of(), 0, msSince(start), extra);
        }

        int n = text.length();
        int m = pattern.length();
        // every hash stays below a 31-bit prime, so hash * base fits comfortably in a long
        long hp1 = 0, hp2 = 0, ht1 = 0, ht2 = 0;
        for (int i = 0; i < m; i++) {
            hp1 = (hp1 * b1 + pattern.charAt(i)) % p1;
            hp2 = (hp2 * b2 + pattern.charAt(i)) % p2;
            ht1 = (ht1 * b1 + text.charAt(i)) % p1;
            ht2 = (ht2 * b2 + text.charAt(i)) % p2;
        }
        // b^(m-1) mod p, used to remove the outgoing character
        long pow1 = 1, pow2 = 1;
        for (int i = 0; i < m - 1; i++) {
            pow1 = pow1 * b1 % p1;
            pow2 = pow2 * b2 % p2;
        }

        List<Integer> positions = new ArrayList<>();
        long comparisons = 0;
        int hashHits = 0;
        int spurious = 0;
        for (int i = 0; i <= n - m; i++) {
            if (ht1 == hp1 && ht2 == hp2) {
                hashHits++;
                int j = 0;
                while (j < m) {
                    comparisons++;
                    if (text.charAt(i + j) != pattern.charAt(j)) {
                        break;
                    }
                    j++;
                }
                if (j == m) {
                    positions.add(i);
                } else {
                    spurious++;
                }
            }
            if (i + m < n) {
                ht1 = (Math.floorMod(ht1 - text.charAt(i) * pow1 % p1, p1) * b1 + text.charAt(i + m)) % p1;
                ht2 = (Math.floorMod(ht2 - text.charAt(i) * pow2 % p2, p2) * b2 + text.charAt(i + m)) % p2;
            }
        }

        extra.put("hash_hits", hashHits);
        extra.put("spurious_hits", spurious);
        extra.put("windows_hashed", n - m + 1);
        return new SearchResult("RABIN_KARP", positions, comparisons, msSince(start), extra);
    }

    // ------------------------------------------------------------------ suffix structures

    /**
     * Prefix-doubling construction: sort suffixes by their first 2^k characters.
     *
     * <p>Each round sorts by the pair (rank[i], rank[i+k]) - O(n log n) per round, O(log n) rounds,
     * the practical O(n log^2 n) bound.
     */
    public static int[] suffixArray(String s) {
        int n = s.length();
        if (n == 0) {
            return new int[0];
        }
        Integer[] sa = new Integer[n];
        int[] rank = new int[n];
        for (int i = 0; i < n; i++) {
            sa[i] = i;
            rank[i] = s.charAt(i);
        }
        for (int k = 1; ; k *= 2) {
            final int step = k;
            final int[] r = rank;
            java.util.Comparator<Integer> byPair = (a, b) -> {
                if (r[a] != r[b]) {
                    return Integer.compare(r[a], r[b]);
                }
                int ra = a + step < n ? r[a + step] : -1;
                int rb = b + step < n ? r[b + step] : -1;
                return Integer.compare(ra, rb);
            };
            Arrays.sort(sa, byPair);
            int[] newRank = new int[n];
            for (int idx = 1; idx < n; idx++) {
                newRank[sa[idx]] = newRank[sa[idx - 1]] + (byPair.compare(sa[idx], sa[idx - 1]) != 0 ? 1 : 0);
            }
            rank = newRank;
            if (rank[sa[n - 1]] == n - 1 || k >= n) {
                break;
            }
        }
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            out[i] = sa[i];
        }
        return out;
    }

    /**
     * lcp[i] = longest common prefix of suffixes sa[i-1] and sa[i]; lcp[0] = 0.
     *
     * <p>Kasai's observation: moving from suffix i to i+1 drops at most one character of the
     * previous LCP, so the pointer {@code h} only decreases by one per step and the pass is O(n).
     */
    public static int[] lcpKasai(String s, int[] sa) {
        int n = s.length();
        int[] lcp = new int[n];
        if (n == 0) {
            return lcp;
        }
        int[] rank = new int[n];
        for (int i = 0; i < n; i++) {
            rank[sa[i]] = i;
        }
        int h = 0;
        for (int i = 0; i < n; i++) {
            if (rank[i] > 0) {
                int j = sa[rank[i] - 1];
                while (i + h < n && j + h < n && s.charAt(i + h) == s.charAt(j + h)) {
                    h++;
                }
                lcp[rank[i]] = h;
                if (h > 0) {
                    h--;
                }
            } else {
                h = 0;
            }
        }
        return lcp;
    }

    /** Compares text[start..start+m) against pattern; returns {-1|0|1, comparisons}. */
    private static long[] comparePrefix(String text, int start, String pattern) {
        long comparisons = 0;
        for (int j = 0; j < pattern.length(); j++) {
            if (start + j >= text.length()) {
                return new long[] {-1, comparisons}; // suffix shorter than pattern and equal so far -> smaller
            }
            comparisons++;
            char a = text.charAt(start + j);
            char b = pattern.charAt(j);
            if (a != b) {
                return new long[] {a < b ? -1 : 1, comparisons};
            }
        }
        return new long[] {0, comparisons};
    }

    public static SearchResult suffixArraySearch(String text, String pattern) {
        return suffixArraySearch(text, pattern, null);
    }

    /** Two binary searches over the suffix array bracket every suffix that starts with {@code pattern}. */
    public static SearchResult suffixArraySearch(String text, String pattern, int[] sa) {
        long start = System.nanoTime();
        if (trivial(text.length(), pattern.length())) {
            return new SearchResult("SUFFIX_ARRAY", List.of(), 0, msSince(start), Map.of());
        }
        if (sa == null) {
            sa = suffixArray(text);
        }
        long comparisons = 0;

        int lo = 0;
        int hi = sa.length;
        while (lo < hi) { // first suffix >= pattern
            int mid = (lo + hi) / 2;
            long[] cmp = comparePrefix(text, sa[mid], pattern);
            comparisons += cmp[1];
            if (cmp[0] < 0) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        int first = lo;

        hi = sa.length;
        while (lo < hi) { // first suffix whose prefix > pattern
            int mid = (lo + hi) / 2;
            long[] cmp = comparePrefix(text, sa[mid], pattern);
            comparisons += cmp[1];
            if (cmp[0] <= 0) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        List<Integer> positions = new ArrayList<>();
        for (int i = first; i < lo; i++) {
            positions.add(sa[i]);
        }
        Collections.sort(positions);
        return new SearchResult("SUFFIX_ARRAY", positions, comparisons, msSince(start),
                Map.of("sa_range", List.of(first, lo)));
    }

    public record SuffixSummary(int[] suffixArray, int[] lcp, List<String> suffixes, String longestRepeatedSubstring,
                                long distinctSubstrings) {}

    public static SuffixSummary suffixStructureSummary(String s) {
        int[] sa = suffixArray(s);
        int[] lcp = lcpKasai(s, sa);
        int n = s.length();
        int best = 0;
        long lcpSum = 0;
        for (int i = 0; i < n; i++) {
            if (lcp[i] > lcp[best]) {
                best = i;
            }
            lcpSum += lcp[i];
        }
        String longestRepeat = n > 0 && lcp[best] > 0 ? s.substring(sa[best], sa[best] + lcp[best]) : "";
        List<String> suffixes = new ArrayList<>();
        for (int i : sa) {
            suffixes.add(s.substring(i));
        }
        // every distinct substring is a prefix of exactly one suffix, minus prefixes shared with the previous suffix
        long distinct = (long) n * (n + 1) / 2 - lcpSum;
        return new SuffixSummary(sa, lcp, suffixes, longestRepeat, distinct);
    }

    // ------------------------------------------------------------------ dispatch

    public static final Map<String, BiFunction<String, String, SearchResult>> SEARCH_ALGORITHMS;

    static {
        Map<String, BiFunction<String, String, SearchResult>> algorithms = new LinkedHashMap<>();
        algorithms.put("NAIVE", Strings::naiveSearch);
        algorithms.put("KMP", Strings::kmpSearch);
        algorithms.put("Z_FUNCTION", Strings::zSearch);
        algorithms.put("RABIN_KARP", Strings::rabinKarp);
        algorithms.put("SUFFIX_ARRAY", Strings::suffixArraySearch);
        SEARCH_ALGORITHMS = Collections.unmodifiableMap(algorithms);
    }

    public static SearchResult findAll(String text, String pattern) {
        return findAll(text, pattern, "KMP");
    }

    public static SearchResult findAll(String text, String pattern, String algorithm) {
        BiFunction<String, String, SearchResult> fn = SEARCH_ALGORITHMS.get(algorithm);
        if (fn == null) {
            throw new IllegalArgumentException("Unknown string algorithm: " + algorithm);
        }
        return fn.apply(text, pattern);
    }
}
