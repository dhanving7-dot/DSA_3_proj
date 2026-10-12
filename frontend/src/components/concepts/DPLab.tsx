import { useState } from "react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DemoCard, Field, MetricTile, Verified } from "@/components/concepts/DemoCard"
import { DPTable } from "@/components/concepts/DPTable"
import { BinaryTreeSVG, TourSVG, TreeSVG, type BinaryTreeNode } from "@/components/concepts/Plots"
import { useConceptDemo } from "@/hooks/useInsights"
import { apiErrorMessage } from "@/lib/api"
import { SERIES } from "@/lib/chartTheme"
import { formatMs, parseNumberList } from "@/lib/utils"

function onError(err: unknown) {
  toast.error(apiErrorMessage(err))
}

export function DPLab() {
  return (
    <div className="space-y-4">
      <EditDistanceDemo />
      <AlignmentDemo />
      <MatrixChainDemo />
      <OptimalBSTDemo />
      <TSPDemo />
      <TreeDemo />
    </div>
  )
}

// --------------------------------------------------------------------------- edit distance

interface EditResponse {
  variant: string
  distance: number
  table: number[][]
  operations: { op: string; a: string; b: string }[]
  path: [number, number][]
  cells_computed: number
}

const OP_COLORS: Record<string, string> = {
  match: "text-ink-muted",
  substitute: "text-warning",
  insert: "text-good",
  delete: "text-critical",
  transpose: "text-violet-400",
}

