import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  ArrowRight,
  GitBranch,
  Waypoints,
  Brain,
  ShieldCheck,
  LineChart,
  Sparkles,
  Network,
  Users,
  FlaskConical,
  Gauge,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { HeroGraphAnimation } from "@/components/graph/HeroGraphAnimation"

const FEATURES = [
  {
    icon: GitBranch,
    title: "Kuhn's Algorithm",
    description: "Classic O(V·E) augmenting-path search over the bipartite graph of eligible student-lab edges.",
  },
  {
    icon: Waypoints,
    title: "Hopcroft-Karp",
    description: "BFS-layered, vertex-disjoint augmenting paths bring matching down to O(E·√V).",
  },
  {
    icon: Network,
    title: "Edmonds-Karp Max-Flow",
    description: "Models capacity-aware allocation as a source→student→lab→sink flow network.",
  },
  {
    icon: Gauge,
    title: "Dinic's Algorithm",
    description: "Blocking-flow phases over a BFS level graph — O(E·√V) on unit-capacity bipartite graphs.",
  },
  {
    icon: Brain,
    title: "AI Command Center",
    description: "Natural language is parsed into structured constraints; the deterministic engine still decides.",
  },
  {
    icon: ShieldCheck,
    title: "Explainable Allocation",
    description: "Every match stores its eligibility reason, preference rank and score — nothing is a black box.",
  },
]

const ALGO_CARDS = [
  { name: "Kuhn", complexity: "O(V · E)", tag: "Bipartite Matching" },
  { name: "Hopcroft-Karp", complexity: "O(E · √V)", tag: "Bipartite Matching" },
  { name: "Ford-Fulkerson", complexity: "O(E · |f*|)", tag: "Maximum Flow" },
  { name: "Edmonds-Karp", complexity: "O(V · E²)", tag: "Maximum Flow" },
  { name: "Dinic", complexity: "O(V² · E)", tag: "Maximum Flow" },
  { name: "Min-Cost Flow", complexity: "O(F · E log V)", tag: "Assignment Problem" },
]

