import { useState } from "react"
import { toast } from "sonner"
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DemoCard, Field, MetricTile, Verified } from "@/components/concepts/DemoCard"
import { useConceptDemo } from "@/hooks/useInsights"
import { parseNumberList } from "@/lib/utils"
import { apiErrorMessage } from "@/lib/api"
import { CHART_CHROME, SERIES } from "@/lib/chartTheme"

function onError(err: unknown) {
  toast.error(apiErrorMessage(err))
}

export function RandomLab() {
  return (
    <div className="space-y-4">
      <PrimalityDemo />
      <QuicksortDemo />
      <ReservoirDemo />
      <HashingDemo />
      <ScanDemo />
    </div>
  )
}

// --------------------------------------------------------------------------- primality

interface PrimalityResponse {
  n: string
  miller_rabin: { probably_prime: boolean; rounds: { a: string | null; chain: string[]; verdict: string }[] }
  error_bound: string
  fermat: { probably_prime: boolean; witnesses: { a: number; a_pow_n_minus_1: string; coprime: boolean; passes: boolean }[] }
  deterministic: boolean
  deterministic_is_exact: boolean
  trial_division: boolean | null
  carmichael: boolean | null
  known_carmichael_numbers: number[]
}

function verdict(v: boolean | null) {
  if (v == null) return "too large"
  return v ? "prime" : "composite"
}

