package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Edmonds-Karp algorithm: Ford-Fulkerson using BFS to pick the <em>shortest</em> (fewest-edges)
 * augmenting path in the residual graph on every iteration.
 *
 * <p>Used as the max-flow formulation of bipartite matching: source -> each student (capacity 1)
 * -> each eligible lab (capacity 1 per edge) -> sink (capacity = lab capacity). The value of the
 * maximum flow equals the size of the maximum matching (integrality of flow guarantees an
 * integral, 0/1 solution on the student edges).
 *
 * <p>Time complexity: O(V * E^2). Space complexity: O(V + E).
 */
public final class EdmondsKarp {
    private EdmondsKarp() {}

    /** BFS for the shortest source-to-sink path; returns its nodes (source..sink) and edges, or null. */
    private record Path(List<Integer> nodes, List<Edge> edges) {}

    private static Path bfsFindPath(FlowNetwork network, int source, int sink) {
        Edge[] parentEdge = new Edge[network.numNodes()];
        int[] parentNode = new int[network.numNodes()];
        boolean[] visited = new boolean[network.numNodes()];
        visited[source] = true;
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(source);
        while (!queue.isEmpty()) {
            int u = queue.poll();
            if (u == sink) {
                break;
            }
            for (Edge edge : network.edgesFrom(u)) {
                if (!visited[edge.to] && edge.residual() > 0) {
                    visited[edge.to] = true;
                    parentEdge[edge.to] = edge;
                    parentNode[edge.to] = u;
                    queue.add(edge.to);
                }
            }
        }
        if (!visited[sink]) {
            return null;
        }
        List<Integer> nodes = new ArrayList<>();
        List<Edge> edges = new ArrayList<>();
        nodes.add(sink);
        for (int node = sink; node != source; node = parentNode[node]) {
            edges.add(parentEdge[node]);
            nodes.add(parentNode[node]);
        }
        Collections.reverse(nodes);
        Collections.reverse(edges);
        return new Path(nodes, edges);
    }

    public static FlowResult maxFlow(FlowNetwork network, int source, int sink) {
        return maxFlow(network, source, sink, "EDMONDS_KARP");
    }

    public static FlowResult maxFlow(FlowNetwork network, int source, int sink, String algorithmLabel) {
        StepRecorder recorder = new StepRecorder();
        recorder.emit(StepEvent.GRAPH_CREATED,
                "Built flow network with " + network.numNodes() + " nodes (source, students, labs, sink).",
                "num_nodes", network.numNodes(), "num_edges", network.numEdges());

        int maxFlow = 0;
        int augmentingPathsFound = 0;
        long start = System.nanoTime();

        while (true) {
            recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH, "BFS search for shortest augmenting path in residual graph.");
            Path path = bfsFindPath(network, source, sink);
            if (path == null) {
                recorder.emit(StepEvent.NO_PATH_FOUND, "No augmenting path remains from source to sink.");
                break;
            }

            int bottleneck = Integer.MAX_VALUE;
            for (Edge edge : path.edges()) {
                bottleneck = Math.min(bottleneck, edge.residual());
            }
            for (Edge edge : path.edges()) {
                edge.flow += bottleneck;
                network.reverseEdge(edge).flow -= bottleneck;
            }

            maxFlow += bottleneck;
            augmentingPathsFound++;
            recorder.emit(StepEvent.AUGMENTING_PATH_FOUND, "Augmenting path #" + augmentingPathsFound
                    + " found with bottleneck capacity " + bottleneck + ".",
                    "path", path.nodes(), "bottleneck", bottleneck);
            recorder.emit(StepEvent.MATCH_UPDATED,
                    "Flow increased by " + bottleneck + "; total flow now " + maxFlow + ".", "flow", maxFlow);
        }

        double elapsedMs = (System.nanoTime() - start) / 1e6;
        recorder.emit(StepEvent.ALGORITHM_COMPLETE,
                "Maximum flow reached: " + maxFlow + " units (== size of maximum matching).", "max_flow", maxFlow);

        MatchingResult trace = MatchingResult.flowTrace(algorithmLabel, network.numNodes(), network.numEdges(),
                augmentingPathsFound, augmentingPathsFound, elapsedMs, "O(V * E^2)", "O(V + E)", recorder.steps());
        return new FlowResult(maxFlow, trace);
    }
}
