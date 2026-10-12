import { useState } from "react"
import { toast } from "sonner"
import { ArrowRight } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { DemoCard, Field, MetricTile, Verified } from "@/components/concepts/DemoCard"
import { useConceptDemo } from "@/hooks/useInsights"
import { apiErrorMessage } from "@/lib/api"
import { formatMs, parseNumberList } from "@/lib/utils"
import type { Reduction } from "@/types/insights"

function onError(err: unknown) {
  toast.error(apiErrorMessage(err))
}

export function NPLab({ reductions }: { reductions: Reduction[] }) {
  return (
    <div className="space-y-4">
      <ReductionZoo reductions={reductions} />
      <VertexCoverDemo />
      <SetCoverDemo />
      <KnapsackDemo />
    </div>
  )
}

function ReductionZoo({ reductions }: { reductions: Reduction[] }) {
  return (
    <Card id="reductions" className="scroll-mt-24 p-5">
      <p className="text-base font-medium text-ink">The reduction zoo</p>
      <p className="mt-1 text-xs text-ink-secondary">
        A polynomial-time reduction A ≤ₚ B says "if B were easy, A would be too". Starting from SAT (Cook-Levin), every problem below is
        NP-complete. Recognising one of these shapes in a real requirement is the practical engineer's checklist - which is why the
        allocation engine stays within max-flow (polynomial) rather than claiming to solve, say, timetabling with arbitrary conflicts exactly.
      </p>
      <ol className="mt-4 grid gap-2 sm:grid-cols-2">
        {reductions.map((r, i) => (
          <li key={i} className="rounded-lg border border-border-subtle bg-white/[0.02] p-3 text-xs">
            <p className="flex items-center gap-1.5 font-mono text-ink">
              <span>{r.from}</span>
              <ArrowRight className="h-3 w-3 text-brand-400" />
              <span>{r.to}</span>
            </p>
            <p className="mt-1 text-ink-muted">{r.idea}</p>
          </li>
        ))}
      </ol>
    </Card>
  )
}

// --------------------------------------------------------------------------- vertex cover

interface VCResponse {
  num_vertices: number
  edges: [number, number][]
  approx: { cover: number[]; size: number; maximal_matching: [number, number][] }
  exact: { cover: number[]; size: number; subsets_checked: number; time_ms: number }
  ratio: number
}

