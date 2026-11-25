"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  Node,
  Edge,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { GraphData } from "@/lib/api";

/** Colors per node type (blue/green palette). */
const TYPE_STYLE: Record<string, { bg: string; border: string }> = {
  supplier: { bg: "#eff6ff", border: "#2563eb" },
  lot: { bg: "#fef2f2", border: "#dc2626" },
  batch: { bg: "#ecfdf5", border: "#16a34a" },
  shipment: { bg: "#f8fafc", border: "#64748b" },
};

/**
 * Lay out nodes in vertical columns by type:
 *   col 0 supplier | col 1 lot | col 2 batch | col 3 shipment
 */
function buildFlow(data: GraphData): { nodes: Node[]; edges: Edge[] } {
  const columns: Record<string, number> = {
    supplier: 0,
    lot: 1,
    batch: 2,
    shipment: 3,
  };
  const counters: Record<string, number> = {
    supplier: 0,
    lot: 0,
    batch: 0,
    shipment: 0,
  };

  const nodes: Node[] = data.nodes.map((n) => {
    const col = columns[n.type] ?? 0;
    const row = counters[n.type]++;
    const style = TYPE_STYLE[n.type] ?? TYPE_STYLE.shipment;
    return {
      id: n.id,
      position: { x: col * 250, y: row * 110 },
      data: {
        label: (
          <div className="text-center">
            <div className="font-semibold text-sm">{n.label}</div>
            <div className="text-[10px] text-slate-500">{n.sublabel}</div>
          </div>
        ),
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        background: style.bg,
        border: `2px solid ${style.border}`,
        borderRadius: 10,
        padding: 8,
        width: 190,
      },
    };
  });

  const edges: Edge[] = data.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: true,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "#94a3b8" },
  }));

  return { nodes, edges };
}

export function SupplyChainGraph({ data }: { data: GraphData }) {
  const { nodes, edges } = useMemo(() => buildFlow(data), [data]);

  return (
    <div className="h-[460px] w-full rounded-lg border bg-muted/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable
      >
        <Background gap={16} color="#e2e8f0" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
