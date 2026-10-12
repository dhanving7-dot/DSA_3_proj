package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.IntBinaryOperator;

/**
 * Module 6 - Parallel primitives, simulated on a PRAM.
 *
 * <p>Each primitive is executed round-by-round exactly as a PRAM would: every operation inside
 * one round is independent of the others in that round. The simulator counts work T1 (total
 * operations across all rounds) and span T_inf (number of rounds), the two quantities Brent's
 * theorem needs: T_p &lt;= T1/p + T_inf.
 *
 * <p>The allocation engine uses {@link #blellochExclusiveScan} for real: the starting slot index
 * of every laboratory in the capacity-expanded bipartite graph is the exclusive prefix sum of the
 * capacities.
 */
public final class Parallel {
    private Parallel() {}

    /** One PRAM round; {@code stride} is null for reductions. */
    public record Round(String phase, Integer stride, int operations, List<Integer> values) {}

    public record ParallelTrace<T>(T result, int work, int span, List<Round> rounds) {
        /** Upper bound on running time with p processors: T1/p + T_inf. */
        public double brentBound(int processors) {
            return (double) work / Math.max(processors, 1) + span;
        }

        /** Average parallelism T1 / T_inf, or null when there were no rounds. */
        public Double parallelism() {
            return span == 0 ? null : (double) work / span;
        }
    }

    private static int nextPow2(int n) {
        int size = 1;
        while (size < n) {
            size *= 2;
        }
        return size;
    }

    public static ParallelTrace<Integer> parallelReduce(int[] values) {
        return parallelReduce(values, Integer::sum, 0);
    }

    /** Balanced binary-tree reduction: n-1 operations, ceil(log2 n) rounds. */
    public static ParallelTrace<Integer> parallelReduce(int[] values, IntBinaryOperator op, int identity) {
        if (values.length == 0) {
            return new ParallelTrace<>(identity, 0, 0, List.of());
        }
        List<Integer> level = new ArrayList<>();
        for (int v : values) {
            level.add(v);
        }
        List<Round> rounds = new ArrayList<>();
        int work = 0;
        while (level.size() > 1) {
            List<Integer> next = new ArrayList<>();
            int ops = 0;
            for (int i = 0; i + 1 < level.size(); i += 2) {
                next.add(op.applyAsInt(level.get(i), level.get(i + 1)));
                ops++;
            }
            if (level.size() % 2 == 1) {
                next.add(level.get(level.size() - 1));
            }
            work += ops;
            rounds.add(new Round("reduce", null, ops, List.copyOf(next)));
            level = next;
        }
        return new ParallelTrace<>(level.get(0), work, rounds.size(), rounds);
    }

    /**
     * Work-efficient exclusive prefix sum (Blelloch 1990).
     *
     * <p>Up-sweep builds partial sums in a balanced tree (n-1 additions, log n rounds); down-sweep
     * pushes prefixes back down (n-1 additions + swaps, log n rounds). Total work O(n), span
     * O(log n). Input is padded with zeros to a power of two.
     */
    public static ParallelTrace<int[]> blellochExclusiveScan(int[] values) {
        int n = values.length;
        if (n == 0) {
            return new ParallelTrace<>(new int[0], 0, 0, List.of());
        }
        int size = nextPow2(n);
        int[] a = Arrays.copyOf(values, size);
        List<Round> rounds = new ArrayList<>();
        int work = 0;

        for (int d = 1; d < size; d *= 2) { // up-sweep (reduce)
            int ops = 0;
            for (int i = 0; i < size; i += 2 * d) {
                a[i + 2 * d - 1] += a[i + d - 1];
                ops++;
            }
            work += ops;
            rounds.add(new Round("up-sweep", d, ops, snapshot(a, n)));
        }

        a[size - 1] = 0;
        for (int d = size / 2; d >= 1; d /= 2) { // down-sweep
            int ops = 0;
            for (int i = 0; i < size; i += 2 * d) {
                int left = a[i + d - 1];
                a[i + d - 1] = a[i + 2 * d - 1];
                a[i + 2 * d - 1] += left;
                ops++;
            }
            work += ops;
            rounds.add(new Round("down-sweep", d, ops, snapshot(a, n)));
        }

        return new ParallelTrace<>(Arrays.copyOf(a, n), work, rounds.size(), rounds);
    }

    public static int[] sequentialExclusiveScan(int[] values) {
        int[] out = new int[values.length];
        int running = 0;
        for (int i = 0; i < values.length; i++) {
            out[i] = running;
            running += values[i];
        }
        return out;
    }

    private static List<Integer> snapshot(int[] a, int n) {
        List<Integer> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(a[i]);
        }
        return out;
    }
}
