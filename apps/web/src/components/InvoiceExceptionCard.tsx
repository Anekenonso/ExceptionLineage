import React from "react";
import { InvestigationResponse, LineageData } from "@/types/investigation";
import { formatAmount } from "@/lib/formatters";

interface InvoiceExceptionCardProps {
  investigation: InvestigationResponse;
  lineage?: LineageData | null;
  onOpenClauseDiff?: () => void;
}

export function InvoiceExceptionCard({
  investigation,
  lineage,
  onOpenClauseDiff,
}: InvoiceExceptionCardProps) {
  const inv = lineage?.invoice;
  const exc = lineage?.exception;
  const contract = lineage?.contract;
  const customer = lineage?.customer;

  // 1. Invoice Number
  const invoiceNumber = investigation.invoice_id || inv?.id || "—";

  // 2. Customer
  const customerName =
    investigation.customer_name ||
    customer?.name ||
    (investigation.customer_id ? `Customer ${investigation.customer_id}` : "Unavailable");
  const customerId = investigation.customer_id || customer?.id || inv?.customer_id;

  // 3. Contract
  const contractTitle =
    contract?.title ||
    (contract?.id
      ? `Contract ${contract.id}`
      : inv?.contract_id
      ? `Contract ${inv.contract_id}`
      : "Not identified");
  const contractId = contract?.id || inv?.contract_id;

  // 4. Product / Service
  const product = inv?.product_id || null;

  // 5. Invoice Date
  const invoiceDate = inv?.issued_at
    ? new Date(inv.issued_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "Unavailable";

  // 6. Billed Amount
  const rawBilled = investigation.amount || inv?.amount || exc?.actual_amount;
  const currency = investigation.currency || inv?.currency || exc?.currency || "USD";
  const billedAmount = formatAmount(rawBilled, currency);

  // 7. Expected Amount
  const rawExpected = exc?.expected_amount;
  const expectedAmount =
    rawExpected !== undefined && rawExpected !== null
      ? formatAmount(rawExpected, currency)
      : null;

  // 8. Variance
  let varianceDisplay: string | null = null;
  let varianceIsPositive = false;
  let varianceIsZero = false;

  if (
    rawBilled !== undefined &&
    rawBilled !== null &&
    rawExpected !== undefined &&
    rawExpected !== null
  ) {
    const billedNum = Number(rawBilled);
    const expectedNum = Number(rawExpected);
    const diff = billedNum - expectedNum;
    varianceIsPositive = diff > 0;
    varianceIsZero = Math.abs(diff) < 0.001;
    const sign = diff > 0 ? "+" : "";
    varianceDisplay = `${sign}${formatAmount(diff, currency)}`;
  }

  // Exception description / flag
  const exceptionDesc = exc?.description || null;
  const exceptionType = exc?.exception_type || investigation.exception_id || null;

  return (
    <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[var(--color-line)] gap-2">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)]">
            Audited Instrument
          </span>
          <h2 className="font-serif text-lg font-bold text-[var(--color-ink)] tracking-tight">
            Invoice Summary
          </h2>
          <p className="text-xs text-[var(--color-ink-faint)]">
            Billing transaction, entity mapping, and flagged discrepancy terms
          </p>
        </div>

        <div className="flex items-center gap-2">
          {exceptionType && (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--color-clay-soft)] border border-[var(--color-clay)]/20 text-[var(--color-clay)] text-xs font-mono font-medium">
              <span>Flag:</span>
              <span className="font-bold">{exceptionType}</span>
            </div>
          )}

          {onOpenClauseDiff && (
            <button
              type="button"
              onClick={onOpenClauseDiff}
              className="inline-flex items-center gap-1 px-3 py-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] text-xs font-mono font-medium text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)] transition shadow-2xs"
            >
              <span>Clause Diff</span>
              <span className="text-[var(--color-clay)]">&rarr;</span>
            </button>
          )}
        </div>
      </div>

      {exceptionDesc && (
        <div className="p-3 rounded-lg bg-[var(--color-paper)] border border-[var(--color-line)] text-xs text-[var(--color-ink-soft)]">
          <span className="font-semibold text-[var(--color-ink)] block mb-0.5 font-mono text-[11px] uppercase tracking-wider">
            Flag Trigger Reason:
          </span>
          {exceptionDesc}
        </div>
      )}

      {/* Grid of Business Information */}
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-y-4 gap-x-6 text-xs">
        {/* Invoice Number */}
        <div>
          <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
            Invoice Number
          </dt>
          <dd className="font-mono font-bold text-[var(--color-ink)] text-sm">
            {invoiceNumber}
          </dd>
        </div>

        {/* Customer */}
        <div>
          <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
            Customer Entity
          </dt>
          <dd className="font-medium text-[var(--color-ink)] text-sm truncate" title={customerName}>
            {customerName}
            {customerId && customerId !== customerName && (
              <span className="block text-[11px] text-[var(--color-ink-faint)] font-mono font-normal">
                {customerId}
              </span>
            )}
          </dd>
        </div>

        {/* Amount */}
        <div>
          <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
            Amount Billed
          </dt>
          <dd className="font-serif font-bold text-[var(--color-ink)] text-base">
            {billedAmount}
          </dd>
        </div>

        {/* Expected Amount / Variance if flagged */}
        {expectedAmount ? (
          <div>
            <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
              Expected Baseline
            </dt>
            <dd className="font-mono font-medium text-[var(--color-ink)] text-sm">
              {expectedAmount}
              {varianceDisplay && (
                <span
                  className={`block text-[11px] font-mono font-semibold ${
                    varianceIsZero
                      ? "text-[var(--color-ink-faint)]"
                      : varianceIsPositive
                      ? "text-[var(--color-clay)]"
                      : "text-[var(--color-forest)]"
                  }`}
                >
                  Variance: {varianceDisplay}
                </span>
              )}
            </dd>
          </div>
        ) : (
          <div>
            <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
              Currency
            </dt>
            <dd className="font-mono font-medium text-[var(--color-ink)] text-sm">
              {currency}
            </dd>
          </div>
        )}

        {/* Invoice Date */}
        <div>
          <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
            Invoice Date
          </dt>
          <dd className="text-[var(--color-ink)] font-mono font-medium">
            {invoiceDate}
          </dd>
        </div>

        {/* Governing Contract */}
        <div className="sm:col-span-2">
          <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
            Governing Contract
          </dt>
          <dd className="text-[var(--color-ink)] font-medium truncate" title={contractTitle}>
            {contractTitle}
            {contractId && contractTitle !== contractId && (
              <span className="text-[11px] text-[var(--color-ink-faint)] font-mono font-normal ml-1">
                ({contractId})
              </span>
            )}
          </dd>
        </div>

        {/* Product / Service if available */}
        {product && (
          <div>
            <dt className="text-[var(--color-ink-faint)] text-[10px] font-mono uppercase tracking-wider mb-0.5">
              Product SKU / Scope
            </dt>
            <dd className="text-[var(--color-ink)] font-mono font-medium truncate" title={product}>
              {product}
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}
