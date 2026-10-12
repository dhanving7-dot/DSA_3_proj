package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Hopcroft-Karp algorithm for Maximum Bipartite Matching.
 *
 * <p>Improves on Kuhn's algorithm by finding a <em>maximal set of vertex-disjoint shortest
 * augmenting paths</em> in each phase (BFS to compute layers + DFS restricted to those layers),
 * instead of one augmenting path at a time. There are at most O(sqrt(V)) phases, and each phase
 * costs O(E).
 *
 * <p>Time complexity: O(E * sqrt(V)). Space complexity: O(V + E).
 */
public final class HopcroftKarp {
    private static final int INF = Integer.MAX_VALUE;
    private static final int NIL = -1;

    private HopcroftKarp() {}

    public static MatchingResult maxMatching(BipartiteGraph graph) {
        return new Run(graph).execute();
    }

    private static final class Run {
        private final BipartiteGraph graph;
        private final int[] matchLeft;
        private final int[] matchRight;
        private final int[] dist;
        private final StepRecorder recorder = new StepRecorder();
        private long bfsDfsOps;

        Run(BipartiteGraph graph) {
            this.graph = graph;
            this.matchLeft = new int[graph.numLeft()];
            this.matchRight = new int[graph.numRight()];
            this.dist = new int[graph.numLeft()];
            Arrays.fill(matchLeft, NIL);
            Arrays.fill(matchRight, NIL);
        }

        private boolean bfs() {
            ArrayDeque<Integer> queue = new ArrayDeque<>();
            for (int u = 0; u < graph.numLeft(); u++) {
                if (matchLeft[u] == NIL) {
                    dist[u] = 0;
                    queue.add(u);
                } else {
                    dist[u] = INF;
                }
            }
            int distNil = INF;
            while (!queue.isEmpty()) {
                int u = queue.poll();
                bfsDfsOps++;
                if (dist[u] < distNil) {
                    for (int v : graph.neighbors(u)) {
                        int matchedU = matchRight[v];
                        if (matchedU == NIL) {
                            distNil = dist[u] + 1;
                        } else if (dist[matchedU] == INF) {
                            dist[matchedU] = dist[u] + 1;
                            queue.add(matchedU);
                        }
                    }
                }
            }
            return distNil != INF;
        }

        private boolean dfs(int u) {
            bfsDfsOps++;
            for (int v : graph.neighbors(u)) {
                int matchedU = matchRight[v];
                if (matchedU == NIL || (dist[matchedU] == dist[u] + 1 && dfs(matchedU))) {
                    matchRight[v] = u;
                    matchLeft[u] = v;
                    return true;
                }
            }
            dist[u] = INF;
            return false;
        }

        MatchingResult execute() {
            recorder.emit(StepEvent.GRAPH_CREATED,
                    "Built bipartite graph with " + graph.numLeft() + " students and " + graph.numRight() + " lab slots.",
                    "num_left", graph.numLeft(), "num_right", graph.numRight(), "num_edges", graph.numEdges());

            int phase = 0;
            int augmentingPathsFound = 0;
            long start = System.nanoTime();

            while (bfs()) {
                phase++;
                recorder.emit(StepEvent.PHASE_START, "Phase " + phase
                        + ": BFS layering complete, searching vertex-disjoint shortest augmenting paths.", "phase", phase);
                for (int u = 0; u < graph.numLeft(); u++) {
                    if (matchLeft[u] != NIL) {
                        continue;
                    }
                    recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH,
                            "Phase " + phase + ": DFS augmenting attempt from student #" + u + ".", "phase", phase, "left", u);
                    if (dfs(u)) {
                        augmentingPathsFound++;
                        recorder.emit(StepEvent.MATCH_UPDATED, "Phase " + phase + ": augmenting path found, student #"
                                        + u + " -> lab-slot #" + matchLeft[u] + ".",
                                "phase", phase, "left", u, "right", matchLeft[u]);
                    }
                }
            }

            double elapsedMs = (System.nanoTime() - start) / 1e6;

            List<MatchingResult.MatchedPair> matchedPairs = new ArrayList<>();
            List<Integer> unmatchedLeft = new ArrayList<>();
            List<Integer> unmatchedRight = new ArrayList<>();
            for (int u = 0; u < matchLeft.length; u++) {
                if (matchLeft[u] != NIL) {
                    matchedPairs.add(new MatchingResult.MatchedPair(u, matchLeft[u]));
                } else {
                    unmatchedLeft.add(u);
                }
            }
            for (int v = 0; v < matchRight.length; v++) {
                if (matchRight[v] == NIL) {
                    unmatchedRight.add(v);
                }
            }

            recorder.emit(StepEvent.ALGORITHM_COMPLETE, "Maximum matching reached after " + phase + " phases: "
                    + matchedPairs.size() + " pairs matched.", "match_size", matchedPairs.size(), "phases", phase);

            return new MatchingResult("HOPCROFT_KARP", matchedPairs, unmatchedLeft, unmatchedRight,
                    graph.numVertices(), graph.numEdges(), bfsDfsOps, augmentingPathsFound, elapsedMs,
                    "O(E * sqrt(V))", "O(V + E)", recorder.steps());
        }
    }
}
