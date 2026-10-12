package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.List;

/**
 * Adjacency-list bipartite graph, left = students, right = lab-slots.
 *
 * <p>Used by Kuhn's algorithm and Hopcroft-Karp. Laboratory <em>capacity</em> is handled by
 * expanding each laboratory into {@code capacity} distinct "slot" vertices on the right side
 * before the algorithm ever runs - the standard reduction from many-to-one bipartite b-matching
 * to plain 1-to-1 bipartite matching.
 */
public final class BipartiteGraph {
    private final int numLeft;
    private final int numRight;
    private final List<List<Integer>> adjacency;

    public BipartiteGraph(int numLeft, int numRight) {
        this.numLeft = numLeft;
        this.numRight = numRight;
        this.adjacency = new ArrayList<>(numLeft);
        for (int i = 0; i < numLeft; i++) {
            adjacency.add(new ArrayList<>());
        }
    }

    public int numLeft() {
        return numLeft;
    }

    public int numRight() {
        return numRight;
    }

    public List<Integer> neighbors(int left) {
        return adjacency.get(left);
    }

    public int numEdges() {
        int total = 0;
        for (List<Integer> neighbors : adjacency) {
            total += neighbors.size();
        }
        return total;
    }

    public int numVertices() {
        return numLeft + numRight;
    }

    public void addEdge(int left, int right) {
        adjacency.get(left).add(right);
    }
}
