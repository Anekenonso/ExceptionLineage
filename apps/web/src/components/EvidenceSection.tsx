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
    <div id="evidence" className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[var(--color-line)] gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)]">
            Evidentiary Pedigree
          </span>
          <h3 className="font-serif text-base font-bold text-[var(--color-ink)] tracking-tight">
            Supporting Records
          </h3>
          <p className="text-xs text-[var(--color-ink-faint)] mt-0.5">
            Documentary evidence, contract excerpts and approvals cited during verification
          </p>
        </div>

        <div className="text-xs font-mono text-[var(--color-ink-soft)] bg-[var(--color-paper)] px-3 py-1.5 rounded-lg border border-[var(--color-line)]">
          <span className="font-bold text-[var(--color-ink)]">{items.length}</span> records (
          <span className="text-[var(--color-forest)] font-semibold">{citedEvidenceIds.length} cited in findings</span>)
        </div>
      </div>

      {items.length === 0 ? (
        <div className="py-8 text-center text-xs font-mono text-[var(--color-ink-faint)]">
          No supporting records returned for this investigation.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--color-line)]">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-paper)]/70 text-[var(--color-ink-faint)] font-mono text-[10px] uppercase tracking-wider">
                <th className="py-3 px-3.5">Record</th>
                <th className="py-3 px-3.5">Type</th>
                <th className="py-3 px-3.5">Source & Locator</th>
                <th className="py-3 px-3.5">Effective Date</th>
                <th className="py-3 px-3.5">Excerpt Preview</th>
                <th className="py-3 px-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-line)] bg-[var(--color-card)]">
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
                    className={`hover:bg-[var(--color-paper)]/50 transition cursor-pointer ${
                      isCited ? "bg-[var(--color-forest-soft)]/20" : ""
                    }`}
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    {/* Record Title & ID */}
                    <td className="py-3 px-3.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[var(--color-ink)]">{recordTitle}</span>
                        {isCited && (
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-forest-soft)] text-[var(--color-forest)] border border-[var(--color-forest)]/20 font-bold">
                            Cited
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-[var(--color-ink-faint)] font-mono block mt-0.5">
                        {ev.id}
                      </span>
                    </td>

                    {/* Record Type */}
                    <td className="py-3 px-3.5 text-[var(--color-ink-soft)] font-mono text-[11px] capitalize">
                      {ev.evidence_type.toLowerCase().replace(/_/g, " ")}
                    </td>

                    {/* Source & Locator */}
                    <td className="py-3 px-3.5 text-[var(--color-ink)]">
                      <div className="font-mono text-xs font-semibold">
                        {ev.source_id || ev.source}
                      </div>
                      {ev.locator && (
                        <div className="text-[11px] text-[var(--color-ink-faint)] font-mono truncate max-w-[180px]">
                          {ev.locator}
                        </div>
                      )}
                    </td>

                    {/* Dates */}
                    <td className="py-3 px-3.5 text-[var(--color-ink-soft)] font-mono text-[11px]">
                      {dateDisplay}
                    </td>

                    {/* Excerpt */}
                    <td className="py-3 px-3.5 text-[var(--color-ink-soft)]">
                      <div className="truncate max-w-[260px] italic font-serif text-xs" title={ev.excerpt || ""}>
                        {ev.excerpt ? `"${ev.excerpt}"` : "—"}
                      </div>
                    </td>

                    {/* Action */}
                    <td className="py-3 px-3.5 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEvidence(ev);
                        }}
                        className="text-xs font-mono font-medium text-[var(--color-forest)] hover:underline"
                      >
                        Inspect &rarr;
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
