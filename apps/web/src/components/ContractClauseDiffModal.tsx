"use client";

import React, { useEffect } from "react";
import { formatAmount, formatVariance } from "@/lib/formatters";

export interface ClauseDiffData {
  clauseSection: string;
  clauseTitle: string;
  agreedRate: number;
  agreedUnit?: string;
  effectiveDate?: string;
  agreedScope: string;
  itemCode: string;
  itemDescription: string;
  billedRate: number;
  billedQuantity?: number;
  billedTotal: number;
  currency?: string;
  invoiceDate?: string;
  ruleTriggered?: string;
  reasonNotes?: string;
}

interface ContractClauseDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  diffData: ClauseDiffData | null;
}

export function ContractClauseDiffModal({
  isOpen,
  onClose,
  diffData,
}: ContractClauseDiffModalProps) {
  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !diffData) return null;

  const currency = diffData.currency || "USD";
  const variance = formatVariance(diffData.billedRate, diffData.agreedRate, currency);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="clause-diff-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
    >
      {/* Dimmed backdrop */}
      <div
        className="fixed inset-0 bg-[var(--color-ink)]/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-3xl rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] shadow-2xl overflow-hidden z-10 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-5 border-b border-[var(--color-line)] bg-[var(--color-paper)]/70 flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-[var(--color-clay-soft)] text-[var(--color-clay)] border border-[var(--color-clay)]/20">
                Discrepancy Analysis
              </span>
              <span className="font-mono text-xs text-[var(--color-ink-faint)]">
                {diffData.ruleTriggered || "Pricing Schedule Reconciliation"}
              </span>
            </div>
            <h2 id="clause-diff-title" className="font-serif text-xl font-bold text-[var(--color-ink)]">
              Contract Clause vs Billed Discrepancy
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)] transition"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Variance Summary Banner */}
        <div className="px-6 py-4 border-b border-[var(--color-line)] bg-[var(--color-paper)]/30 flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-ink-faint)] block">
              Calculated Rate Variance
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span
                className={`font-serif text-2xl font-bold ${
                  variance.isOver ? "text-[var(--color-clay)]" : "text-[var(--color-forest)]"
                }`}
              >
                {variance.formattedDiff}
              </span>
              <span
                className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded ${
                  variance.isOver
                    ? "bg-[var(--color-clay-soft)] text-[var(--color-clay)]"
                    : "bg-[var(--color-forest-soft)] text-[var(--color-forest)]"
                }`}
              >
                {variance.percentChange}
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-ink-faint)] block">
              Total Discrepancy Impact
            </span>
            <span className="font-mono text-base font-semibold text-[var(--color-ink)]">
              {formatAmount(
                (diffData.billedRate - diffData.agreedRate) * (diffData.billedQuantity || 1),
                currency
              )}
            </span>
          </div>
        </div>

        {/* Side-by-Side Comparison Columns */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column: Authorized Contract Terms */}
          <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-line)]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-forest)]">
                  Authorized Baseline
                </span>
                <h3 className="font-serif text-base font-bold text-[var(--color-ink)]">
                  {diffData.clauseTitle}
                </h3>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--color-forest-soft)] text-[var(--color-forest)] border border-[var(--color-forest)]/20">
                {diffData.clauseSection}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                  Agreed Rate
                </span>
                <span className="font-serif text-lg font-bold text-[var(--color-forest)]">
                  {formatAmount(diffData.agreedRate, currency)}{" "}
                  <span className="text-xs font-sans font-normal text-[var(--color-ink-soft)]">
                    / {diffData.agreedUnit || "unit"}
                  </span>
                </span>
              </div>

              {diffData.effectiveDate && (
                <div>
                  <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                    Term Effective
                  </span>
                  <span className="font-mono text-[var(--color-ink)]">{diffData.effectiveDate}</span>
                </div>
              )}

              <div>
                <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                  Agreed Scope / Clause Language
                </span>
                <p className="text-[var(--color-ink-soft)] leading-relaxed mt-1 bg-[var(--color-paper)] p-3 rounded-lg border border-[var(--color-line)] font-serif italic text-xs">
                  &ldquo;{diffData.agreedScope}&rdquo;
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Actual Billed Invoice Item */}
          <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-line)]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-clay)]">
                  Billed on Invoice
                </span>
                <h3 className="font-serif text-base font-bold text-[var(--color-ink)]">
                  {diffData.itemDescription}
                </h3>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[var(--color-clay-soft)] text-[var(--color-clay)] border border-[var(--color-clay)]/20">
                Code {diffData.itemCode}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                  Actual Billed Rate
                </span>
                <span className="font-serif text-lg font-bold text-[var(--color-clay)]">
                  {formatAmount(diffData.billedRate, currency)}{" "}
                  <span className="text-xs font-sans font-normal text-[var(--color-ink-soft)]">
                    / {diffData.agreedUnit || "unit"}
                  </span>
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                    Quantity
                  </span>
                  <span className="font-mono text-[var(--color-ink)] font-semibold">
                    {diffData.billedQuantity || 1}
                  </span>
                </div>
                <div>
                  <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                    Billed Total
                  </span>
                  <span className="font-mono text-[var(--color-ink)] font-semibold">
                    {formatAmount(diffData.billedTotal, currency)}
                  </span>
                </div>
              </div>

              {diffData.invoiceDate && (
                <div>
                  <span className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase block">
                    Invoice Date
                  </span>
                  <span className="font-mono text-[var(--color-ink)]">{diffData.invoiceDate}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Reasoning / Audit Footnote */}
        {diffData.reasonNotes && (
          <div className="px-6 py-3 border-t border-[var(--color-line)] bg-[var(--color-paper-deep)]/40 text-xs">
            <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)] block">
              Auditor Note
            </span>
            <p className="text-[var(--color-ink-soft)] mt-0.5">{diffData.reasonNotes}</p>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--color-line)] bg-[var(--color-paper)]/50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-lg text-xs font-mono font-semibold bg-[var(--color-ink)] text-[var(--color-paper)] hover:opacity-90 transition shadow-2xs"
          >
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
}
