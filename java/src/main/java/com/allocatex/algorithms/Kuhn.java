package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Kuhn's algorithm for Maximum Bipartite Matching.
 *
 * <p>For every left vertex (student) we attempt to find an augmenting path to an unmatched right
 * vertex (lab slot) via DFS, following unmatched edges out and matched edges back ("alternating
 * path"). If such a path exists we flip every edge along it, growing the matching by exactly one
 * pair. Repeating this for every left vertex once yields a maximum matching.
 *
 * <p>Time complexity: O(V * E) (one DFS of O(E) per left vertex). Space complexity: O(V + E).
 */
public final class Kuhn {
    private Kuhn() {}

    public static MatchingResult maxMatching(BipartiteGraph graph) {
        return new Run(graph).execute();
    }

    private static final class Run {
        private final BipartiteGraph graph;
        private final int[] matchLeft;
        private final int[] matchRight;
        private final StepRecorder recorder = new StepRecorder();
        private long dfsCalls;

        Run(BipartiteGraph graph) {
            this.graph = graph;
            this.matchLeft = new int[graph.numLeft()];
            this.matchRight = new int[graph.numRight()];
            Arrays.fill(matchLeft, -1);
            Arrays.fill(matchRight, -1);
        }

        private boolean tryKuhn(int left, boolean[] visited) {
            dfsCalls++;
            for (int right : graph.neighbors(left)) {
                if (visited[right]) {
                    continue;
                }
                visited[right] = true;
                if (matchRight[right] == -1 || tryKuhn(matchRight[right], visited)) {
                    matchRight[right] = left;
                    matchLeft[left] = right;
                    return true;
                }
            }
            return false;
        }

        MatchingResult execute() {
            recorder.emit(StepEvent.GRAPH_CREATED,
                    "Built bipartite graph with " + graph.numLeft() + " students and " + graph.numRight() + " lab slots.",
                    "num_left", graph.numLeft(), "num_right", graph.numRight(), "num_edges", graph.numEdges());

            int augmentingPathsFound = 0;
            long start = System.nanoTime();

            for (int left = 0; left < graph.numLeft(); left++) {
                recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH,
                        "Searching augmenting path from student #" + left + " via DFS.", "left", left);
                boolean found = tryKuhn(left, new boolean[graph.numRight()]);
                if (found) {
                    augmentingPathsFound++;
                    recorder.emit(StepEvent.MATCH_UPDATED,
                            "Augmenting path found for student #" + left + " -> lab-slot #" + matchLeft[left] + ".",
                            "left", left, "right", matchLeft[left]);
                } else {
                    recorder.emit(StepEvent.NO_PATH_FOUND,
                            "No augmenting path exists for student #" + left + "; remains unmatched.", "left", left);
                }
            }

            double elapsedMs = (System.nanoTime() - start) / 1e6;

            List<MatchingResult.MatchedPair> matchedPairs = new ArrayList<>();
            List<Integer> unmatchedLeft = new ArrayList<>();
            List<Integer> unmatchedRight = new ArrayList<>();
            for (int left = 0; left < matchLeft.length; left++) {
                if (matchLeft[left] != -1) {
                    matchedPairs.add(new MatchingResult.MatchedPair(left, matchLeft[left]));
                } else {
                    unmatchedLeft.add(left);
                }
            }
            for (int right = 0; right < matchRight.length; right++) {
                if (matchRight[right] == -1) {
                    unmatchedRight.add(right);
                }
            }

            recorder.emit(StepEvent.ALGORITHM_COMPLETE,
                    "Maximum matching reached: " + matchedPairs.size() + " pairs matched.",
                    "match_size", matchedPairs.size());

            return new MatchingResult("KUHN", matchedPairs, unmatchedLeft, unmatchedRight, graph.numVertices(),
                    graph.numEdges(), dfsCalls, augmentingPathsFound, elapsedMs, "O(V * E)", "O(V + E)",
                    recorder.steps());
        }
    }
}
