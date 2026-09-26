"use client";

import React from "react";
import { EvidenceItem } from "@/types/investigation";

interface EvidenceDrawerProps {
  evidence: EvidenceItem | null;
  onClose: () => void;
}

export function EvidenceDrawer({ evidence, onClose }: EvidenceDrawerProps) {
  if (!evidence) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex justify-end bg-[var(--color-ink)]/40 backdrop-blur-xs transition"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-[var(--color-card)] h-full shadow-2xl flex flex-col border-l border-[var(--color-line)] overflow-y-auto animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="p-5 border-b border-[var(--color-line)] bg-[var(--color-paper)]/70 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[var(--color-forest)]">
                Supporting Record
              </span>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-[var(--color-paper-deep)] text-[var(--color-ink)] border border-[var(--color-line)]">
                {evidence.id}
              </span>
            </div>
            <h3 className="font-serif text-lg font-bold text-[var(--color-ink)] mt-1 tracking-tight">
              {evidence.title || evidence.evidence_type.replace(/_/g, " ")}
            </h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] p-1 rounded-lg hover:bg-[var(--color-paper-deep)] transition"
            aria-label="Close drawer"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drawer Body */}
        <div className="p-6 space-y-6 text-xs text-[var(--color-ink-soft)] flex-1">
          {/* Excerpt / Clause Content */}
          {evidence.excerpt && (
            <div>
              <span className="font-mono text-[10px] uppercase tracking-wider font-semibold text-[var(--color-ink-faint)] block mb-1.5">
                Verbatim Clause / Excerpt
              </span>
              <div className="p-4 rounded-xl bg-[var(--color-paper)] border border-[var(--color-line)] text-[var(--color-ink)] font-serif leading-relaxed italic text-sm shadow-inner">
                &ldquo;{evidence.excerpt}&rdquo;
              </div>
            </div>
          )}

          {/* Properties Table */}
          <div className="space-y-3">
            <span className="font-mono text-[10px] uppercase tracking-wider font-semibold text-[var(--color-ink-faint)] block">
              Source & Pedigree
            </span>

            <dl className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-[var(--color-paper)]/40 border border-[var(--color-line)] text-xs">
              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Record ID</dt>
                <dd className="font-mono font-bold text-[var(--color-ink)] mt-0.5">{evidence.id}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Record Type</dt>
                <dd className="text-[var(--color-ink)] mt-0.5 capitalize font-mono">{evidence.evidence_type.replace(/_/g, " ")}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Document / Source</dt>
                <dd className="font-mono text-[var(--color-ink)] mt-0.5">{evidence.source}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Related Entity Ref</dt>
                <dd className="font-mono font-semibold text-[var(--color-sky)] mt-0.5">{evidence.source_id}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Document Section</dt>
                <dd className="text-[var(--color-ink)] font-mono mt-0.5">{evidence.locator || "—"}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Scope</dt>
                <dd className="text-[var(--color-ink)] mt-0.5">{evidence.scope || "—"}</dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Effective From</dt>
                <dd className="text-[var(--color-ink)] font-mono mt-0.5">
                  {evidence.effective_from ? new Date(evidence.effective_from).toLocaleDateString() : "—"}
                </dd>
              </div>

              <div>
                <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Effective Until</dt>
                <dd className="text-[var(--color-ink)] font-mono mt-0.5">
                  {evidence.effective_until ? new Date(evidence.effective_until).toLocaleDateString() : "Active / Open"}
                </dd>
              </div>

              {evidence.confidence !== undefined && evidence.confidence !== null && (
                <div>
                  <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Confidence</dt>
                  <dd className="font-mono text-[var(--color-forest)] font-bold mt-0.5">{(evidence.confidence * 100).toFixed(0)}%</dd>
                </div>
              )}

              {evidence.captured_at && (
                <div>
                  <dt className="text-[var(--color-ink-faint)] font-mono text-[10px] uppercase">Timestamp</dt>
                  <dd className="font-mono text-[var(--color-ink-faint)] mt-0.5 text-[11px]">
                    {new Date(evidence.captured_at).toISOString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-[var(--color-line)] bg-[var(--color-paper)]/60 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-[var(--color-ink)] text-[var(--color-paper)] font-mono text-xs font-semibold hover:opacity-90 transition shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
