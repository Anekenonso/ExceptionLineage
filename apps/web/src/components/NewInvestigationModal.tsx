"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { createInvestigation } from "@/lib/api";

interface NewInvestigationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (investigationId: string) => void;
}

export function NewInvestigationModal({
  isOpen,
  onClose,
  onCreated,
}: NewInvestigationModalProps) {
  const router = useRouter();
  const [invoiceId, setInvoiceId] = useState("");
  const [exceptionId, setExceptionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const standardScenarios = [
    {
      invoice: "INV-1001",
      exception: "EX-001",
      customer: "Acme Global Enterprise Inc.",
      title: "Rate Adjustment with Approved Variance (Flagship)",
      outcome: "VERIFIED",
      outcomeBadge: "bg-emerald-100 text-emerald-800",
    },
    {
      invoice: "INV-1002",
      exception: "EX-002",
      customer: "Acme Global Enterprise Inc.",
      title: "Surcharge Variance with Missing Approval Evidence",
      outcome: "INSUFFICIENT EVIDENCE",
      outcomeBadge: "bg-amber-100 text-amber-800",
    },
    {
      invoice: "INV-1003",
      exception: "EX-003",
      customer: "Acme Global Enterprise Inc.",
      title: "Rate Discrepancy Exceeding Allowable Threshold",
      outcome: "NOT VERIFIED",
      outcomeBadge: "bg-rose-100 text-rose-800",
    },
    {
      invoice: "INV-1004",
      exception: "EX-004",
      customer: "Acme Global Enterprise Inc.",
      title: "Expired Contractual Rate & Unauthorized Variance",
      outcome: "NOT VERIFIED",
      outcomeBadge: "bg-rose-100 text-rose-800",
    },
    {
      invoice: "INV-1005",
      exception: "EX-005",
      customer: "Acme Global Enterprise Inc.",
      title: "Conflicting Amendment & SOW Terms",
      outcome: "NEEDS REVIEW",
      outcomeBadge: "bg-purple-100 text-purple-800",
    },
    {
      invoice: "INV-1006",
      exception: "EX-006",
      customer: "Acme Global Enterprise Inc.",
      title: "Duplicate Invoice Submission with Modified Terms",
      outcome: "NOT VERIFIED",
      outcomeBadge: "bg-rose-100 text-rose-800",
    },
    {
      invoice: "INV-1007",
      exception: "EX-007",
      customer: "Beta Logistics Corp",
      title: "Orphaned Invoice Missing Governing Contract",
      outcome: "INSUFFICIENT EVIDENCE",
      outcomeBadge: "bg-amber-100 text-amber-800",
    },
    {
      invoice: "INV-1008",
      exception: "EX-008",
      customer: "Beta Logistics Corp",
      title: "Amended Multi-Tier SOW with Verified VP Approval",
      outcome: "VERIFIED",
      outcomeBadge: "bg-emerald-100 text-emerald-800",
    },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceId.trim()) {
      setError("Please provide an Invoice ID.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await createInvestigation(invoiceId, exceptionId || null);
      setLoading(false);
      onClose();
      if (onCreated) {
        onCreated(res.investigation_id);
      } else {
        router.push(`/investigations/${res.investigation_id}`);
      }
    } catch (err: unknown) {
      setLoading(false);
      const msg = err instanceof Error ? err.message : "Failed to run investigation";
      setError(msg);
    }
  };

  const selectPreset = (inv: string, exc: string) => {
    setInvoiceId(inv);
    setExceptionId(exc);
    setError(null);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-2xl space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Initiate Investigation
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Execute agentic discovery and deterministic contractual validation.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-rose-500 hover:text-rose-800 ml-2 font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* Quick Presets */}
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold block mb-2">
            Target Dataset Scenarios
          </span>
          <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-1">
            {standardScenarios.map((sc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => selectPreset(sc.invoice, sc.exception)}
                className={`p-2.5 rounded-lg border text-left text-xs transition flex items-center justify-between gap-2 ${
                  invoiceId === sc.invoice
                    ? "border-blue-500 bg-blue-50/40 ring-1 ring-blue-500"
                    : "border-slate-200 bg-slate-50/50 hover:bg-slate-100 hover:border-slate-300"
                }`}
              >
                <div>
                  <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-slate-900">
                    <span>{sc.invoice}</span>
                    {sc.exception && <span className="text-slate-400">/ {sc.exception}</span>}
                  </div>
                  <div className="text-[11.5px] text-slate-600 font-medium">{sc.title}</div>
                </div>

                <span
                  className={`text-[9.5px] font-mono px-2 py-0.5 rounded font-semibold shrink-0 ${sc.outcomeBadge}`}
                >
                  {sc.outcome}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Manual Form */}
        <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-slate-100">
          <div>
            <label htmlFor="invoice-id" className="block text-xs font-semibold text-slate-700 mb-1">
              Target Invoice ID *
            </label>
            <input
              id="invoice-id"
              type="text"
              required
              placeholder="e.g. INV-1001"
              value={invoiceId}
              onChange={(e) => setInvoiceId(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-xs font-mono text-slate-900 focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 shadow-2xs"
            />
          </div>

          <div>
            <label htmlFor="exception-id" className="block text-xs font-semibold text-slate-700 mb-1">
              Transaction Exception ID (Optional)
            </label>
            <input
              id="exception-id"
              type="text"
              placeholder="e.g. EX-001"
              value={exceptionId}
              onChange={(e) => setExceptionId(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-xs font-mono text-slate-900 focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 shadow-2xs"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-slate-900 rounded-md border border-slate-200 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !invoiceId.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 disabled:opacity-50 transition"
            >
              {loading && (
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              <span>{loading ? "Running Pipeline…" : "Execute Investigation"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
