"use client";

import React, { useState } from "react";
import { InvestigationResponse, InvestigationEvidenceTrace } from "@/types/investigation";
import {
  getStatusLabel,
  getValidationStatusLabel,
  formatCheckName,
  formatAmount,
  formatDateTime,
} from "@/lib/formatters";

interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  investigation: InvestigationResponse;
  trace?: InvestigationEvidenceTrace | null;
}

export function ExportReportModal({
  isOpen,
  onClose,
  investigation,
  trace,
}: ExportReportModalProps) {
  const [copied, setCopied] = useState(false);
  const [format, setFormat] = useState<"markdown" | "csv" | "json">("markdown");

  if (!isOpen) return null;

  const markdownReport = `# ExceptionLineage Investigation Audit Report

- **Invoice**: ${investigation.invoice_id}
- **Customer**: ${investigation.customer_name || investigation.customer_id || "Unavailable"}
- **Amount**: ${formatAmount(investigation.amount, investigation.currency || "USD")}
- **Finding**: ${getStatusLabel(investigation.status)}
- **Date**: ${formatDateTime(investigation.created_at)}
- **Investigation Ref**: ${investigation.investigation_id}
- **Supporting Records Cited**: ${investigation.cited_evidence_ids?.join(", ") || "None"}

---

## Finding & Summary
${investigation.summary || "No summary recorded."}
${investigation.failure_reason ? `\n**Auditor Notes / Discrepancy Context**:\n${investigation.failure_reason}` : ""}

---

## Verification Checks
${
  investigation.validation_results && investigation.validation_results.length > 0
    ? investigation.validation_results
        .map(
          (r) =>
            `- [${getValidationStatusLabel(r.status)}] **${formatCheckName(r.check_name)}**: ${r.message || "Evaluated"} ${
              r.evidence_ids && r.evidence_ids.length > 0
                ? `(Citations: ${r.evidence_ids.join(", ")})`
                : ""
            }`
        )
        .join("\n")
    : "No verification checks recorded."
}

---

## Contract Lineage & Pedigree
- **Governing Contract**: ${investigation.lineage?.contract?.title || investigation.lineage?.contract?.id || "None"}
- **Amendments**: ${investigation.lineage?.amendments?.map((a) => a.id).join(", ") || "None"}
- **SOWs**: ${investigation.lineage?.sows?.map((s) => s.id).join(", ") || "None"}
- **Operational Approval**: ${investigation.lineage?.approval?.status || "None"} (${investigation.lineage?.approval?.approver || "—"})

---

## Supporting Evidentiary Records
${
  investigation.lineage?.evidence && investigation.lineage.evidence.length > 0
    ? investigation.lineage.evidence
        .map(
          (ev) =>
            `### Record ${ev.id}: ${ev.title || ev.evidence_type}
- **Type**: ${ev.evidence_type}
- **Source**: ${ev.source} (ID: ${ev.source_id})
- **Locator / Section**: ${ev.locator || "—"}
- **Excerpt**: "${ev.excerpt || "—"}"`
        )
        .join("\n\n")
    : "No supporting records returned in lineage."
}

---
*Report certified by ExceptionLineage — Deterministic Contract & Billing Verification Engine.*
`;

  // CSV Reconciliation Report
  const csvReport = [
    ["Invoice ID", "Customer", "Check Name", "Status", "Message", "Cited Evidence", "Timestamp"].map((h) => `"${h}"`).join(","),
    ...(investigation.validation_results || []).map((r) =>
      [
        investigation.invoice_id,
        investigation.customer_name || investigation.customer_id || "Unavailable",
        formatCheckName(r.check_name),
        getValidationStatusLabel(r.status),
        (r.message || "").replace(/"/g, '""'),
        (r.evidence_ids || []).join("; "),
        investigation.created_at || "",
      ]
        .map((cell) => `"${cell}"`)
        .join(",")
    ),
  ].join("\n");

  const jsonReport = JSON.stringify(
    {
      investigation,
      trace,
      exported_at: new Date().toISOString(),
    },
    null,
    2
  );

  const getActiveContent = () => {
    switch (format) {
      case "markdown":
        return markdownReport;
      case "csv":
        return csvReport;
      case "json":
        return jsonReport;
    }
  };

  const activeContent = getActiveContent();

  const handleCopy = () => {
    navigator.clipboard.writeText(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const extensions = {
      markdown: "md",
      csv: "csv",
      json: "json",
    };
    const mimeTypes = {
      markdown: "text/markdown",
      csv: "text/csv",
      json: "application/json",
    };
    const filename = `audit-report-${investigation.invoice_id}.${extensions[format]}`;
    const blob = new Blob([activeContent], { type: mimeTypes[format] });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="export-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
    >
      {/* Dimmed backdrop */}
      <div
        className="fixed inset-0 bg-[var(--color-ink)]/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        className="relative w-full max-w-2xl rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] p-6 shadow-2xl space-y-4 z-10 animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between pb-3 border-b border-[var(--color-line)]">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-forest)]">
              Formal Audit Record
            </span>
            <h2 id="export-modal-title" className="font-serif text-xl font-bold text-[var(--color-ink)] tracking-tight">
              Export Investigation Report
            </h2>
            <p className="text-xs text-[var(--color-ink-faint)] mt-0.5 font-mono">
              Invoice #{investigation.invoice_id} &middot; Ref: {investigation.investigation_id}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] p-1 rounded-lg hover:bg-[var(--color-paper-deep)] transition"
            aria-label="Close export dialog"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Format Selector Pills + Print Button */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-[var(--color-paper-deep)]/60 border border-[var(--color-line)]">
            <button
              type="button"
              onClick={() => setFormat("markdown")}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition ${
                format === "markdown"
                  ? "bg-[var(--color-card)] text-[var(--color-ink)] shadow-2xs font-bold"
                  : "text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]"
              }`}
            >
              Markdown (.md)
            </button>
            <button
              type="button"
              onClick={() => setFormat("csv")}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition ${
                format === "csv"
                  ? "bg-[var(--color-card)] text-[var(--color-ink)] shadow-2xs font-bold"
                  : "text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]"
              }`}
            >
              CSV Ledger (.csv)
            </button>
            <button
              type="button"
              onClick={() => setFormat("json")}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition ${
                format === "json"
                  ? "bg-[var(--color-card)] text-[var(--color-ink)] shadow-2xs font-bold"
                  : "text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]"
              }`}
            >
              JSON Raw (.json)
            </button>
          </div>

          {/* Quick Print Action */}
          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] text-xs font-mono font-medium text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)] transition shadow-2xs"
            title="Print or Save as PDF"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print / Save PDF
          </button>
        </div>

        {/* Content Preview */}
        <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)] p-3.5 max-h-80 overflow-y-auto font-mono text-[11px] text-[var(--color-ink)] whitespace-pre-wrap leading-relaxed shadow-inner">
          {activeContent}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-[var(--color-line)] text-xs">
          <span className="text-[var(--color-ink-faint)] font-mono text-[11px]">
            {activeContent.length.toLocaleString()} characters &middot; UTF-8
          </span>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3.5 py-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] text-[var(--color-ink)] hover:bg-[var(--color-paper)] font-mono text-xs font-medium transition shadow-2xs"
            >
              {copied ? "✓ Copied" : "Copy to Clipboard"}
            </button>
            <button
              type="button"
              onClick={handleDownload}
              className="px-4 py-2 rounded-lg bg-[var(--color-forest)] text-[var(--color-paper)] font-mono text-xs font-semibold hover:opacity-90 transition shadow-2xs"
            >
              Download {format.toUpperCase()}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
