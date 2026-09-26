import React from "react";
import { InvestigationResponse, LineageData } from "@/types/investigation";
import { formatAmount } from "@/lib/formatters";

interface InvoiceExceptionCardProps {
  investigation: InvestigationResponse;
  lineage?: LineageData | null;
}

export function InvoiceExceptionCard({ investigation, lineage }: InvoiceExceptionCardProps) {
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
    contract?.title || (contract?.id ? `Contract ${contract.id}` : inv?.contract_id ? `Contract ${inv.contract_id}` : "Not identified");
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
  const expectedAmount = rawExpected !== undefined && rawExpected !== null
    ? formatAmount(rawExpected, currency)
    : null;

  // 8. Variance
  let varianceDisplay: string | null = null;
  let varianceIsPositive = false;
  let varianceIsZero = false;

  if (rawBilled !== undefined && rawBilled !== null && rawExpected !== undefined && rawExpected !== null) {
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
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">
            Invoice
          </h2>
          <p className="text-xs text-slate-500">
            Transaction details and flagged reason
          </p>
        </div>

        {exceptionType && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 text-xs font-medium">
            <span>Flagged:</span>
            <span className="font-semibold">{exceptionType}</span>
          </div>
        )}
      </div>

      {exceptionDesc && (
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
          <span className="font-semibold text-slate-900 block mb-0.5">Why it was flagged:</span>
          {exceptionDesc}
        </div>
      )}

      {/* Grid of Business Information */}
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-y-4 gap-x-6 text-xs">
        {/* Invoice Number */}
        <div>
          <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Invoice Number</dt>
          <dd className="font-mono font-semibold text-slate-900 text-sm">
            {invoiceNumber}
          </dd>
        </div>

        {/* Customer */}
        <div>
          <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Customer</dt>
          <dd className="font-medium text-slate-900 text-sm truncate" title={customerName}>
            {customerName}
            {customerId && customerId !== customerName && (
              <span className="block text-[11px] text-slate-400 font-mono font-normal">
                {customerId}
              </span>
            )}
          </dd>
        </div>

        {/* Amount */}
        <div>
          <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Amount Billed</dt>
          <dd className="font-mono font-semibold text-slate-900 text-sm">
            {billedAmount}
          </dd>
        </div>

        {/* Expected Amount / Variance if flagged */}
        {expectedAmount ? (
          <div>
            <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Expected Baseline</dt>
            <dd className="font-mono font-medium text-slate-700 text-sm">
              {expectedAmount}
              {varianceDisplay && (
                <span
                  className={`block text-[11px] font-medium ${
                    varianceIsZero
                      ? "text-slate-500"
                      : varianceIsPositive
                      ? "text-rose-600"
                      : "text-emerald-600"
                  }`}
                >
                  Variance: {varianceDisplay}
                </span>
              )}
            </dd>
          </div>
        ) : (
          <div>
            <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Currency</dt>
            <dd className="font-medium text-slate-900 text-sm font-mono">
              {currency}
            </dd>
          </div>
        )}

        {/* Invoice Date */}
        <div>
          <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Invoice Date</dt>
          <dd className="text-slate-900 font-medium">
            {invoiceDate}
          </dd>
        </div>

        {/* Governing Contract */}
        <div className="sm:col-span-2">
          <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Governing Contract</dt>
          <dd className="text-slate-900 font-medium truncate" title={contractTitle}>
            {contractTitle}
            {contractId && contractTitle !== contractId && (
              <span className="text-[11px] text-slate-400 font-mono font-normal ml-1">
                ({contractId})
              </span>
            )}
          </dd>
        </div>

        {/* Product / Service if available */}
        {product && (
          <div>
            <dt className="text-slate-500 text-[11px] font-medium mb-0.5">Product</dt>
            <dd className="text-slate-900 font-medium truncate" title={product}>
              {product}
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}
