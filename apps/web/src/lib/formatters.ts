import { InvestigationStatus, ValidationStatus } from "@/types/investigation";

/**
 * Human-readable translations for internal statuses.
 * Internal backend enums remain strictly preserved.
 */
export function getStatusLabel(status: InvestigationStatus | string): string {
  const norm = (status || "").toUpperCase();
  switch (norm) {
    case "VERIFIED":
      return "Verified";
    case "NOT_VERIFIED":
      return "Not verified";
    case "INSUFFICIENT_EVIDENCE":
      return "Not enough evidence";
    case "NEEDS_REVIEW":
      return "Needs review";
    case "FAILED":
      return "Review couldn't be completed";
    case "QUEUED":
      return "Queued";
    case "INVESTIGATING":
      return "Investigating";
    case "VALIDATING":
      return "Verifying";
    default:
      return status || "Unknown";
  }
}

/**
 * Human-readable translation for verification check outcomes.
 */
export function getValidationStatusLabel(status: ValidationStatus | string): string {
  const norm = (status || "").toUpperCase();
  switch (norm) {
    case "PASS":
      return "Passed";
    case "FAIL":
      return "Failed";
    case "UNKNOWN":
      return "Not available";
    default:
      return status || "Not available";
  }
}

/**
 * Translates raw check identifiers into clear business descriptions.
 */
const CHECK_NAME_MAP: Record<string, { title: string; defaultReason: string }> = {
  contract_active_check: {
    title: "Contract was active on invoice date",
    defaultReason: "Governing contract was active and in effect on the date this invoice was issued.",
  },
  customer_entity_match_check: {
    title: "Customer matches the contract",
    defaultReason: "The customer named on the invoice matches the contracted entity.",
  },
  pricing_schedule_match_check: {
    title: "Invoice rate matches the authorized fee schedule",
    defaultReason: "Billed pricing corresponds to agreed fee schedules in contract terms.",
  },
  amendment_terms_check: {
    title: "Amendment covers billed services and rates",
    defaultReason: "An active amendment modifies contract terms to authorize this rate.",
  },
  approval_authorization_check: {
    title: "Required operational approval exists",
    defaultReason: "The variance or transaction has an authorized operational approval recorded.",
  },
  currency_consistency_check: {
    title: "Currency matches contract and invoice",
    defaultReason: "Consistent currency is used across the invoice, contract, and any amendments.",
  },
  date_sequence_check: {
    title: "Invoice issued within valid contract period",
    defaultReason: "The invoice date falls appropriately in sequence after contract execution.",
  },
  lineage_provenance_check: {
    title: "Complete record lineage verified",
    defaultReason: "A continuous, verified record chain connects the customer to this charge.",
  },
};

export function formatCheckName(rawCheckName: string): string {
  if (CHECK_NAME_MAP[rawCheckName]) {
    return CHECK_NAME_MAP[rawCheckName].title;
  }
  // Convert snake_case or SCREAMING_SNAKE_CASE to Title Case
  return rawCheckName
    .replace(/_check$/i, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

export function formatCheckDefaultReason(rawCheckName: string): string {
  if (CHECK_NAME_MAP[rawCheckName]) {
    return CHECK_NAME_MAP[rawCheckName].defaultReason;
  }
  return `Verification check for ${formatCheckName(rawCheckName).toLowerCase()}.`;
}

/**
 * Formats monetary amounts cleanly.
 */
export function formatAmount(
  amount: string | number | null | undefined,
  currency: string = "USD"
): string {
  if (amount === null || amount === undefined || amount === "") {
    return "—";
  }
  const num = typeof amount === "number" ? amount : parseFloat(String(amount));
  if (isNaN(num)) {
    return String(amount);
  }
  const formatted = num.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currency} ${formatted}`;
}

/**
 * Formats timestamps cleanly in UTC.
 */
export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return (
      d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
      }) + " UTC"
    );
  } catch {
    return isoString;
  }
}

/**
 * Formats timestamps as relative time (e.g. "12m ago", "2h ago").
 */
export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    if (diffMs < 0) return formatDateTime(isoString);

    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;

    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;

    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return isoString;
  }
}

/**
 * Formats duration between two timestamps or milliseconds (e.g., "340ms", "1.8s").
 */
export function formatDuration(startIso?: string | null, endIso?: string | null): string {
  if (!startIso || !endIso) return "—";
  try {
    const start = new Date(startIso).getTime();
    const end = new Date(endIso).getTime();
    const durationMs = Math.max(0, end - start);
    if (durationMs < 1000) return `${durationMs}ms`;
    return `${(durationMs / 1000).toFixed(1)}s`;
  } catch {
    return "—";
  }
}

/**
 * Formats variance between billed and expected amounts with percentage and sign.
 */
export function formatVariance(
  billed: number | string | null | undefined,
  expected: number | string | null | undefined,
  currency: string = "USD"
): { formattedDiff: string; percentChange: string; isOver: boolean; isZero: boolean } {
  const b = typeof billed === "number" ? billed : parseFloat(String(billed || "0"));
  const e = typeof expected === "number" ? expected : parseFloat(String(expected || "0"));

  if (isNaN(b) || isNaN(e)) {
    return { formattedDiff: "—", percentChange: "0.0%", isOver: false, isZero: true };
  }

  const diff = b - e;
  const isZero = Math.abs(diff) < 0.001;
  const isOver = diff > 0;
  const pct = e !== 0 ? (diff / e) * 100 : 0;

  const sign = isOver ? "+" : isZero ? "" : "-";
  const absDiff = Math.abs(diff).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return {
    formattedDiff: `${sign}${currency} ${absDiff}`,
    percentChange: `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`,
    isOver,
    isZero,
  };
}

