"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  InvestigationResponse,
  InvestigationEvidenceTrace,
  LineageData,
  EvidenceItem,
} from "@/types/investigation";
import {
  fetchInvestigation,
  fetchInvestigationTrace,
  fetchInvestigationLineage,
} from "@/lib/api";
import { ALL_FIXTURES, FIXTURE_EVIDENCE_TRACE } from "@/fixtures/investigations";
import { Navigation } from "@/components/Navigation";
import { StatusBadge } from "@/components/StatusBadge";
import { AuthorityBoundaryBanner } from "@/components/AuthorityBoundaryBanner";
import { InvoiceExceptionCard } from "@/components/InvoiceExceptionCard";
import { DeterminationCard } from "@/components/DeterminationCard";
import { LineageGraph } from "@/components/LineageGraph";
import { ValidationSection } from "@/components/ValidationSection";
import { EvidenceSection } from "@/components/EvidenceSection";
import { InvestigationActivityTrace } from "@/components/InvestigationActivityTrace";
import { ExportReportModal } from "@/components/ExportReportModal";
import { LoadingSkeleton, EmptyState, ApiErrorBanner } from "@/components/StateHandlers";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";
import { formatAmount } from "@/lib/formatters";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function InvestigationWorkspacePage({ params }: PageProps) {
  const resolvedParams = use(params);
  const investigationId = resolvedParams.id;

  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [trace, setTrace] = useState<InvestigationEvidenceTrace | null>(null);
  const [lineage, setLineage] = useState<LineageData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [usingFixtures, setUsingFixtures] = useState<boolean>(false);
  const [isExportOpen, setIsExportOpen] = useState<boolean>(false);
  const [inspectedEvidence, setInspectedEvidence] = useState<EvidenceItem | null>(null);

  const loadInvestigation = async () => {
    setLoading(true);
    setError(null);
    try {
      const invData = await fetchInvestigation(investigationId);
      setInvestigation(invData);

      // Attempt to load trace & lineage in parallel
      try {
        const traceData = await fetchInvestigationTrace(investigationId);
        setTrace(traceData);
      } catch {
        // Trace is optional / fallback to events on investigation
      }

      try {
        const linData = await fetchInvestigationLineage(investigationId);
        setLineage(linData || invData.lineage || null);
      } catch {
        setLineage(invData.lineage || null);
      }

      setUsingFixtures(false);
    } catch (err: unknown) {
      // Check if there is a matching fixture
      const fixtureMatch = ALL_FIXTURES.find(
        (f) =>
          f.investigation_id === investigationId ||
          f.invoice_id === investigationId ||
          investigationId.includes(f.invoice_id.toLowerCase())
      );

      if (fixtureMatch) {
        setInvestigation(fixtureMatch);
        setLineage(fixtureMatch.lineage || null);
        setTrace(FIXTURE_EVIDENCE_TRACE);
        setUsingFixtures(true);
      } else {
        const msg = err instanceof Error ? err.message : "Failed to load investigation details.";
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvestigation();
  }, [investigationId]);

  const handleUseFixtures = () => {
    const fallback =
      ALL_FIXTURES.find((f) => f.investigation_id === investigationId) || ALL_FIXTURES[0];
    setInvestigation(fallback);
    setLineage(fallback.lineage || null);
    setTrace(FIXTURE_EVIDENCE_TRACE);
    setUsingFixtures(true);
    setError(null);
  };

  const handleSelectEvidenceById = (evId: string) => {
    const allEvidence = lineage?.evidence || investigation?.lineage?.evidence || [];
    const found = allEvidence.find((e) => e.id === evId);
    if (found) {
      setInspectedEvidence(found);
    }
  };

  const customerDisplay =
    investigation?.customer_name ||
    lineage?.customer?.name ||
    investigation?.customer_id ||
    "Customer";

  const amountDisplay = formatAmount(investigation?.amount, investigation?.currency || "USD");

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navigation
        onOpenReportModal={() => {
          if (investigation) setIsExportOpen(true);
        }}
      />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Error State */}
        {error && (
          <ApiErrorBanner
            error={error}
            onRetry={loadInvestigation}
            onUseFixtures={handleUseFixtures}
          />
        )}

        {/* Fixtures Indicator */}
        {usingFixtures && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 flex items-center justify-between">
            <span className="font-medium">
              Demo Mode Active: Displaying local sample investigation.
            </span>
            <button
              type="button"
              onClick={loadInvestigation}
              className="underline font-semibold hover:text-amber-950"
            >
              Retry Live API
            </button>
          </div>
        )}

        {loading ? (
          <LoadingSkeleton title={`Loading invoice review…`} />
        ) : !investigation ? (
          <EmptyState
            title="Investigation Not Found"
            description={`Could not find an invoice investigation matching "${investigationId}".`}
            actionLabel="Return to Investigations"
            onAction={() => window.location.assign("/investigations")}
          />
        ) : (
          <div className="space-y-8">
            {/* Top Bar: Back Link & Quick Actions */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
              <div className="space-y-1">
                <Link
                  href="/investigations"
                  className="text-xs text-slate-500 hover:text-slate-900 font-medium flex items-center gap-1"
                >
                  ← Back to investigations
                </Link>
                <div className="flex items-center gap-3 pt-1">
                  <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
                    Review: {investigation.invoice_id}
                  </h1>
                  <StatusBadge status={investigation.status} size="md" />
                </div>
                <p className="text-xs text-slate-500">
                  {customerDisplay} · {amountDisplay}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsExportOpen(true)}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
                >
                  <svg
                    className="h-4 w-4 text-slate-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"
                    />
                  </svg>
                  <span>Export report</span>
                </button>
              </div>
            </div>

            {/* =========================================================================
                PHASE 6 INFORMATION HIERARCHY
                1. Invoice
                2. Finding
                3. Why (integrated inside Finding card)
                4. Verification checks
                5. Contract history
                6. Supporting records
                7. Investigation activity & Technical trace
                ========================================================================= */}

            {/* 1. INVOICE SECTION */}
            <InvoiceExceptionCard
              investigation={investigation}
              lineage={lineage || investigation.lineage}
            />

            {/* 2 & 3. FINDING & WHY SECTION (Dominant Focal Point) */}
            <DeterminationCard investigation={investigation} />

            {/* 4. VERIFICATION CHECKS */}
            <ValidationSection
              results={investigation.validation_results}
              onSelectEvidenceId={handleSelectEvidenceById}
            />

            {/* 5. CONTRACT HISTORY */}
            <LineageGraph
              lineage={lineage || investigation.lineage}
              onSelectEvidence={(ev) => setInspectedEvidence(ev)}
            />

            {/* 6. SUPPORTING RECORDS */}
            <EvidenceSection
              evidence={lineage?.evidence || investigation.lineage?.evidence}
              citedEvidenceIds={investigation.cited_evidence_ids}
            />

            {/* 7. INVESTIGATION ACTIVITY & TECHNICAL TRACE */}
            <InvestigationActivityTrace
              trace={trace}
              events={investigation.events || investigation.agent_events}
            />

            {/* 8. HOW WE VERIFY */}
            <AuthorityBoundaryBanner />
          </div>
        )}
      </main>

      {/* Export Report Modal */}
      {investigation && (
        <ExportReportModal
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
          investigation={investigation}
          trace={trace}
        />
      )}

      {/* Quick Evidence Inspector Drawer */}
      <EvidenceDrawer
        evidence={inspectedEvidence}
        onClose={() => setInspectedEvidence(null)}
      />
    </div>
  );
}
