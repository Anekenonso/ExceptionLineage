"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { createInvestigation, uploadTestCase, fetchTestCaseTemplate } from "@/lib/api";
import { storeEphemeralInvestigation } from "@/lib/ephemeralStore";
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
  const [activeTab, setActiveTab] = useState<"demo" | "custom">("demo");
  const [invoiceId, setInvoiceId] = useState("");
  const [exceptionId, setExceptionId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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

  const handleDemoSubmit = async (e: React.FormEvent) => {
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

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a .json case file to evaluate.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await uploadTestCase(selectedFile);
      storeEphemeralInvestigation(res);
      setLoading(false);
      onClose();
      if (onCreated) {
        onCreated(res.investigation_id);
      } else {
        router.push(`/investigations/${res.investigation_id}`);
      }
    } catch (err: unknown) {
      setLoading(false);
      const msg = err instanceof Error ? err.message : "Failed to evaluate custom case";
      setError(msg);
    }
  };

  const selectPreset = (inv: string, exc: string) => {
    setInvoiceId(inv);
    setExceptionId(exc);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);
    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Invalid file format. Only strictly .json case files are accepted.");
      return;
    }
    if (file.size > 1024 * 1024) {
      setError(`File size exceeds 1 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB).`);
      return;
    }
    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleDownloadTemplate = async () => {
    setDownloadingTemplate(true);
    setError(null);
    try {
      const template = await fetchTestCaseTemplate();
      const blob = new Blob([JSON.stringify(template, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sample_test_case.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download sample template");
    } finally {
      setDownloadingTemplate(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Start an Investigation
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Review canonical benchmark invoices or test your own independent JSON case.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded-md hover:bg-slate-100 transition"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-lg bg-slate-100 p-1 text-xs font-medium text-slate-600">
          <button
            type="button"
            onClick={() => {
              setActiveTab("demo");
              setError(null);
            }}
            className={`flex-1 py-1.5 px-3 rounded-md transition text-center ${
              activeTab === "demo"
                ? "bg-white text-slate-900 font-semibold shadow-xs"
                : "hover:text-slate-900"
            }`}
          >
            Demo Benchmark Cases
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("custom");
              setError(null);
            }}
            className={`flex-1 py-1.5 px-3 rounded-md transition text-center flex items-center justify-center gap-1.5 ${
              activeTab === "custom"
                ? "bg-white text-slate-900 font-semibold shadow-xs"
                : "hover:text-slate-900"
            }`}
          >
            <span>Test Your Own Case</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-mono">
              JSON
            </span>
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

        {/* TAB 1: DEMO CASES */}
        {activeTab === "demo" && (
          <div className="space-y-4">
            <div>
              <span className="text-xs font-semibold text-slate-700 block mb-2">
                Select a benchmark scenario
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
            <form onSubmit={handleDemoSubmit} className="space-y-3 pt-2 border-t border-slate-100">
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
        )}

        {/* TAB 2: TEST YOUR OWN CASE */}
        {activeTab === "custom" && (
          <form onSubmit={handleCustomSubmit} className="space-y-4">
            {/* Overview & Security Badge */}
            <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200/80 text-xs text-emerald-950 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-emerald-900 flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-emerald-700" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                  Isolated Ephemeral Sandbox
                </span>
                <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                  Zero Persistence
                </span>
              </div>
              <p className="text-[11.5px] text-emerald-800 leading-relaxed">
                Test custom invoice lineage against the validation engine. Case data is evaluated in memory and discarded upon completion—never stored in any database or file system.
              </p>
            </div>

            {/* Template Download Option */}
            <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
              <div>
                <div className="font-semibold text-slate-800">Need a schema template?</div>
                <div className="text-[11px] text-slate-500">
                  Mandatory: <span className="font-mono text-slate-700">invoice</span>. Optional: <span className="font-mono text-slate-700">customer, contract, exception, amendments, sows, evidence, approval</span>.
                </div>
              </div>
              <button
                type="button"
                onClick={handleDownloadTemplate}
                disabled={downloadingTemplate}
                className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-300 bg-white font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition text-[11px] shadow-2xs"
              >
                {downloadingTemplate ? (
                  <span>Downloading…</span>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                    <span>Download Template</span>
                  </>
                )}
              </button>
            </div>

            {/* Dropzone Area */}
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                onChange={handleFileChange}
                className="hidden"
              />

              {!selectedFile ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center gap-2 ${
                    isDragging
                      ? "border-slate-900 bg-slate-50/80 scale-[1.01]"
                      : "border-slate-300 hover:border-slate-400 bg-slate-50/40 hover:bg-slate-50"
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.8" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-slate-900 block">
                      Choose a JSON case file, or drag and drop
                    </span>
                    <span className="text-[11px] text-slate-500 mt-0.5 block">
                      Strictly .json format up to 1 MB
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 rounded-lg border border-slate-300 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-emerald-100 text-emerald-800 flex items-center justify-center font-mono font-bold text-xs">
                      JSON
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 font-mono">
                        {selectedFile.name}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {formatFileSize(selectedFile.size)}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="text-xs text-rose-600 hover:text-rose-800 font-semibold px-2 py-1 rounded hover:bg-rose-50 transition"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
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
                disabled={loading || !selectedFile}
                className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 disabled:opacity-50 transition"
              >
                {loading && (
                  <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                )}
                <span>{loading ? "Evaluating in sandbox…" : "Run Test Case"}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
