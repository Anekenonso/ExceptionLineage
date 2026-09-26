import React from "react";
import { InvestigationStatus, ValidationStatus } from "@/types/investigation";

interface StatusBadgeProps {
  status: InvestigationStatus | ValidationStatus | string;
  size?: "sm" | "md" | "lg";
  showDot?: boolean;
}

export function StatusBadge({ status, size = "md", showDot = true }: StatusBadgeProps) {
  const normStatus = (status || "").toUpperCase();

  // Colors aligned with restrained enterprise SaaS style
  const configMap: Record<
    string,
    { bg: string; text: string; border: string; dot: string; label: string }
  > = {
    VERIFIED: {
      bg: "bg-emerald-50 text-emerald-800",
      text: "text-emerald-700",
      border: "border-emerald-200",
      dot: "bg-emerald-500",
      label: "Verified",
    },
    PASS: {
      bg: "bg-emerald-50 text-emerald-800",
      text: "text-emerald-700",
      border: "border-emerald-200",
      dot: "bg-emerald-500",
      label: "Pass",
    },
    NOT_VERIFIED: {
      bg: "bg-rose-50 text-rose-800",
      text: "text-rose-700",
      border: "border-rose-200",
      dot: "bg-rose-500",
      label: "Not Verified",
    },
    FAIL: {
      bg: "bg-rose-50 text-rose-800",
      text: "text-rose-700",
      border: "border-rose-200",
      dot: "bg-rose-500",
      label: "Fail",
    },
    INSUFFICIENT_EVIDENCE: {
      bg: "bg-amber-50 text-amber-900",
      text: "text-amber-800",
      border: "border-amber-200",
      dot: "bg-amber-500",
      label: "Insufficient Evidence",
    },
    UNKNOWN: {
      bg: "bg-amber-50 text-amber-900",
      text: "text-amber-800",
      border: "border-amber-200",
      dot: "bg-amber-500",
      label: "Unknown",
    },
    NEEDS_REVIEW: {
      bg: "bg-purple-50 text-purple-900",
      text: "text-purple-800",
      border: "border-purple-200",
      dot: "bg-purple-500",
      label: "Needs Review",
    },
    FAILED: {
      bg: "bg-red-50 text-red-900",
      text: "text-red-700",
      border: "border-red-200",
      dot: "bg-red-500",
      label: "Failed",
    },
    INVESTIGATING: {
      bg: "bg-blue-50 text-blue-800",
      text: "text-blue-700",
      border: "border-blue-200",
      dot: "bg-blue-500 animate-pulse",
      label: "Investigating",
    },
    VALIDATING: {
      bg: "bg-indigo-50 text-indigo-800",
      text: "text-indigo-700",
      border: "border-indigo-200",
      dot: "bg-indigo-500 animate-pulse",
      label: "Validating",
    },
    QUEUED: {
      bg: "bg-slate-100 text-slate-700",
      text: "text-slate-600",
      border: "border-slate-200",
      dot: "bg-slate-400",
      label: "Queued",
    },
  };

  const current = configMap[normStatus] || {
    bg: "bg-slate-100 text-slate-700",
    text: "text-slate-600",
    border: "border-slate-200",
    dot: "bg-slate-400",
    label: normStatus || "Unknown",
  };

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs font-medium tracking-tight",
    md: "px-2.5 py-1 text-xs font-semibold tracking-tight",
    lg: "px-3.5 py-1.5 text-sm font-semibold tracking-wide",
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${current.bg} ${current.border} ${sizeClasses}`}
      title={`Status: ${current.label}`}
    >
      {showDot && (
        <span
          className={`inline-block h-1.5 w-1.5 rounded-full shrink-0 ${current.dot}`}
          aria-hidden="true"
        />
      )}
      <span>{current.label}</span>
    </span>
  );
}
