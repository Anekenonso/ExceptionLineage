"use client";

import React, { useState, useMemo, useRef } from "react";
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
  badgeStyle?: string;
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
  const [panOffset, setPanOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const startPanPos = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

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
        title: c.name || "Customer Entity",
        subtitle: `ID: ${c.id}`,
        statusBadge: "Entity",
        badgeStyle: "bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)] border border-[var(--color-line)]",
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
        badgeStyle: k.status === "ACTIVE"
          ? "bg-[var(--color-forest-soft)] text-[var(--color-forest)] border border-[var(--color-forest)]/20"
          : "bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)] border border-[var(--color-line)]",
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
        statusBadge: `Amd #${amd.amendment_number}`,
        badgeStyle: "bg-[var(--color-sky-soft)] text-[var(--color-sky)] border border-[var(--color-sky)]/20",
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
        badgeStyle: "bg-[var(--color-sky-soft)] text-[var(--color-sky)] border border-[var(--color-sky)]/20",
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
        badgeStyle: "bg-[var(--color-clay-soft)] text-[var(--color-clay)] border border-[var(--color-clay)]/20",
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
        badgeStyle: apr.status === "APPROVED"
          ? "bg-[var(--color-forest-soft)] text-[var(--color-forest)] border border-[var(--color-forest)]/20"
          : "bg-[var(--color-honey-soft)] text-[var(--color-honey)] border border-[var(--color-honey)]/20",
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
        subtitle: inv.amount ? formatAmount(inv.amount, inv.currency || "USD") : "Target Invoice",
        statusBadge: "Target Invoice",
        badgeStyle: "bg-[var(--color-honey-soft)] text-[var(--color-honey)] border border-[var(--color-honey)]/30 font-semibold",
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
        badgeStyle: "bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)] border border-[var(--color-line)]",
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
  const nodeWidth = 200;
  const nodeHeight = 84;
  const colSpacing = 250;
  const rowSpacing = 110;
  const startX = 30;
  const startY = 40;

  const getNodePos = (node: GraphNode) => {
    const x = startX + node.column * colSpacing;
    const y = startY + node.row * rowSpacing;
    return { x, y, cx: x + nodeWidth / 2, cy: y + nodeHeight / 2 };
  };

  const maxCol = Math.max(1, ...nodes.map((n) => n.column));
  const maxRow = Math.max(1, ...nodes.map((n) => n.row));
  const canvasWidth = Math.max(1100, startX * 2 + (maxCol + 1) * colSpacing);
  const canvasHeight = Math.max(340, startY * 2 + (maxRow + 1) * rowSpacing);

  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) : null;

  // Pan interaction handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest(".graph-node-card") || (e.target as HTMLElement).closest("button")) {
      return;
    }
    setIsPanning(true);
    startPanPos.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isPanning) return;
    setPanOffset({
      x: e.clientX - startPanPos.current.x,
      y: e.clientY - startPanPos.current.y,
    });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleFit = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth - 40;
      const fitZoom = Math.min(1, Math.max(0.5, containerWidth / canvasWidth));
      setZoomLevel(fitZoom);
      setPanOffset({ x: 0, y: 0 });
    }
  };

  if (!lineage || nodes.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-8 text-center shadow-xs">
        <h3 className="font-serif text-base font-semibold text-[var(--color-ink)]">Contract History Unavailable</h3>
        <p className="text-xs text-[var(--color-ink-faint)] mt-1 max-w-sm mx-auto">
          No relationship records were found for this invoice.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] shadow-xs overflow-hidden">
      {/* Header bar */}
      <div className="px-5 py-4 border-b border-[var(--color-line)] bg-[var(--color-paper)]/50 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-serif text-base font-semibold text-[var(--color-ink)] tracking-tight">
            Lineage & Contract Governance Graph
          </h3>
          <p className="text-xs text-[var(--color-ink-faint)] mt-0.5 font-sans">
            Visual record pedigree connecting invoice to contracts, amendments, approvals and cited evidence.
          </p>
        </div>

        {/* Pan / Zoom Toolbar */}
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] shadow-2xs overflow-hidden">
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.max(0.5, Number((z - 0.1).toFixed(1))))}
              className="px-2.5 py-1 text-xs text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper)] border-r border-[var(--color-line)] transition font-mono"
              title="Zoom Out"
            >
              −
            </button>
            <span className="px-2.5 py-1 text-[11px] font-mono text-[var(--color-ink-soft)] select-none">
              {Math.round(zoomLevel * 100)}%
            </span>
            <button
              type="button"
              onClick={() => setZoomLevel((z) => Math.min(1.4, Number((z + 0.1).toFixed(1))))}
              className="px-2.5 py-1 text-xs text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper)] border-r border-[var(--color-line)] transition font-mono"
              title="Zoom In"
            >
              +
            </button>
            <button
              type="button"
              onClick={handleFit}
              className="px-2.5 py-1 text-[11px] text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper)] border-r border-[var(--color-line)] transition font-mono"
              title="Fit to Container"
            >
              Fit
            </button>
            <button
              type="button"
              onClick={() => {
                setZoomLevel(1);
                setPanOffset({ x: 0, y: 0 });
              }}
              className="px-2.5 py-1 text-[11px] text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper)] transition font-mono"
              title="Reset Zoom & Pan"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* SVG Canvas Container with interactive Pan & Zoom */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`relative overflow-hidden bg-[var(--color-paper)]/30 p-4 select-none ${
          isPanning ? "cursor-grabbing" : "cursor-grab"
        }`}
        style={{ minHeight: "360px" }}
      >
        <div
          style={{
            transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})`,
            transformOrigin: "top left",
            width: canvasWidth,
            height: canvasHeight,
          }}
          className="transition-transform duration-75 ease-out"
        >
          <svg
            width={canvasWidth}
            height={canvasHeight}
            className="select-none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <marker
                id="nestor-arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="var(--color-line-strong, #cfc2ab)" />
              </marker>
              <marker
                id="nestor-arrowhead-active"
                markerWidth="8"
                markerHeight="6"
                refX="7"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="var(--color-forest, #1f4d3a)" />
              </marker>
            </defs>

            {/* Column Headers */}
            {[
              "Customer Entity",
              "Master Contract",
              "Amendments & SOWs",
              "Approvals & Flags",
              "Target Invoice",
              "Supporting Evidence",
            ].map((header, colIdx) => (
              <text
                key={colIdx}
                x={startX + colIdx * colSpacing + nodeWidth / 2}
                y={20}
                textAnchor="middle"
                className="fill-[var(--color-ink-faint)] text-[11px] font-mono uppercase tracking-wider font-semibold"
              >
                {header}
              </text>
            ))}

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
                    stroke={isEdgeActive ? "var(--color-forest, #1f4d3a)" : "var(--color-line-strong, #cfc2ab)"}
                    strokeWidth={isEdgeActive ? 2.2 : 1.2}
                    markerEnd={isEdgeActive ? "url(#nestor-arrowhead-active)" : "url(#nestor-arrowhead)"}
                  />
                  <rect
                    x={midX - 44}
                    y={midY - 8}
                    width={88}
                    height={16}
                    rx={4}
                    fill="var(--color-card, #fffdf9)"
                    stroke={isEdgeActive ? "var(--color-forest, #1f4d3a)" : "var(--color-line, #e6dccb)"}
                    strokeWidth={1}
                  />
                  <text
                    x={midX}
                    y={midY + 4}
                    textAnchor="middle"
                    className={`text-[9px] font-sans font-medium ${
                      isEdgeActive
                        ? "fill-[var(--color-forest, #1f4d3a)] font-bold"
                        : "fill-[var(--color-ink-soft, #4a564f)]"
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
              const isTargetInvoice = node.type === "invoice";

              return (
                <foreignObject
                  key={node.id}
                  x={pos.x}
                  y={pos.y}
                  width={nodeWidth}
                  height={nodeHeight}
                  className="cursor-pointer overflow-visible graph-node-card"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
                    if (node.type === "evidence" && onSelectEvidence) {
                      onSelectEvidence(node.data as unknown as EvidenceItem);
                    }
                  }}
                >
                  <div
                    className={`h-full w-full rounded-xl border p-2.5 flex flex-col justify-between transition shadow-2xs hover:shadow-md ${
                      isSelected
                        ? "ring-2 ring-[var(--color-forest)] border-[var(--color-forest)] bg-[var(--color-card)]"
                        : isTargetInvoice
                        ? "border-[var(--color-forest)] bg-[var(--color-forest)] text-[var(--color-paper)]"
                        : "border-[var(--color-line)] bg-[var(--color-card)] text-[var(--color-ink)]"
                    }`}
                  >
                    {/* Top Row: Type tag & Status badge */}
                    <div className="flex items-center justify-between gap-1">
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider font-semibold ${
                          isTargetInvoice ? "text-[var(--color-forest-soft)]" : "text-[var(--color-ink-faint)]"
                        }`}
                      >
                        {node.type}
                      </span>

                      {node.statusBadge && (
                        <span
                          className={`text-[9px] px-1.5 py-0.5 rounded font-mono truncate max-w-[95px] ${
                            isTargetInvoice
                              ? "bg-[var(--color-paper)]/15 text-[var(--color-paper)] border border-[var(--color-paper)]/25"
                              : node.badgeStyle || "bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)]"
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
                        className={`text-xs font-serif font-semibold truncate leading-tight ${
                          isTargetInvoice ? "text-[var(--color-paper)]" : "text-[var(--color-ink)]"
                        }`}
                        title={node.title}
                      >
                        {node.title}
                      </div>
                    </div>

                    {/* Bottom: Subtitle / ref */}
                    <div
                      className={`text-[10px] font-mono truncate ${
                        isTargetInvoice ? "text-[var(--color-forest-soft)]" : "text-[var(--color-ink-faint)]"
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
        <div className="p-4 border-t border-[var(--color-line)] bg-[var(--color-paper-deep)]/40 text-xs">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)]">
                  Record Pedigree: {selectedNode.type}
                </span>
                <span className="font-mono text-[var(--color-ink)] font-bold">{selectedNode.id}</span>
                {selectedNode.statusBadge && (
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${selectedNode.badgeStyle}`}>
                    {selectedNode.statusBadge}
                  </span>
                )}
              </div>
              <p className="font-serif text-sm font-semibold text-[var(--color-ink)]">{selectedNode.title}</p>
            </div>

            <button
              type="button"
              onClick={() => setSelectedNodeId(null)}
              className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] p-1 font-bold text-xs"
              title="Close details"
            >
              ✕
            </button>
          </div>

          {/* Properties Grid */}
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[var(--color-card)] p-3 rounded-lg border border-[var(--color-line)] text-xs">
            {Object.entries(selectedNode.data)
              .filter(([k, v]) => v !== null && v !== undefined && typeof v !== "object")
              .slice(0, 8)
              .map(([k, v]) => (
                <div key={k}>
                  <span className="text-[var(--color-ink-faint)] block text-[10px] font-mono uppercase tracking-wider">
                    {k.replace(/_/g, " ")}
                  </span>
                  <span
                    className="text-[var(--color-ink)] font-medium truncate block font-mono text-[11px]"
                    title={String(v)}
                  >
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
