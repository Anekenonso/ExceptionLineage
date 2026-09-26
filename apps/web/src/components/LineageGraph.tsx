"use client";

import React, { useState, useMemo } from "react";
import { LineageData, EvidenceItem } from "@/types/investigation";

interface LineageGraphProps {
  lineage?: LineageData | null;
  onSelectEvidence?: (evidence: EvidenceItem) => void;
}

interface GraphNode {
  id: string;
  type: "customer" | "contract" | "amendment" | "sow" | "exception" | "approval" | "invoice" | "evidence";
  label: string;
  sublabel: string;
  statusBadge?: string;
  badgeColor?: string;
  column: number;
  row: number;
  data: Record<string, unknown>;
  isCited?: boolean;
}

interface GraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  label: string;
  type: string;
}

export function LineageGraph({ lineage, onSelectEvidence }: LineageGraphProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // Parse nodes & edges strictly from backend-returned lineage
  const { nodes, edges, nodeMap } = useMemo(() => {
    if (!lineage) {
      return { nodes: [], edges: [], nodeMap: new Map<string, GraphNode>() };
    }

    const nList: GraphNode[] = [];
    const eList: GraphEdge[] = [];
    const nMap = new Map<string, GraphNode>();

    // 1. Customer
    if (lineage.customer && lineage.customer.id) {
      const c = lineage.customer;
      const node: GraphNode = {
        id: c.id,
        type: "customer",
        label: c.name || c.id,
        sublabel: `Customer ${c.id}`,
        column: 0,
        row: 0,
        data: c as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);
    }

    // 2. Contract
    if (lineage.contract && lineage.contract.id) {
      const k = lineage.contract;
      const node: GraphNode = {
        id: k.id,
        type: "contract",
        label: k.title || k.id,
        sublabel: `Contract ${k.id}`,
        statusBadge: k.status,
        badgeColor: k.status === "ACTIVE" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700",
        column: 1,
        row: 0,
        data: k as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (k.customer_id && nMap.has(k.customer_id)) {
        eList.push({
          id: `${k.customer_id}->${k.id}`,
          sourceId: k.customer_id,
          targetId: k.id,
          label: "HAS_CONTRACT",
          type: "has_contract",
        });
      }
    }

    // 3. Amendments & SOWs (Column 2)
    let col2Row = 0;
    (lineage.amendments || []).forEach((amd) => {
      if (!amd.id) return;
      const node: GraphNode = {
        id: amd.id,
        type: "amendment",
        label: amd.title || `Amendment #${amd.amendment_number}`,
        sublabel: `Amendment ${amd.id}`,
        statusBadge: `Amd #${amd.amendment_number}`,
        badgeColor: "bg-amber-100 text-amber-800",
        column: 2,
        row: col2Row++,
        data: amd as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (amd.contract_id && nMap.has(amd.contract_id)) {
        eList.push({
          id: `${amd.contract_id}->${amd.id}`,
          sourceId: amd.contract_id,
          targetId: amd.id,
          label: "HAS_AMENDMENT",
          type: "has_amendment",
        });
      }
    });

    (lineage.sows || []).forEach((sow) => {
      if (!sow.id) return;
      const node: GraphNode = {
        id: sow.id,
        type: "sow",
        label: sow.title || sow.reference,
        sublabel: `SOW ${sow.id}`,
        statusBadge: sow.reference || "SOW",
        badgeColor: "bg-cyan-100 text-cyan-800",
        column: 2,
        row: col2Row++,
        data: sow as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (sow.contract_id && nMap.has(sow.contract_id)) {
        eList.push({
          id: `${sow.contract_id}->${sow.id}`,
          sourceId: sow.contract_id,
          targetId: sow.id,
          label: "HAS_SOW",
          type: "has_sow",
        });
      }
    });

    // 4. Exception & Approval (Column 3)
    let col3Row = 0;
    if (lineage.exception && lineage.exception.id) {
      const exc = lineage.exception;
      const node: GraphNode = {
        id: exc.id,
        type: "exception",
        label: exc.exception_type || "Exception",
        sublabel: `Exception ${exc.id}`,
        statusBadge: exc.exception_type,
        badgeColor: "bg-purple-100 text-purple-800",
        column: 3,
        row: col3Row++,
        data: exc as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (exc.contract_id && nMap.has(exc.contract_id)) {
        eList.push({
          id: `${exc.contract_id}->${exc.id}`,
          sourceId: exc.contract_id,
          targetId: exc.id,
          label: "HAS_EXCEPTION",
          type: "has_exception",
        });
      }
    }

    if (lineage.approval && lineage.approval.id) {
      const apr = lineage.approval;
      const node: GraphNode = {
        id: apr.id,
        type: "approval",
        label: apr.status || "Approval",
        sublabel: `Approval ${apr.id}`,
        statusBadge: apr.status,
        badgeColor: apr.status === "APPROVED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800",
        column: 3,
        row: col3Row++,
        data: apr as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (apr.exception_id && nMap.has(apr.exception_id)) {
        eList.push({
          id: `${apr.exception_id}->${apr.id}`,
          sourceId: apr.exception_id,
          targetId: apr.id,
          label: "HAS_APPROVAL",
          type: "has_approval",
        });
      }
    }

    // 5. Invoice (Column 4)
    if (lineage.invoice && lineage.invoice.id) {
      const inv = lineage.invoice;
      const node: GraphNode = {
        id: inv.id,
        type: "invoice",
        label: `Invoice ${inv.id}`,
        sublabel: inv.amount ? `${inv.currency || "USD"} ${Number(inv.amount).toFixed(2)}` : "Invoice",
        statusBadge: "Target Invoice",
        badgeColor: "bg-slate-900 text-white",
        column: 4,
        row: 0,
        data: inv as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (inv.customer_id && nMap.has(inv.customer_id)) {
        eList.push({
          id: `${inv.id}->${inv.customer_id}`,
          sourceId: inv.id,
          targetId: inv.customer_id,
          label: "BILLED_TO",
          type: "billed_to",
        });
      }
      if (inv.contract_id && nMap.has(inv.contract_id)) {
        eList.push({
          id: `${inv.id}->${inv.contract_id}`,
          sourceId: inv.id,
          targetId: inv.contract_id,
          label: "GOVERNED_BY",
          type: "governed_by",
        });
      }
      if (inv.exception_id && nMap.has(inv.exception_id)) {
        eList.push({
          id: `${inv.id}->${inv.exception_id}`,
          sourceId: inv.id,
          targetId: inv.exception_id,
          label: "HAS_EXCEPTION",
          type: "has_exception",
        });
      }
    }

    // 6. Evidence Items (Column 5)
    (lineage.evidence || []).forEach((ev, idx) => {
      if (!ev.id) return;
      const node: GraphNode = {
        id: ev.id,
        type: "evidence",
        label: ev.title || ev.evidence_type,
        sublabel: ev.locator || ev.source,
        statusBadge: ev.evidence_type.replace(/_/g, " "),
        badgeColor: "bg-teal-100 text-teal-800",
        column: 5,
        row: idx,
        isCited: true,
        data: ev as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);

      if (ev.source_id && nMap.has(ev.source_id)) {
        eList.push({
          id: `${ev.source_id}->${ev.id}`,
          sourceId: ev.source_id,
          targetId: ev.id,
          label: "HAS_EVIDENCE",
          type: "has_evidence",
        });
      }
    });

    return { nodes: nList, edges: eList, nodeMap: nMap };
  }, [lineage]);

  // Layout coordinates calculation
  const nodeWidth = 180;
  const nodeHeight = 84;
  const colSpacing = 240;
  const rowSpacing = 110;
  const startX = 30;
  const startY = 40;

  const getNodePos = (node: GraphNode) => {
    const x = startX + node.column * colSpacing;
    const y = startY + node.row * rowSpacing;
    return { x, y, cx: x + nodeWidth / 2, cy: y + nodeHeight / 2 };
  };

  // Compute total canvas dimensions
  const maxCol = Math.max(1, ...nodes.map((n) => n.column));
  const maxRow = Math.max(1, ...nodes.map((n) => n.row));
  const canvasWidth = Math.max(1000, startX * 2 + (maxCol + 1) * colSpacing);
  const canvasHeight = Math.max(340, startY * 2 + (maxRow + 1) * rowSpacing);

  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;

  if (!lineage || nodes.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-xs">
        <div className="h-10 w-10 mx-auto rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-3">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-slate-900">Lineage Unavailable</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No directional relationship graph was returned by the backend for this invoice.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
      {/* Header bar with controls */}
      <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded bg-slate-900 text-white flex items-center justify-center text-[10px] font-mono font-bold">
            G
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Evidence Lineage Graph
            </h3>
            <p className="text-[11px] text-slate-500 font-mono">
              Directional graph retrieval ({nodes.length} nodes, {edges.length} relationships)
            </p>
          </div>
        </div>

        {/* Graph Legend & Zoom Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 text-[10px] text-slate-500 font-mono">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-indigo-500 inline-block" /> Customer
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-blue-500 inline-block" /> Contract
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500 inline-block" /> Amendment
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-purple-500 inline-block" /> Exception
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" /> Approval
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-teal-500 inline-block" /> Evidence
            </span>
          </div>

          <div className="flex items-center rounded-md border border-slate-200 bg-white shadow-2xs">
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.1))}
              className="px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-r border-slate-200"
              title="Zoom Out"
            >
              −
            </button>
            <span className="px-2 py-1 text-[11px] font-mono text-slate-600">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.min(1.4, z + 0.1))}
              className="px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-r border-slate-200"
              title="Zoom In"
            >
              +
            </button>
            <button
              type="button"
              onClick={() => setZoomLevel(1)}
              className="px-2 py-1 text-[11px] text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              title="Reset Zoom"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* SVG Canvas Container */}
      <div className="relative overflow-x-auto overflow-y-hidden bg-slate-50/20 p-4">
        <div
          style={{
            transform: `scale(${zoomLevel})`,
            transformOrigin: "top left",
            width: canvasWidth,
            height: canvasHeight,
          }}
          className="transition-transform duration-150"
        >
          <svg
            width={canvasWidth}
            height={canvasHeight}
            className="select-none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              {/* Arrowhead marker */}
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#94a3b8" />
              </marker>
              <marker
                id="arrowhead-active"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#3b82f6" />
              </marker>
            </defs>

            {/* Stage Column Labels */}
            {["Customer", "Contract", "Amendments & SOWs", "Exception & Approval", "Target Invoice", "Cited Evidence"].map(
              (header, colIdx) => (
                <text
                  key={colIdx}
                  x={startX + colIdx * colSpacing + nodeWidth / 2}
                  y={22}
                  textAnchor="middle"
                  className="fill-slate-400 text-[10px] uppercase font-mono font-bold tracking-wider"
                >
                  {header}
                </text>
              )
            )}

            {/* Edges */}
            {edges.map((edge) => {
              const src = nodeMap.get(edge.sourceId);
              const tgt = nodeMap.get(edge.targetId);
              if (!src || !tgt) return null;

              const srcPos = getNodePos(src);
              const tgtPos = getNodePos(tgt);

              // Connect from right of source to left of target (or vice-versa depending on columns)
              const isReverse = srcPos.x > tgtPos.x;
              const x1 = isReverse ? srcPos.x : srcPos.x + nodeWidth;
              const y1 = srcPos.cy;
              const x2 = isReverse ? tgtPos.x + nodeWidth : tgtPos.x;
              const y2 = tgtPos.cy;

              // Cubic bezier control points
              const dx = Math.abs(x2 - x1) * 0.5;
              const pathD = `M ${x1} ${y1} C ${isReverse ? x1 - dx : x1 + dx} ${y1}, ${
                isReverse ? x2 + dx : x2 - dx
              } ${y2}, ${x2} ${y2}`;

              const isEdgeActive =
                selectedNodeId && (edge.sourceId === selectedNodeId || edge.targetId === selectedNodeId);

              // Midpoint for label
              const midX = (x1 + x2) / 2;
              const midY = (y1 + y2) / 2 - 4;

              return (
                <g key={edge.id} className="transition-opacity">
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isEdgeActive ? "#3b82f6" : "#cbd5e1"}
                    strokeWidth={isEdgeActive ? 2 : 1.5}
                    markerEnd={isEdgeActive ? "url(#arrowhead-active)" : "url(#arrowhead)"}
                    strokeDasharray={edge.type.includes("exception") ? "4 3" : undefined}
                  />
                  <rect
                    x={midX - 35}
                    y={midY - 7}
                    width={70}
                    height={14}
                    rx={3}
                    fill="#ffffff"
                    stroke={isEdgeActive ? "#bfdbfe" : "#e2e8f0"}
                    strokeWidth={1}
                  />
                  <text
                    x={midX}
                    y={midY + 3.5}
                    textAnchor="middle"
                    className={`text-[8.5px] font-mono tracking-tight font-semibold ${
                      isEdgeActive ? "fill-blue-700" : "fill-slate-500"
                    }`}
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {nodes.map((node) => {
              const pos = getNodePos(node);
              const isSelected = selectedNodeId === node.id;

              // Border and styling based on type
              const typeColorMap: Record<
                string,
                { border: string; bg: string; dot: string; tag: string }
              > = {
                customer: { border: "border-indigo-200", bg: "bg-white", dot: "bg-indigo-500", tag: "Customer" },
                contract: { border: "border-blue-200", bg: "bg-white", dot: "bg-blue-500", tag: "Contract" },
                amendment: { border: "border-amber-200", bg: "bg-white", dot: "bg-amber-500", tag: "Amendment" },
                sow: { border: "border-cyan-200", bg: "bg-white", dot: "bg-cyan-500", tag: "SOW" },
                exception: { border: "border-purple-200", bg: "bg-white", dot: "bg-purple-500", tag: "Exception" },
                approval: { border: "border-emerald-200", bg: "bg-white", dot: "bg-emerald-500", tag: "Approval" },
                invoice: { border: "border-slate-800", bg: "bg-slate-900 text-white", dot: "bg-slate-400", tag: "Invoice" },
                evidence: { border: "border-teal-200", bg: "bg-teal-50/50", dot: "bg-teal-500", tag: "Evidence" },
              };

              const style = typeColorMap[node.type] || typeColorMap.contract;

              return (
                <foreignObject
                  key={node.id}
                  x={pos.x}
                  y={pos.y}
                  width={nodeWidth}
                  height={nodeHeight}
                  className="cursor-pointer overflow-visible"
                  onClick={() => {
                    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
                    if (node.type === "evidence" && onSelectEvidence) {
                      onSelectEvidence(node.data as unknown as EvidenceItem);
                    }
                  }}
                >
                  <div
                    className={`h-full w-full rounded-lg border p-2.5 flex flex-col justify-between transition shadow-2xs hover:shadow-md ${
                      isSelected
                        ? "ring-2 ring-blue-500 border-blue-500 bg-blue-50/20"
                        : `${style.border} ${style.bg}`
                    }`}
                  >
                    {/* Top Row: Type tag & Status badge */}
                    <div className="flex items-center justify-between gap-1">
                      <span className="flex items-center gap-1 text-[10px] font-mono font-bold tracking-tight text-slate-500">
                        <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
                        <span>{style.tag}</span>
                      </span>

                      {node.statusBadge && (
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded truncate max-w-[85px] ${
                            node.badgeColor || "bg-slate-100 text-slate-700"
                          }`}
                          title={node.statusBadge}
                        >
                          {node.statusBadge}
                        </span>
                      )}
                    </div>

                    {/* Middle: ID / Primary identifier */}
                    <div className="my-1">
                      <div className="font-mono text-xs font-bold text-slate-900 truncate" title={node.id}>
                        {node.id}
                      </div>
                      <div className="text-[11px] text-slate-600 truncate leading-tight" title={node.label}>
                        {node.label}
                      </div>
                    </div>

                    {/* Bottom: Sublabel or locator */}
                    <div className="text-[9.5px] font-mono text-slate-400 truncate">
                      {node.sublabel}
                    </div>
                  </div>
                </foreignObject>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Selected Node Details Drawer / Inspector */}
      {selectedNode && (
        <div className="p-4 border-t border-slate-200 bg-slate-50 text-xs">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="uppercase tracking-wider font-mono text-[10px] font-bold text-slate-500">
                  Node Inspector: {selectedNode.type}
                </span>
                <span className="font-mono font-bold text-slate-900">{selectedNode.id}</span>
                {selectedNode.statusBadge && (
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${selectedNode.badgeColor}`}>
                    {selectedNode.statusBadge}
                  </span>
                )}
              </div>
              <p className="text-slate-700 font-medium">{selectedNode.label}</p>
            </div>

            <button
              type="button"
              onClick={() => setSelectedNodeId(null)}
              className="text-slate-400 hover:text-slate-700 p-1"
              title="Close inspector"
            >
              ✕
            </button>
          </div>

          {/* Properties Grid */}
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-3 rounded-lg border border-slate-200 font-mono text-[11px]">
            {Object.entries(selectedNode.data)
              .filter(([k, v]) => v !== null && v !== undefined && typeof v !== "object")
              .slice(0, 8)
              .map(([k, v]) => (
                <div key={k}>
                  <span className="text-slate-400 block text-[9.5px] uppercase">{k}</span>
                  <span className="text-slate-800 font-medium truncate block" title={String(v)}>
                    {String(v)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
