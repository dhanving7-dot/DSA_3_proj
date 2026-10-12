package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;

/**
 * Dinic's algorithm: max flow via repeated blocking flows on a BFS level graph.
 *
 * <p>Each phase (1) runs a BFS from the source to assign levels, then (2) uses a DFS with the
 * classic "current arc" pointer optimisation to saturate a blocking flow restricted to edges that
 * advance exactly one level. There are at most O(V) phases and each blocking flow costs O(V*E),
 * giving the general bound below - but on unit-capacity bipartite-matching networks this
 * specialises to O(E * sqrt(V)), matching Hopcroft-Karp exactly.
 *
 * <p>Time complexity: O(V^2 * E) (O(E * sqrt(V)) on unit-capacity bipartite graphs).
 * Space complexity: O(V + E).
 */
public final class Dinic {
    private Dinic() {}

    public static FlowResult maxFlow(FlowNetwork network, int source, int sink) {
        return new Run(network, source, sink).execute();
    }

    private static final class Run {
        private final FlowNetwork network;
        private final int source;
        private final int sink;
        private final int[] level;
        private final int[] it;
        private final StepRecorder recorder = new StepRecorder();

        Run(FlowNetwork network, int source, int sink) {
            this.network = network;
            this.source = source;
            this.sink = sink;
            this.level = new int[network.numNodes()];
            this.it = new int[network.numNodes()];
        }

        private boolean bfsLevels() {
            Arrays.fill(level, -1);
            level[source] = 0;
            ArrayDeque<Integer> queue = new ArrayDeque<>();
            queue.add(source);
            while (!queue.isEmpty()) {
                int u = queue.poll();
                for (Edge edge : network.edgesFrom(u)) {
                    if (edge.residual() > 0 && level[edge.to] == -1) {
                        level[edge.to] = level[u] + 1;
                        queue.add(edge.to);
                    }
                }
            }
            return level[sink] != -1;
        }

        private int dfsBlockingFlow(int u, int pushed) {
            if (u == sink) {
                return pushed;
            }
            List<Edge> edges = network.edgesFrom(u);
            while (it[u] < edges.size()) {
                Edge edge = edges.get(it[u]);
                if (level[edge.to] == level[u] + 1 && edge.residual() > 0) {
                    int bottleneck = dfsBlockingFlow(edge.to, Math.min(pushed, edge.residual()));
                    if (bottleneck > 0) {
                        edge.flow += bottleneck;
                        network.reverseEdge(edge).flow -= bottleneck;
                        return bottleneck;
                    }
                }
                it[u]++;
            }
            return 0;
        }

        FlowResult execute() {
            recorder.emit(StepEvent.GRAPH_CREATED,
                    "Built flow network with " + network.numNodes() + " nodes (source, students, labs, sink).",
                    "num_nodes", network.numNodes(), "num_edges", network.numEdges());

            int maxFlow = 0;
            int phase = 0;
            int augmentingPathsFound = 0;
            long start = System.nanoTime();

            while (bfsLevels()) {
                phase++;
                Arrays.fill(it, 0);
                recorder.emit(StepEvent.PHASE_START,
                        "Phase " + phase + ": BFS level graph built (sink at level " + level[sink] + ").",
                        "phase", phase, "sink_level", level[sink]);
                while (true) {
                    recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH,
                            "Phase " + phase + ": DFS searching blocking-flow augmenting path.", "phase", phase);
                    int pushed = dfsBlockingFlow(source, Integer.MAX_VALUE);
                    if (pushed == 0) {
                        recorder.emit(StepEvent.NO_PATH_FOUND,
                                "Phase " + phase + ": blocking flow saturated, no more paths at this level.");
                        break;
                    }
                    maxFlow += pushed;
                    augmentingPathsFound++;
                    recorder.emit(StepEvent.AUGMENTING_PATH_FOUND, "Phase " + phase + ": augmenting path #"
                            + augmentingPathsFound + " pushed " + pushed + " unit(s) of flow.",
                            "phase", phase, "pushed", pushed);
                    recorder.emit(StepEvent.MATCH_UPDATED, "Total flow now " + maxFlow + ".", "flow", maxFlow);
                }
            }

            double elapsedMs = (System.nanoTime() - start) / 1e6;
            recorder.emit(StepEvent.ALGORITHM_COMPLETE, "Maximum flow reached after " + phase + " phases: " + maxFlow
                    + " units (== size of maximum matching).", "max_flow", maxFlow, "phases", phase);

            MatchingResult trace = MatchingResult.flowTrace("DINIC", network.numNodes(), network.numEdges(),
                    augmentingPathsFound, augmentingPathsFound, elapsedMs,
                    "O(V^2 * E), O(E*sqrt(V)) on unit-capacity bipartite graphs", "O(V + E)", recorder.steps());
            return new FlowResult(maxFlow, trace);
        }
    }
}
