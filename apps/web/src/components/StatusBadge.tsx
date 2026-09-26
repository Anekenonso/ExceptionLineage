import React from "react";
import { InvestigationStatus, ValidationStatus } from "@/types/investigation";
import { getStatusLabel, getValidationStatusLabel } from "@/lib/formatters";

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
      bg: "bg-[#dfeae3] text-[#163828]",
      text: "text-[#163828]",
      border: "border-[#1f4d3a]/25",
      dot: "bg-[#1f4d3a]",
      label: getStatusLabel("VERIFIED"),
    },
    PASS: {
      bg: "bg-[#dfeae3] text-[#163828]",
      text: "text-[#163828]",
      border: "border-[#1f4d3a]/25",
      dot: "bg-[#1f4d3a]",
      label: getValidationStatusLabel("PASS"),
    },
    NOT_VERIFIED: {
      bg: "bg-[#f8e4db] text-[#9d3f22]",
      text: "text-[#9d3f22]",
      border: "border-[#c2512f]/25",
      dot: "bg-[#c2512f]",
      label: getStatusLabel("NOT_VERIFIED"),
    },
    FAIL: {
      bg: "bg-[#f8e4db] text-[#9d3f22]",
      text: "text-[#9d3f22]",
      border: "border-[#c2512f]/25",
      dot: "bg-[#c2512f]",
      label: getValidationStatusLabel("FAIL"),
    },
    INSUFFICIENT_EVIDENCE: {
      bg: "bg-[#fbefd2] text-[#8c5e08]",
      text: "text-[#8c5e08]",
      border: "border-[#b97d10]/30",
      dot: "bg-[#b97d10]",
      label: getStatusLabel("INSUFFICIENT_EVIDENCE"),
    },
    UNKNOWN: {
      bg: "bg-[#fbefd2] text-[#8c5e08]",
      text: "text-[#8c5e08]",
      border: "border-[#b97d10]/30",
      dot: "bg-[#b97d10]",
      label: getValidationStatusLabel("UNKNOWN"),
    },
    NEEDS_REVIEW: {
      bg: "bg-[#f8e4db] text-[#9d3f22]",
      text: "text-[#9d3f22]",
      border: "border-[#c2512f]/25",
      dot: "bg-[#c2512f]",
      label: getStatusLabel("NEEDS_REVIEW"),
    },
    FAILED: {
      bg: "bg-[#f8e4db] text-[#9d3f22]",
      text: "text-[#9d3f22]",
      border: "border-[#c2512f]/25",
      dot: "bg-[#c2512f]",
      label: getStatusLabel("FAILED"),
    },
    INVESTIGATING: {
      bg: "bg-[#e0ecf5] text-[#2f6690]",
      text: "text-[#2f6690]",
      border: "border-[#2f6690]/25",
      dot: "bg-[#2f6690] animate-pulse",
      label: getStatusLabel("INVESTIGATING"),
    },
    VALIDATING: {
      bg: "bg-[#e0ecf5] text-[#2f6690]",
      text: "text-[#2f6690]",
      border: "border-[#2f6690]/25",
      dot: "bg-[#2f6690] animate-pulse",
      label: getStatusLabel("VALIDATING"),
    },
    QUEUED: {
      bg: "bg-[#f2ebdf] text-[#4a564f]",
      text: "text-[#4a564f]",
      border: "border-[#e6dccb]",
      dot: "bg-[#7d877f]",
      label: getStatusLabel("QUEUED"),
    },
  };

  const current = configMap[normStatus] || {
    bg: "bg-slate-100 text-slate-700",
    text: "text-slate-600",
    border: "border-slate-200",
    dot: "bg-slate-400",
    label: normStatus ? getStatusLabel(normStatus) : "Unknown",
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
