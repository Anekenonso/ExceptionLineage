import React, { useState } from "react";
import { EvidenceItem } from "@/types/investigation";
import { EvidenceDrawer } from "./EvidenceDrawer";

interface EvidenceSectionProps {
  evidence?: EvidenceItem[] | null;
  citedEvidenceIds?: string[];
}

export function EvidenceSection({ evidence, citedEvidenceIds = [] }: EvidenceSectionProps) {
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);

  const items = evidence || [];
  const citedSet = new Set(citedEvidenceIds);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-slate-900 text-white flex items-center justify-center text-[10px] font-mono font-bold">
              EV
            </div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Evidentiary Records
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable contract clauses, amendments, and approvals retrieved by the investigation.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-600 bg-slate-50 px-3 py-1 rounded-md border border-slate-200">
          <span className="font-bold text-slate-900">{items.length}</span> Total Records (
          <span className="text-emerald-700 font-semibold">{citedEvidenceIds.length} Cited</span>)
        </div>
      </div>

      {items.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          No evidentiary records returned for this investigation.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/50 text-slate-500 font-mono text-[11px] uppercase">
                <th className="py-2.5 px-3 font-semibold">Evidence ID</th>
                <th className="py-2.5 px-3 font-semibold">Type</th>
                <th className="py-2.5 px-3 font-semibold">Source</th>
                <th className="py-2.5 px-3 font-semibold">Related Entity</th>
                <th className="py-2.5 px-3 font-semibold">Locator / Scope</th>
                <th className="py-2.5 px-3 font-semibold">Effective Validity</th>
                <th className="py-2.5 px-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((ev) => {
                const isCited = citedSet.has(ev.id);
                return (
                  <tr
                    key={ev.id}
                    className={`hover:bg-slate-50/80 transition cursor-pointer ${
                      isCited ? "bg-emerald-50/15" : ""
                    }`}
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    {/* ID */}
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-slate-900">{ev.id}</span>
                        {isCited && (
                          <span className="text-[9.5px] font-mono px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-semibold">
                            CITED
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Type */}
                    <td className="py-3 px-3 font-mono text-slate-700">
                      {ev.evidence_type}
                    </td>

                    {/* Source */}
                    <td className="py-3 px-3 font-mono text-slate-600">
                      {ev.source}
                    </td>

                    {/* Related Entity */}
                    <td className="py-3 px-3 font-mono font-semibold text-blue-700">
                      {ev.source_id}
                    </td>

                    {/* Locator / Scope */}
                    <td className="py-3 px-3 text-slate-700">
                      <div className="truncate max-w-[200px]" title={ev.locator || ev.scope || "—"}>
                        {ev.locator || ev.scope || "—"}
                      </div>
                    </td>

                    {/* Effective Dates */}
                    <td className="py-3 px-3 font-mono text-slate-600">
                      {ev.effective_from ? new Date(ev.effective_from).toLocaleDateString() : "—"}{" "}
                      →{" "}
                      {ev.effective_until ? new Date(ev.effective_until).toLocaleDateString() : "Open"}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEvidence(ev);
                        }}
                        className="text-xs text-blue-600 hover:text-blue-900 font-medium font-mono"
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        evidence={selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}
