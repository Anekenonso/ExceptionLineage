"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchInvestigations } from "@/lib/api";
import { InvestigationResponse } from "@/types/investigation";
import { Navigation } from "@/components/Navigation";
import { StatusBadge } from "@/components/StatusBadge";
import { NewInvestigationModal } from "@/components/NewInvestigationModal";
import { AuthorityBoundaryBanner } from "@/components/AuthorityBoundaryBanner";
import { formatAmount, formatDateTime } from "@/lib/formatters";

export default function Home() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<InvestigationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchInvestigations();
        setInvestigations(data || []);
      } catch {
        // Fallback gracefully
        setInvestigations([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Compute operational overview
  const totalCount = investigations.length;
  const verifiedCount = investigations.filter((i) => i.status === "VERIFIED").length;
  const needsAttentionCount = investigations.filter(
    (i) => i.status === "NEEDS_REVIEW" || i.status === "INSUFFICIENT_EVIDENCE" || i.status === "NOT_VERIFIED"
  ).length;

  const recentItems = investigations.slice(0, 5);

  return (
    <div className="min-h-screen bg-[#faf6ef] flex flex-col text-[#1c2621]">
      <Navigation onOpenNewModal={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Hero Section */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5b7f6a]">
            LINEAGE VERIFICATION ENGINE · BENCHMARK v20.5
          </p>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif text-[#1c2621] leading-tight tracking-tight">
            Understand why a charge was flagged.
            <span className="block italic text-[#c2512f] font-normal mt-1">
              Traced back to the signed agreement.
            </span>
          </h1>
          <p className="text-base sm:text-lg text-[#4a564f] leading-relaxed max-w-2xl mx-auto">
            Trace invoices through contracts, amendments, SOWs and approvals to explain what happened and whether the available records support the charge.
          </p>

          <div className="pt-3 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1f4d3a] px-5 py-2.5 text-sm font-semibold text-[#faf6ef] shadow-xs hover:bg-[#163828] transition focus:outline-none focus:ring-2 focus:ring-[#1f4d3a] focus:ring-offset-2 cursor-pointer"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span>Review an invoice</span>
            </button>

            <Link
              href="/investigations"
              className="inline-flex items-center gap-2 rounded-xl border border-[#cfc2ab] bg-[#fffdf9] px-5 py-2.5 text-sm font-semibold text-[#1c2621] shadow-2xs hover:border-[#1f4d3a] hover:text-[#1f4d3a] transition"
            >
              <span>View investigations</span>
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        {/* Operational Attention Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-5 shadow-2xs">
            <span className="text-xs font-medium text-[#7d877f] block">Total Invoices Reviewed</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-serif text-[#1c2621]">
                {loading ? "…" : totalCount}
              </span>
              <span className="text-xs text-[#7d877f]">records</span>
            </div>
          </div>

          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#7d877f]">Requires Attention</span>
              <span className="bg-[#f8e4db] text-[#9d3f22] border border-[#c2512f]/20 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider">
                Clay
              </span>
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-serif text-[#9d3f22]">
                {loading ? "…" : needsAttentionCount}
              </span>
              <span className="text-xs text-[#7d877f]">unverified / needs review</span>
            </div>
          </div>

          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-5 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#7d877f]">Supported by Records</span>
              <span className="bg-[#dfeae3] text-[#163828] border border-[#1f4d3a]/20 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider">
                Forest
              </span>
            </div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-3xl font-bold font-serif text-[#1f4d3a]">
                {loading ? "…" : verifiedCount}
              </span>
              <span className="text-xs text-[#7d877f]">contractually verified</span>
            </div>
          </div>
        </div>

        {/* Recent Flagged Invoices */}
        <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-6 shadow-2xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#e6dccb]">
            <div>
              <h2 className="text-lg font-serif font-bold text-[#1c2621] tracking-tight">
                Recent Invoice Investigations
              </h2>
              <p className="text-xs text-[#7d877f] mt-0.5">
                Flagged transactions investigated against governing agreements
              </p>
            </div>
            <Link
              href="/investigations"
              className="text-xs font-semibold text-[#1f4d3a] hover:text-[#163828] transition"
            >
              See all investigations →
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-[#7d877f]">
              Loading recent investigations…
            </div>
          ) : recentItems.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-xs text-[#7d877f]">
                No investigations have been started yet.
              </p>
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1f4d3a] hover:underline"
              >
                Review an invoice now →
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#f2ebdf]">
              {recentItems.map((inv) => (
                <div
                  key={inv.investigation_id}
                  onClick={() => router.push(`/investigations/${inv.investigation_id}`)}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#faf6ef] px-3 rounded-xl cursor-pointer transition"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono font-semibold text-xs text-[#1c2621]">
                        {inv.invoice_id}
                      </span>
                      <StatusBadge status={inv.status} size="sm" />
                    </div>
                    <p className="text-xs text-[#4a564f]">
                      {inv.customer_name || inv.customer_id || "Customer"} —{" "}
                      <span className="font-mono font-medium text-[#1c2621]">
                        {formatAmount(inv.amount, inv.currency || "USD")}
                      </span>
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-[#7d877f] font-mono text-[11px]">
                      {formatDateTime(inv.created_at)}
                    </span>
                    <span className="text-[#1f4d3a] font-semibold group-hover:underline">
                      Review →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3 Core Value Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-6 shadow-2xs space-y-2">
            <div className="h-8 w-8 rounded-lg bg-[#faf6ef] text-[#1f4d3a] border border-[#e6dccb] flex items-center justify-center font-bold font-serif text-xs">
              01
            </div>
            <h3 className="font-serif font-bold text-[#1c2621] text-base tracking-tight">
              Contract & Amendment Lineage
            </h3>
            <p className="text-xs text-[#4a564f] leading-relaxed">
              Trace invoices directly to the governing master agreements, effective amendments, and specific SOW terms that authorize billed rates.
            </p>
          </div>

          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-6 shadow-2xs space-y-2">
            <div className="h-8 w-8 rounded-lg bg-[#faf6ef] text-[#1f4d3a] border border-[#e6dccb] flex items-center justify-center font-bold font-serif text-xs">
              02
            </div>
            <h3 className="font-serif font-bold text-[#1c2621] text-base tracking-tight">
              Operational Approvals & Evidence
            </h3>
            <p className="text-xs text-[#4a564f] leading-relaxed">
              Verify whether billing discrepancies or rate variances have verified sign-offs and evidentiary documentation recorded.
            </p>
          </div>

          <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-6 shadow-2xs space-y-2">
            <div className="h-8 w-8 rounded-lg bg-[#faf6ef] text-[#1f4d3a] border border-[#e6dccb] flex items-center justify-center font-bold font-serif text-xs">
              03
            </div>
            <h3 className="font-serif font-bold text-[#1c2621] text-base tracking-tight">
              Deterministic Verification
            </h3>
            <p className="text-xs text-[#4a564f] leading-relaxed">
              Rule evaluations fail closed when critical evidence is absent. Trust determinations backed by immutable proof.
            </p>
          </div>
        </div>

        {/* How We Verify Banner */}
        <AuthorityBoundaryBanner />

        {/* Secondary Technical Trace / Architecture Disclosure */}
        <div className="rounded-2xl border border-[#e6dccb] bg-[#fffdf9] p-5 shadow-2xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-[#1c2621] tracking-tight">
                Engine & Technical Implementation Details
              </h3>
              <p className="text-[11px] text-[#7d877f]">
                Explore backend graph retrieval, agent reasoning, and evaluation metrics
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowTechnicalDetails((v) => !v)}
              className="text-xs font-medium text-[#4a564f] hover:text-[#1c2621] border border-[#e6dccb] px-3 py-1.5 rounded-lg hover:bg-[#faf6ef] transition cursor-pointer"
            >
              {showTechnicalDetails ? "Hide technical details" : "View technical details"}
            </button>
          </div>

          {showTechnicalDetails && (
            <div className="mt-4 pt-4 border-t border-[#e6dccb] text-xs space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[#4a564f] font-mono text-[11px]">
                <div className="p-3.5 rounded-xl bg-[#faf6ef] border border-[#e6dccb]">
                  <span className="text-[#7d877f] block text-[10px] uppercase">Retrieval Engine</span>
                  <span className="font-semibold text-[#1c2621]">Neo4j Property Graph</span>
                  <p className="text-[10px] text-[#7d877f] mt-1">Multi-hop directional contractual relationship traversal</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#faf6ef] border border-[#e6dccb]">
                  <span className="text-[#7d877f] block text-[10px] uppercase">Reasoning Core</span>
                  <span className="font-semibold text-[#1c2621]">Controlled Agentic Loop</span>
                  <p className="text-[10px] text-[#7d877f] mt-1">Tool execution with backtracking and early stopping</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#faf6ef] border border-[#e6dccb]">
                  <span className="text-[#7d877f] block text-[10px] uppercase">Authority Enforcement</span>
                  <span className="font-semibold text-[#1c2621]">Deterministic Rule Engine</span>
                  <p className="text-[10px] text-[#7d877f] mt-1">Fail-closed contractual compliance verification</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-[#e6dccb] bg-[#fffdf9] py-6 text-center text-xs text-[#7d877f]">
        ExceptionLineage — Evidence-backed transaction investigation.
      </footer>

      {/* New Investigation Modal */}
      <NewInvestigationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={(id) => router.push(`/investigations/${id}`)}
      />
    </div>
  );
}
