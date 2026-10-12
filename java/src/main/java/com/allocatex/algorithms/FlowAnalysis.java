package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Module 4 - What a finished max flow <em>proves</em>: min cuts, König covers, project selection.
 *
 * <p>After any max-flow algorithm stops, the set S of nodes still reachable from the source in
 * the residual graph is the source side of a minimum cut. Every edge from S to T is saturated and
 * their capacities sum to exactly the max flow - the max-flow min-cut theorem.
 *
 * <p>For bipartite matching the same residual search yields König's theorem (a minimum vertex
 * cover of size |maximum matching|) and Hall's condition (a set of students whose combined
 * eligible-lab capacity is smaller than the set itself).
 */
public final class FlowAnalysis {
    private FlowAnalysis() {}

    public record CutEdge(int from, int to, int capacity) {}

    public record MinCut(List<Integer> sourceSide, List<CutEdge> cutEdges, long cutCapacity) {}

    public record VertexCover(List<Integer> left, List<Integer> right, int size) {}

    public record ProjectSelection(int maxProfit, int minCut, List<Integer> projects, List<Integer> tools) {}

    public static boolean[] residualReachable(FlowNetwork network, int source) {
        boolean[] seen = new boolean[network.numNodes()];
        seen[source] = true;
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(source);
        while (!queue.isEmpty()) {
            int u = queue.poll();
            for (Edge edge : network.edgesFrom(u)) {
                if (edge.residual() > 0 && !seen[edge.to]) {
                    seen[edge.to] = true;
                    queue.add(edge.to);
                }
            }
        }
        return seen;
    }

    /** Call after max flow has been computed on {@code network}. */
    public static MinCut minCut(FlowNetwork network, int source) {
        boolean[] side = residualReachable(network, source);
        List<CutEdge> cutEdges = new ArrayList<>();
        List<Integer> sourceSide = new ArrayList<>();
        long capacity = 0;
        for (int u = 0; u < network.numNodes(); u++) {
            if (!side[u]) {
                continue;
            }
            sourceSide.add(u);
            for (Edge edge : network.edgesFrom(u)) {
                if (edge.capacity > 0 && !side[edge.to]) {
                    cutEdges.add(new CutEdge(u, edge.to, edge.capacity));
                    capacity += edge.capacity;
                }
            }
        }
        return new MinCut(sourceSide, cutEdges, capacity);
    }

    /**
     * Minimum vertex cover of a bipartite graph from a maximum matching.
     *
     * <p>Z = vertices reachable from unmatched left vertices along alternating paths (unmatched
     * edge left->right, matched edge right->left). Then cover = (L \ Z) u (R n Z), and
     * |cover| == |matching|.
     */
    public static VertexCover konigVertexCover(BipartiteGraph graph, List<MatchingResult.MatchedPair> matchedPairs) {
        int[] matchLeft = new int[graph.numLeft()];
        int[] matchRight = new int[graph.numRight()];
        Arrays.fill(matchLeft, -1);
        Arrays.fill(matchRight, -1);
        for (MatchingResult.MatchedPair pair : matchedPairs) {
            matchLeft[pair.left()] = pair.right();
            matchRight[pair.right()] = pair.left();
        }

        boolean[] zLeft = new boolean[graph.numLeft()];
        boolean[] zRight = new boolean[graph.numRight()];
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        for (int u = 0; u < graph.numLeft(); u++) {
            if (matchLeft[u] == -1) {
                zLeft[u] = true;
                queue.add(u);
            }
        }
        while (!queue.isEmpty()) {
            int u = queue.poll();
            for (int v : graph.neighbors(u)) {
                if (zRight[v] || matchLeft[u] == v) {
                    continue;
                }
                zRight[v] = true;
                int w = matchRight[v];
                if (w != -1 && !zLeft[w]) {
                    zLeft[w] = true;
                    queue.add(w);
                }
            }
        }

        List<Integer> coverLeft = new ArrayList<>();
        List<Integer> coverRight = new ArrayList<>();
        for (int u = 0; u < graph.numLeft(); u++) {
            if (!zLeft[u]) {
                coverLeft.add(u);
            }
        }
        for (int v = 0; v < graph.numRight(); v++) {
            if (zRight[v]) {
                coverRight.add(v);
            }
        }
        return new VertexCover(coverLeft, coverRight, coverLeft.size() + coverRight.size());
    }

    /**
     * Choose projects (profit p_i) that each need tools (cost c_j) to maximise profit - costs.
     *
     * <p>Reduction: source -> project (cap p_i), tool -> sink (cap c_j), project -> tool (cap inf).
     * A finite cut can never separate a chosen project from a tool it needs, and best profit =
     * sum(p_i) - min cut. Chosen sets are the source side of the cut.
     *
     * @param requires pairs {project, tool}
     */
    public static ProjectSelection projectSelection(int[] profits, int[] costs, int[][] requires) {
        int numProjects = profits.length;
        int numTools = costs.length;
        int source = 0;
        int projectOffset = 1;
        int toolOffset = projectOffset + numProjects;
        int sink = toolOffset + numTools;
        int totalProfit = Arrays.stream(profits).sum();
        int big = totalProfit + Arrays.stream(costs).sum() + 1; // acts as infinity: larger than any finite cut
        FlowNetwork network = new FlowNetwork(sink + 1);
        for (int i = 0; i < numProjects; i++) {
            network.addEdge(source, projectOffset + i, profits[i]);
        }
        for (int j = 0; j < numTools; j++) {
            network.addEdge(toolOffset + j, sink, costs[j]);
        }
        for (int[] req : requires) {
            network.addEdge(projectOffset + req[0], toolOffset + req[1], big);
        }

        int flow = Dinic.maxFlow(network, source, sink).maxFlow();
        boolean[] side = residualReachable(network, source);
        List<Integer> chosenProjects = new ArrayList<>();
        List<Integer> chosenTools = new ArrayList<>();
        for (int i = 0; i < numProjects; i++) {
            if (side[projectOffset + i]) {
                chosenProjects.add(i);
            }
        }
        for (int j = 0; j < numTools; j++) {
            if (side[toolOffset + j]) {
                chosenTools.add(j);
            }
        }
        return new ProjectSelection(totalProfit - flow, flow, chosenProjects, chosenTools);
    }
}
