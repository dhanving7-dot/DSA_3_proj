package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Ford-Fulkerson method with DFS path selection - the generic form that Edmonds-Karp (BFS) and
 * Dinic (level graphs) refine.
 *
 * <p>Any augmenting path works; correctness follows from the max-flow min-cut theorem (no
 * augmenting path &lt;=&gt; the reachable set defines a cut of equal capacity). With integer
 * capacities each augmentation adds at least one unit, so it terminates after at most |f*|
 * augmentations - but unlike Edmonds-Karp there is no bound independent of the capacities.
 *
 * <p>Time complexity: O(E * |f*|). Space complexity: O(V + E).
 */
public final class FordFulkerson {
    private FordFulkerson() {}

    /** Iterative DFS. Returns the source-to-sink path as edges, or null; counts explored nodes into {@code explored[0]}. */
    private static List<Edge> dfsFindPath(FlowNetwork network, int source, int sink, long[] explored) {
        Edge[] parentEdge = new Edge[network.numNodes()];
        int[] parentNode = new int[network.numNodes()];
        boolean[] visited = new boolean[network.numNodes()];
        visited[source] = true;
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        stack.push(source);
        while (!stack.isEmpty()) {
            int u = stack.pop();
            explored[0]++;
            if (u == sink) {
                break;
            }
            for (Edge edge : network.edgesFrom(u)) {
                if (!visited[edge.to] && edge.residual() > 0) {
                    visited[edge.to] = true;
                    parentEdge[edge.to] = edge;
                    parentNode[edge.to] = u;
                    stack.push(edge.to);
                }
            }
        }
        if (!visited[sink]) {
            return null;
        }
        List<Edge> path = new ArrayList<>();
        for (int node = sink; node != source; node = parentNode[node]) {
            path.add(parentEdge[node]);
        }
        Collections.reverse(path);
        return path;
    }

    public static FlowResult maxFlow(FlowNetwork network, int source, int sink) {
        StepRecorder recorder = new StepRecorder();
        recorder.emit(StepEvent.GRAPH_CREATED,
                "Built flow network with " + network.numNodes() + " nodes (source, students, labs, sink).",
                "num_nodes", network.numNodes(), "num_edges", network.numEdges());

        int maxFlow = 0;
        int augmentingPathsFound = 0;
        long[] explored = {0};
        long start = System.nanoTime();
        while (true) {
            recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH, "DFS for any augmenting path in the residual graph.");
            List<Edge> path = dfsFindPath(network, source, sink, explored);
            if (path == null) {
                recorder.emit(StepEvent.NO_PATH_FOUND,
                        "No augmenting path remains: the reachable set now defines a minimum cut.");
                break;
            }
            int bottleneck = Integer.MAX_VALUE;
            for (Edge edge : path) {
                bottleneck = Math.min(bottleneck, edge.residual());
            }
            for (Edge edge : path) {
                edge.flow += bottleneck;
                network.reverseEdge(edge).flow -= bottleneck;
            }
            maxFlow += bottleneck;
            augmentingPathsFound++;
            recorder.emit(StepEvent.AUGMENTING_PATH_FOUND, "Augmenting path #" + augmentingPathsFound + " ("
                    + path.size() + " edges) pushed " + bottleneck + " unit(s).",
                    "path_length", path.size(), "pushed", bottleneck);
            recorder.emit(StepEvent.MATCH_UPDATED, "Total flow now " + maxFlow + ".", "flow", maxFlow);
        }

        double elapsedMs = (System.nanoTime() - start) / 1e6;
        recorder.emit(StepEvent.ALGORITHM_COMPLETE,
                "Maximum flow reached: " + maxFlow + " units (== size of maximum matching).", "max_flow", maxFlow);
        MatchingResult trace = MatchingResult.flowTrace("FORD_FULKERSON", network.numNodes(), network.numEdges(),
                explored[0], augmentingPathsFound, elapsedMs, "O(E * |f*|)", "O(V + E)", recorder.steps());
        return new FlowResult(maxFlow, trace);
    }
}
