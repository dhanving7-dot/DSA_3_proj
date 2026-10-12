package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Min-cost max-flow via Successive Shortest Paths with Johnson potentials.
 *
 * <p>Plain max-flow (Edmonds-Karp, Dinic) maximises <em>how many</em> students are placed but is
 * indifferent to <em>which</em> maximum matching it returns. Giving every student->lab edge a cost
 * of (best_score - score) and asking for the cheapest maximum flow selects, among all maximum
 * matchings, one with the largest total match score - the "assignment problem" generalisation of
 * bipartite matching.
 *
 * <p>SSP repeatedly augments along a cheapest residual s->t path. Residual reverse edges carry
 * negative cost, so Dijkstra is run on <em>reduced</em> costs c'(u,v) = c(u,v) + h(u) - h(v) >= 0,
 * where the potentials h are the previous round's shortest distances. Initial costs are
 * non-negative, so h = 0 is a valid start (Bellman-Ford would be needed otherwise).
 *
 * <p>Time complexity: O(F * E log V) (F = max flow value). Space complexity: O(V + E).
 */
public final class MinCostFlow {
    private static final long INF = Long.MAX_VALUE;

    private MinCostFlow() {}

    public static final class CostEdge extends Edge {
        public final int cost;

        CostEdge(int to, int capacity, int cost) {
            super(to, capacity);
            this.cost = cost;
        }
    }

    public static final class CostFlowNetwork {
        private final int numNodes;
        private final List<List<CostEdge>> graph;

        public CostFlowNetwork(int numNodes) {
            this.numNodes = numNodes;
            this.graph = new ArrayList<>(numNodes);
            for (int i = 0; i < numNodes; i++) {
                graph.add(new ArrayList<>());
            }
        }

        public int numNodes() {
            return numNodes;
        }

        public List<CostEdge> edgesFrom(int u) {
            return graph.get(u);
        }

        List<List<CostEdge>> adjacency() {
            return graph;
        }

        public int numEdges() {
            int total = 0;
            for (List<CostEdge> adj : graph) {
                for (CostEdge e : adj) {
                    if (e.capacity > 0) {
                        total++;
                    }
                }
            }
            return total;
        }

        public void addEdge(int u, int v, int capacity, int cost) {
            if (cost < 0) {
                throw new IllegalArgumentException("SSP with zero initial potentials requires non-negative edge costs");
            }
            CostEdge forward = new CostEdge(v, capacity, cost);
            CostEdge backward = new CostEdge(u, 0, -cost);
            graph.get(u).add(forward);
            graph.get(v).add(backward);
            forward.reverseIndex = graph.get(v).size() - 1;
            backward.reverseIndex = graph.get(u).size() - 1;
        }
    }

    public record Result(int maxFlow, long minCost, MatchingResult trace) {}

    public static Result minCostMaxFlow(CostFlowNetwork network, int source, int sink) {
        int n = network.numNodes();
        long[] potential = new long[n];
        StepRecorder recorder = new StepRecorder();
        int augmentations = 0;
        long relaxations = 0;

        recorder.emit(StepEvent.GRAPH_CREATED,
                "Built cost-flow network with " + n + " nodes; student->lab edges cost (best score - score).",
                "num_nodes", n, "num_edges", network.numEdges());

        int flow = 0;
        long cost = 0;
        long start = System.nanoTime();
        long[] dist = new long[n];
        int[] prevNode = new int[n];
        int[] prevEdge = new int[n];
        while (true) {
            recorder.emit(StepEvent.SEARCHING_AUGMENTING_PATH, "Dijkstra on reduced costs for the cheapest augmenting path.");
            Arrays.fill(dist, INF);
            Arrays.fill(prevNode, -1);
            Arrays.fill(prevEdge, -1);
            dist[source] = 0;
            MinHeap heap = new MinHeap();
            heap.push(0, source);
            while (!heap.isEmpty()) {
                MinHeap.Entry entry = heap.pop();
                long d = entry.key();
                int u = entry.value();
                if (d > dist[u]) {
                    continue; // stale entry (lazy deletion)
                }
                List<CostEdge> edges = network.edgesFrom(u);
                for (int idx = 0; idx < edges.size(); idx++) {
                    CostEdge edge = edges.get(idx);
                    if (edge.residual() <= 0) {
                        continue;
                    }
                    long nd = d + edge.cost + potential[u] - potential[edge.to];
                    relaxations++;
                    if (nd < dist[edge.to]) {
                        dist[edge.to] = nd;
                        prevNode[edge.to] = u;
                        prevEdge[edge.to] = idx;
                        heap.push(nd, edge.to);
                    }
                }
            }

            if (dist[sink] == INF) {
                recorder.emit(StepEvent.NO_PATH_FOUND,
                        "Sink unreachable in the residual graph: flow is maximum and cost is minimum.");
                break;
            }

            for (int v = 0; v < n; v++) {
                if (dist[v] < INF) {
                    potential[v] += dist[v];
                }
            }

            int bottleneck = Integer.MAX_VALUE;
            for (int v = sink; v != source; v = prevNode[v]) {
                bottleneck = Math.min(bottleneck, network.edgesFrom(prevNode[v]).get(prevEdge[v]).residual());
            }

            long pathCost = 0;
            for (int v = sink; v != source; ) {
                int u = prevNode[v];
                CostEdge edge = network.edgesFrom(u).get(prevEdge[v]);
                edge.flow += bottleneck;
                network.edgesFrom(v).get(edge.reverseIndex).flow -= bottleneck;
                pathCost += edge.cost;
                v = u;
            }

            flow += bottleneck;
            cost += bottleneck * pathCost;
            augmentations++;
            recorder.emit(StepEvent.AUGMENTING_PATH_FOUND, "Augmentation #" + augmentations + ": pushed "
                    + bottleneck + " unit(s) along a path of cost " + pathCost + ".",
                    "pushed", bottleneck, "path_cost", pathCost);
            recorder.emit(StepEvent.MATCH_UPDATED, "Flow " + flow + ", total cost " + cost + ".", "flow", flow, "cost", cost);
        }

        double elapsedMs = (System.nanoTime() - start) / 1e6;
        recorder.emit(StepEvent.ALGORITHM_COMPLETE, "Min-cost max-flow reached: flow " + flow + " with total cost "
                + cost + " after " + augmentations + " shortest-path augmentations.", "max_flow", flow, "min_cost", cost);
        MatchingResult trace = MatchingResult.flowTrace("MIN_COST_FLOW", n, network.numEdges(), relaxations,
                augmentations, elapsedMs, "O(F * E log V)", "O(V + E)", recorder.steps());
        return new Result(flow, cost, trace);
    }
}
