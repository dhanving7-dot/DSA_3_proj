import { useState } from "react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DemoCard, Field, MetricTile, Verified } from "@/components/concepts/DemoCard"
import { HighlightSpans, HighlightText } from "@/components/concepts/HighlightText"
import { useConceptDemo } from "@/hooks/useInsights"
import { api, apiErrorMessage } from "@/lib/api"
import { formatMs } from "@/lib/utils"
import type { SearchAlgorithm, SearchResponse } from "@/types/insights"

interface SearchRun {
  algorithm: string
  positions: number[]
  occurrences: number
  comparisons: number
  execution_time_ms: number
  failure_function?: number[]
  preprocessing_comparisons?: number
  z_array?: number[]
  moduli?: number[]
  hash_hits?: number
  spurious_hits?: number
  build_time_ms?: number
}

interface PatternSearchResponse {
  positions: number[]
  all_agree: boolean
  naive_worst_case: number
  runs: SearchRun[]
}

interface AhoResponse {
  matches: { position: number; pattern: string }[]
  trie_nodes: number
  nodes: { node: number; label: string; fail: number; fail_label: string; outputs: string[] }[]
  execution_time_ms: number
  separate_kmp_comparisons: number
  separate_kmp_occurrences: number
}

interface SuffixResponse {
  suffix_array: number[]
  lcp: number[]
  suffixes: string[]
  longest_repeated_substring: string
  distinct_substrings: number
}

const ALGO_NOTES: Record<string, string> = {
  NAIVE: "re-reads text after every mismatch",
  KMP: "never moves backwards in the text",
  Z_FUNCTION: "Z-array over pattern + $ + text",
  RABIN_KARP: "compares characters only on a hash hit",
  SUFFIX_ARRAY: "two binary searches over sorted suffixes",
}

function onError(err: unknown) {
  toast.error(apiErrorMessage(err))
}

export function StringsLab() {
  return (
    <div className="space-y-4">
      <PatternRace />
      <CorpusRace />
      <AhoCorasickDemo />
      <SuffixArrayDemo />
    </div>
  )
}

