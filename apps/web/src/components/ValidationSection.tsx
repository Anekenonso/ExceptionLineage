import React from "react";
import { ValidationResult } from "@/types/investigation";
import { StatusBadge } from "./StatusBadge";
import { formatCheckName, getValidationStatusLabel } from "@/lib/formatters";

interface ValidationSectionProps {
  results?: ValidationResult[] | null;
  onSelectEvidenceId?: (id: string) => void;
}

export function ValidationSection({ results, onSelectEvidenceId }: ValidationSectionProps) {
  const checks = results || [];

  const passedCount = checks.filter((c) => c.status === "PASS").length;
  const failedCount = checks.filter((c) => c.status === "FAIL").length;
  const unknownCount = checks.filter((c) => c.status === "UNKNOWN").length;

  return (
    <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:p-6 shadow-xs space-y-4">
      {/* Header with counts */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[var(--color-line)] gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)]">
            Deterministic Rule Matrix
          </span>
          <h3 className="font-serif text-base font-bold text-[var(--color-ink)] tracking-tight">
            Verification Checks
          </h3>
          <p className="text-xs text-[var(--color-ink-faint)] mt-0.5">
            Strict rule-based evaluation against contract governance records and cited evidence
          </p>
        </div>

        {/* Status Counters */}
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-md bg-[var(--color-forest-soft)] text-[var(--color-forest)] border border-[var(--color-forest)]/20 font-mono font-semibold">
            {passedCount} {getValidationStatusLabel("PASS")}
          </span>
          {failedCount > 0 && (
            <span className="px-2.5 py-1 rounded-md bg-[var(--color-clay-soft)] text-[var(--color-clay)] border border-[var(--color-clay)]/20 font-mono font-semibold">
              {failedCount} {getValidationStatusLabel("FAIL")}
            </span>
          )}
          {unknownCount > 0 && (
            <span className="px-2.5 py-1 rounded-md bg-[var(--color-honey-soft)] text-[var(--color-honey)] border border-[var(--color-honey)]/20 font-mono font-semibold">
              {unknownCount} {getValidationStatusLabel("UNKNOWN")}
            </span>
          )}
        </div>
      </div>

      {/* Checks List */}
      {checks.length === 0 ? (
        <div className="py-8 text-center text-xs text-[var(--color-ink-faint)] font-mono">
          No verification checks recorded for this investigation.
        </div>
      ) : (
        <div className="divide-y divide-[var(--color-line)] border border-[var(--color-line)] rounded-xl overflow-hidden">
          {checks.map((check, idx) => (
            <div
              key={idx}
              className={`p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs transition ${
                check.status === "FAIL"
                  ? "bg-[var(--color-clay-soft)]/20"
                  : check.status === "UNKNOWN"
                  ? "bg-[var(--color-honey-soft)]/20"
                  : "bg-[var(--color-card)] hover:bg-[var(--color-paper)]/50"
              }`}
            >
              {/* Left: Human Title and Message */}
              <div className="space-y-1 sm:max-w-xl">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[var(--color-ink)] text-xs sm:text-sm">
                    {formatCheckName(check.check_name)}
                  </span>
                  {check.is_required && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)] border border-[var(--color-line)]">
                      Required
                    </span>
                  )}
                  <span className="text-[10px] text-[var(--color-ink-faint)] font-mono hidden md:inline">
                    ({check.check_name})
                  </span>
                </div>
                {check.message && (
                  <p className="text-[var(--color-ink-soft)] text-xs leading-relaxed">
                    {check.message}
                  </p>
                )}
              </div>

              {/* Right: Cited Evidence and Status Badge */}
              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                {check.evidence_ids && check.evidence_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] font-mono text-[var(--color-ink-faint)]">Cited:</span>
                    {check.evidence_ids.map((evId) => (
                      <button
                        key={evId}
                        type="button"
                        onClick={() => onSelectEvidenceId && onSelectEvidenceId(evId)}
                        className="font-mono text-[10px] px-2 py-0.5 rounded bg-[var(--color-sky-soft)] text-[var(--color-sky)] border border-[var(--color-sky)]/20 hover:opacity-80 transition"
                        title={`Inspect evidence citation ${evId}`}
                      >
                        {evId}
                      </button>
                    ))}
                  </div>
                )}

                <StatusBadge status={check.status} size="sm" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
