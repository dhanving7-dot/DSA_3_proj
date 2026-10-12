package com.allocatex.algorithms;

/** Residual-graph edge with a paired reverse edge at {@code graph[to][reverseIndex]}. */
public class Edge {
    public final int to;
    public final int capacity;
    public int flow;
    int reverseIndex = -1;

    public Edge(int to, int capacity) {
        this.to = to;
        this.capacity = capacity;
    }

    public int residual() {
        return capacity - flow;
    }
}
