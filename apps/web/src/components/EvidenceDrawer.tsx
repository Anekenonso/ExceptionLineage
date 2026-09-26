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
      className="fixed inset-0 z-50 flex justify-end bg-slate-900/30 backdrop-blur-xs transition"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Supporting Record
              </span>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                {evidence.id}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 mt-1">
              {evidence.title || evidence.evidence_type.replace(/_/g, " ")}
            </h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded-md"
            aria-label="Close drawer"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drawer Body */}
        <div className="p-6 space-y-6 text-xs text-slate-700 flex-1">
          {/* Excerpt / Clause Content */}
          {evidence.excerpt && (
            <div>
              <span className="font-semibold text-slate-900 text-xs block mb-2">
                Verbatim Clause / Record Excerpt
              </span>
              <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 font-serif leading-relaxed italic text-[13px]">
                “{evidence.excerpt}”
              </div>
            </div>
          )}

          {/* Properties Table */}
          <div className="space-y-3">
            <span className="font-semibold text-slate-900 text-xs block">
              Source & Provenance
            </span>

            <dl className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-slate-50/60 border border-slate-200 text-xs">
              <div>
                <dt className="text-slate-500 font-medium">Record ID</dt>
                <dd className="font-mono font-semibold text-slate-900 mt-0.5">{evidence.id}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Record Type</dt>
                <dd className="text-slate-900 mt-0.5 capitalize">{evidence.evidence_type.replace(/_/g, " ")}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Document / Source</dt>
                <dd className="font-mono text-slate-900 mt-0.5">{evidence.source}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Related Entity Ref</dt>
                <dd className="font-mono font-semibold text-blue-700 mt-0.5">{evidence.source_id}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Document Section</dt>
                <dd className="text-slate-900 mt-0.5">{evidence.locator || "—"}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Scope</dt>
                <dd className="text-slate-900 mt-0.5">{evidence.scope || "—"}</dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Effective From</dt>
                <dd className="text-slate-900 mt-0.5">
                  {evidence.effective_from ? new Date(evidence.effective_from).toLocaleDateString() : "—"}
                </dd>
              </div>

              <div>
                <dt className="text-slate-500 font-medium">Effective Until</dt>
                <dd className="text-slate-900 mt-0.5">
                  {evidence.effective_until ? new Date(evidence.effective_until).toLocaleDateString() : "Active / Open"}
                </dd>
              </div>

              {evidence.confidence !== undefined && evidence.confidence !== null && (
                <div>
                  <dt className="text-slate-500 font-medium">Confidence</dt>
                  <dd className="font-mono text-slate-900 mt-0.5">{(evidence.confidence * 100).toFixed(0)}%</dd>
                </div>
              )}

              {evidence.captured_at && (
                <div>
                  <dt className="text-slate-500 font-medium">Timestamp</dt>
                  <dd className="font-mono text-slate-700 mt-0.5 text-[11px]">
                    {new Date(evidence.captured_at).toISOString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-md bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
