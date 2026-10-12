# Project Report

## Automated Student-to-Laboratory Allocation Using Maximum Bipartite Matching

*Advanced Algorithms / Data Structures & Algorithms — Capstone Submission*

---

### 1. Abstract

This project designs and implements a full-stack system that allocates
students to laboratories by modeling the problem as **Maximum Bipartite
Matching**, solved both via classical augmenting-path algorithms (Kuhn's,
Hopcroft-Karp) and via its equivalent **Maximum Flow** formulation
(Edmonds-Karp, Dinic's). All four algorithms are implemented from first
principles. The system is wrapped in a real REST + WebSocket API, a
relational database, and a React frontend that visualizes the graph, the
algorithm's execution trace, and the resulting allocation — with an AI
layer that translates natural language into the same structured
constraints a human administrator would configure, and explains results
using only real, stored facts.

### 2. Problem Definition

**Given:**
- A set of students `S`, each with a department, year, CGPA, a skill
  profile, and a ranked list of preferred laboratories.
- A set of laboratories `L`, each with a capacity, department, required
  skills/equipment, and availability.
- A set of configurable constraints (eligibility rules, priority weights,
  fairness caps).

**Find:** an assignment `M ⊆ S × L` such that:
1. Each student appears in at most one pair (`∀s, |{(s,l) ∈ M}| ≤ 1`).
2. Each lab `l` appears in at most `capacity(l)` pairs.
3. Every pair `(s,l) ∈ M` is *eligible* under the active constraints.
4. `|M|` is maximum, subject to (1)-(3), and — among maximum matchings —
   preference/skill/priority score is maximized as a tie-break.

This is precisely the **Maximum Bipartite Matching** problem generalized
with vertex capacities on one side (a many-to-one b-matching), which
reduces to plain 1-1 bipartite matching by vertex splitting, and is
strictly more naturally expressed as a **Maximum Flow** problem.

### 3. Literature / Theoretical Background

- **König's theorem** and **Hall's marriage theorem** motivate why maximum
  matching size is the right optimality notion here (it characterizes
  exactly when a "perfect" allocation is impossible, and by how much).
- **Kuhn's algorithm** (a specialization of the Hungarian algorithm to the
  unweighted case) builds a maximum matching by repeatedly finding
  augmenting paths via DFS. Its correctness rests on **Berge's theorem**:
  a matching is maximum iff it admits no augmenting path.
- **Hopcroft-Karp** improves the phase count to `O(√V)` by proving that
  after `k` phases, the shortest augmenting path has length `≥ k`, and
  batching all vertex-disjoint shortest augmenting paths per phase.
- **Ford-Fulkerson / Edmonds-Karp**: the **max-flow min-cut theorem**
  guarantees that repeatedly saturating augmenting paths in the residual
  graph converges to a maximum flow; Edmonds-Karp's BFS choice bounds the
  number of augmentations by `O(V·E)`, giving `O(V·E²)` overall.
- **Dinic's algorithm** reorganizes augmentation into level-graph phases,
  each solved by a single blocking flow, giving a general `O(V²·E)` bound
  that specializes to `O(E√V)` on unit-capacity graphs — matching
  Hopcroft-Karp exactly, which is the direct proof-by-implementation that
  the matching and flow formulations are computationally equivalent here.

### 4. System Design