function VertexCoverDemo() {
  const [n, setN] = useState(12)
  const [p, setP] = useState(0.3)
  const [seed, setSeed] = useState(4)
  const demo = useConceptDemo<VCResponse>("/np/vertex-cover")
  const run = () => demo.mutate({ num_vertices: n, edge_probability: p, seed }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="vertexcover"
      title="Vertex cover: 2-approximation via maximal matching vs exact search"
      complexity="O(V + E) approx · O(2ⁿ·E) exact"
      concept={
        <>
          Pick any uncovered edge, take <em>both</em> endpoints, repeat. The picked edges form a matching M, and every cover needs at
          least one endpoint of each edge in M, so OPT ≥ |M| and our cover is 2|M| ≤ 2·OPT. The exact answer checks subsets in increasing
          size - fine at 16 vertices, hopeless at 60. The measured ratio is usually well under the worst-case 2.
        </>
      }
      controls={
        <>
          <Field label="Vertices (2-16)"><Input type="number" min={2} max={16} value={n} onChange={(e) => setN(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Edge probability"><Input type="number" min={0} max={1} step={0.05} value={p} onChange={(e) => setP(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Edges" value={data.edges.length} />
            <MetricTile label="2-approx cover" value={data.approx.size} hint={`from a maximal matching of ${data.approx.maximal_matching.length}`} />
            <MetricTile label="Exact minimum" value={data.exact.size} hint={`${data.exact.subsets_checked.toLocaleString()} subsets · ${formatMs(data.exact.time_ms)}`} tone="brand" />
            <MetricTile label="Measured ratio" value={`${data.ratio}×`} hint="guarantee: ≤ 2×" tone={data.ratio <= 2 ? "good" : "critical"} />
          </div>
          <Verified ok={data.ratio <= 2 && data.exact.size <= data.approx.size}>
            Lower bound |M| = {data.approx.maximal_matching.length} ≤ OPT = {data.exact.size} ≤ approx = {data.approx.size}.
          </Verified>
          <div className="flex flex-wrap gap-1 text-xs">
            <span className="text-ink-muted">Exact cover:</span>
            {data.exact.cover.map((v) => <Badge key={v} variant="default">{v}</Badge>)}
            <span className="ml-3 text-ink-muted">Approx cover:</span>
            {data.approx.cover.map((v) => <Badge key={v} variant="secondary">{v}</Badge>)}
          </div>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- set cover

interface SCResponse {
  universe_size: number
  coverable_elements: number
  sets: number[][]
  greedy: { chosen: number[]; gains: number[]; fully_covered: boolean }
  exact: { chosen: number[] | null; size: number | null; subsets_evaluated: number }
  ratio: number
  harmonic_bound: number
}

function SetCoverDemo() {
  const [u, setU] = useState(20)
  const [k, setK] = useState(10)
  const [seed, setSeed] = useState(9)
  const demo = useConceptDemo<SCResponse>("/np/set-cover")
  const run = () => demo.mutate({ universe_size: u, num_sets: k, seed }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="setcover"
      title="Set cover: greedy H(n) approximation vs exact subset DP"
      complexity="O(k·|U|) greedy · O(2ᵏ) exact"
      concept={
        <>
          "Which labs must stay open so every placeable student still has somewhere to go?" is set cover. Greedy takes the set with the
          most still-uncovered elements each round and is within H(n) ≈ ln n + 1 of optimal - and that bound is essentially tight for
          polynomial algorithms unless P = NP. The exact DP ORs together unions for all 2ᵏ subsets of sets; the Allocation Insights page
          runs both on the real lab data.
        </>
      }
      controls={
        <>
          <Field label="Elements (1-30)"><Input type="number" min={1} max={30} value={u} onChange={(e) => setU(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Sets (1-14)"><Input type="number" min={1} max={14} value={k} onChange={(e) => setK(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Coverable elements" value={`${data.coverable_elements} / ${data.universe_size}`} />
            <MetricTile label="Greedy picks" value={data.greedy.chosen.length} hint={`gains: ${data.greedy.gains.join(" + ")}`} />
            <MetricTile label="Exact minimum" value={data.exact.size ?? "—"} hint={`${data.exact.subsets_evaluated.toLocaleString()} subsets`} tone="brand" />
            <MetricTile label="Ratio vs H(n) bound" value={`${data.ratio}× vs ${data.harmonic_bound}×`} tone={data.ratio <= data.harmonic_bound ? "good" : "critical"} />
          </div>
          <div className="space-y-1">
            {data.sets.map((members, i) => {
              const g = data.greedy.chosen.indexOf(i)
              const inExact = data.exact.chosen?.includes(i)
              return (
                <div key={i} className="flex items-center gap-2 text-[11px]">
                  <span className="w-10 font-mono text-ink-secondary">S{i}</span>
                  <span className="flex flex-1 flex-wrap gap-px">
                    {Array.from({ length: data.universe_size }, (_, e) => (
                      <span
                        key={e}
                        className={`h-3 w-3 rounded-sm ${members.includes(e) ? (inExact ? "bg-brand-500" : "bg-white/[0.25]") : "bg-white/[0.04]"}`}
                        title={`element ${e}`}
                      />
                    ))}
                  </span>
                  {g >= 0 && <Badge variant="secondary" className="text-[10px]">greedy #{g + 1}</Badge>}
                  {inExact && <Badge variant="default" className="text-[10px]">exact</Badge>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- knapsack

interface KnapsackResponse {
  exact: { value: number; items: number[]; cells: number }
  greedy: { value: number; items: number[]; ratio: number }
  fptas: { value: number; items: number[]; scale: number | null; ratio: number; guarantee: number }
}

function KnapsackDemo() {
  const [weights, setWeights] = useState("10 20 30 15 25 5")
  const [values, setValues] = useState("60 100 120 70 90 20")
  const [capacity, setCapacity] = useState(50)
  const [epsilon, setEpsilon] = useState(0.2)
  const demo = useConceptDemo<KnapsackResponse>("/np/knapsack")
  const run = () => demo.mutate({ weights: parseNumberList(weights), values: parseNumberList(values), capacity, epsilon }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="knapsack"
      title="Knapsack: exact pseudo-polynomial DP, greedy, and an FPTAS"
      complexity="O(n·W) exact · O(n³/ε) FPTAS"
      concept={
        <>
          The O(n·W) table looks polynomial but W is a <em>number</em>, so the table is exponential in its bit length - knapsack stays
          NP-hard. Greedy by value density can be arbitrarily bad. The FPTAS rounds values down to multiples of ε·vmax/n and solves that
          exactly: it loses at most ε·OPT yet runs in time polynomial in n and 1/ε.
        </>
      }
      controls={
        <>
          <Field label="Weights"><Input value={weights} onChange={(e) => setWeights(e.target.value)} className="w-52 font-mono" /></Field>
          <Field label="Values"><Input value={values} onChange={(e) => setValues(e.target.value)} className="w-52 font-mono" /></Field>
          <Field label="Capacity"><Input type="number" min={0} max={2000} value={capacity} onChange={(e) => setCapacity(Number(e.target.value))} className="w-24" /></Field>
          <Field label="ε"><Input type="number" min={0.05} max={0.9} step={0.05} value={epsilon} onChange={(e) => setEpsilon(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <MetricTile label="Exact DP" value={data.exact.value} hint={`items ${data.exact.items.join(", ")} · ${data.exact.cells.toLocaleString()} cells`} tone="brand" />
            <MetricTile label="Greedy by density" value={`${data.greedy.value} (${data.greedy.ratio}× opt)`} hint={`items ${data.greedy.items.join(", ")} · no guarantee`} />
            <MetricTile
              label={`FPTAS ε=${epsilon}`}
              value={`${data.fptas.value} (${data.fptas.ratio}× opt)`}
              hint={`guaranteed ≥ ${data.fptas.guarantee}× · scale K=${data.fptas.scale?.toFixed(2) ?? "—"}`}
              tone={data.fptas.ratio >= data.fptas.guarantee ? "good" : "critical"}
            />
          </div>
          <Verified ok={data.fptas.ratio >= data.fptas.guarantee - 1e-9}>FPTAS result ≥ (1 − ε)·OPT on this instance.</Verified>
        </div>
      )}
    </DemoCard>
  )
}
