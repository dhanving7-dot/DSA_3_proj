package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.List;

/**
 * Directed graph with edge capacities, stored as adjacency lists of {@link Edge} objects.
 *
 * <p>Every added edge (u -> v, cap) is paired with an implicit reverse edge (v -> u, cap = 0) so
 * augmenting paths can "cancel" flow, which Ford-Fulkerson-style algorithms need to reach a true
 * maximum flow. Used by Ford-Fulkerson, Edmonds-Karp and Dinic; laboratory capacity is expressed
 * directly as edge capacity, which is what makes the flow formulation strictly more general than
 * the plain matching formulation.
 */
public final class FlowNetwork {
    private final int numNodes;
    private final List<List<Edge>> graph;

    public FlowNetwork(int numNodes) {
        this.numNodes = numNodes;
        this.graph = new ArrayList<>(numNodes);
        for (int i = 0; i < numNodes; i++) {
            graph.add(new ArrayList<>());
        }
    }

    public int numNodes() {
        return numNodes;
    }

    public List<Edge> edgesFrom(int u) {
        return graph.get(u);
    }

    List<List<Edge>> adjacency() {
        return graph;
    }

    /** Counts forward edges only (every forward edge has one paired reverse edge). */
    public int numEdges() {
        int total = 0;
        for (List<Edge> adj : graph) {
            for (Edge e : adj) {
                if (e.capacity > 0) {
                    total++;
                }
            }
        }
        return total;
    }

    public void addEdge(int u, int v, int capacity) {
        Edge forward = new Edge(v, capacity);
        Edge backward = new Edge(u, 0);
        graph.get(u).add(forward);
        graph.get(v).add(backward);
        forward.reverseIndex = graph.get(v).size() - 1;
        backward.reverseIndex = graph.get(u).size() - 1;
    }

    public Edge reverseEdge(Edge edge) {
        return graph.get(edge.to).get(edge.reverseIndex);
    }
}
