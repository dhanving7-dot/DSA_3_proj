import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Play, ArrowRight, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { AlgorithmStepper } from "@/components/graph/AlgorithmStepper"
import { useGenerateAllocation } from "@/hooks/useAllocation"
import { useAlgorithmSocket } from "@/hooks/useAlgorithmSocket"
import { apiErrorMessage } from "@/lib/api"
import { DEFAULT_ALLOCATION_CONFIG, type AlgorithmName, type AllocationConfig } from "@/types"
import { ALLOCATION_ALGORITHMS, FAIRNESS_EXPLANATION, supportsFairnessCap } from "@/lib/algorithms"

const FAMILY_LABEL = { matching: "Bipartite matching", flow: "Maximum flow", "cost-flow": "Min-cost flow" } as const

export default function AllocationConfigPage() {
  const [algorithm, setAlgorithm] = useState<AlgorithmName>("HOPCROFT_KARP")
  const [config, setConfig] = useState<AllocationConfig>(DEFAULT_ALLOCATION_CONFIG)
  const [channel, setChannel] = useState<string | null>(null)

  const generate = useGenerateAllocation()
  const socket = useAlgorithmSocket(channel)
  const navigate = useNavigate()
  const fairnessOn = config.max_share_per_department != null

  async function onRun() {
    const runChannel = `run:pending`
    setChannel(runChannel)
    socket.reset()
    await new Promise((r) => setTimeout(r, 200)) // let the WebSocket connect before the backend starts broadcasting
    try {
      const result = await generate.mutateAsync({ algorithm, config, stream_progress: true })
      toast.success(`Run #${result.id} complete: ${result.matched_count} matched, ${result.unmatched_count} unmatched`)
    } catch (err) {
      toast.error(apiErrorMessage(err))
    }
  }

  function updateWeight(key: keyof AllocationConfig, value: number) {
    setConfig((c) => ({ ...c, [key]: value }))
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_380px]">
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Algorithm Selection</CardTitle>
            <CardDescription>Choose which graph algorithm formulation resolves this allocation run.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
              {ALLOCATION_ALGORITHMS.map((a) => {
                const blocked = fairnessOn && !supportsFairnessCap(a.value)
                return (
                  <button
                    key={a.value}
                    onClick={() => !blocked && setAlgorithm(a.value)}
                    disabled={blocked}
                    title={blocked ? FAIRNESS_EXPLANATION : undefined}
                    className={`rounded-xl border px-4 py-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                      algorithm === a.value ? "border-brand-500/50 bg-brand-500/[0.08]" : "border-border-subtle bg-white/[0.02] hover:bg-white/[0.04]"
                    }`}
                  >
                    <p className="text-[10px] uppercase tracking-wide text-ink-muted">{FAMILY_LABEL[a.family]}</p>
                    <p className="text-sm font-medium text-ink">{a.label}</p>
                    <p className="mt-0.5 font-mono text-[11px] text-ink-muted">{a.hint}</p>
                  </button>
                )
              })}
            </div>
            {algorithm === "MIN_COST_FLOW" && (
              <p className="flex gap-2 text-xs text-ink-secondary">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-400" />
                Places the same maximum number of students as every other algorithm, but among all maximum matchings returns one with the
                largest total match score - the weights below decide what "best" means.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Eligibility & Priority Rules</CardTitle>
            <CardDescription>These constraints shape which (student, lab) edges even exist in the graph.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink">Same department only</p>
                <p className="text-xs text-ink-muted">Only allow eligibility within a student's own department</p>
              </div>
              <Switch checked={config.same_department_only} onCheckedChange={(v) => setConfig((c) => ({ ...c, same_department_only: v }))} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink">Require stated preference</p>
                <p className="text-xs text-ink-muted">Only labs a student explicitly ranked are eligible</p>
              </div>
              <Switch checked={config.require_preference} onCheckedChange={(v) => setConfig((c) => ({ ...c, require_preference: v }))} />
            </div>

            <Separator />

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label>Preference weight</Label>
                <Input type="number" step="0.05" min={0} max={1} value={config.preference_weight} onChange={(e) => updateWeight("preference_weight", Number(e.target.value))} />
              </div>
              <div className="space-y-1">
                <Label>Skill weight</Label>
                <Input type="number" step="0.05" min={0} max={1} value={config.skill_weight} onChange={(e) => updateWeight("skill_weight", Number(e.target.value))} />
              </div>
              <div className="space-y-1">
                <Label>Priority weight</Label>
                <Input type="number" step="0.05" min={0} max={1} value={config.priority_weight} onChange={(e) => updateWeight("priority_weight", Number(e.target.value))} />
              </div>
            </div>
            <p className="text-[11px] text-ink-muted">Weights combine into each edge's match score — they need not sum to exactly 1.</p>

            <div className="space-y-1">
              <Label>Fairness cap: max share of a lab's capacity per department (optional)</Label>
              <Select
                value={config.max_share_per_department == null ? "none" : String(config.max_share_per_department)}
                onValueChange={(v) => {
                  const share = v === "none" ? null : Number(v)
                  setConfig((c) => ({ ...c, max_share_per_department: share }))
                  // quotas need the flow formulation; move off plain matching instead of failing at run time
                  if (share != null && !supportsFairnessCap(algorithm)) setAlgorithm("DINIC")
                }}
              >
                <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No fairness cap</SelectItem>
                  <SelectItem value="0.4">40% max per department</SelectItem>
                  <SelectItem value="0.6">60% max per department</SelectItem>
                  <SelectItem value="0.8">80% max per department</SelectItem>
                </SelectContent>
              </Select>
              {fairnessOn && <p className="pt-1 text-[11px] text-ink-muted">{FAIRNESS_EXPLANATION}</p>}
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button size="lg" onClick={onRun} disabled={generate.isPending}>
            <Play className="h-4 w-4" /> {generate.isPending ? "Running..." : "Run Allocation"}
          </Button>
          {generate.data && (
            <Button size="lg" variant="secondary" onClick={() => navigate("/app/results")}>
              View Results <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <Card className="h-fit">
        <CardHeader>
          <CardTitle>Live Algorithm Progress</CardTitle>
          <CardDescription>{socket.connected ? "Connected to backend event stream" : "Streams once you run an allocation"}</CardDescription>
        </CardHeader>
        <CardContent>
          {socket.steps.length === 0 ? (
            <p className="py-8 text-center text-xs text-ink-muted">No run in progress. Click "Run Allocation" to watch it live.</p>
          ) : (
            <AlgorithmStepper steps={socket.steps} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
