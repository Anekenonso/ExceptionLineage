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
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-4">
      {/* Header with counts */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Verification checks
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Checks performed against contract records and evidence.
          </p>
        </div>

        {/* Status Counters */}
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
            {passedCount} {getValidationStatusLabel("PASS")}
          </span>
          {failedCount > 0 && (
            <span className="px-2.5 py-1 rounded-md bg-rose-50 text-rose-800 border border-rose-200 font-semibold">
              {failedCount} {getValidationStatusLabel("FAIL")}
            </span>
          )}
          {unknownCount > 0 && (
            <span className="px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
              {unknownCount} {getValidationStatusLabel("UNKNOWN")}
            </span>
          )}
        </div>
      </div>

      {/* Checks List */}
      {checks.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No verification checks recorded for this investigation.
        </div>
      ) : (
        <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
          {checks.map((check, idx) => (
            <div
              key={idx}
              className={`p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs transition ${
                check.status === "FAIL"
                  ? "bg-rose-50/25"
                  : check.status === "UNKNOWN"
                  ? "bg-amber-50/25"
                  : "bg-white hover:bg-slate-50/50"
              }`}
            >
              {/* Left: Human Title and Message */}
              <div className="space-y-1 sm:max-w-xl">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900 text-xs sm:text-sm">
                    {formatCheckName(check.check_name)}
                  </span>
                  {check.is_required && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                      Required
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400 font-mono hidden md:inline">
                    ({check.check_name})
                  </span>
                </div>
                {check.message && (
                  <p className="text-slate-600 text-xs leading-relaxed">
                    {check.message}
                  </p>
                )}
              </div>

              {/* Right: Cited Evidence and Status Badge */}
              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                {check.evidence_ids && check.evidence_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[11px] text-slate-400">Evidence:</span>
                    {check.evidence_ids.map((evId) => (
                      <button
                        key={evId}
                        type="button"
                        onClick={() => onSelectEvidenceId && onSelectEvidenceId(evId)}
                        className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition"
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
