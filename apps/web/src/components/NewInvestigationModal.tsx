"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { createInvestigation } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

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

  const demoCases = [
    {
      invoice: "INV-1001",
      exception: "EX-001",
      customer: "Acme Global Enterprise",
      title: "Rate adjustment with approved variance",
      status: "VERIFIED",
    },
    {
      invoice: "INV-1002",
      exception: "EX-002",
      customer: "Acme Global Enterprise",
      title: "Surcharge variance with missing approval evidence",
      status: "INSUFFICIENT_EVIDENCE",
    },
    {
      invoice: "INV-1003",
      exception: "EX-003",
      customer: "Acme Global Enterprise",
      title: "Rate discrepancy exceeding contract threshold",
      status: "NOT_VERIFIED",
    },
    {
      invoice: "INV-1004",
      exception: "EX-004",
      customer: "Acme Global Enterprise",
      title: "Expired contractual rate & unapproved variance",
      status: "NOT_VERIFIED",
    },
    {
      invoice: "INV-1005",
      exception: "EX-005",
      customer: "Acme Global Enterprise",
      title: "Conflicting amendment & SOW terms",
      status: "NEEDS_REVIEW",
    },
    {
      invoice: "INV-1006",
      exception: "EX-006",
      customer: "Acme Global Enterprise",
      title: "Duplicate submission with modified terms",
      status: "NOT_VERIFIED",
    },
    {
      invoice: "INV-1007",
      exception: "EX-007",
      customer: "Beta Logistics Corp",
      title: "Missing governing master contract",
      status: "INSUFFICIENT_EVIDENCE",
    },
    {
      invoice: "INV-1008",
      exception: "EX-008",
      customer: "Beta Logistics Corp",
      title: "Amended multi-tier SOW with recorded VP approval",
      status: "VERIFIED",
    },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceId.trim()) {
      setError("Please provide an invoice number.");
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
      const msg = err instanceof Error ? err.message : "Failed to review invoice";
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
              Review an invoice
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter an invoice to understand why it was flagged and check the supporting records.
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

        {/* Demo Cases */}
        <div>
          <span className="text-xs font-semibold text-slate-700 block mb-2">
            Try a demo case
          </span>
          <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-1">
            {demoCases.map((sc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => selectPreset(sc.invoice, sc.exception)}
                className={`p-2.5 rounded-lg border text-left text-xs transition flex items-center justify-between gap-3 ${
                  invoiceId === sc.invoice
                    ? "border-slate-900 bg-slate-50 ring-1 ring-slate-900"
                    : "border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300"
                }`}
              >
                <div>
                  <div className="flex items-center gap-1.5 font-semibold text-slate-900">
                    <span className="font-mono">{sc.invoice}</span>
                    <span className="text-slate-400 font-normal">·</span>
                    <span className="text-slate-700 font-normal">{sc.customer}</span>
                  </div>
                  <div className="text-[11.5px] text-slate-500 mt-0.5">{sc.title}</div>
                </div>

                <div className="shrink-0">
                  <StatusBadge status={sc.status} size="sm" />
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Manual Form */}
        <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-slate-100">
          <div>
            <label htmlFor="invoice-id" className="block text-xs font-semibold text-slate-700 mb-1">
              Invoice number *
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
              Exception or flag reference (Optional)
            </label>
            <input
              id="exception-id"
              type="text"
              placeholder="e.g. EX-001 or Rate variance"
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
              <span>{loading ? "Reviewing invoice…" : "Start review"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
