import { useMemo, useState } from "react"
import { toast } from "sonner"
import { Play, GitBranch, Clock, Layers, CheckCircle2, XCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BipartiteFlowGraph } from "@/components/graph/BipartiteFlowGraph"
import { AlgorithmStepper } from "@/components/graph/AlgorithmStepper"
import { useAlgorithmInfo, useRunPlayground } from "@/hooks/useAllocation"
import { useAlgorithmSocket } from "@/hooks/useAlgorithmSocket"
import { apiErrorMessage } from "@/lib/api"
import { formatMs } from "@/lib/utils"
import { ALLOCATION_ALGORITHMS } from "@/lib/algorithms"
import type { AlgorithmName } from "@/types"

export default function AlgorithmPlaygroundPage() {
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("KUHN")
  const [numLeft, setNumLeft] = useState(10)
  const [numRight, setNumRight] = useState(6)
  const [edgeProbability, setEdgeProbability] = useState(0.4)
  const [seed, setSeed] = useState(42)
  const [channel, setChannel] = useState<string | null>(null)

  const { data: algoInfo } = useAlgorithmInfo()
  const runPlayground = useRunPlayground()
  const socket = useAlgorithmSocket(channel)

  async function onRun() {
    const newChannel = `playground:${crypto.randomUUID()}`
    setChannel(newChannel)
    socket.reset()
    await new Promise((r) => setTimeout(r, 150)) // let the socket connect before the run starts
    try {
      await runPlayground.mutateAsync({ algorithm, num_left: numLeft, num_right: numRight, edge_probability: edgeProbability, seed, channel: newChannel })
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  const result = runPlayground.data?.result
  const info = algoInfo?.[algorithm]

  const { leftItems, rightItems, edges } = useMemo(() => {
    const left = Array.from({ length: numLeft }).map((_, i) => ({ id: i, label: `Student ${i}` }))
    const right = Array.from({ length: numRight }).map((_, i) => ({ id: i, label: `Lab ${i}` }))
    const matchedSet = new Set((result?.matched_pairs ?? []).map(([l, r]) => `${l}-${r}`))
    const graphEdges = (runPlayground.data?.input_edges ?? []).map(([l, r]) => ({
      source: l,
      target: r,
      matched: socket.complete && matchedSet.has(`${l}-${r}`),
    }))
    return { leftItems: left, rightItems: right, edges: graphEdges }
  }, [numLeft, numRight, runPlayground.data, result, socket.complete])

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Configure & Run</CardTitle>
          <CardDescription>Generates a random bipartite graph and executes the chosen algorithm on the real backend implementation.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <Label>Algorithm</Label>
            <Select value={algorithm} onValueChange={(v) => setAlgorithm(v as AlgorithmName)}>
              <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ALLOCATION_ALGORITHMS.map((a) => <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Students (|L|)</Label>
            <Input type="number" min={1} max={40} value={numLeft} onChange={(e) => setNumLeft(Number(e.target.value))} className="w-24" />
          </div>
          <div className="space-y-1">
            <Label>Labs (|R|)</Label>
            <Input type="number" min={1} max={20} value={numRight} onChange={(e) => setNumRight(Number(e.target.value))} className="w-24" />
          </div>
          <div className="space-y-1">
            <Label>Edge probability</Label>
            <Input type="number" step="0.05" min={0.05} max={1} value={edgeProbability} onChange={(e) => setEdgeProbability(Number(e.target.value))} className="w-24" />
          </div>
          <div className="space-y-1">
            <Label>Seed</Label>
            <Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" />
          </div>
          <Button onClick={onRun} disabled={runPlayground.isPending}>
            <Play className="h-4 w-4" /> {runPlayground.isPending ? "Running..." : "Generate & Run"}
          </Button>
        </CardContent>
      </Card>

      {info && (
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <Badge>{info.category}</Badge>
            <span className="font-mono text-brand-400">{info.time_complexity}</span>
            <span className="text-ink-muted">Space: {info.space_complexity}</span>
          </div>
          <p className="mt-2 text-xs text-ink-secondary">{info.description}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_360px]">
        <Card className="p-2">
          <BipartiteFlowGraph leftItems={leftItems} rightItems={rightItems} edges={edges} height={480} />
        </Card>

        <div className="space-y-4">
          {result && (
            <Card>
              <CardHeader><CardTitle>Run Metrics</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-xs">
                <MetricRow icon={GitBranch} label="Vertices / Edges" value={`${result.vertices} / ${result.edges}`} />
                <MetricRow icon={Clock} label="Execution Time" value={formatMs(result.execution_time_ms)} />
                <MetricRow icon={Layers} label="Iterations" value={String(result.iterations)} />
                <MetricRow icon={CheckCircle2} label="Matched" value={String(result.match_size)} accent="good" />
                <MetricRow icon={XCircle} label="Unmatched Students" value={String(result.unmatched_left.length)} accent="critical" />
                {runPlayground.data?.total_cost != null && (
                  <MetricRow icon={Layers} label="Min total cost (edge costs 1-9)" value={String(runPlayground.data.total_cost)} />
                )}
                <p className="pt-1 font-mono text-brand-400">{result.time_complexity}</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Algorithm Steps</CardTitle>
              <CardDescription>{socket.connected ? "Live from backend" : "Run the algorithm to stream steps"}</CardDescription>
            </CardHeader>
            <CardContent>
              {socket.steps.length === 0 ? (
                <p className="py-6 text-center text-xs text-ink-muted">No steps yet.</p>
              ) : (
                <AlgorithmStepper steps={socket.steps} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function MetricRow({ icon: Icon, label, value, accent }: { icon: typeof Clock; label: string; value: string; accent?: "good" | "critical" }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2">
      <span className="flex items-center gap-1.5 text-ink-muted">
        <Icon className="h-3.5 w-3.5" /> {label}
      </span>
      <span className={`tabular font-medium ${accent === "good" ? "text-good" : accent === "critical" ? "text-critical" : "text-ink"}`}>{value}</span>
    </div>
  )
}
