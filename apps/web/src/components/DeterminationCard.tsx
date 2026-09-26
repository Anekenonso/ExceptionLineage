import React from "react";
import { InvestigationResponse } from "@/types/investigation";
import { StatusBadge } from "./StatusBadge";

interface DeterminationCardProps {
  investigation: InvestigationResponse;
}

export function DeterminationCard({ investigation }: DeterminationCardProps) {
  const status = investigation.status;
  const summary = investigation.summary;
  const failureReason = investigation.failure_reason;
  const validationResults = investigation.validation_results || [];

  // Identify failed and unknown checks from deterministic validation
  const failedChecks = validationResults.filter((r) => r.status === "FAIL");
  const unknownChecks = validationResults.filter((r) => r.status === "UNKNOWN");

  // Style container based on terminal status
  const cardStyles: Record<
    string,
    { border: string; bg: string; iconBg: string; textCol: string; title: string }
  > = {
    VERIFIED: {
      border: "border-emerald-200",
      bg: "bg-emerald-50/40",
      iconBg: "bg-emerald-500 text-white",
      textCol: "text-emerald-950",
      title: "Contractually Verified & Approved",
    },
    NOT_VERIFIED: {
      border: "border-rose-200",
      bg: "bg-rose-50/40",
      iconBg: "bg-rose-500 text-white",
      textCol: "text-rose-950",
      title: "Contractual Non-Compliance Detected",
    },
    INSUFFICIENT_EVIDENCE: {
      border: "border-amber-200",
      bg: "bg-amber-50/40",
      iconBg: "bg-amber-500 text-white",
      textCol: "text-amber-950",
      title: "Insufficient Evidentiary Lineage",
    },
    NEEDS_REVIEW: {
      border: "border-purple-200",
      bg: "bg-purple-50/40",
      iconBg: "bg-purple-500 text-white",
      textCol: "text-purple-950",
      title: "Conflicting Contractual Authority",
    },
    FAILED: {
      border: "border-red-200",
      bg: "bg-red-50/40",
      iconBg: "bg-red-600 text-white",
      textCol: "text-red-950",
      title: "Investigation Execution Failure",
    },
    INVESTIGATING: {
      border: "border-blue-200",
      bg: "bg-blue-50/40",
      iconBg: "bg-blue-500 text-white",
      textCol: "text-blue-950",
      title: "Investigation In Progress",
    },
    VALIDATING: {
      border: "border-indigo-200",
      bg: "bg-indigo-50/40",
      iconBg: "bg-indigo-500 text-white",
      textCol: "text-indigo-950",
      title: "Evaluating Deterministic Rules",
    },
    QUEUED: {
      border: "border-slate-200",
      bg: "bg-slate-50",
      iconBg: "bg-slate-400 text-white",
      textCol: "text-slate-900",
      title: "Investigation Queued",
    },
  };

  const style = cardStyles[status] || cardStyles.QUEUED;

  return (
    <div
      className={`rounded-xl border ${style.border} ${style.bg} p-5 sm:p-6 shadow-xs transition`}
      data-testid="determination-card"
    >
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-black/5">
        <div className="flex items-start gap-3">
          <div
            className={`h-8 w-8 rounded-lg ${style.iconBg} flex items-center justify-center shrink-0 shadow-2xs mt-0.5`}
          >
            {status === "VERIFIED" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            ) : status === "NOT_VERIFIED" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            ) : status === "FAILED" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
              </svg>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-xs uppercase tracking-wider font-mono text-slate-500 font-semibold">
                Final Determination
              </span>
              <StatusBadge status={status} size="sm" />
            </div>
            <h3 className={`text-base font-bold tracking-tight mt-0.5 ${style.textCol}`}>
              {style.title}
            </h3>
          </div>
        </div>

        {/* Evidence citation count */}
        {investigation.cited_evidence_ids?.length > 0 && (
          <div className="text-xs text-slate-600 font-mono bg-white/70 border border-slate-200 px-3 py-1.5 rounded-md self-start">
            <span className="font-semibold text-slate-900">
              {investigation.cited_evidence_ids.length}
            </span>{" "}
            Citations Substantiated
          </div>
        )}
      </div>

      {/* Main explanation content based strictly on rules */}
      <div className="mt-4 space-y-3 text-xs leading-relaxed">
        {/* VERIFIED: Show backend-provided explanation */}
        {status === "VERIFIED" && (
          <div className="space-y-2">
            <p className="text-slate-800 text-sm font-normal leading-relaxed">
              {summary || "All deterministic validation rules passed with verified evidentiary citations."}
            </p>
          </div>
        )}

        {/* NOT_VERIFIED: Explain which validation/evidence caused determination */}
        {status === "NOT_VERIFIED" && (
          <div className="space-y-2.5">
            <p className="text-rose-900 text-sm font-medium">
              {failureReason || summary || "One or more deterministic contractual validation checks failed."}
            </p>

            {failedChecks.length > 0 && (
              <div className="rounded-lg bg-white/80 border border-rose-200 p-3 space-y-2">
                <span className="font-semibold text-rose-950 block text-xs">
                  Caused by Failed Deterministic Rules:
                </span>
                <ul className="space-y-1.5">
                  {failedChecks.map((chk, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-rose-900">
                      <span className="font-mono text-rose-700 shrink-0 font-bold">✕</span>
                      <span>
                        <strong className="font-mono font-semibold text-slate-900">{chk.check_name}:</strong>{" "}
                        {chk.message || "Rule violated"}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* INSUFFICIENT_EVIDENCE: Clearly show what evidence is missing */}
        {status === "INSUFFICIENT_EVIDENCE" && (
          <div className="space-y-2.5">
            <p className="text-amber-950 text-sm font-medium">
              {failureReason || summary || "Investigation inconclusive due to absent contractual records."}
            </p>

            {unknownChecks.length > 0 && (
              <div className="rounded-lg bg-white/80 border border-amber-200 p-3 space-y-2">
                <span className="font-semibold text-amber-950 block text-xs">
                  Missing Evidence / Indeterminate Checks:
                </span>
                <ul className="space-y-1.5">
                  {unknownChecks.map((chk, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-amber-900">
                      <span className="font-mono text-amber-600 shrink-0 font-bold">?</span>
                      <span>
                        <strong className="font-mono font-semibold text-slate-900">{chk.check_name}:</strong>{" "}
                        {chk.message || "Missing evidentiary documentation"}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* NEEDS_REVIEW: Clearly show conflicting or unresolved authority */}
        {status === "NEEDS_REVIEW" && (
          <div className="space-y-2.5">
            <p className="text-purple-950 text-sm font-medium">
              {failureReason || summary || "Conflicting authority detected requiring manual review."}
            </p>

            <div className="rounded-lg bg-white/80 border border-purple-200 p-3 space-y-2">
              <span className="font-semibold text-purple-950 block text-xs">
                Unresolved Contractual Conflict:
              </span>
              <p className="text-purple-900">
                {failureReason ||
                  "Multiple governing records with conflicting pricing terms exist without clear precedence resolution."}
              </p>
            </div>
          </div>
        )}

        {/* FAILED: Show "No determination was made." Never convert to business conclusion */}
        {status === "FAILED" && (
          <div className="space-y-2">
            <div className="p-3 rounded-lg bg-red-100/60 border border-red-200">
              <p className="font-semibold text-red-950 text-sm">
                No determination was made.
              </p>
              <p className="text-red-800 text-xs mt-1">
                Technical Reason: {failureReason || "System or infrastructure error during investigation."}
              </p>
            </div>
            <p className="text-slate-500 text-[11px] italic">
              Note: Technical failure indicates an infrastructure or graph retrieval issue; it does not indicate contractual compliance or violation.
            </p>
          </div>
        )}

        {/* Active states */}
        {(status === "QUEUED" || status === "INVESTIGATING" || status === "VALIDATING") && (
          <p className="text-slate-700 text-sm">
            {status === "QUEUED" && "Investigation is scheduled to begin evidence gathering."}
            {status === "INVESTIGATING" && "Agent loop is actively traversing the knowledge graph and collecting records."}
            {status === "VALIDATING" && "Lineage discovered. Evaluating deterministic contractual rules."}
          </p>
        )}
      </div>
    </div>
  );
}