function PatternRace() {
  const [text, setText] = useState("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab abracadabra abababab aaaaaab")
  const [pattern, setPattern] = useState("aaaaab")
  const demo = useConceptDemo<PatternSearchResponse>("/strings/search")
  const run = () => demo.mutate({ text, pattern, seed: 7 }, { onError })
  const data = demo.data
  const kmp = data?.runs.find((r) => r.algorithm === "KMP")
  const rk = data?.runs.find((r) => r.algorithm === "RABIN_KARP")

  return (
    <DemoCard
      id="pattern"
      title="Exact pattern matching: five algorithms, one answer"
      complexity="naive O(n·m) vs O(n + m)"
      concept={
        <>
          Every algorithm below returns the same occurrences; what differs is the work. Try a pattern like <code>aaaaab</code> against a
          long run of <code>a</code>s: the naive scan re-reads up to m characters at every shift, while KMP's failure function lets it
          resume from the longest border it already matched, so the text pointer never moves backwards.
        </>
      }
      controls={
        <>
          <Field label="Text" className="w-full">
            <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} maxLength={5000} className="font-mono text-xs" />
          </Field>
          <Field label="Pattern">
            <Input value={pattern} onChange={(e) => setPattern(e.target.value)} maxLength={200} className="w-56 font-mono" />
          </Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
      runLabel="Race them"
    >
      {data && (
        <div className="space-y-4">
          <HighlightText text={text} positions={data.positions} length={pattern.length} />
          <Verified ok={data.all_agree}>All five algorithms report the same {data.positions.length} occurrence(s).</Verified>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Algorithm</TableHead>
                <TableHead>Character comparisons</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Why</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.runs.map((r) => (
                <TableRow key={r.algorithm}>
                  <TableCell className="font-medium text-ink">{r.algorithm.replace("_", "-")}</TableCell>
                  <TableCell className="tabular">
                    {r.comparisons.toLocaleString()}
                    <ComparisonBar value={r.comparisons} max={Math.max(...data.runs.map((x) => x.comparisons), 1)} />
                  </TableCell>
                  <TableCell className="tabular">
                    {formatMs(r.execution_time_ms)}
                    {r.build_time_ms != null && <span className="block text-[10px] text-ink-muted">+ {formatMs(r.build_time_ms)} to build the index</span>}
                  </TableCell>
                  <TableCell className="text-xs text-ink-muted">{ALGO_NOTES[r.algorithm]}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="grid gap-3 lg:grid-cols-2">
            {kmp?.failure_function && (
              <div>
                <p className="mb-1 text-xs font-medium text-ink-secondary">KMP failure function π (longest proper border of each prefix)</p>
                <div className="overflow-auto">
                  <table className="text-[11px] tabular">
                    <tbody>
                      <tr>{pattern.split("").map((c, i) => <td key={i} className="border border-border-subtle px-2 py-1 text-center font-mono text-ink">{c}</td>)}</tr>
                      <tr>{kmp.failure_function.map((v, i) => <td key={i} className="border border-border-subtle px-2 py-1 text-center text-brand-400">{v}</td>)}</tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {rk && (
              <div className="grid grid-cols-2 gap-2">
                <MetricTile label="Rabin-Karp moduli" value={<span className="font-mono text-xs">{rk.moduli?.join(" · ")}</span>} hint="31-bit primes drawn by a Las Vegas loop around Miller-Rabin" />
                <MetricTile label="Hash hits / spurious" value={`${rk.hash_hits} / ${rk.spurious_hits}`} hint="double hashing makes false hits vanishingly rare" />
              </div>
            )}
          </div>
        </div>
      )}
    </DemoCard>
  )
}

function ComparisonBar({ value, max }: { value: number; max: number }) {
  return (
    <span className="mt-1 block h-1.5 w-32 rounded-full bg-white/[0.06]">
      <span className="block h-1.5 rounded-full bg-series-blue" style={{ width: `${Math.max(2, (value / max) * 100)}%` }} />
    </span>
  )
}

const SEARCH_ALGOS: SearchAlgorithm[] = ["NAIVE", "KMP", "Z_FUNCTION", "RABIN_KARP", "SUFFIX_ARRAY"]

function CorpusRace() {
  const [query, setQuery] = useState("lab")
  const [results, setResults] = useState<SearchResponse[] | null>(null)
  const [running, setRunning] = useState(false)

  async function run() {
    setRunning(true)
    try {
      const out: SearchResponse[] = []
      for (const algorithm of SEARCH_ALGOS) {
        // sequential so the suffix-array cache state is reported honestly for each call
        const { data } = await api.get<SearchResponse>("/search", { params: { q: query, algorithm, fuzzy: true, limit: 8 } })
        out.push(data)
      }
      setResults(out)
    } catch (err) {
      onError(err)
    } finally {
      setRunning(false)
    }
  }

  const first = results?.[0]
  return (
    <DemoCard
      id="search-race"
      title="The same algorithms on the real database"
      complexity="one pass over a ~11k-character corpus"
      concept={
        <>
          Entity search (<kbd className="rounded border border-border-subtle px-1">Ctrl</kbd> + <kbd className="rounded border border-border-subtle px-1">K</kbd>) concatenates every
          student and lab field into one corpus, runs a single search, then maps each hit back to its record by binary search over field
          offsets. The suffix array is built once and cached; if nothing matches exactly, Damerau-Levenshtein distance finds near misses
          such as <code>jonh</code> → John.
        </>
      }
      controls={
        <Field label="Query">
          <Input value={query} onChange={(e) => setQuery(e.target.value)} maxLength={100} className="w-56" />
        </Field>
      }
      onRun={run}
      running={running}
      runLabel="Search with all five"
    >
      {results && first && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Corpus" value={`${first.corpus_length.toLocaleString()} chars`} hint={`${first.fields_indexed} fields`} />
            <MetricTile label="Exact occurrences" value={first.occurrences} />
            <MetricTile label="Records matched" value={first.exact_matches} />
            <MetricTile label="Fuzzy matches" value={first.fuzzy_matches} />
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Algorithm</TableHead>
                <TableHead>Comparisons</TableHead>
                <TableHead>Search time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {results.map((r) => (
                <TableRow key={r.algorithm}>
                  <TableCell className="text-ink">
                    {r.algorithm.replace("_", "-")}
                    {r.suffix_array_cached != null && (
                      <Badge variant="secondary" className="ml-2 text-[10px]">{r.suffix_array_cached ? "index cached" : "index built"}</Badge>
                    )}
                  </TableCell>
                  <TableCell className="tabular">{r.comparisons.toLocaleString()}</TableCell>
                  <TableCell className="tabular">{formatMs(r.search_time_ms)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <ul className="space-y-1 text-xs">
            {first.results.map((hit) => {
              const field = Object.entries(hit.fields)[0]
              return (
                <li key={`${hit.type}-${hit.id}`} className="flex items-center justify-between rounded-md border border-border-subtle px-3 py-1.5">
                  <span className="text-ink">
                    {field ? <HighlightSpans value={field[1].value} spans={field[1].spans} /> : hit.title}
                    <span className="ml-2 text-ink-muted">{hit.subtitle}</span>
                  </span>
                  <Badge variant={hit.match === "exact" ? "default" : "warning"}>{hit.match === "exact" ? hit.type : `fuzzy · d=${hit.distance}`}</Badge>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </DemoCard>
  )
}

function AhoCorasickDemo() {
  const [text, setText] = useState("Allocate ushers and his helpers to the hers lab")
  const [patterns, setPatterns] = useState("he, she, his, hers")
  const demo = useConceptDemo<AhoResponse>("/strings/aho-corasick")
  const list = patterns.split(",").map((p) => p.trim()).filter(Boolean)
  const run = () => demo.mutate({ text, patterns: list }, { onError })
  const data = demo.data

  return (
    <DemoCard
      id="aho"
      title="Aho-Corasick: every keyword in one pass"
      complexity="O(n + Σ|P| + matches)"
      concept={
        <>
          The AI Command Center parser builds one automaton from every department alias and algorithm keyword, then reads the command once.
          A failure link sends a mismatching state to the longest suffix that is still a trie path, like KMP's failure function generalised
          to many patterns; dictionary links report patterns nested inside others (<code>he</code> inside <code>she</code>).
        </>
      }
      controls={
        <>
          <Field label="Text" className="min-w-72 flex-1">
            <Input value={text} onChange={(e) => setText(e.target.value)} maxLength={5000} />
          </Field>
          <Field label="Patterns (comma separated)" className="w-64">
            <Input value={patterns} onChange={(e) => setPatterns(e.target.value)} />
          </Field>
        </>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1.5">
            {data.matches.length === 0 && <span className="text-xs text-ink-muted">No matches.</span>}
            {data.matches.map((m, i) => (
              <Badge key={i} variant="secondary" className="font-mono">
                {m.pattern} @ {m.position}
              </Badge>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <MetricTile label="Trie nodes" value={data.trie_nodes} />
            <MetricTile label="Occurrences" value={data.matches.length} hint={`separate KMP runs agree: ${data.separate_kmp_occurrences}`} />
            <MetricTile label="Separate KMP comparisons" value={data.separate_kmp_comparisons} hint={`${list.length} passes over the text instead of 1`} />
          </div>
          <div className="max-h-64 overflow-auto rounded-lg border border-border-subtle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Node</TableHead>
                  <TableHead>Spells</TableHead>
                  <TableHead>Failure link →</TableHead>
                  <TableHead>Outputs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.nodes.map((n) => (
                  <TableRow key={n.node}>
                    <TableCell className="tabular">{n.node}</TableCell>
                    <TableCell className="font-mono text-ink">{n.label || "ε (root)"}</TableCell>
                    <TableCell className="font-mono">{n.fail_label || "ε"}</TableCell>
                    <TableCell className="font-mono text-brand-400">{n.outputs.join(", ")}</TableCell>
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

function SuffixArrayDemo() {
  const [text, setText] = useState("mississippi")
  const demo = useConceptDemo<SuffixResponse>("/strings/suffix-array")
  const run = () => demo.mutate({ text }, { onError })
  const data = demo.data
  return (
    <DemoCard
      id="suffix"
      title="Suffix array + LCP (Kasai)"
      complexity="O(n log² n) build · O(n) LCP"
      concept={
        <>
          Sorting all suffixes puts every occurrence of any substring into one contiguous block, so a substring query is two binary searches.
          The LCP array (common prefix of neighbouring suffixes) is built in linear time: going from suffix i to i+1 loses at most one
          matched character. Its maximum is the longest repeated substring, and n(n+1)/2 − ΣLCP counts the distinct substrings.
        </>
      }
      controls={
        <Field label="Text (max 60 chars)">
          <Input value={text} onChange={(e) => setText(e.target.value)} maxLength={60} className="w-72 font-mono" />
        </Field>
      }
      onRun={run}
      running={demo.isPending}
    >
      {data && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <MetricTile label="Longest repeated substring" value={<span className="font-mono">{data.longest_repeated_substring || "—"}</span>} />
            <MetricTile label="Distinct substrings" value={data.distinct_substrings} />
          </div>
          <div className="max-h-72 overflow-auto rounded-lg border border-border-subtle">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rank</TableHead>
                  <TableHead>SA[i]</TableHead>
                  <TableHead>LCP</TableHead>
                  <TableHead>Suffix</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.suffix_array.map((pos, i) => (
                  <TableRow key={i}>
                    <TableCell className="tabular">{i}</TableCell>
                    <TableCell className="tabular">{pos}</TableCell>
                    <TableCell className="tabular text-brand-400">{data.lcp[i]}</TableCell>
                    <TableCell className="font-mono text-ink">
                      <span className="text-brand-400">{data.suffixes[i].slice(0, data.lcp[i])}</span>
                      {data.suffixes[i].slice(data.lcp[i])}
                    </TableCell>
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
