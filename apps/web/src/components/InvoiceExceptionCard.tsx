import React from "react";
import { InvestigationResponse, LineageData } from "@/types/investigation";

interface InvoiceExceptionCardProps {
  investigation: InvestigationResponse;
  lineage?: LineageData | null;
}

export function InvoiceExceptionCard({ investigation, lineage }: InvoiceExceptionCardProps) {
  const inv = lineage?.invoice;
  const exc = lineage?.exception;
  const contract = lineage?.contract;
  const customer = lineage?.customer;

  // 1. Invoice ID
  const invoiceId = investigation.invoice_id || inv?.id || "—";

  // 2. Customer
  const customerName = investigation.customer_name || customer?.name || (investigation.customer_id ? `ID: ${investigation.customer_id}` : "Unavailable");
  const customerId = investigation.customer_id || customer?.id || inv?.customer_id;

  // 3. Contract
  const contractTitle = contract?.title ? `${contract.title} (${contract.id})` : contract?.id ? contract.id : inv?.contract_id || "Unavailable";

  // 4. Product
  const product = inv?.product_id || "Unavailable";

  // 5. Invoice Date
  const invoiceDate = inv?.issued_at
    ? new Date(inv.issued_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "Unavailable";

  // 6. Billed amount
  const rawBilled = investigation.amount || inv?.amount || exc?.actual_amount;
  const currency = investigation.currency || inv?.currency || exc?.currency || "USD";
  const billedAmount = rawBilled !== undefined && rawBilled !== null
    ? `${currency} ${Number(rawBilled).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : "Unavailable";

  // 7. Expected amount
  const rawExpected = exc?.expected_amount;
  const expectedAmount = rawExpected !== undefined && rawExpected !== null
    ? `${currency} ${Number(rawExpected).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : "Unavailable";

  // 8. Variance
  let varianceDisplay = "Unavailable";
  let varianceIsPositive = false;
  let varianceIsZero = false;

  if (rawBilled !== undefined && rawBilled !== null && rawExpected !== undefined && rawExpected !== null) {
    const billedNum = Number(rawBilled);
    const expectedNum = Number(rawExpected);
    const diff = billedNum - expectedNum;
    varianceIsPositive = diff > 0;
    varianceIsZero = Math.abs(diff) < 0.001;
    const sign = diff > 0 ? "+" : "";
    varianceDisplay = `${sign}${currency} ${diff.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  // Exception code / type if present
  const exceptionType = exc?.exception_type || investigation.exception_id || null;
  const exceptionDesc = exc?.description || null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-mono font-bold">
            TX
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Invoice Exception Details
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              Target Invoice {invoiceId}
            </p>
          </div>
        </div>

        {exceptionType && (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs font-mono">
            <span className="font-semibold">Exception:</span>
            <span>{exceptionType}</span>
          </div>
        )}
      </div>

      {exceptionDesc && (
        <div className="mb-5 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700">
          <span className="font-semibold text-slate-900 block mb-0.5">Reported Variance Trigger:</span>
          {exceptionDesc}
        </div>
      )}

      {/* Grid of Fields */}
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-y-4 gap-x-6 text-xs">
        {/* Invoice ID */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Invoice ID</dt>
          <dd className="font-mono font-semibold text-slate-900 text-sm">
            {invoiceId}
          </dd>
        </div>

        {/* Customer */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Customer</dt>
          <dd className="font-medium text-slate-900 truncate" title={customerName}>
            {customerName}
            {customerId && customerId !== customerName && (
              <span className="block text-[11px] text-slate-500 font-mono">{customerId}</span>
            )}
          </dd>
        </div>

        {/* Billed Amount */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Billed Amount</dt>
          <dd className="font-mono font-semibold text-slate-900 text-sm">
            {billedAmount}
          </dd>
        </div>

        {/* Expected Amount */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Expected Amount</dt>
          <dd className="font-mono font-semibold text-slate-700 text-sm">
            {expectedAmount}
          </dd>
        </div>

        {/* Variance */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Variance</dt>
          <dd
            className={`font-mono font-bold text-sm ${
              varianceIsZero
                ? "text-slate-700"
                : varianceIsPositive
                ? "text-rose-600"
                : varianceDisplay === "Unavailable"
                ? "text-slate-400 font-normal"
                : "text-emerald-600"
            }`}
          >
            {varianceDisplay}
          </dd>
        </div>

        {/* Product / Service */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Product</dt>
          <dd className="font-mono text-slate-900 truncate" title={product}>
            {product}
          </dd>
        </div>

        {/* Invoice Date */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Invoice Date</dt>
          <dd className="text-slate-900 font-medium">
            {invoiceDate}
          </dd>
        </div>

        {/* Governing Contract */}
        <div>
          <dt className="text-slate-500 font-medium mb-1">Governing Contract</dt>
          <dd className="font-mono text-slate-900 truncate" title={contractTitle}>
            {contractTitle}
          </dd>
        </div>
      </dl>
    </div>
  );
}