See [`README.md § 3-4`](README.md#3-system-architecture) for the full
architecture and ER diagram. In summary: FastAPI + SQLAlchemy + PostgreSQL
backend, React + TypeScript + Vite frontend, JWT auth with role-based
access (`ADMIN` / `FACULTY` / `STUDENT`), and a WebSocket channel that
replays each algorithm's real, recorded execution trace live to the UI.

### 5. Algorithm Design & Implementation

All four algorithms live in `backend/app/algorithms/` as dependency-free
Python (no `networkx`), each returning a common `MatchingResult` /
`(max_flow, MatchingResult)` shape carrying: matched pairs, vertex/edge
counts, iteration counts, measured execution time, complexity strings, and
a full step trace. Implementation notes:

- **`kuhn.py`** — recursive DFS `try_kuhn(left, visited)`; flips the
  matched/unmatched edge labels along any discovered augmenting path.
- **`hopcroft_karp.py`** — BFS `bfs()` assigns layer distances from all
  free left vertices; DFS `dfs(u)` is restricted to edges where
  `dist[match_right[v]] == dist[u] + 1`, guaranteeing only shortest
  augmenting paths are taken per phase.
- **`edmonds_karp.py`** — BFS `_bfs_find_path` over a residual `FlowNetwork`
  (adjacency of mutable `Edge` objects paired with an implicit reverse
  edge); pushes the bottleneck capacity along the discovered path.
- **`dinic.py`** — BFS `bfs_levels()` + DFS `dfs_blocking_flow()` with the
  classic **current-arc optimization** (`it[u]` pointer) so each node's
  adjacency list is scanned only once per phase.

`matching_engine.py` is the domain layer on top of these: it builds the
eligible-edge set from constraints (department rule, skill fit, lab
status/availability), scores each edge, and constructs either a
capacity-expanded `BipartiteGraph` (for Kuhn/Hopcroft-Karp) or a
source/sink `FlowNetwork` (for Edmonds-Karp/Dinic) before dispatching to
the requested algorithm.

### 6. Correctness Verification

Beyond unit tests per algorithm, two **cross-validation properties** are
tested directly against randomized inputs (see `backend/tests/`):

- Kuhn's algorithm and Hopcroft-Karp always agree on the maximum matching
  *size* across 20+ randomized bipartite graphs of varying density.
- Edmonds-Karp and Dinic's algorithm always agree on the maximum flow
  *value* across 15+ randomized flow networks, and both agree with Kuhn's
  matching size when the same bipartite structure is expressed as a flow
  network.

This is a stronger correctness argument than testing each algorithm in
isolation: it directly exercises the theoretical equivalence the project
claims to demonstrate.

### 7. Complexity Analysis

| Algorithm | Time | Space |
|---|---|---|
| Kuhn's | `O(V·E)` | `O(V+E)` |
| Hopcroft-Karp | `O(E√V)` | `O(V+E)` |
| Edmonds-Karp | `O(V·E²)` | `O(V+E)` |
| Dinic's | `O(V²E)` general, `O(E√V)` unit-capacity bipartite | `O(V+E)` |

Empirically measured execution time for every run is persisted in
`algorithm_metrics` and exposed on the Analytics and Algorithm Playground
pages, so the theoretical bounds above can be checked against real
wall-clock behavior on the seeded 220-student / 11-lab dataset (and on
arbitrary synthetic graphs in the Playground).

### 8. AI-Assisted Layer

Implemented as a strictly-bounded enhancement (see
[`README.md § 13`](README.md#13-ai-layer--design-contract)): natural
language is parsed into the *same* `AllocationConfig` structure a human
would configure, and is always executed by the unmodified deterministic
engine. Explanations, conflict detection and reports read only real,
already-persisted database rows.

### 9. Results & Discussion

On the seeded dataset (220 students, 10 active labs + 1 under
maintenance, default constraint weights), all four algorithms converge to
the same maximum matching size (105 matched students), confirming the
theoretical equivalence of the matching and flow formulations in practice.
Unmatched students are attributable, with a stored reason per student, to
either missing required skills or capacity exhaustion by higher-scoring
peers — both inspectable via the AI Explanation panel and the Analytics /
Conflicts views.

### 10. Conclusion

The project demonstrates that Maximum Bipartite Matching is not merely a
textbook exercise but a directly deployable solution to a real
institutional resource-allocation problem, and that a natural-language
interface can meaningfully improve usability *without* compromising the
correctness guarantees of the underlying deterministic algorithm.

### 11. References

- Berge, C. "Two theorems in graph theory." *PNAS*, 1957.
- Hopcroft, J. E., & Karp, R. M. "An n^{5/2} algorithm for maximum
  matchings in bipartite graphs." *SIAM Journal on Computing*, 1973.
- Edmonds, J., & Karp, R. M. "Theoretical improvements in algorithmic
  efficiency for network flow problems." *JACM*, 1972.
- Dinic, E. A. "Algorithm for solution of a problem of maximum flow in a
  network with power estimation." *Soviet Math. Doklady*, 1970.
- Cormen, Leiserson, Rivest, Stein. *Introduction to Algorithms*, chapters
  on Elementary Graph Algorithms, Maximum Flow, and Bipartite Matching.
