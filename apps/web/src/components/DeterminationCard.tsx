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

  // Visual styling strictly aligned with Nestor calm palette
  const stylesMap: Record<
    string,
    { border: string; bg: string; textCol: string; headline: string; defaultDesc: string }
  > = {
    VERIFIED: {
      border: "border-[#1f4d3a]/30",
      bg: "bg-[#dfeae3]/30",
      textCol: "text-[#163828]",
      headline: "Verified",
      defaultDesc: investigation.amount
        ? `The ${amountDisplay} charge is supported by the contract records we found.`
        : "This charge is supported by the contract records we found.",
    },
    NOT_VERIFIED: {
      border: "border-[#c2512f]/30",
      bg: "bg-[#f8e4db]/30",
      textCol: "text-[#9d3f22]",
      headline: "Not verified",
      defaultDesc: "We couldn't verify this charge against the applicable contract terms.",
    },
    INSUFFICIENT_EVIDENCE: {
      border: "border-[#b97d10]/30",
      bg: "bg-[#fbefd2]/30",
      textCol: "text-[#8c5e08]",
      headline: "Not enough evidence",
      defaultDesc:
        "We found the relevant contract records, but the evidence needed to verify this charge was not available.",
    },
    NEEDS_REVIEW: {
      border: "border-[#c2512f]/30",
      bg: "bg-[#f8e4db]/30",
      textCol: "text-[#9d3f22]",
      headline: "Needs review",
      defaultDesc: "We found conflicting terms and couldn't determine which one takes precedence.",
    },
    FAILED: {
      border: "border-[#c2512f]/30",
      bg: "bg-[#f8e4db]/30",
      textCol: "text-[#9d3f22]",
      headline: "Review couldn't be completed",
      defaultDesc:
        "The investigation could not be completed because the required system information was unavailable.",
    },
    INVESTIGATING: {
      border: "border-[#2f6690]/25",
      bg: "bg-[#e0ecf5]/30",
      textCol: "text-[#2f6690]",
      headline: "Investigating",
      defaultDesc: "Reviewing invoice against contracts, amendments, and approval records.",
    },
    VALIDATING: {
      border: "border-[#2f6690]/25",
      bg: "bg-[#e0ecf5]/30",
      textCol: "text-[#2f6690]",
      headline: "Verifying",
      defaultDesc: "Checking invoice against gathered contract terms and evidentiary records.",
    },
    QUEUED: {
      border: "border-[#e6dccb]",
      bg: "bg-[#faf6ef]",
      textCol: "text-[#1c2621]",
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
      className={`rounded-2xl border ${currentStyle.border} ${currentStyle.bg} p-6 sm:p-7 shadow-2xs space-y-6 transition`}
      data-testid="finding-card"
    >
      {/* Top Finding Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-[#e6dccb]/50">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <span className="text-xs uppercase tracking-[0.14em] text-[#5b7f6a] font-semibold">
              Finding
            </span>
            <StatusBadge status={status} size="sm" />
          </div>
          <h2 className={`text-2xl sm:text-3xl font-serif font-bold tracking-tight ${currentStyle.textCol}`}>
            {getStatusLabel(status)}
          </h2>
          <p className="text-sm sm:text-base text-[#4a564f] leading-relaxed max-w-2xl font-normal pt-1">
            {findingStatement}
          </p>
        </div>

        {/* Supporting records count */}
        {investigation.cited_evidence_ids && investigation.cited_evidence_ids.length > 0 && (
          <div className="text-xs text-[#4a564f] bg-[#fffdf9] border border-[#e6dccb] px-3 py-1.5 rounded-xl self-start shrink-0 font-medium">
            <span className="font-serif font-bold text-[#1c2621]">
              {investigation.cited_evidence_ids.length}
            </span>{" "}
            supporting records cited
          </div>
        )}
      </div>

      {/* PHASE 9: Why / Explanation Section */}
      {validationResults.length > 0 ? (
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5b7f6a]">
            Why
          </h3>

          <div className="space-y-2 text-xs sm:text-sm">
            {/* If NOT_VERIFIED or NEEDS_REVIEW or INSUFFICIENT_EVIDENCE, show issues first */}
            {failedChecks.map((chk, idx) => (
              <div key={`fail-${idx}`} className="flex items-start gap-2.5 text-[#9d3f22]">
                <span className="font-bold text-[#c2512f] text-sm leading-none mt-0.5">✕</span>
                <div>
                  <span className="font-semibold text-[#1c2621]">{formatCheckName(chk.check_name)}:</span>{" "}
                  <span className="text-[#4a564f]">{chk.message || "Does not meet contract criteria."}</span>
                </div>
              </div>
            ))}

            {unknownChecks.map((chk, idx) => (
              <div key={`unk-${idx}`} className="flex items-start gap-2.5 text-[#8c5e08]">
                <span className="font-bold text-[#b97d10] text-sm leading-none mt-0.5">?</span>
                <div>
                  <span className="font-semibold text-[#1c2621]">{formatCheckName(chk.check_name)}:</span>{" "}
                  <span className="text-[#4a564f]">{chk.message || "Record or approval was not found."}</span>
                </div>
              </div>
            ))}

            {passedChecks.map((chk, idx) => (
              <div key={`pass-${idx}`} className="flex items-start gap-2.5 text-[#163828]">
                <span className="font-bold text-[#1f4d3a] text-sm leading-none mt-0.5">✓</span>
                <div>
                  <span className="font-semibold text-[#1c2621]">{formatCheckName(chk.check_name)}</span>
                  {chk.message && (
                    <span className="text-[#4a564f] text-xs sm:text-sm"> — {chk.message}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : status === "FAILED" ? (
        <div className="space-y-2 text-xs text-[#4a564f] bg-[#fffdf9] p-4 rounded-2xl border border-[#c2512f]/30">
          <span className="font-serif font-bold text-[#9d3f22] block text-sm">
            Review could not be completed
          </span>
          <p className="text-[#4a564f]">
            No determination was made. Technical reason: {failureReason || "System information unavailable."}
          </p>
        </div>
      ) : null}
    </div>
  );
}
