import React from "react";
import { InvestigationResponse } from "@/types/investigation";
import { StatusBadge } from "./StatusBadge";
import {
  getStatusLabel,
  formatAmount,
  formatCheckName,
} from "@/lib/formatters";

interface DeterminationCardProps {
  investigation: InvestigationResponse;
}

export function DeterminationCard({ investigation }: DeterminationCardProps) {
  const status = investigation.status;
  const summary = investigation.summary;
  const failureReason = investigation.failure_reason;
  const validationResults = investigation.validation_results || [];

  const amountDisplay = formatAmount(investigation.amount, investigation.currency || "USD");

  // Visual styling aligned with enterprise finding
  const stylesMap: Record<
    string,
    { border: string; bg: string; textCol: string; headline: string; defaultDesc: string }
  > = {
    VERIFIED: {
      border: "border-emerald-200",
      bg: "bg-emerald-50/50",
      textCol: "text-emerald-950",
      headline: "Verified",
      defaultDesc: investigation.amount
        ? `The ${amountDisplay} charge is supported by the contract records we found.`
        : "This charge is supported by the contract records we found.",
    },
    NOT_VERIFIED: {
      border: "border-rose-200",
      bg: "bg-rose-50/50",
      textCol: "text-rose-950",
      headline: "Not verified",
      defaultDesc: "We couldn't verify this charge against the applicable contract terms.",
    },
    INSUFFICIENT_EVIDENCE: {
      border: "border-amber-200",
      bg: "bg-amber-50/50",
      textCol: "text-amber-950",
      headline: "Not enough evidence",
      defaultDesc:
        "We found the relevant contract records, but the evidence needed to verify this charge was not available.",
    },
    NEEDS_REVIEW: {
      border: "border-purple-200",
      bg: "bg-purple-50/50",
      textCol: "text-purple-950",
      headline: "Needs review",
      defaultDesc: "We found conflicting terms and couldn't determine which one takes precedence.",
    },
    FAILED: {
      border: "border-red-200",
      bg: "bg-red-50/50",
      textCol: "text-red-950",
      headline: "Review couldn't be completed",
      defaultDesc:
        "The investigation could not be completed because the required system information was unavailable.",
    },
    INVESTIGATING: {
      border: "border-blue-200",
      bg: "bg-blue-50/40",
      textCol: "text-blue-950",
      headline: "Investigating",
      defaultDesc: "Reviewing invoice against contracts, amendments, and approval records.",
    },
    VALIDATING: {
      border: "border-indigo-200",
      bg: "bg-indigo-50/40",
      textCol: "text-indigo-950",
      headline: "Verifying",
      defaultDesc: "Checking invoice against gathered contract terms and evidentiary records.",
    },
    QUEUED: {
      border: "border-slate-200",
      bg: "bg-slate-50",
      textCol: "text-slate-900",
      headline: "Queued",
      defaultDesc: "Scheduled for contract and evidence review.",
    },
  };

  const currentStyle = stylesMap[status] || stylesMap.QUEUED;

  // Lead finding statement
  const findingStatement =
    status === "VERIFIED"
      ? summary || currentStyle.defaultDesc
      : status === "NOT_VERIFIED"
      ? failureReason || summary || currentStyle.defaultDesc
      : status === "INSUFFICIENT_EVIDENCE"
      ? failureReason || summary || currentStyle.defaultDesc
      : status === "NEEDS_REVIEW"
      ? failureReason || summary || currentStyle.defaultDesc
      : status === "FAILED"
      ? currentStyle.defaultDesc
      : currentStyle.defaultDesc;

  // Passed, failed, and unknown checks for the "Why" section
  const passedChecks = validationResults.filter((r) => r.status === "PASS");
  const failedChecks = validationResults.filter((r) => r.status === "FAIL");
  const unknownChecks = validationResults.filter((r) => r.status === "UNKNOWN");

  return (
    <div
      className={`rounded-xl border ${currentStyle.border} ${currentStyle.bg} p-6 sm:p-7 shadow-xs space-y-6 transition`}
      data-testid="finding-card"
    >
      {/* Top Finding Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-black/5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
              Finding
            </span>
            <StatusBadge status={status} size="sm" />
          </div>
          <h2 className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${currentStyle.textCol}`}>
            {getStatusLabel(status)}
          </h2>
          <p className="text-sm sm:text-base text-slate-700 leading-relaxed max-w-2xl font-normal pt-1">
            {findingStatement}
          </p>
        </div>

        {/* Supporting records count */}
        {investigation.cited_evidence_ids && investigation.cited_evidence_ids.length > 0 && (
          <div className="text-xs text-slate-600 bg-white/80 border border-slate-200 px-3 py-1.5 rounded-md self-start shrink-0">
            <span className="font-semibold text-slate-900">
              {investigation.cited_evidence_ids.length}
            </span>{" "}
            supporting records cited
          </div>
        )}
      </div>

      {/* PHASE 9: Why / Explanation Section */}
      {validationResults.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Why
          </h3>

          <div className="space-y-2 text-xs sm:text-sm">
            {/* If NOT_VERIFIED or NEEDS_REVIEW or INSUFFICIENT_EVIDENCE, show issues first */}
            {failedChecks.map((chk, idx) => (
              <div key={`fail-${idx}`} className="flex items-start gap-2.5 text-rose-900">
                <span className="font-bold text-rose-600 text-sm leading-none mt-0.5">✕</span>
                <div>
                  <span className="font-semibold text-slate-900">{formatCheckName(chk.check_name)}:</span>{" "}
                  <span className="text-slate-700">{chk.message || "Does not meet contract criteria."}</span>
                </div>
              </div>
            ))}

            {unknownChecks.map((chk, idx) => (
              <div key={`unk-${idx}`} className="flex items-start gap-2.5 text-amber-900">
                <span className="font-bold text-amber-600 text-sm leading-none mt-0.5">?</span>
                <div>
                  <span className="font-semibold text-slate-900">{formatCheckName(chk.check_name)}:</span>{" "}
                  <span className="text-slate-700">{chk.message || "Record or approval was not found."}</span>
                </div>
              </div>
            ))}

            {passedChecks.map((chk, idx) => (
              <div key={`pass-${idx}`} className="flex items-start gap-2.5 text-slate-800">
                <span className="font-bold text-emerald-600 text-sm leading-none mt-0.5">✓</span>
                <div>
                  <span className="font-semibold text-slate-900">{formatCheckName(chk.check_name)}</span>
                  {chk.message && (
                    <span className="text-slate-600 text-xs sm:text-sm"> — {chk.message}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : status === "FAILED" ? (
        <div className="space-y-2 text-xs text-slate-600 bg-white/70 p-3.5 rounded-lg border border-red-200">
          <span className="font-semibold text-red-950 block text-xs">
            Review could not be completed
          </span>
          <p className="text-slate-700">
            No determination was made. Technical reason: {failureReason || "System information unavailable."}
          </p>
        </div>
      ) : null}
    </div>
  );
}
