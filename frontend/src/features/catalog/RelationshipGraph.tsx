import { useRef, useEffect, useState, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import type { EntityGraph, GraphNode, GraphEdge } from '@/types/entities'

// ─── Force-directed layout (simple spring sim) ───────────────────────────────

interface NodePos {
  id: string
  x: number
  y: number
  vx: number
  vy: number
}

function initialPositions(nodes: GraphNode[], cx: number, cy: number): NodePos[] {
  return nodes.map((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length
    const r = nodes.length === 1 ? 0 : Math.min(cx, cy) * 0.65
    return { id: n.id, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), vx: 0, vy: 0 }
  })
}

const REPULSION = 3500
const SPRING_LEN = 140
const SPRING_K = 0.06
const DAMPING = 0.82
const ITERATIONS = 180

function runSimulation(positions: NodePos[], edges: GraphEdge[]): NodePos[] {
  const pos = positions.map((p) => ({ ...p }))
  const adjacency = new Set(edges.flatMap((e) => [`${e.source_id}-${e.target_id}`, `${e.target_id}-${e.source_id}`]))

  for (let iter = 0; iter < ITERATIONS; iter++) {
    // Repulsion between all pairs
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        const dx = pos[i].x - pos[j].x
        const dy = pos[i].y - pos[j].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = REPULSION / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        pos[i].vx += fx
        pos[i].vy += fy
        pos[j].vx -= fx
        pos[j].vy -= fy
      }
    }
    // Spring attraction along edges
    for (const e of edges) {
      const a = pos.find((p) => p.id === e.source_id)
      const b = pos.find((p) => p.id === e.target_id)
      if (!a || !b) continue
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = SPRING_K * (dist - SPRING_LEN)
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      a.vx += fx
      a.vy += fy
      b.vx -= fx
      b.vy -= fy
    }
    void adjacency
    // Integrate + damp
    for (const p of pos) {
      p.vx *= DAMPING
      p.vy *= DAMPING
      p.x += p.vx
      p.y += p.vy
    }
  }
  return pos
}

// ─── Node colors ─────────────────────────────────────────────────────────────

const nodeColor: Record<string, string> = {
  Service: '#3b82f6',
  AzureResource: '#0ea5e9',
  Environment: '#8b5cf6',
  Team: '#6366f1',
  ApiEndpoint: '#14b8a6',
  Package: '#f97316',
  Incident: '#ef4444',
  ADOWorkItem: '#06b6d4',
}

// ─── Component ───────────────────────────────────────────────────────────────

interface Props {
  graph: EntityGraph
}

export function RelationshipGraph({ graph }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const navigate = useNavigate()
  const [positions, setPositions] = useState<NodePos[]>([])
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: GraphNode } | null>(null)
  const [width, setWidth] = useState(600)
  const [height] = useState(400)

  // Compute layout
  useEffect(() => {
    if (graph.nodes.length === 0) return
    const cx = width / 2
    const cy = height / 2
    const initial = initialPositions(graph.nodes, cx, cy)
    const computed = runSimulation(initial, graph.edges)
    setPositions(computed)
  }, [graph, width, height])

  // Observe container width
  const containerRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const obs = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width
      if (w) setWidth(w)
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  const getPos = useCallback(
    (id: string) => positions.find((p) => p.id === id),
    [positions],
  )

  if (graph.nodes.length <= 1) return null

  const edgeLabels = new Map(graph.edges.map((e) => [e.id, e.relationship_type]))

  return (
    <div ref={containerRef} className="relative w-full" style={{ height }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full"
        onMouseLeave={() => setTooltip(null)}
      >
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="currentColor" className="text-muted-foreground" />
          </marker>
        </defs>

        {/* Edges */}
        {graph.edges.map((edge) => {
          const a = getPos(edge.source_id)
          const b = getPos(edge.target_id)
          if (!a || !b) return null
          const mx = (a.x + b.x) / 2
          const my = (a.y + b.y) / 2
          return (
            <g key={edge.id}>
              <line
                x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke="var(--border)"
                strokeWidth={1.5}
                markerEnd="url(#arrow)"
              />
              <text x={mx} y={my - 4} fontSize={9} textAnchor="middle" fill="var(--muted-foreground)">
                {edgeLabels.get(edge.id) ?? ''}
              </text>
            </g>
          )
        })}

        {/* Nodes */}
        {graph.nodes.map((node) => {
          const p = getPos(node.id)
          if (!p) return null
          const isRoot = node.id === graph.root_id
          const color = nodeColor[node.entity_type] ?? '#6b7280'
          return (
            <g
              key={node.id}
              transform={`translate(${p.x},${p.y})`}
              className="cursor-pointer"
              onClick={() => navigate({ to: '/catalog/$entityId', params: { entityId: node.id } })}
              onMouseEnter={(e) => setTooltip({ x: p.x, y: p.y - 40, node })}
              onMouseLeave={() => setTooltip(null)}
            >
              <circle
                r={isRoot ? 22 : 16}
                fill={color}
                fillOpacity={isRoot ? 1 : 0.75}
                stroke={isRoot ? 'white' : color}
                strokeWidth={isRoot ? 3 : 1}
              />
              <text
                y={isRoot ? 34 : 28}
                fontSize={10}
                textAnchor="middle"
                fill="var(--foreground)"
                className="select-none pointer-events-none"
              >
                {node.name.length > 14 ? node.name.slice(0, 13) + '…' : node.name}
              </text>
              <text
                y={isRoot ? 46 : 38}
                fontSize={8}
                textAnchor="middle"
                fill="var(--muted-foreground)"
                className="select-none pointer-events-none"
              >
                {node.entity_type}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute pointer-events-none z-10 bg-card border border-border rounded-lg px-3 py-2 shadow-lg text-xs"
          style={{ left: tooltip.x, top: tooltip.y, transform: 'translate(-50%, -100%)' }}
        >
          <p className="font-medium">{tooltip.node.name}</p>
          <p className="text-muted-foreground">{tooltip.node.entity_type}</p>
        </div>
      )}
    </div>
  )
}
