package com.allocatex.algorithms;

import java.util.List;

/**
 * Common result / trace shape returned by every algorithm implementation.
 *
 * <p>Keeping one shared shape means the matching engine and any caller can treat Kuhn /
 * Hopcroft-Karp / Ford-Fulkerson / Edmonds-Karp / Dinic / min-cost flow interchangeably.
 */
public record MatchingResult(
        String algorithm,
        List<MatchedPair> matchedPairs,
        List<Integer> unmatchedLeft,
        List<Integer> unmatchedRight,
        int vertices,
        int edges,
        long iterations,
        int augmentingPathsFound,
        double executionTimeMs,
        String timeComplexity,
        String spaceComplexity,
        List<AlgorithmStep> steps) {

    /** A (left, right) pair of a matching: student index and lab-slot (or lab) index. */
    public record MatchedPair(int left, int right) {}

    public int matchSize() {
        return matchedPairs.size();
    }

    /** Trace for a flow algorithm: pairs are filled in later by the matching engine from flow-carrying edges. */
    static MatchingResult flowTrace(String algorithm, int vertices, int edges, long iterations, int augmentingPaths,
                                    double elapsedMs, String time, String space, List<AlgorithmStep> steps) {
        return new MatchingResult(algorithm, List.of(), List.of(), List.of(), vertices, edges, iterations,
                augmentingPaths, elapsedMs, time, space, steps);
    }
}
