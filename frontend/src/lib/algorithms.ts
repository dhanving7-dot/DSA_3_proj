import type { AlgorithmName } from "@/types"

export interface AlgorithmMeta {
  value: AlgorithmName
  label: string
  hint: string
  family: "matching" | "flow" | "cost-flow"
}

/** Every allocation algorithm the engine can run, in the order the UI lists them. */
export const ALLOCATION_ALGORITHMS: AlgorithmMeta[] = [
  { value: "KUHN", label: "Kuhn's Algorithm", hint: "O(V·E) DFS augmenting paths", family: "matching" },
  { value: "HOPCROFT_KARP", label: "Hopcroft-Karp", hint: "O(E·√V) BFS-layered phases", family: "matching" },
  { value: "FORD_FULKERSON", label: "Ford-Fulkerson", hint: "O(E·|f*|) any augmenting path (DFS)", family: "flow" },
  { value: "EDMONDS_KARP", label: "Edmonds-Karp", hint: "O(V·E²) shortest augmenting paths", family: "flow" },
  { value: "DINIC", label: "Dinic's Algorithm", hint: "O(V²·E) blocking flows on level graphs", family: "flow" },
  { value: "MIN_COST_FLOW", label: "Min-Cost Max-Flow", hint: "O(F·E log V) max matching, max total score", family: "cost-flow" },
]

export const ALGORITHM_LABELS: Record<string, string> = Object.fromEntries(
  ALLOCATION_ALGORITHMS.map((a) => [a.value, a.label])
)

/** Plain bipartite matching cannot express per-department quotas inside a lab (a laminar constraint). */
export function supportsFairnessCap(algorithm: AlgorithmName): boolean {
  return ALLOCATION_ALGORITHMS.find((a) => a.value === algorithm)?.family !== "matching"
}

export const FAIRNESS_EXPLANATION =
  "A fairness cap nests a per-department quota inside each lab's capacity. Plain bipartite matching (Kuhn, Hopcroft-Karp) " +
  "cannot express that; the flow formulation can, by routing each department through a quota gadget node."
