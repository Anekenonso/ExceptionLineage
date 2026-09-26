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
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navigation onOpenNewModal={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Hero Section */}
        <div className="text-center space-y-5 max-w-3xl mx-auto">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900">
            Understand why a transaction was flagged
          </h1>
          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Trace invoices through contracts, amendments and approvals to see what happened and whether the available records support the charge.
          </p>

          <div className="pt-3 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              <span>Review an invoice</span>
            </button>

            <Link
              href="/investigations"
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
            >
              <span>View investigations</span>
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        {/* Operational Attention Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <span className="text-xs font-medium text-slate-500 block">Total Invoices Reviewed</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {loading ? "…" : totalCount}
              </span>
              <span className="text-xs text-slate-500">records</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <span className="text-xs font-medium text-slate-500 block">Requires Attention</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-600 font-mono">
                {loading ? "…" : needsAttentionCount}
              </span>
              <span className="text-xs text-slate-500">unverified / needs review</span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <span className="text-xs font-medium text-slate-500 block">Supported by Records</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-600 font-mono">
                {loading ? "…" : verifiedCount}
              </span>
              <span className="text-xs text-slate-500">contractually verified</span>
            </div>
          </div>
        </div>

        {/* Recent Flagged Invoices Needing Attention */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Recent Invoice Investigations
              </h2>
              <p className="text-xs text-slate-500">
                Flagged transactions investigated against governing agreements
              </p>
            </div>
            <Link
              href="/investigations"
              className="text-xs font-semibold text-slate-700 hover:text-slate-900"
            >
              See all investigations →
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">
              Loading recent investigations…
            </div>
          ) : recentItems.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-xs text-slate-500">
                No investigations have been started yet.
              </p>
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-900 hover:underline"
              >
                Review an invoice now →
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentItems.map((inv) => (
                <div
                  key={inv.investigation_id}
                  onClick={() => router.push(`/investigations/${inv.investigation_id}`)}
                  className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/80 px-2 rounded-lg cursor-pointer transition"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-xs text-slate-900">
                        {inv.invoice_id}
                      </span>
                      <StatusBadge status={inv.status} size="sm" />
                    </div>
                    <p className="text-xs text-slate-600">
                      {inv.customer_name || inv.customer_id || "Customer"} —{" "}
                      <span className="font-mono font-medium text-slate-900">
                        {formatAmount(inv.amount, inv.currency || "USD")}
                      </span>
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-slate-400 font-mono text-[11px]">
                      {formatDateTime(inv.created_at)}
                    </span>
                    <span className="text-slate-700 font-medium group-hover:text-slate-900">
                      Review →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3 Core Value Pillars - Product Oriented */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-blue-50 text-blue-700 flex items-center justify-center font-bold text-xs">
              01
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              Contract & Amendment Lineage
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Trace invoices directly to the governing master agreements, effective amendments, and specific SOW terms that authorize billed rates.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-purple-50 text-purple-700 flex items-center justify-center font-bold text-xs">
              02
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              Operational Approvals & Evidence
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Verify whether billing discrepancies or rate variances have verified sign-offs and evidentiary documentation recorded.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xs">
              03
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              Deterministic Verification
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Rule evaluations fail closed when critical evidence is absent. Trust determinations backed by immutable proof.
            </p>
          </div>
        </div>

        {/* How We Verify Banner */}
        <AuthorityBoundaryBanner />

        {/* Secondary Technical Trace / Architecture Disclosure */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-semibold text-slate-900 tracking-tight">
                Engine & Technical Implementation Details
              </h3>
              <p className="text-[11px] text-slate-500">
                Explore backend graph retrieval, agent reasoning, and evaluation metrics
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowTechnicalDetails((v) => !v)}
              className="text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 px-3 py-1.5 rounded-md hover:bg-slate-50 transition"
            >
              {showTechnicalDetails ? "Hide technical details" : "View technical details"}
            </button>
          </div>

          {showTechnicalDetails && (
            <div className="mt-4 pt-4 border-t border-slate-100 text-xs space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-slate-700 font-mono text-[11px]">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase">Retrieval Engine</span>
                  <span className="font-semibold text-slate-900">Neo4j Property Graph</span>
                  <p className="text-[10px] text-slate-500 mt-1">Multi-hop directional contractual relationship traversal</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase">Reasoning Core</span>
                  <span className="font-semibold text-slate-900">Controlled Agentic Loop</span>
                  <p className="text-[10px] text-slate-500 mt-1">Tool execution with backtracking and early stopping</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-slate-400 block text-[10px] uppercase">Authority Enforcement</span>
                  <span className="font-semibold text-slate-900">Deterministic Rule Engine</span>
                  <p className="text-[10px] text-slate-500 mt-1">Fail-closed contractual compliance verification</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
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
