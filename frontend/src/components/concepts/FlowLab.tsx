import { useMemo, useState } from "react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { BipartiteFlowGraph } from "@/components/graph/BipartiteFlowGraph"
import { AlgorithmStepper } from "@/components/graph/AlgorithmStepper"
import { DemoCard, Field, MetricTile, Verified } from "@/components/concepts/DemoCard"
import { useConceptDemo } from "@/hooks/useInsights"
import { parseNumberList } from "@/lib/utils"
import { apiErrorMessage } from "@/lib/api"
import type { AlgorithmStep } from "@/types"

function onError(err: unknown) {
  toast.error(apiErrorMessage(err))
}

export function FlowLab() {
  return (
    <div className="space-y-4">
      <MinCutDemo />
      <MinCostDemo />
      <ProjectSelectionDemo />
    </div>
  )
}

// --------------------------------------------------------------------------- min cut / König

interface MinCutResponse {
  num_left: number
  num_right: number
  edges: [number, number][]
  max_flow: number
  cut_capacity: number
  cut_edges: { from: string; to: string; capacity: number }[]
  source_side: string[]
  matching: [number, number][]
  konig_cover: { students: number[]; labs: number[]; size: number }
  approx_cover_size: number
}

function MinCutDemo() {
  const [numLeft, setNumLeft] = useState(7)
  const [numRight, setNumRight] = useState(5)
  const [p, setP] = useState(0.35)
  const [seed, setSeed] = useState(11)
  const demo = useConceptDemo<MinCutResponse>("/flow/min-cut")
  const run = () => demo.mutate({ num_left: numLeft, num_right: numRight, edge_probability: p, seed }, { onError })
  const data = demo.data

  const graph = useMemo(() => {
    if (!data) return null
    const matched = new Set(data.matching.map(([l, r]) => `${l}-${r}`))
    const coverL = new Set(data.konig_cover.students)
    const coverR = new Set(data.konig_cover.labs)
    return {
      left: Array.from({ length: data.num_left }, (_, i) => ({ id: i, label: `Student ${i}`, sublabel: coverL.has(i) ? "in cover" : undefined })),
      right: Array.from({ length: data.num_right }, (_, i) => ({ id: i, label: `Lab ${i}`, sublabel: coverR.has(i) ? "in cover" : undefined })),
      edges: data.edges.map(([l, r]) => ({ source: l, target: r, matched: matched.has(`${l}-${r}`) })),
    }
  }, [data])

  return (
    <DemoCard
      id="mincut"
      title="Max-flow min-cut, König's theorem and Hall's condition"
      complexity="O(V + E) after one max flow"
      concept={
        <>
          When no augmenting path remains, the nodes still reachable from the source in the residual graph form a cut whose capacity equals
          the flow - that equality is the proof of optimality. On a bipartite graph the same reachability set gives König's minimum vertex
          cover (students not reached + labs reached), which has exactly |maximum matching| vertices. Vertex cover is NP-hard in general;
          bipartite structure makes it polynomial.
        </>
      }
      controls={
        <>
          <Field label="Students"><Input type="number" min={1} max={12} value={numLeft} onChange={(e) => setNumLeft(Number(e.target.value))} className="w-20" /></Field>
          <Field label="Labs"><Input type="number" min={1} max={12} value={numRight} onChange={(e) => setNumRight(Number(e.target.value))} className="w-20" /></Field>
          <Field label="Edge probability"><Input type="number" min={0} max={1} step={0.05} value={p} onChange={(e) => setP(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && graph && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Max flow = |matching|" value={data.max_flow} tone="brand" />
            <MetricTile label="Min cut capacity" value={data.cut_capacity} />
            <MetricTile label="König cover size" value={data.konig_cover.size} hint={`${data.konig_cover.students.length} students + ${data.konig_cover.labs.length} labs`} />
            <MetricTile label="2-approx cover size" value={data.approx_cover_size} hint="maximal-matching endpoints" />
          </div>
          <Verified ok={data.max_flow === data.cut_capacity && data.konig_cover.size === data.max_flow}>
            max flow = min cut = minimum vertex cover = {data.max_flow} (theorem checked on this instance).
          </Verified>
          <div className="rounded-xl border border-border-subtle p-1">
            <BipartiteFlowGraph leftItems={graph.left} rightItems={graph.right} edges={graph.edges} height={Math.max(260, Math.max(numLeft, numRight) * 66)} showMiniMap={false} />
          </div>
          <div className="flex flex-wrap gap-1.5 text-xs">
            <span className="text-ink-muted">Cut edges (all saturated):</span>
            {data.cut_edges.map((e, i) => (
              <Badge key={i} variant="secondary" className="font-mono">
                {e.from}→{e.to}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- min-cost flow

interface MinCostResponse {
  num_left: number
  num_right: number
  edges: { student: number; lab: number; score: number }[]
  min_cost_flow: { flow: number; total_score: number; pairs: [number, number][]; augmentations: number; steps: AlgorithmStep[] }
  edmonds_karp: { flow: number; total_score: number; pairs: [number, number][] }
  bitmask_dp_oracle: { matched: number; total_score: number }
  optimal_verified: boolean
}

function MinCostDemo() {
  const [numLeft, setNumLeft] = useState(6)
  const [numRight, setNumRight] = useState(5)
  const [seed, setSeed] = useState(11)
  const demo = useConceptDemo<MinCostResponse>("/flow/min-cost")
  const run = () => demo.mutate({ num_left: numLeft, num_right: numRight, edge_probability: 0.6, seed }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="mincost"
      title="Min-cost max-flow: the assignment problem"
      complexity="O(F·E log V) with Dijkstra + potentials"
      concept={
        <>
          Max-flow finds <em>a</em> maximum matching; which one is an accident of search order. Give each student→lab edge a cost
          (10 − score) and ask for the cheapest maximum flow: successive shortest paths augment along the cheapest residual path, using
          Johnson potentials so Dijkstra works despite negative reverse edges. The result is a maximum matching with maximum total score -
          verified here against an exact bitmask DP over all assignments.
        </>
      }
      controls={
        <>
          <Field label="Students"><Input type="number" min={1} max={8} value={numLeft} onChange={(e) => setNumLeft(Number(e.target.value))} className="w-20" /></Field>
          <Field label="Labs"><Input type="number" min={1} max={8} value={numRight} onChange={(e) => setNumRight(Number(e.target.value))} className="w-20" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Edmonds-Karp" value={`${data.edmonds_karp.flow} matched · score ${data.edmonds_karp.total_score}`} hint="some maximum matching" />
            <MetricTile label="Min-cost flow" value={`${data.min_cost_flow.flow} matched · score ${data.min_cost_flow.total_score}`} hint="best maximum matching" tone="brand" />
            <MetricTile label="Bitmask DP oracle" value={`${data.bitmask_dp_oracle.matched} · score ${data.bitmask_dp_oracle.total_score}`} hint="exhaustive, independent" />
            <MetricTile label="Shortest-path augmentations" value={data.min_cost_flow.augmentations} />
          </div>
          <Verified ok={data.optimal_verified}>Min-cost flow matches the exhaustive optimum in both cardinality and total score.</Verified>
          <ScoreMatrix data={data} />
          <div>
            <p className="mb-1 text-xs font-medium text-ink-secondary">Successive shortest paths trace</p>
            <AlgorithmStepper steps={data.min_cost_flow.steps} />
          </div>
        </div>
      )}
    </DemoCard>
  )
}

function ScoreMatrix({ data }: { data: MinCostResponse }) {
  const score: Record<string, number> = {}
  for (const e of data.edges) score[`${e.student}-${e.lab}`] = e.score
  const mc = new Set(data.min_cost_flow.pairs.map(([s, l]) => `${s}-${l}`))
  const ek = new Set(data.edmonds_karp.pairs.map(([s, l]) => `${s}-${l}`))
  return (
    <div className="overflow-auto rounded-lg border border-border-subtle">
      <table className="text-[11px] tabular">
        <thead>
          <tr>
            <th className="px-2 py-1 text-ink-muted">score</th>
            {Array.from({ length: data.num_right }, (_, l) => <th key={l} className="px-2 py-1 font-medium text-ink-secondary">Lab {l}</th>)}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: data.num_left }, (_, s) => (
            <tr key={s}>
              <th className="px-2 py-1 text-right font-medium text-ink-secondary">Student {s}</th>
              {Array.from({ length: data.num_right }, (_, l) => {
                const key = `${s}-${l}`
                const v = score[key]
                const inMc = mc.has(key)
                const inEk = ek.has(key)
                return (
                  <td
                    key={l}
                    className={`border border-border-subtle/60 px-2 py-1 text-center ${v == null ? "text-ink-muted/30" : "text-ink-secondary"} ${inMc ? "bg-brand-500/25 font-semibold text-ink" : ""} ${inEk && !inMc ? "ring-1 ring-inset ring-series-aqua" : ""}`}
                    title={inMc ? "chosen by min-cost flow" : inEk ? "chosen by Edmonds-Karp" : undefined}
                  >
                    {v ?? "·"}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-2 py-1 text-[10px] text-ink-muted">filled = min-cost flow choice · outlined = Edmonds-Karp choice (when different)</p>
    </div>
  )
}

// --------------------------------------------------------------------------- project selection

interface ProjectResponse {
  max_profit: number
  min_cut: number
  projects: number[]
  tools: number[]
  bruteforce_best: number
  verified: boolean
}

function ProjectSelectionDemo() {
  const [profits, setProfits] = useState("12 8 5 9")
  const [costs, setCosts] = useState("6 4 7 3")
  const [requires, setRequires] = useState("0-0 0-1 1-1 2-2 3-3 3-0")
  const demo = useConceptDemo<ProjectResponse>("/flow/project-selection")
  const run = () =>
    demo.mutate(
      {
        profits: parseNumberList(profits),
        costs: parseNumberList(costs),
        requires: requires.split(/[\s,]+/).filter(Boolean).map((t) => t.split("-").map(Number)),
      },
      { onError }
    )
  const data = demo.data

  return (
    <DemoCard
      id="projects"
      title="Reduction: project selection as a minimum cut"
      complexity="one max flow"
      concept={
        <>
          Labs (projects) bring revenue but need equipment (tools) that costs money; equipment can be shared. Build source→project
          (capacity = profit), tool→sink (capacity = cost), project→tool (∞). Any finite cut keeps every chosen project together with its
          tools, and best profit = Σprofits − min cut. The source side of the cut is the plan. Verified against all 2ⁿ subsets.
        </>
      }
      controls={
        <>
          <Field label="Project profits"><Input value={profits} onChange={(e) => setProfits(e.target.value)} className="w-40 font-mono" /></Field>
          <Field label="Tool costs"><Input value={costs} onChange={(e) => setCosts(e.target.value)} className="w-40 font-mono" /></Field>
          <Field label="Requirements project-tool"><Input value={requires} onChange={(e) => setRequires(e.target.value)} className="w-64 font-mono" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Best net profit" value={data.max_profit} tone="brand" />
            <MetricTile label="Min cut" value={data.min_cut} hint="= Σ profits − best" />
            <MetricTile label="Projects chosen" value={data.projects.length ? data.projects.map((i) => `P${i}`).join(", ") : "none"} />
            <MetricTile label="Tools bought" value={data.tools.length ? data.tools.map((i) => `T${i}`).join(", ") : "none"} />
          </div>
          <Verified ok={data.verified}>Brute force over every subset of projects also finds {data.bruteforce_best}.</Verified>
        </div>
      )}
    </DemoCard>
  )
}
