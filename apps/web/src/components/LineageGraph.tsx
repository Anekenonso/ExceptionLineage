"use client";

import React, { useState, useMemo } from "react";
import { LineageData, EvidenceItem } from "@/types/investigation";
import { formatAmount } from "@/lib/formatters";

interface LineageGraphProps {
  lineage?: LineageData | null;
  onSelectEvidence?: (evidence: EvidenceItem) => void;
}

interface GraphNode {
  id: string;
  type: "customer" | "contract" | "amendment" | "sow" | "exception" | "approval" | "invoice" | "evidence";
  title: string;
  subtitle: string;
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

    // 1. Customer (Column 0)
    if (lineage.customer && lineage.customer.id) {
      const c = lineage.customer;
      const node: GraphNode = {
        id: c.id,
        type: "customer",
        title: c.name || "Customer",
        subtitle: `ID: ${c.id}`,
        column: 0,
        row: 0,
        data: c as unknown as Record<string, unknown>,
      };
      nList.push(node);
      nMap.set(node.id, node);
    }

    // 2. Contract (Column 1)
    if (lineage.contract && lineage.contract.id) {
      const k = lineage.contract;
      const node: GraphNode = {
        id: k.id,
        type: "contract",
        title: k.title || "Governing Contract",
        subtitle: `Contract ${k.id}`,
        statusBadge: k.status === "ACTIVE" ? "Active" : k.status,
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
          label: "Contract with",
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
        title: amd.title || `Amendment #${amd.amendment_number}`,
        subtitle: `Ref: ${amd.id}`,
        statusBadge: `Amendment #${amd.amendment_number}`,
        badgeColor: "bg-blue-50 text-blue-800",
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
          label: "Amended by",
          type: "has_amendment",
        });
      }
    });

    (lineage.sows || []).forEach((sow) => {
      if (!sow.id) return;
      const node: GraphNode = {
        id: sow.id,
        type: "sow",
        title: sow.title || "Statement of Work",
        subtitle: sow.reference || `SOW ${sow.id}`,
        statusBadge: "SOW",
        badgeColor: "bg-cyan-50 text-cyan-800",
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
          label: "Includes scope",
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
        title: exc.exception_type ? `Flag: ${exc.exception_type}` : "Flagged Variance",
        subtitle: exc.expected_amount ? `Expected ${formatAmount(exc.expected_amount, exc.currency || "USD")}` : "Discrepancy",
        statusBadge: "Flagged",
        badgeColor: "bg-amber-100 text-amber-800",
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
          label: "Pertains to",
          type: "has_exception",
        });
      }
    }

    if (lineage.approval && lineage.approval.id) {
      const apr = lineage.approval;
      const node: GraphNode = {
        id: apr.id,
        type: "approval",
        title: apr.approver ? `Approval by ${apr.approver}` : "Operational Approval",
        subtitle: `Ref: ${apr.id}`,
        statusBadge: apr.status === "APPROVED" ? "Approved" : apr.status,
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
          label: "Approved by",
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
        title: `Invoice ${inv.id}`,
        subtitle: inv.amount ? formatAmount(inv.amount, inv.currency || "USD") : "Invoice",
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
          label: "Billed to",
          type: "billed_to",
        });
      }
      if (inv.contract_id && nMap.has(inv.contract_id)) {
        eList.push({
          id: `${inv.id}->${inv.contract_id}`,
          sourceId: inv.id,
          targetId: inv.contract_id,
          label: "Governed by",
          type: "governed_by",
        });
      }
      if (inv.exception_id && nMap.has(inv.exception_id)) {
        eList.push({
          id: `${inv.id}->${inv.exception_id}`,
          sourceId: inv.id,
          targetId: inv.exception_id,
          label: "Flagged with",
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
        title: ev.title || ev.evidence_type.replace(/_/g, " "),
        subtitle: ev.locator || ev.source,
        statusBadge: "Evidence",
        badgeColor: "bg-slate-100 text-slate-800",
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
          label: "Documented in",
          type: "has_evidence",
        });
      }
    });

    return { nodes: nList, edges: eList, nodeMap: nMap };
  }, [lineage]);

  // Layout coordinates calculation
  const nodeWidth = 190;
  const nodeHeight = 82;
  const colSpacing = 240;
  const rowSpacing = 105;
  const startX = 30;
  const startY = 40;

  const getNodePos = (node: GraphNode) => {
    const x = startX + node.column * colSpacing;
    const y = startY + node.row * rowSpacing;
    return { x, y, cx: x + nodeWidth / 2, cy: y + nodeHeight / 2 };
  };

  const maxCol = Math.max(1, ...nodes.map((n) => n.column));
  const maxRow = Math.max(1, ...nodes.map((n) => n.row));
  const canvasWidth = Math.max(1050, startX * 2 + (maxCol + 1) * colSpacing);
  const canvasHeight = Math.max(320, startY * 2 + (maxRow + 1) * rowSpacing);

  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;

  if (!lineage || nodes.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-xs">
        <h3 className="text-sm font-semibold text-slate-900">Contract History Unavailable</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          No relationship records were found for this invoice.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
      {/* Header bar */}
      <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Contract history
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            See how this invoice connects to the contract, amendments and approvals.
          </p>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center rounded-md border border-slate-200 bg-white shadow-2xs">
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.1))}
              className="px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-r border-slate-200"
              title="Zoom Out"
            >
              −
            </button>
            <span className="px-2.5 py-1 text-[11px] font-mono text-slate-600">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.min(1.4, z + 0.1))}
              className="px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-r border-slate-200"
              title="Zoom In"
            >
              +
            </button>
            <button
              type="button"
              onClick={() => setZoomLevel(1)}
              className="px-2.5 py-1 text-[11px] text-slate-600 hover:text-slate-900 hover:bg-slate-50"
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
                <polygon points="0 0, 8 3, 0 6" fill="#0f172a" />
              </marker>
            </defs>

            {/* Column Titles */}
            {["Customer", "Contract", "Amendments & SOWs", "Approvals & Variance", "Invoice", "Supporting Records"].map(
              (header, colIdx) => (
                <text
                  key={colIdx}
                  x={startX + colIdx * colSpacing + nodeWidth / 2}
                  y={20}
                  textAnchor="middle"
                  className="fill-slate-400 text-[11px] font-medium"
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

              const isReverse = srcPos.x > tgtPos.x;
              const x1 = isReverse ? srcPos.x : srcPos.x + nodeWidth;
              const y1 = srcPos.cy;
              const x2 = isReverse ? tgtPos.x + nodeWidth : tgtPos.x;
              const y2 = tgtPos.cy;

              const dx = Math.abs(x2 - x1) * 0.5;
              const pathD = `M ${x1} ${y1} C ${isReverse ? x1 - dx : x1 + dx} ${y1}, ${
                isReverse ? x2 + dx : x2 - dx
              } ${y2}, ${x2} ${y2}`;

              const isEdgeActive =
                selectedNodeId && (edge.sourceId === selectedNodeId || edge.targetId === selectedNodeId);

              const midX = (x1 + x2) / 2;
              const midY = (y1 + y2) / 2 - 4;

              return (
                <g key={edge.id} className="transition-opacity">
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isEdgeActive ? "#0f172a" : "#cbd5e1"}
                    strokeWidth={isEdgeActive ? 2 : 1.2}
                    markerEnd={isEdgeActive ? "url(#arrowhead-active)" : "url(#arrowhead)"}
                  />
                  <rect
                    x={midX - 40}
                    y={midY - 7}
                    width={80}
                    height={15}
                    rx={3}
                    fill="#ffffff"
                    stroke={isEdgeActive ? "#94a3b8" : "#e2e8f0"}
                    strokeWidth={1}
                  />
                  <text
                    x={midX}
                    y={midY + 4}
                    textAnchor="middle"
                    className={`text-[9px] font-medium ${
                      isEdgeActive ? "fill-slate-900 font-semibold" : "fill-slate-500"
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
                        ? "ring-2 ring-slate-900 border-slate-900 bg-slate-50"
                        : node.type === "invoice"
                        ? "border-slate-800 bg-slate-900 text-white"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    {/* Top Row: Type tag & Status badge */}
                    <div className="flex items-center justify-between gap-1">
                      <span
                        className={`text-[10px] font-medium tracking-tight ${
                          node.type === "invoice" ? "text-slate-300" : "text-slate-500"
                        }`}
                      >
                        {node.type.charAt(0).toUpperCase() + node.type.slice(1)}
                      </span>

                      {node.statusBadge && (
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded truncate max-w-[95px] font-medium ${
                            node.type === "invoice"
                              ? "bg-slate-800 text-white"
                              : node.badgeColor || "bg-slate-100 text-slate-700"
                          }`}
                          title={node.statusBadge}
                        >
                          {node.statusBadge}
                        </span>
                      )}
                    </div>

                    {/* Middle: Title */}
                    <div className="my-0.5">
                      <div
                        className={`text-xs font-semibold truncate leading-tight ${
                          node.type === "invoice" ? "text-white" : "text-slate-900"
                        }`}
                        title={node.title}
                      >
                        {node.title}
                      </div>
                    </div>

                    {/* Bottom: Subtitle / ref */}
                    <div
                      className={`text-[10px] truncate ${
                        node.type === "invoice" ? "text-slate-400" : "text-slate-400"
                      }`}
                    >
                      {node.subtitle}
                    </div>
                  </div>
                </foreignObject>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="p-4 border-t border-slate-200 bg-slate-50 text-xs">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  Record Details: {selectedNode.type}
                </span>
                <span className="font-mono text-slate-900 font-bold">{selectedNode.id}</span>
                {selectedNode.statusBadge && (
                  <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${selectedNode.badgeColor}`}>
                    {selectedNode.statusBadge}
                  </span>
                )}
              </div>
              <p className="text-slate-800 font-medium">{selectedNode.title}</p>
            </div>

            <button
              type="button"
              onClick={() => setSelectedNodeId(null)}
              className="text-slate-400 hover:text-slate-700 p-1 font-bold text-sm"
              title="Close details"
            >
              ✕
            </button>
          </div>

          {/* Properties Grid */}
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-3 rounded-lg border border-slate-200 text-xs">
            {Object.entries(selectedNode.data)
              .filter(([k, v]) => v !== null && v !== undefined && typeof v !== "object")
              .slice(0, 8)
              .map(([k, v]) => (
                <div key={k}>
                  <span className="text-slate-400 block text-[10px] uppercase font-medium">{k.replace(/_/g, " ")}</span>
                  <span className="text-slate-800 font-medium truncate block font-mono text-[11px]" title={String(v)}>
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