function EditDistanceDemo() {
  const [a, setA] = useState("hopcrfot")
  const [b, setB] = useState("hopcroft")
  const [variant, setVariant] = useState<"LEVENSHTEIN" | "DAMERAU" | "WEIGHTED">("DAMERAU")
  const [costs, setCosts] = useState({ insert_cost: 1, delete_cost: 1, substitute_cost: 2 })
  const demo = useConceptDemo<EditResponse>("/dp/edit-distance")
  const run = () => demo.mutate({ a, b, variant, ...costs }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="edit"
      title="Edit distance: Levenshtein, Damerau and weighted (Wagner-Fischer)"
      complexity="O(n·m)"
      concept={
        <>
          D[i][j] is the cheapest way to turn the first i characters of A into the first j of B, built from three neighbours (delete,
          insert, substitute) - Damerau adds a fourth, the diagonal two steps back, for swapped adjacent letters. The highlighted path is
          the traceback: read it bottom-right to top-left and it spells the edit script. This is what lets the AI parser accept
          <code> dinik</code> for Dinic and entity search find <code>jonh</code>.
        </>
      }
      controls={
        <>
          <Field label="A">
            <Input value={a} onChange={(e) => setA(e.target.value)} maxLength={40} className="w-44 font-mono" />
          </Field>
          <Field label="B">
            <Input value={b} onChange={(e) => setB(e.target.value)} maxLength={40} className="w-44 font-mono" />
          </Field>
          <Field label="Variant">
            <Select value={variant} onValueChange={(v) => setVariant(v as typeof variant)}>
              <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="LEVENSHTEIN">Levenshtein</SelectItem>
                <SelectItem value="DAMERAU">Damerau (OSA)</SelectItem>
                <SelectItem value="WEIGHTED">Weighted</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          {variant === "WEIGHTED" &&
            (["insert_cost", "delete_cost", "substitute_cost"] as const).map((k) => (
              <Field key={k} label={k.replace("_cost", "")}>
                <Input type="number" min={0} max={10} step={0.5} value={costs[k]} onChange={(e) => setCosts((c) => ({ ...c, [k]: Number(e.target.value) }))} className="w-20" />
              </Field>
            ))}
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <MetricTile label="Distance" value={data.distance} tone="brand" />
            <MetricTile label="Cells computed" value={data.cells_computed} hint="= |A| × |B|" />
            <MetricTile label="Edit script" value={<span className="font-mono text-xs">{data.operations.map((o) => (o.op === "match" ? "=" : o.op[0].toUpperCase())).join("")}</span>} hint="= match, S/I/D/T" />
          </div>
          <div className="flex flex-wrap gap-1">
            {data.operations.map((o, i) => (
              <span key={i} className={`rounded border border-border-subtle px-1.5 py-0.5 font-mono text-[11px] ${OP_COLORS[o.op] ?? ""}`}>
                {o.op === "match" ? o.a : o.op === "insert" ? `+${o.b}` : o.op === "delete" ? `−${o.a}` : o.op === "transpose" ? `${o.a}⇄` : `${o.a}→${o.b}`}
              </span>
            ))}
          </div>
          <DPTable table={data.table} rowLabels={["ε", ...a.split("")]} colLabels={["ε", ...b.split("")]} path={data.path} corner="A\\B" />
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- alignment

interface AlignResponse {
  mode: string
  score: number
  table: number[][]
  aligned_a: string
  aligned_b: string
  path: [number, number][]
  a_range?: [number, number]
  b_range?: [number, number]
}

function AlignmentDemo() {
  const [a, setA] = useState("GATTACA")
  const [b, setB] = useState("GCATGCU")
  const [mode, setMode] = useState<"GLOBAL" | "LOCAL">("GLOBAL")
  const [scores, setScores] = useState({ match: 1, mismatch: -1, gap: -1 })
  const demo = useConceptDemo<AlignResponse>("/dp/alignment")
  const run = () => demo.mutate({ a, b, mode, ...scores }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="align"
      title="Sequence alignment: Needleman-Wunsch (global) vs Smith-Waterman (local)"
      complexity="O(n·m)"
      concept={
        <>
          Edit distance with a scoring matrix: a match earns, a mismatch or gap costs. Global alignment must consume both strings end to end.
          Local alignment clamps every cell at 0, so a bad region can be abandoned and the best-scoring pair of <em>substrings</em> wins -
          the trace starts at the table's maximum, not its corner.
        </>
      }
      controls={
        <>
          <Field label="Sequence A"><Input value={a} onChange={(e) => setA(e.target.value.toUpperCase())} maxLength={40} className="w-44 font-mono" /></Field>
          <Field label="Sequence B"><Input value={b} onChange={(e) => setB(e.target.value.toUpperCase())} maxLength={40} className="w-44 font-mono" /></Field>
          <Field label="Mode">
            <Select value={mode} onValueChange={(v) => setMode(v as typeof mode)}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="GLOBAL">Global (NW)</SelectItem>
                <SelectItem value="LOCAL">Local (SW)</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          {(["match", "mismatch", "gap"] as const).map((k) => (
            <Field key={k} label={k}>
              <Input type="number" min={-10} max={10} value={scores[k]} onChange={(e) => setScores((s) => ({ ...s, [k]: Number(e.target.value) }))} className="w-20" />
            </Field>
          ))}
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <MetricTile label={`${data.mode.toLowerCase()} score`} value={data.score} tone="brand" />
            {data.a_range && <MetricTile label="Aligned regions" value={`A[${data.a_range[0]}:${data.a_range[1]}] · B[${data.b_range?.[0]}:${data.b_range?.[1]}]`} />}
          </div>
          <pre className="rounded-lg border border-border-subtle bg-white/[0.02] p-3 font-mono text-sm leading-6 text-ink">
            {data.aligned_a}
            {"\n"}
            {data.aligned_a.split("").map((c, i) => (c === data.aligned_b[i] ? "|" : " ")).join("")}
            {"\n"}
            {data.aligned_b}
          </pre>
          <DPTable table={data.table} rowLabels={["ε", ...a.split("")]} colLabels={["ε", ...b.split("")]} path={data.path} corner="A\\B" />
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- matrix chain

interface MatrixChainResponse {
  min_cost: number
  parenthesization: string
  left_to_right_cost: number
  cost_table: (number | null)[][]
}

function MatrixChainDemo() {
  const [dims, setDims] = useState("30 35 15 5 10 20 25")
  const demo = useConceptDemo<MatrixChainResponse>("/dp/matrix-chain")
  const run = () => demo.mutate({ dims: parseNumberList(dims) }, { onError })
  const data = demo.data
  const n = parseNumberList(dims).length - 1

  return (
    <DemoCard
      id="interval"
      title="Interval DP: matrix-chain multiplication"
      complexity="O(n³) time · O(n²) space"
      concept={
        <>
          Multiplying A₁…Aₙ costs wildly different amounts depending on where you put the parentheses. cost[i][j] is the cheapest way to
          multiply the chain i…j, found by trying every split k between them - intervals are filled shortest first, so both halves are
          always ready. The CLRS instance here saves 73% over left-to-right evaluation.
        </>
      }
      controls={
        <Field label="Dimensions p₀ p₁ … pₙ (matrix i is pᵢ₋₁ × pᵢ)">
          <Input value={dims} onChange={(e) => setDims(e.target.value)} className="w-80 font-mono" />
        </Field>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <MetricTile label="Minimum scalar multiplications" value={data.min_cost.toLocaleString()} tone="brand" />
            <MetricTile label="Left-to-right cost" value={data.left_to_right_cost.toLocaleString()} hint={`${Math.round((1 - data.min_cost / data.left_to_right_cost) * 100)}% saved`} />
            <MetricTile label="Optimal parenthesization" value={<span className="font-mono text-xs">{data.parenthesization}</span>} />
          </div>
          <DPTable
            table={data.cost_table.slice(1).map((r) => r.slice(1))}
            rowLabels={Array.from({ length: n }, (_, i) => `A${i + 1}`)}
            colLabels={Array.from({ length: n }, (_, i) => `A${i + 1}`)}
            corner="i\\j"
            highlight={[0, n - 1]}
            format={(v) => v.toLocaleString()}
          />
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- optimal BST

interface OBSTResponse {
  keys: string[]
  freqs: number[]
  cost: number
  tree: BinaryTreeNode | null
  cubic_root_evaluations: number
  knuth_root_evaluations: number
  costs_agree: boolean
  balanced_tree_cost: number
}

function OptimalBSTDemo() {
  const [keys, setKeys] = useState("k1 k2 k3 k4 k5")
  const [freqs, setFreqs] = useState("25 10 20 5 40")
  const [fromLabs, setFromLabs] = useState(true)
  const demo = useConceptDemo<OBSTResponse>("/dp/obst")
  const run = () =>
    demo.mutate(fromLabs ? { from_lab_data: true } : { keys: keys.split(/[\s,]+/).filter(Boolean), freqs: parseNumberList(freqs) }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="obst"
      title="Optimal binary search tree (with Knuth's speed-up)"
      complexity="O(n³) → O(n²) with Knuth"
      concept={
        <>
          Given sorted keys and how often each is looked up, which BST minimises total search depth? e[i][j] tries every root r of the
          interval. Knuth's observation that the optimal root never moves left when the interval grows right shrinks each search to
          root[i][j−1]…root[i+1][j], and the ranges telescope to O(n²). With lab codes as keys and preference counts as frequencies you get
          the tree that finds popular labs fastest.
        </>
      }
      controls={
        <>
          <Field label="Source">
            <Select value={fromLabs ? "labs" : "custom"} onValueChange={(v) => setFromLabs(v === "labs")}>
              <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="labs">Lab codes × preference counts</SelectItem>
                <SelectItem value="custom">Custom keys</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          {!fromLabs && (
            <>
              <Field label="Keys"><Input value={keys} onChange={(e) => setKeys(e.target.value)} className="w-56 font-mono" /></Field>
              <Field label="Frequencies"><Input value={freqs} onChange={(e) => setFreqs(e.target.value)} className="w-56 font-mono" /></Field>
            </>
          )}
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Optimal cost Σ f·depth" value={data.cost.toLocaleString()} tone="brand" />
            <MetricTile label="Balanced tree cost" value={data.balanced_tree_cost.toLocaleString()} hint="median splits, ignoring frequencies" />
            <MetricTile label="Root candidates tried (O(n³))" value={data.cubic_root_evaluations} />
            <MetricTile label="With Knuth (O(n²))" value={data.knuth_root_evaluations} tone="good" />
          </div>
          <Verified ok={data.costs_agree}>Both recurrences produce the same optimal cost.</Verified>
          <BinaryTreeSVG root={data.tree} weights={Object.fromEntries(data.keys.map((k, i) => [k, data.freqs[i]]))} />
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- TSP

interface TSPResponse {
  points: number[][]
  held_karp: { cost: number; tour: number[]; states: number; time_ms: number }
  nearest_neighbour: { cost: number; tour: number[]; ratio: number }
  mst_2approx: { cost: number; tour: number[]; mst_weight: number; ratio: number }
}

function TSPDemo() {
  const [n, setN] = useState(9)
  const [seed, setSeed] = useState(7)
  const demo = useConceptDemo<TSPResponse>("/dp/tsp")
  const run = () => demo.mutate({ num_cities: n, seed }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="tsp"
      title="Bitmask DP: Held-Karp TSP vs two heuristics"
      complexity="O(2ⁿ·n²) exact · O(n²) approximations"
      concept={
        <>
          dp[mask][v] = shortest path from city 0 that visits exactly the cities in <code>mask</code> and ends at v. 2ⁿ masks × n endpoints
          is exponential but far better than n! permutations, and it is exact. Beside it: the nearest-neighbour heuristic (no guarantee)
          and the MST preorder walk, which is provably within 2× of optimal on metric instances - compare the measured ratios.
        </>
      }
      controls={
        <>
          <Field label="Cities (3-11)"><Input type="number" min={3} max={11} value={n} onChange={(e) => setN(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <TourSVG points={data.points} tour={data.held_karp.tour} title={`Held-Karp · ${data.held_karp.cost} (optimal)`} color={SERIES.blue} />
            <TourSVG points={data.points} tour={data.mst_2approx.tour} title={`MST walk · ${data.mst_2approx.cost} (${data.mst_2approx.ratio}× opt)`} color={SERIES.orange} />
            <TourSVG points={data.points} tour={data.nearest_neighbour.tour} title={`Nearest neighbour · ${data.nearest_neighbour.cost} (${data.nearest_neighbour.ratio}× opt)`} color={SERIES.aqua} />
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="DP states expanded" value={data.held_karp.states.toLocaleString()} hint={`vs ${factorialLabel(n - 1)} permutations`} />
            <MetricTile label="Held-Karp time" value={formatMs(data.held_karp.time_ms)} />
            <MetricTile label="MST weight (lower bound)" value={data.mst_2approx.mst_weight} hint="MST ≤ OPT ≤ 2·MST" />
            <MetricTile label="2-approx guarantee holds" value={data.mst_2approx.ratio <= 2 ? "yes" : "no"} tone={data.mst_2approx.ratio <= 2 ? "good" : "critical"} />
          </div>
        </div>
      )}
    </DemoCard>
  )
}

function factorialLabel(k: number) {
  let f = 1
  for (let i = 2; i <= k; i++) f *= i
  return f.toLocaleString()
}

// --------------------------------------------------------------------------- tree DP

interface TreeResponse {
  num_nodes: number
  edges: [number, number][]
  diameter: number
  centroids: number[]
  max_independent_set: number
  sum_of_distances: number[]
  subtree_sizes: number[]
  parent: number[]
  rerooting_matches_bfs: boolean
}

function TreeDemo() {
  const [n, setN] = useState(14)
  const [seed, setSeed] = useState(5)
  const demo = useConceptDemo<TreeResponse>("/dp/tree")
  const run = () => demo.mutate({ num_nodes: n, seed }, { onError })
  const data = demo.data
  const best = data ? data.sum_of_distances.indexOf(Math.min(...data.sum_of_distances)) : -1

  return (
    <DemoCard
      id="tree"
      title="DP on trees and the rerooting technique"
      complexity="O(n) for all four answers"
      concept={
        <>
          One post-order pass computes subtree sizes, the diameter (two deepest child paths meeting at a node) and the maximum independent
          set (take a node and skip its children, or skip it). Rerooting then answers "sum of distances from <em>every</em> node" in one more
          pass: moving the root from u to child v brings size[v] nodes one step closer and pushes n − size[v] one step away. The result is
          checked against n separate BFS runs.
        </>
      }
      controls={
        <>
          <Field label="Nodes (2-60)"><Input type="number" min={2} max={60} value={n} onChange={(e) => setN(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Diameter" value={data.diameter} />
            <MetricTile label="Centroid(s)" value={data.centroids.join(", ")} hint="ringed in the drawing" />
            <MetricTile label="Max independent set" value={data.max_independent_set} />
            <MetricTile label="Best meeting point" value={`node ${best}`} hint={`Σ distances = ${data.sum_of_distances[best]}`} />
          </div>
          <Verified ok={data.rerooting_matches_bfs}>Rerooted distance sums equal {data.num_nodes} independent BFS computations.</Verified>
          <TreeSVG n={data.num_nodes} parent={data.parent} highlight={data.centroids} />
          <div className="max-h-40 overflow-auto rounded-lg border border-border-subtle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Node</TableHead>
                  <TableHead>Subtree size</TableHead>
                  <TableHead>Σ distances to all nodes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.sum_of_distances.map((d, v) => (
                  <TableRow key={v}>
                    <TableCell className="tabular">{v}{data.centroids.includes(v) && <Badge variant="secondary" className="ml-2 text-[10px]">centroid</Badge>}</TableCell>
                    <TableCell className="tabular">{data.subtree_sizes[v]}</TableCell>
                    <TableCell className="tabular">{d}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </DemoCard>
  )
}
