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
    <div id="evidence" className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Supporting records
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Records used to reach this finding.
          </p>
        </div>

        <div className="text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
          <span className="font-semibold text-slate-900">{items.length}</span> records found (
          <span className="text-emerald-700 font-semibold">{citedEvidenceIds.length} cited in checks</span>)
        </div>
      </div>

      {items.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No supporting records returned for this investigation.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/60 text-slate-500 text-[11px] font-medium">
                <th className="py-2.5 px-3">Record</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Source & Section</th>
                <th className="py-2.5 px-3">Effective Date</th>
                <th className="py-2.5 px-3">Excerpt Preview</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((ev) => {
                const isCited = citedSet.has(ev.id);
                const recordTitle = ev.title || ev.evidence_type.replace(/_/g, " ");
                const dateDisplay =
                  ev.effective_from || ev.effective_until
                    ? `${ev.effective_from ? new Date(ev.effective_from).toLocaleDateString() : "Open"} → ${
                        ev.effective_until ? new Date(ev.effective_until).toLocaleDateString() : "Present"
                      }`
                    : "—";

                return (
                  <tr
                    key={ev.id}
                    className={`hover:bg-slate-50/80 transition cursor-pointer ${
                      isCited ? "bg-emerald-50/15" : ""
                    }`}
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    {/* Record Title & ID */}
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900">{recordTitle}</span>
                        {isCited && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">
                            Cited
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
                        {ev.id}
                      </span>
                    </td>

                    {/* Record Type */}
                    <td className="py-3 px-3 text-slate-700 capitalize">
                      {ev.evidence_type.toLowerCase().replace(/_/g, " ")}
                    </td>

                    {/* Source & Locator */}
                    <td className="py-3 px-3 text-slate-800">
                      <div className="font-medium text-slate-900">
                        {ev.source_id || ev.source}
                      </div>
                      {ev.locator && (
                        <div className="text-[11px] text-slate-500 truncate max-w-[180px]">
                          {ev.locator}
                        </div>
                      )}
                    </td>

                    {/* Dates */}
                    <td className="py-3 px-3 text-slate-600 text-[11px]">
                      {dateDisplay}
                    </td>

                    {/* Excerpt */}
                    <td className="py-3 px-3 text-slate-600">
                      <div className="truncate max-w-[260px] italic text-[11.5px]" title={ev.excerpt || ""}>
                        {ev.excerpt ? `"${ev.excerpt}"` : "—"}
                      </div>
                    </td>

                    {/* Action */}
                    <td className="py-3 px-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEvidence(ev);
                        }}
                        className="text-xs text-slate-700 hover:text-slate-900 font-semibold"
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