const MODULES = [
  { n: 2, title: "String Algorithms", items: "KMP · Z · Rabin-Karp · Aho-Corasick · suffix array + LCP", use: "entity search, AI command parsing" },
  { n: 3, title: "Advanced DP", items: "edit distance · alignment · interval · bitmask · tree · SOS", use: "typo tolerance, skill-supply analysis" },
  { n: 4, title: "Network Flow", items: "6 matching/flow algorithms · min cut · König · min-cost flow", use: "the allocation engine itself" },
  { n: 5, title: "NP & Approximation", items: "set cover · vertex cover · knapsack FPTAS · metric TSP", use: "which labs must stay open" },
  { n: 6, title: "Randomised & Parallel", items: "Miller-Rabin · universal hashing · reservoir · Blelloch scan", use: "audits, outage risk, slot offsets" },
]

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-canvas bg-grid">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[560px] bg-radial-fade" />

      <header className="relative z-10 flex items-center justify-between px-6 py-5 lg:px-12">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-500">
            <Network className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold text-ink">AllocateX</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link to="/register">
            <Button size="sm">
              Get Started <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </header>

      <section className="relative z-10 mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-6 py-16 lg:grid-cols-2 lg:px-12 lg:py-24">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-400">
            <Sparkles className="h-3 w-3" /> DSA Capstone · Graph Algorithms in Production
          </div>
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-5xl lg:text-6xl">
            Automated <span className="text-gradient-brand">Student-to-Laboratory</span> Allocation
          </h1>
          <p className="mt-5 max-w-lg text-lg text-ink-secondary">
            Intelligent allocation powered by Maximum Bipartite Matching.
          </p>
          <p className="mt-3 max-w-lg text-sm text-ink-muted">
            Six hand-implemented matching and flow algorithms - from Kuhn to min-cost max-flow - resolve real eligibility,
            preference, skill, capacity and fairness constraints, backed by 40+ string, DP, approximation and randomised
            algorithms that explain every result. No black-box heuristics, no fabricated results.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/register">
              <Button size="lg">
                Launch the Platform <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="secondary">
                View Algorithm Playground
              </Button>
            </Link>
          </div>

          <div className="mt-12 grid grid-cols-3 gap-6 border-t border-border-subtle pt-6">
            <div>
              <p className="text-2xl font-semibold tabular text-ink">47</p>
              <p className="text-xs text-ink-muted">Algorithms, all hand-built</p>
            </div>
            <div>
              <p className="text-2xl font-semibold tabular text-ink">220+</p>
              <p className="text-xs text-ink-muted">Seeded students in demo dataset</p>
            </div>
            <div>
              <p className="text-2xl font-semibold tabular text-ink">10</p>
              <p className="text-xs text-ink-muted">Laboratories across 7 departments</p>
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.7, delay: 0.1 }}>
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between text-xs text-ink-muted">
              <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5" /> Students</span>
              <span className="flex items-center gap-1.5"><FlaskConical className="h-3.5 w-3.5" /> Laboratories</span>
            </div>
            <HeroGraphAnimation />
            <p className="mt-4 text-center text-xs text-ink-muted">
              Live augmenting-path style reveal — the same event stream the backend WebSocket emits during a real run.
            </p>
          </Card>
        </motion.div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-6 py-16 lg:px-12">
        <h2 className="text-center text-2xl font-semibold text-ink">Built on real algorithm theory</h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-sm text-ink-muted">
          Every allocation run persists its own algorithm metrics — vertices, edges, iterations and measured
          execution time — so complexity claims are always backed by data from that exact run.
        </p>
        <div className="mt-10 grid grid-cols-2 gap-4 lg:grid-cols-3">
          {ALGO_CARDS.map((a, i) => (
            <motion.div key={a.name} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}>
              <Card className="p-5 text-center">
                <p className="text-sm font-semibold text-ink">{a.name}</p>
                <p className="mt-1 font-mono text-xs text-brand-400">{a.complexity}</p>
                <p className="mt-2 text-[11px] text-ink-muted">{a.tag}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-6 py-16 lg:px-12">
        <h2 className="text-center text-2xl font-semibold text-ink">The advanced-algorithms canon, working in production</h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-sm text-ink-muted">
          Each course module powers a real feature - and every algorithm can also be run on your own input in the Concept Lab.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {MODULES.map((m, i) => (
            <motion.div key={m.n} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.06 }}>
              <Card className="h-full p-5">
                <p className="text-[11px] font-medium uppercase tracking-wide text-brand-400">Module {m.n}</p>
                <p className="mt-1 text-sm font-medium text-ink">{m.title}</p>
                <p className="mt-2 text-xs text-ink-secondary">{m.items}</p>
                <p className="mt-3 text-[11px] text-ink-muted">Used for: {m.use}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-6 py-16 lg:px-12">
        <h2 className="text-center text-2xl font-semibold text-ink">Everything a real allocation system needs</h2>
        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div key={f.title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.06 }}>
              <Card className="h-full p-5">
                <div className="mb-3 inline-flex rounded-lg bg-brand-500/15 p-2 text-brand-400">
                  <f.icon className="h-4 w-4" />
                </div>
                <p className="text-sm font-medium text-ink">{f.title}</p>
                <p className="mt-1 text-xs text-ink-muted">{f.description}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-4xl px-6 py-20 text-center lg:px-12">
        <LineChart className="mx-auto mb-4 h-8 w-8 text-brand-400" />
        <h2 className="text-3xl font-semibold text-ink">See the algorithm think, not just the answer.</h2>
        <p className="mx-auto mt-3 max-w-lg text-sm text-ink-muted">
          The Algorithm Playground streams every augmenting-path search and match update live over WebSockets,
          straight from the running Python implementation.
        </p>
        <Link to="/register" className="mt-8 inline-block">
          <Button size="lg">
            Get Started <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </section>

      <footer className="relative z-10 border-t border-border-subtle px-6 py-8 text-center text-xs text-ink-muted lg:px-12">
        AllocateX — Automated Student-to-Laboratory Allocation Using Maximum Bipartite Matching. A DSA systems project.
      </footer>
    </div>
  )
}
