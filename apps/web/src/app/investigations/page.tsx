"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { InvestigationResponse } from "@/types/investigation";
import { fetchInvestigations, createInvestigation } from "@/lib/api";
import { ALL_FIXTURES } from "@/fixtures/investigations";
import { Navigation } from "@/components/Navigation";
import { StatusBadge } from "@/components/StatusBadge";
import { NewInvestigationModal } from "@/components/NewInvestigationModal";
import { LoadingSkeleton, EmptyState, ApiErrorBanner } from "@/components/StateHandlers";
import { AuthorityBoundaryBanner } from "@/components/AuthorityBoundaryBanner";
import { formatAmount, formatDateTime } from "@/lib/formatters";

export default function InvestigationsDashboard() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<InvestigationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFixtures, setUsingFixtures] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isSeeding, setIsSeeding] = useState<boolean>(false);

  // Load investigations
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInvestigations();
      setInvestigations(data);
      setUsingFixtures(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load investigations from API.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUseFixtures = () => {
    setInvestigations(ALL_FIXTURES);
    setUsingFixtures(true);
    setError(null);
  };

  // Seed sample cases into the live backend
  const handleRunSeedScenarios = async () => {
    setIsSeeding(true);
    setError(null);
    try {
      const scenarios = [
        { invoice: "INV-1001", exception: "EX-001" },
        { invoice: "INV-1002", exception: "EX-002" },
        { invoice: "INV-1003", exception: "EX-003" },
        { invoice: "INV-1004", exception: "EX-004" },
        { invoice: "INV-1005", exception: "EX-005" },
        { invoice: "INV-1006", exception: "EX-006" },
        { invoice: "INV-1007", exception: "EX-007" },
        { invoice: "INV-1008", exception: "EX-008" },
      ];

      for (const sc of scenarios) {
        await createInvestigation(sc.invoice, sc.exception);
      }

      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load sample cases";
      setError(msg);
    } finally {
      setIsSeeding(false);
    }
  };

  // Search and filter logic
  const filteredInvestigations = useMemo(() => {
    return investigations.filter((inv) => {
      // Status filter
      if (statusFilter !== "ALL" && inv.status !== statusFilter) {
        return false;
      }

      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const invIdMatch = inv.investigation_id?.toLowerCase().includes(query);
        const invoiceMatch = inv.invoice_id?.toLowerCase().includes(query);
        const customerMatch =
          inv.customer_name?.toLowerCase().includes(query) ||
          inv.customer_id?.toLowerCase().includes(query);
        const summaryMatch = inv.summary?.toLowerCase().includes(query);
        if (!invIdMatch && !invoiceMatch && !customerMatch && !summaryMatch) {
          return false;
        }
      }

      return true;
    });
  }, [investigations, statusFilter, searchQuery]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navigation onOpenNewModal={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Investigations
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Review flagged invoices against contracts, amendments and approvals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {investigations.length === 0 && !loading && !error && (
              <button
                type="button"
                onClick={handleRunSeedScenarios}
                disabled={isSeeding}
                className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 disabled:opacity-50 transition"
              >
                {isSeeding ? "Loading sample cases…" : "Load sample cases"}
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span>Review an invoice</span>
            </button>
          </div>
        </div>

        {/* How We Verify Banner */}
        <AuthorityBoundaryBanner />

        {/* Error banner if API is unreachable */}
        {error && (
          <ApiErrorBanner
            error={error}
            onRetry={loadData}
            onUseFixtures={handleUseFixtures}
          />
        )}

        {/* Fixtures active indicator */}
        {usingFixtures && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 flex items-center justify-between">
            <span className="font-medium">
              Demo Mode Active: Displaying local sample investigations.
            </span>
            <button
              type="button"
              onClick={loadData}
              className="underline font-semibold hover:text-amber-950"
            >
              Switch back to Live API
            </button>
          </div>
        )}

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search by invoice, customer, or finding..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 shadow-2xs"
            />
          </div>

          {/* Filter Status Pills - Human Labels */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0 text-xs">
            {[
              { id: "ALL", label: "All" },
              { id: "VERIFIED", label: "Verified" },
              { id: "NOT_VERIFIED", label: "Not verified" },
              { id: "INSUFFICIENT_EVIDENCE", label: "Not enough evidence" },
              { id: "NEEDS_REVIEW", label: "Needs review" },
              { id: "FAILED", label: "Review couldn't be completed" },
            ].map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setStatusFilter(st.id)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition shrink-0 ${
                  statusFilter === st.id
                    ? "bg-slate-900 text-white font-semibold shadow-2xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Section: Loading, Empty, or Table */}
        {loading ? (
          <LoadingSkeleton title="Loading investigations…" />
        ) : filteredInvestigations.length === 0 ? (
          investigations.length === 0 ? (
            <EmptyState
              title="No Invoices Under Review"
              description="No transaction exceptions have been reviewed yet. Enter an invoice to trace contracts, amendments, and approvals."
              actionLabel="Review an invoice"
              onAction={() => setIsModalOpen(true)}
              secondaryActionLabel="Load sample cases"
              onSecondaryAction={handleRunSeedScenarios}
            />
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-500">
              No investigations match the current search or status filter.
            </div>
          )
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 text-[11px] font-medium">
                    <th className="py-3 px-4">Invoice</th>
                    <th className="py-3 px-4">Customer</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Finding</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4 text-right">Review</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredInvestigations.map((inv) => {
                    const formattedDate = formatDateTime(inv.created_at);
                    const amountDisplay = formatAmount(inv.amount, inv.currency || "USD");

                    return (
                      <tr
                        key={inv.investigation_id}
                        className="hover:bg-slate-50/80 transition cursor-pointer group"
                        onClick={() => router.push(`/investigations/${inv.investigation_id}`)}
                      >
                        {/* Invoice */}
                        <td className="py-3.5 px-4 font-semibold text-slate-900">
                          <Link
                            href={`/investigations/${inv.investigation_id}`}
                            className="hover:underline flex flex-col"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <span className="font-mono">{inv.invoice_id}</span>
                            {inv.exception_id && (
                              <span className="text-[11px] text-slate-400 font-normal">
                                Ref: {inv.exception_id}
                              </span>
                            )}
                          </Link>
                        </td>

                        {/* Customer */}
                        <td className="py-3.5 px-4 text-slate-800 font-medium">
                          <div className="truncate max-w-[220px]" title={inv.customer_name || inv.customer_id || "—"}>
                            {inv.customer_name || inv.customer_id || "—"}
                          </div>
                        </td>

                        {/* Amount */}
                        <td className="py-3.5 px-4 font-mono font-medium text-slate-900">
                          {amountDisplay}
                        </td>

                        {/* Finding */}
                        <td className="py-3.5 px-4">
                          <StatusBadge status={inv.status} size="sm" />
                        </td>

                        {/* Date */}
                        <td className="py-3.5 px-4 text-slate-500 text-[11px]">
                          {formattedDate}
                        </td>

                        {/* Review Action */}
                        <td className="py-3.5 px-4 text-right">
                          <span className="text-slate-700 group-hover:text-slate-900 font-semibold text-xs inline-flex items-center gap-1">
                            Review →
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={(id) => router.push(`/investigations/${id}`)}
      />
    </div>
  );
}
