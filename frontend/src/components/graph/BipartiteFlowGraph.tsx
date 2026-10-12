import { useMemo } from "react"
import ReactFlow, { Background, Controls, MiniMap, type Edge, type Node } from "reactflow"
import "reactflow/dist/style.css"
import { nodeTypes } from "@/components/graph/GraphNodes"

export interface GraphItem {
  id: string | number
  label: string
  sublabel?: string
}

export interface GraphEdgeSpec {
  source: string | number
  target: string | number
  matched?: boolean
  active?: boolean
}

interface BipartiteFlowGraphProps {
  leftItems: GraphItem[]
  rightItems: GraphItem[]
  edges: GraphEdgeSpec[]
  height?: number | string
  searchTerm?: string
  highlightId?: string | null
  onNodeClick?: (id: string, kind: "student" | "lab") => void
  showMiniMap?: boolean
}

const V_GAP = 66
const LEFT_X = 40
const RIGHT_X = 520

export function BipartiteFlowGraph({
  leftItems,
  rightItems,
  edges,
  height = 560,
  searchTerm = "",
  highlightId = null,
  onNodeClick,
  showMiniMap = false,
}: BipartiteFlowGraphProps) {
  const term = searchTerm.trim().toLowerCase()

  const relatedIds = useMemo(() => {
    if (!highlightId) return null
    const set = new Set<string>([highlightId])
    for (const e of edges) {
      const s = `s-${e.source}`
      const l = `l-${e.target}`
      if (s === highlightId) set.add(l)
      if (l === highlightId) set.add(s)
    }
    return set
  }, [highlightId, edges])

  const nodes: Node[] = useMemo(() => {
    const left = leftItems.map((item, i) => {
      const id = `s-${item.id}`
      const matches = !term || item.label.toLowerCase().includes(term) || (item.sublabel ?? "").toLowerCase().includes(term)
      const dimmed = (!!term && !matches) || (!!relatedIds && !relatedIds.has(id))
      return {
        id,
        type: "bipartite",
        position: { x: LEFT_X, y: i * V_GAP + 20 },
        data: { label: item.label, sublabel: item.sublabel, kind: "student", status: highlightId === id ? "active" : "neutral", dimmed },
        draggable: false,
      } as Node
    })
    const right = rightItems.map((item, i) => {
      const id = `l-${item.id}`
      const matches = !term || item.label.toLowerCase().includes(term) || (item.sublabel ?? "").toLowerCase().includes(term)
      const dimmed = (!!term && !matches) || (!!relatedIds && !relatedIds.has(id))
      return {
        id,
        type: "bipartite",
        position: { x: RIGHT_X, y: i * V_GAP + 20 },
        data: { label: item.label, sublabel: item.sublabel, kind: "lab", status: highlightId === id ? "active" : "neutral", dimmed },
        draggable: false,
      } as Node
    })
    return [...left, ...right]
  }, [leftItems, rightItems, term, relatedIds, highlightId])

  const flowEdges: Edge[] = useMemo(() => {
    return edges.map((e, idx) => {
      const source = `s-${e.source}`
      const target = `l-${e.target}`
      const dimmed = !!relatedIds && !(relatedIds.has(source) && relatedIds.has(target))
      const color = e.matched ? "#0ca30c" : e.active ? "#818cf8" : "#3a3a42"
      return {
        id: `e-${idx}-${source}-${target}`,
        source,
        target,
        animated: e.matched || e.active,
        style: { stroke: color, strokeWidth: e.matched ? 2 : 1, opacity: dimmed ? 0.08 : e.matched ? 0.9 : 0.35 },
      } as Edge
    })
  }, [edges, relatedIds])

  return (
    <div style={{ height }} className="overflow-hidden rounded-2xl border border-border-subtle bg-canvas-raised/60">
      <ReactFlow
        nodes={nodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => onNodeClick?.(node.id, node.data.kind)}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background color="#2c2c2a" gap={24} size={1} />
        <Controls showInteractive={false} className="[&_button]:!bg-white/[0.05] [&_button]:!border-white/[0.1] [&_button]:!text-white" />
        {showMiniMap && <MiniMap pannable zoomable maskColor="rgba(8,8,10,0.85)" style={{ background: "#0d0d10" }} />}
      </ReactFlow>
    </div>
  )
}
