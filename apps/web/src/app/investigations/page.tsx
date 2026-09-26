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
  const [sortBy, setSortBy] = useState<string>("date_desc");
  const [viewMode, setViewMode] = useState<"table" | "card">("table");
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

  // Status counts
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: investigations.length };
    investigations.forEach((inv) => {
      const st = (inv.status || "").toUpperCase();
      counts[st] = (counts[st] || 0) + 1;
    });
    return counts;
  }, [investigations]);

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

  // Sort logic
  const sortedInvestigations = useMemo(() => {
    return [...filteredInvestigations].sort((a, b) => {
      if (sortBy === "date_desc") {
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
      if (sortBy === "date_asc") {
        return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
      }
      if (sortBy === "amount_desc") {
        return (Number(b.amount) || 0) - (Number(a.amount) || 0);
      }
      if (sortBy === "amount_asc") {
        return (Number(a.amount) || 0) - (Number(b.amount) || 0);
      }
      if (sortBy === "customer_asc") {
        return (a.customer_name || a.customer_id || "").localeCompare(b.customer_name || b.customer_id || "");
      }
      return 0;
    });
  }, [filteredInvestigations, sortBy]);

  return (
    <div className="min-h-screen bg-[#faf6ef] flex flex-col text-[#1c2621]">
      <Navigation onOpenNewModal={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#e6dccb]">
          <div>
            <h1 className="text-2xl sm:text-3xl font-serif font-bold tracking-tight text-[#1c2621]">
              Investigations
            </h1>
            <p className="text-xs text-[#7d877f] mt-1">
              Review flagged invoices against contracts, amendments and approvals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {investigations.length === 0 && !loading && !error && (
              <button
                type="button"
                onClick={handleRunSeedScenarios}
                disabled={isSeeding}
                className="inline-flex items-center gap-2 rounded-xl border border-[#cfc2ab] bg-[#fffdf9] px-3.5 py-2 text-xs font-semibold text-[#1c2621] shadow-2xs hover:border-[#1f4d3a] hover:text-[#1f4d3a] disabled:opacity-50 transition cursor-pointer"
              >
                {isSeeding ? "Loading sample cases…" : "Load sample cases"}
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1f4d3a] px-4 py-2 text-xs font-semibold text-[#faf6ef] shadow-xs hover:bg-[#163828] transition cursor-pointer"
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
          <div className="rounded-2xl border border-[#b97d10]/30 bg-[#fbefd2] p-3 text-xs text-[#8c5e08] flex items-center justify-between shadow-2xs">
            <span className="font-medium">
              Demo Mode Active: Displaying local sample investigations.
            </span>
            <button
              type="button"
              onClick={loadData}
              className="underline font-semibold hover:text-[#1c2621] cursor-pointer"
            >
              Switch back to Live API
            </button>
          </div>
        )}

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 bg-[#fffdf9] p-3.5 rounded-2xl border border-[#e6dccb] shadow-2xs">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#7d877f]">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search by invoice, customer, or finding..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-[#cfc2ab] text-xs text-[#1c2621] placeholder:text-[#7d877f] focus:outline-none focus:border-[#1f4d3a] focus:ring-2 focus:ring-[#1f4d3a]/15 shadow-2xs bg-[#fffdf9]"
            />
          </div>

          {/* Filter Status Pills - Contained Nestor style */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 text-xs font-mono">
            {[
              { id: "ALL", label: `[ ALL (${statusCounts["ALL"] || 0}) ]`, activeBg: "bg-[#1c2621] text-[#faf6ef] border-[#1c2621]" },
              { id: "VERIFIED", label: `[ VERIFIED (${statusCounts["VERIFIED"] || 0}) ]`, activeBg: "bg-[#dfeae3] text-[#163828] border-[#1f4d3a]/30" },
              { id: "NEEDS_REVIEW", label: `[ NEEDS REVIEW (${statusCounts["NEEDS_REVIEW"] || 0}) ]`, activeBg: "bg-[#f8e4db] text-[#9d3f22] border-[#c2512f]/30" },
              { id: "INSUFFICIENT_EVIDENCE", label: `[ NOT ENOUGH EVIDENCE (${statusCounts["INSUFFICIENT_EVIDENCE"] || 0}) ]`, activeBg: "bg-[#fbefd2] text-[#8c5e08] border-[#b97d10]/30" },
              { id: "NOT_VERIFIED", label: `[ NOT VERIFIED (${statusCounts["NOT_VERIFIED"] || 0}) ]`, activeBg: "bg-[#f8e4db] text-[#9d3f22] border-[#c2512f]/30" },
            ].map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setStatusFilter(st.id)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold uppercase tracking-wider transition shrink-0 border cursor-pointer ${
                  statusFilter === st.id
                    ? st.activeBg
                    : "border-[#e6dccb] text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef]"
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Sort & View Mode Switcher */}
          <div className="flex items-center gap-2 shrink-0 pt-1 lg:pt-0">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-[11px] rounded-lg border border-[#cfc2ab] bg-[#fffdf9] px-2.5 py-1 text-[#4a564f] focus:outline-none focus:border-[#1f4d3a] cursor-pointer"
            >
              <option value="date_desc">Sort: Newest</option>
              <option value="date_asc">Sort: Oldest</option>
              <option value="amount_desc">Sort: Amount (High to Low)</option>
              <option value="amount_asc">Sort: Amount (Low to High)</option>
              <option value="customer_asc">Sort: Customer (A-Z)</option>
            </select>

            <div className="flex items-center rounded-lg border border-[#cfc2ab] p-0.5 bg-[#faf6ef]">
              <button
                type="button"
                onClick={() => setViewMode("table")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition cursor-pointer ${
                  viewMode === "table" ? "bg-[#fffdf9] text-[#1c2621] shadow-2xs font-semibold" : "text-[#7d877f] hover:text-[#1c2621]"
                }`}
              >
                Table
              </button>
              <button
                type="button"
                onClick={() => setViewMode("card")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition cursor-pointer ${
                  viewMode === "card" ? "bg-[#fffdf9] text-[#1c2621] shadow-2xs font-semibold" : "text-[#7d877f] hover:text-[#1c2621]"
                }`}
              >
                Cards
              </button>
            </div>
          </div>
        </div>

        {/* Content Section: Loading, Empty, or Table / Cards */}
        {loading ? (
          <LoadingSkeleton title="Loading investigations…" />
        ) : sortedInvestigations.length === 0 ? (
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
            <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-8 text-center text-xs text-[#7d877f]">
              No investigations match the current search or status filter.
            </div>
          )
        ) : viewMode === "card" ? (
          /* Card View Mode */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedInvestigations.map((inv) => (
              <div
                key={inv.investigation_id}
                onClick={() => router.push(`/investigations/${inv.investigation_id}`)}
                className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-5 shadow-2xs hover:shadow-md hover:border-[#1f4d3a]/40 transition cursor-pointer flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono font-bold text-sm text-[#1c2621]">
                      {inv.invoice_id}
                    </span>
                    <StatusBadge status={inv.status} size="sm" />
                  </div>
                  <h3 className="font-semibold text-xs text-[#1c2621] truncate">
                    {inv.customer_name || inv.customer_id || "Customer"}
                  </h3>
                  <p className="text-xs text-[#4a564f] line-clamp-2">
                    {inv.summary || "Investigation records and evidence evaluation."}
                  </p>
                </div>

                <div className="pt-3 border-t border-[#f2ebdf] flex items-center justify-between text-xs">
                  <span className="font-serif font-bold text-[#1c2621] text-base">
                    {formatAmount(inv.amount, inv.currency || "USD")}
                  </span>
                  <span className="text-[#1f4d3a] font-semibold">
                    Inspect →
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* High-Density Table View Mode */
          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] shadow-2xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#e6dccb] bg-[#faf6ef] text-[#7d877f] text-[10px] font-mono uppercase tracking-wider">
                    <th className="py-3 px-4">Invoice ID</th>
                    <th className="py-3 px-4">Customer</th>
                    <th className="py-3 px-4">Amount</th>
                    <th className="py-3 px-4">Finding</th>
                    <th className="py-3 px-4">Verification Score</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f2ebdf]">
                  {sortedInvestigations.map((inv) => {
                    const formattedDate = formatDateTime(inv.created_at);
                    const amountDisplay = formatAmount(inv.amount, inv.currency || "USD");
                    const passedChecks = (inv.validation_results || []).filter((r) => r.status === "PASS").length;
                    const totalChecks = (inv.validation_results || []).length;

                    return (
                      <tr
                        key={inv.investigation_id}
                        className="hover:bg-[#faf6ef] transition cursor-pointer group"
                        onClick={() => router.push(`/investigations/${inv.investigation_id}`)}
                      >
                        {/* Invoice */}
                        <td className="py-3.5 px-4 font-semibold text-[#1c2621]">
                          <Link
                            href={`/investigations/${inv.investigation_id}`}
                            className="hover:underline flex flex-col"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <span className="font-mono font-bold text-[#1c2621]">{inv.invoice_id}</span>
                            {inv.exception_id && (
                              <span className="text-[10px] text-[#7d877f] font-mono font-normal">
                                {inv.exception_id}
                              </span>
                            )}
                          </Link>
                        </td>

                        {/* Customer */}
                        <td className="py-3.5 px-4 text-[#1c2621] font-medium">
                          <div className="truncate max-w-[200px]" title={inv.customer_name || inv.customer_id || "—"}>
                            {inv.customer_name || inv.customer_id || "—"}
                          </div>
                        </td>

                        {/* Amount */}
                        <td className="py-3.5 px-4 font-mono font-medium text-[#1c2621]">
                          {amountDisplay}
                        </td>

                        {/* Finding */}
                        <td className="py-3.5 px-4">
                          <StatusBadge status={inv.status} size="sm" />
                        </td>

                        {/* Verification Score */}
                        <td className="py-3.5 px-4 font-mono text-[11px] text-[#4a564f]">
                          {totalChecks > 0 ? (
                            <span className={passedChecks === totalChecks ? "text-[#1f4d3a] font-semibold" : "text-[#7d877f]"}>
                              {passedChecks}/{totalChecks} checks passed
                            </span>
                          ) : (
                            <span className="text-[#7d877f]">Pending</span>
                          )}
                        </td>

                        {/* Date */}
                        <td className="py-3.5 px-4 text-[#7d877f] text-[11px] font-mono">
                          {formattedDate}
                        </td>

                        {/* Review Action */}
                        <td className="py-3.5 px-4 text-right">
                          <span className="text-[#1f4d3a] group-hover:underline font-semibold text-xs inline-flex items-center gap-1">
                            Inspect →
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