function PrimalityDemo() {
  const [n, setN] = useState("561")
  const [rounds, setRounds] = useState(6)
  const demo = useConceptDemo<PrimalityResponse>("/random/primality")
  const run = () => demo.mutate({ n, rounds, seed: 1 }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="primality"
      title="Miller-Rabin vs Fermat: Monte Carlo primality"
      complexity="O(k log³ n)"
      concept={
        <>
          Fermat checks aⁿ⁻¹ ≡ 1 (mod n). Carmichael numbers such as 561 = 3·11·17 pass that for <em>every</em> coprime base, so Fermat is
          fooled. Miller-Rabin also watches the square roots of 1 along the chain a^d, a^2d, …, a^(n−1): a prime only has ±1, so any other
          root is a witness. A composite survives one random witness with probability ≤ 1/4, so k rounds err with probability ≤ 4⁻ᵏ - and a
          "composite" answer is always certain. Rabin-Karp's moduli are generated this way.
        </>
      }
      controls={
        <>
          <Field label="n (up to 40 digits)"><Input value={n} onChange={(e) => setN(e.target.value.replace(/\D/g, ""))} maxLength={40} className="w-72 font-mono" /></Field>
          <Field label="Rounds k"><Input type="number" min={1} max={20} value={rounds} onChange={(e) => setRounds(Number(e.target.value))} className="w-20" /></Field>
          <div className="flex flex-wrap gap-1">
            {["561", "1105", "7919", "2305843009213693951", "2305843009213693953"].map((v) => (
              <button key={v} onClick={() => setN(v)} className="rounded-md border border-border-subtle px-2 py-1 font-mono text-[11px] text-ink-secondary hover:bg-white/[0.05]">
                {v.length > 10 ? `${v.slice(0, 6)}…` : v}
              </button>
            ))}
          </div>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Fermat test" value={data.fermat.probably_prime ? "probably prime" : "composite"} />
            <MetricTile label="Miller-Rabin" value={data.miller_rabin.probably_prime ? "probably prime" : "composite"} hint={`error ≤ ${data.error_bound}`} tone="brand" />
            <MetricTile label="Fixed witnesses 2…41" value={verdict(data.deterministic)} hint={data.deterministic_is_exact ? "proven exact below 3.3·10²⁴" : "beyond the proven range"} />
            <MetricTile label="Trial division (truth)" value={verdict(data.trial_division)} hint={data.carmichael ? "Carmichael number (Korselt)" : undefined} tone={data.carmichael ? "critical" : undefined} />
          </div>
          {data.carmichael && !data.miller_rabin.probably_prime && data.fermat.probably_prime && (
            <Verified ok>Fermat was fooled by a Carmichael number; Miller-Rabin found a witness.</Verified>
          )}
          <div className="max-h-56 overflow-auto rounded-lg border border-border-subtle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Witness a</TableHead>
                  <TableHead>Chain a^d, a^2d, … (mod n)</TableHead>
                  <TableHead>Verdict</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.miller_rabin.rounds.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-mono text-xs">{r.a ?? "—"}</TableCell>
                    <TableCell className="max-w-md truncate font-mono text-[11px]" title={r.chain.join(" → ")}>{r.chain.join(" → ")}</TableCell>
                    <TableCell><Badge variant={r.verdict.startsWith("witness") || r.verdict.startsWith("divisible") ? "critical" : "secondary"}>{r.verdict}</Badge></TableCell>
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

// --------------------------------------------------------------------------- quicksort

interface QuicksortResponse {
  n: number
  input_kind: string
  deterministic: { comparisons: number; max_depth: number }
  randomized: { runs: { comparisons: number; max_depth: number }[]; mean_comparisons: number }
  n_log2_n: number
  expected_randomized: number
  worst_case: number
  sorted_correctly: boolean
}

function QuicksortDemo() {
  const [n, setN] = useState(1000)
  const [kind, setKind] = useState("sorted")
  const demo = useConceptDemo<QuicksortResponse>("/random/quicksort")
  const run = () => demo.mutate({ n, input_kind: kind, seed: 2, trials: 5 }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="quicksort"
      title="Randomised quicksort: Las Vegas"
      complexity="O(n log n) expected on every input"
      concept={
        <>
          Always pivoting on the first element makes already-sorted input the worst case: every partition peels off one element, n(n−1)/2
          comparisons, recursion depth n. Choosing the pivot at random moves the randomness from the <em>input</em> to the
          <em> algorithm</em>: the answer is always correct (Las Vegas), and the expected comparisons are ≈ 2n ln n for every input,
          including the adversarial ones.
        </>
      }
      controls={
        <>
          <Field label="n (≤ 2000)"><Input type="number" min={1} max={2000} value={n} onChange={(e) => setN(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Input">
            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="sorted">Already sorted</SelectItem>
                <SelectItem value="reversed">Reversed</SelectItem>
                <SelectItem value="random">Random</SelectItem>
                <SelectItem value="few_unique">Few unique values</SelectItem>
              </SelectContent>
            </Select>
          </Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="First-element pivot" value={data.deterministic.comparisons.toLocaleString()} hint={`depth ${data.deterministic.max_depth}`} tone={data.deterministic.comparisons >= data.worst_case ? "critical" : undefined} />
            <MetricTile label="Random pivot (mean of 5)" value={data.randomized.mean_comparisons.toLocaleString()} hint={`depths ${data.randomized.runs.map((r) => r.max_depth).join(", ")}`} tone="good" />
            <MetricTile label="≈ 2n ln n" value={data.expected_randomized.toLocaleString()} hint="expected for random pivots" />
            <MetricTile label="n(n−1)/2 worst case" value={data.worst_case.toLocaleString()} />
          </div>
          <Verified ok={data.sorted_correctly}>Every run produced a correctly sorted array - only the running time was random.</Verified>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- reservoir

interface ReservoirResponse {
  stream_size: number
  k: number
  trials: number
  expected_per_item: number
  counts: number[]
  min_count: number
  max_count: number
  chi_square: number
  degrees_of_freedom: number
  example_sample: number[]
}

function ReservoirDemo() {
  const [stream, setStream] = useState(60)
  const [k, setK] = useState(6)
  const [trials, setTrials] = useState(3000)
  const demo = useConceptDemo<ReservoirResponse>("/random/reservoir")
  const run = () => demo.mutate({ stream_size: stream, k, trials, seed: 8 }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="reservoir"
      title="Reservoir sampling (Algorithm R)"
      complexity="O(n) time · O(k) memory"
      concept={
        <>
          Keep the first k items; the i-th item replaces a random slot with probability k/i. By induction every item seen so far sits in
          the reservoir with probability exactly k/i, without knowing the stream length in advance. The Allocation Results page uses it to
          draw an unbiased audit sample while streaming rows from the database. Below: how often each item was picked over many trials -
          a flat histogram is the uniformity proof.
        </>
      }
      controls={
        <>
          <Field label="Stream length"><Input type="number" min={1} max={1000} value={stream} onChange={(e) => setStream(Number(e.target.value))} className="w-24" /></Field>
          <Field label="k"><Input type="number" min={1} max={50} value={k} onChange={(e) => setK(Number(e.target.value))} className="w-20" /></Field>
          <Field label="Trials"><Input type="number" min={1} max={5000} value={trials} onChange={(e) => setTrials(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Expected picks / item" value={data.expected_per_item} hint={`= trials × k / n`} />
            <MetricTile label="Observed range" value={`${data.min_count} – ${data.max_count}`} />
            <MetricTile label="χ² statistic" value={data.chi_square} hint={`${data.degrees_of_freedom} degrees of freedom - near df means uniform`} />
            <MetricTile label="One sample" value={<span className="font-mono text-xs">{data.example_sample.join(", ")}</span>} />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.counts.map((c, i) => ({ item: i, picks: c }))} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barCategoryGap={1}>
              <CartesianGrid stroke={CHART_CHROME.gridline} vertical={false} />
              <XAxis dataKey="item" tick={{ fill: CHART_CHROME.textMuted, fontSize: 10 }} axisLine={{ stroke: CHART_CHROME.baseline }} tickLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fill: CHART_CHROME.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: "rgba(255,255,255,0.04)" }}
                content={({ active, payload }) =>
                  active && payload?.length ? (
                    <div className="rounded-lg glass-panel-strong px-3 py-2 text-xs text-ink-secondary">
                      item {payload[0].payload.item}: <span className="tabular text-ink">{payload[0].payload.picks}</span> picks
                    </div>
                  ) : null
                }
              />
              <ReferenceLine y={data.expected_per_item} stroke={CHART_CHROME.textSecondary} strokeDasharray="4 4" label={{ value: "expected", fill: CHART_CHROME.textSecondary, fontSize: 10, position: "insideTopRight" }} />
              <Bar dataKey="picks" fill={SERIES.blue} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- universal hashing

interface HashingResponse {
  keys: number
  table_size: number
  key_pattern: string
  universal_params: { p: number; a: number; b: number }
  fixed_mod: { max_bucket: number; colliding_pairs: number; non_empty_buckets: number }
  universal: { max_bucket: number; colliding_pairs: number; non_empty_buckets: number }
  expected_colliding_pairs_bound: number
}

function HashingDemo() {
  const [keys, setKeys] = useState(500)
  const [m, setM] = useState(97)
  const [seed, setSeed] = useState(6)
  const demo = useConceptDemo<HashingResponse>("/random/hashing")
  const run = () => demo.mutate({ num_keys: keys, table_size: m, seed }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="hashing"
      title="Universal hashing vs a fixed hash function"
      complexity="O(1) per key"
      concept={
        <>
          Any fixed hash function has an adversarial input: for h(x) = x mod m, feed it multiples of m and every key lands in bucket 0. A
          universal family picks h(x) = ((a·x + b) mod p) mod m at random <em>after</em> the keys are fixed, so for any two distinct keys the
          collision probability is ≤ 1/m - expected colliding pairs ≤ C(n,2)/m whatever the input. Hashing is fundamentally probabilistic.
        </>
      }
      controls={
        <>
          <Field label="Keys"><Input type="number" min={1} max={2000} value={keys} onChange={(e) => setKeys(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Table size m"><Input type="number" min={2} max={1000} value={m} onChange={(e) => setM(Number(e.target.value))} className="w-24" /></Field>
          <Field label="Seed"><Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} className="w-24" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <p className="text-xs text-ink-muted">Keys: {data.key_pattern} (adversarial for x mod m).</p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <MetricTile label="x mod m" value={`${data.fixed_mod.colliding_pairs.toLocaleString()} colliding pairs`} hint={`${data.fixed_mod.non_empty_buckets} bucket(s) used · max load ${data.fixed_mod.max_bucket}`} tone="critical" />
            <MetricTile label="Universal family" value={`${data.universal.colliding_pairs.toLocaleString()} colliding pairs`} hint={`${data.universal.non_empty_buckets} buckets used · max load ${data.universal.max_bucket}`} tone="good" />
            <MetricTile label="Expected bound C(n,2)/m" value={data.expected_colliding_pairs_bound.toLocaleString()} hint={`p=${data.universal_params.p}, a=${data.universal_params.a}, b=${data.universal_params.b}`} />
          </div>
        </div>
      )}
    </DemoCard>
  )
}

// --------------------------------------------------------------------------- parallel scan

interface TraceDict {
  result: number[] | number
  work: number
  span: number
  rounds: { phase: string; stride?: number; operations: number; values: number[] }[]
  processors: number
  brent_bound: number
  parallelism: number | null
}

interface ScanResponse {
  values: number[]
  scan: TraceDict
  reduce: TraceDict
  sequential_scan: number[]
  scan_correct: boolean
}

function ScanDemo() {
  const [values, setValues] = useState("30 35 30 30 25 25 25 30 25 30 20")
  const [p, setP] = useState(4)
  const demo = useConceptDemo<ScanResponse>("/parallel/scan")
  const run = () => demo.mutate({ values: parseNumberList(values), processors: p }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="scan"
      title="Work and span: Blelloch prefix sum and parallel reduce"
      complexity="work O(n) · span O(log n)"
      concept={
        <>
          Work T₁ counts every operation; span T∞ counts the longest chain of dependent ones (rounds). Brent's theorem bounds p processors
          by T₁/p + T∞, so the speed-up ceiling is the parallelism T₁/T∞. Blelloch's scan does an up-sweep (a reduction tree) then a
          down-sweep that pushes prefixes back down - O(n) work, unlike the naive O(n log n) parallel scan. The allocation engine uses this
          exact scan: the default input is the lab capacities, and the result is each lab's first slot in the capacity-expanded graph.
        </>
      }
      controls={
        <>
          <Field label="Values (≤ 64)"><Input value={values} onChange={(e) => setValues(e.target.value)} className="w-80 font-mono" /></Field>
          <Field label="Processors p"><Input type="number" min={1} max={64} value={p} onChange={(e) => setP(Number(e.target.value))} className="w-20" /></Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Scan work T₁" value={data.scan.work} />
            <MetricTile label="Scan span T∞" value={data.scan.span} hint="rounds" />
            <MetricTile label={`Brent bound, p=${data.scan.processors}`} value={data.scan.brent_bound} hint="T₁/p + T∞" />
            <MetricTile label="Reduce (sum)" value={String(data.reduce.result)} hint={`work ${data.reduce.work} · span ${data.reduce.span}`} />
          </div>
          <Verified ok={data.scan_correct}>Exclusive scan equals the sequential prefix sum.</Verified>
          <div className="overflow-auto rounded-lg border border-border-subtle">
            <table className="text-[11px] tabular">
              <tbody>
                <tr>
                  <th className="px-2 py-1 text-left font-medium text-ink-secondary">input</th>
                  {data.values.map((v, i) => <td key={i} className="border border-border-subtle/60 px-2 py-1 text-center text-ink">{v}</td>)}
                </tr>
                {data.scan.rounds.map((r, i) => (
                  <tr key={i}>
                    <th className="whitespace-nowrap px-2 py-1 text-left font-normal text-ink-muted">{r.phase} d={r.stride} ({r.operations} ops)</th>
                    {r.values.map((v, j) => <td key={j} className="border border-border-subtle/60 px-2 py-1 text-center text-ink-secondary">{v}</td>)}
                  </tr>
                ))}
                <tr>
                  <th className="px-2 py-1 text-left font-medium text-brand-400">exclusive scan</th>
                  {(data.scan.result as number[]).map((v, i) => <td key={i} className="border border-border-subtle/60 bg-brand-500/20 px-2 py-1 text-center font-semibold text-ink">{v}</td>)}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </DemoCard>
  )
}
