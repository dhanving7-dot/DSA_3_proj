import { CHART_CHROME, SERIES } from "@/lib/chartTheme"

export interface BinaryTreeNode {
  key: string | number
  left: BinaryTreeNode | null
  right: BinaryTreeNode | null
}

/** Binary search tree drawn with x = in-order rank, y = depth (so it is visibly a BST). */
export function BinaryTreeSVG({ root, weights }: { root: BinaryTreeNode | null; weights?: Record<string, number> }) {
  if (!root) return null
  const nodes: { key: string; x: number; depth: number }[] = []
  const links: { from: string; to: string }[] = []
  let rank = 0
  let maxDepth = 0
  const walk = (node: BinaryTreeNode | null, depth: number, parent: string | null) => {
    if (!node) return
    walk(node.left, depth + 1, String(node.key))
    nodes.push({ key: String(node.key), x: rank++, depth })
    maxDepth = Math.max(maxDepth, depth)
    if (parent != null) links.push({ from: parent, to: String(node.key) })
    walk(node.right, depth + 1, String(node.key))
  }
  walk(root, 0, null)
  const W = Math.max(320, nodes.length * 64)
  const H = (maxDepth + 1) * 64 + 24
  const pos = Object.fromEntries(nodes.map((n) => [n.key, { x: 32 + (n.x * (W - 64)) / Math.max(nodes.length - 1, 1), y: 28 + n.depth * 64 }]))
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 340 }} role="img" aria-label="Optimal binary search tree">
      {links.map((l, i) => (
        <line key={i} x1={pos[l.from].x} y1={pos[l.from].y} x2={pos[l.to].x} y2={pos[l.to].y} stroke={CHART_CHROME.baseline} strokeWidth={2} />
      ))}
      {nodes.map((n) => (
        <g key={n.key}>
          <circle cx={pos[n.key].x} cy={pos[n.key].y} r={19} fill={CHART_CHROME.surface} stroke={SERIES.blue} strokeWidth={2} />
          <text x={pos[n.key].x} y={pos[n.key].y + 4} textAnchor="middle" fontSize={11} fill={CHART_CHROME.textPrimary}>
            {n.key.length > 6 ? n.key.slice(0, 6) + "…" : n.key}
          </text>
          {weights && weights[n.key] != null && (
            <text x={pos[n.key].x} y={pos[n.key].y + 32} textAnchor="middle" fontSize={10} fill={CHART_CHROME.textMuted}>
              f={weights[n.key]}
            </text>
          )}
        </g>
      ))}
    </svg>
  )
}

/** General rooted tree (root 0) laid out by BFS depth; highlighted nodes get a ring. */
export function TreeSVG({ n, parent, highlight = [] }: { n: number; parent: number[]; highlight?: number[] }) {
  const children: number[][] = Array.from({ length: n }, () => [])
  parent.forEach((p, v) => p >= 0 && children[p].push(v))
  const depth = new Array<number>(n).fill(0)
  const order = [0]
  for (let i = 0; i < order.length; i++) for (const c of children[order[i]]) { depth[c] = depth[order[i]] + 1; order.push(c) }
  // leaf-order x placement keeps edges from crossing
  const x = new Array<number>(n).fill(0)
  let next = 0
  const place = (v: number): number => {
    if (!children[v].length) return (x[v] = next++)
    const xs = children[v].map(place)
    return (x[v] = (xs[0] + xs[xs.length - 1]) / 2)
  }
  place(0)
  const maxDepth = Math.max(...depth)
  const W = Math.max(320, next * 34 + 40)
  const H = (maxDepth + 1) * 52 + 20
  const px = (v: number) => 20 + (x[v] * (W - 40)) / Math.max(next - 1, 1)
  const py = (v: number) => 20 + depth[v] * 52
  const hl = new Set(highlight)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 360 }} role="img" aria-label="Random tree">
      {parent.map((p, v) => (p >= 0 ? <line key={v} x1={px(p)} y1={py(p)} x2={px(v)} y2={py(v)} stroke={CHART_CHROME.baseline} strokeWidth={2} /> : null))}
      {Array.from({ length: n }, (_, v) => (
        <g key={v}>
          <circle cx={px(v)} cy={py(v)} r={12} fill={CHART_CHROME.surface} stroke={hl.has(v) ? SERIES.aqua : SERIES.blue} strokeWidth={hl.has(v) ? 3 : 2} />
          <text x={px(v)} y={py(v) + 4} textAnchor="middle" fontSize={10} fill={CHART_CHROME.textPrimary}>{v}</text>
        </g>
      ))}
    </svg>
  )
}

/** Cities on a 0-100 grid with one tour drawn through them. */
export function TourSVG({ points, tour, title, color }: { points: number[][]; tour: number[]; title: string; color: string }) {
  const S = 220
  const sx = (v: number) => 12 + (v / 100) * (S - 24)
  return (
    <figure className="rounded-lg border border-border-subtle bg-white/[0.02] p-2">
      <svg viewBox={`0 0 ${S} ${S}`} className="w-full" role="img" aria-label={title}>
        <polyline
          points={tour.map((c) => `${sx(points[c][0])},${sx(100 - points[c][1])}`).join(" ")}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
        />
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={sx(p[0])} cy={sx(100 - p[1])} r={i === 0 ? 6 : 4.5} fill={i === 0 ? CHART_CHROME.textPrimary : color} stroke={CHART_CHROME.surface} strokeWidth={2} />
            <text x={sx(p[0]) + 7} y={sx(100 - p[1]) - 6} fontSize={9} fill={CHART_CHROME.textMuted}>{i}</text>
          </g>
        ))}
      </svg>
      <figcaption className="mt-1 text-center text-[11px] text-ink-secondary">{title}</figcaption>
    </figure>
  )
}
