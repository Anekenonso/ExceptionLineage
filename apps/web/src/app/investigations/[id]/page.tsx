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

  // Find evidence by ID for quick inspection from validation checks
  const handleSelectEvidenceById = (evId: string) => {
    const allEvidence = lineage?.evidence || investigation?.lineage?.evidence || [];
    const found = allEvidence.find((e) => e.id === evId);
    if (found) {
      setInspectedEvidence(found);
    }
  };

  // Compute duration display
  const durationDisplay =
    investigation?.duration_seconds !== undefined && investigation?.duration_seconds !== null
      ? `${investigation.duration_seconds}s`
      : investigation?.agent_metrics?.investigation_duration_ms
      ? `${(investigation.agent_metrics.investigation_duration_ms / 1000).toFixed(2)}s`
      : "—";

  const customerDisplay =
    investigation?.customer_name ||
    lineage?.customer?.name ||
    investigation?.customer_id ||
    "Unavailable";

  const formattedStarted = investigation?.created_at
    ? new Date(investigation.created_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZone: "UTC",
      }) + " UTC"
    : "—";

  const formattedCompleted = investigation?.updated_at
    ? new Date(investigation.updated_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZone: "UTC",
      }) + " UTC"
    : investigation?.status !== "QUEUED" &&
      investigation?.status !== "INVESTIGATING" &&
      investigation?.status !== "VALIDATING"
    ? formattedStarted
    : "In Progress";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navigation />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
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
              Demo Fixture Active: Viewing isolated development test data for{" "}
              {investigation?.status}.
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
          <LoadingSkeleton title={`Loading investigation ${investigationId}…`} />
        ) : !investigation ? (
          <EmptyState
            title="Investigation Not Found"
            description={`Could not find an investigation matching identifier "${investigationId}".`}
            actionLabel="Return to Investigations"
            onAction={() => window.location.assign("/investigations")}
          />
        ) : (
          <div className="space-y-6">
            {/* =========================================================================
                1. HEADER
                - Investigation ID
                - Invoice ID
                - Customer
                - Investigation type
                - Current status
                - Started
                - Completed
                - Duration
                Actions: Export Report, Back to Investigations
                ========================================================================= */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-slate-100">
                {/* Identification & Status */}
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Link
                      href="/investigations"
                      className="text-xs text-slate-500 hover:text-slate-800 font-mono flex items-center gap-1"
                    >
                      ← Back to Investigations
                    </Link>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 pt-1">
                    <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 font-mono">
                      {investigation.investigation_id}
                    </h1>
                    <StatusBadge status={investigation.status} size="md" />
                  </div>
                  <p className="text-xs text-slate-500 font-mono">
                    Target Invoice:{" "}
                    <strong className="text-slate-900">{investigation.invoice_id}</strong>
                    {investigation.exception_id && (
                      <span>
                        {" "}
                        | Exception Ref:{" "}
                        <strong className="text-slate-900">{investigation.exception_id}</strong>
                      </span>
                    )}
                  </p>
                </div>

                {/* Actions */}
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
                    <span>Export Report</span>
                  </button>

                  <Link
                    href="/investigations"
                    className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
                  >
                    <span>Dashboard</span>
                  </Link>
                </div>
              </div>

              {/* Metadata Summary Row */}
              <dl className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-y-3 gap-x-6 pt-4 text-xs">
                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Customer</dt>
                  <dd className="font-semibold text-slate-900 truncate" title={customerDisplay}>
                    {customerDisplay}
                  </dd>
                </div>

                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Investigation Type</dt>
                  <dd className="font-medium text-slate-900 truncate">
                    Rate & Terms Compliance
                  </dd>
                </div>

                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Started</dt>
                  <dd className="font-mono text-slate-700 text-[11px]">{formattedStarted}</dd>
                </div>

                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Completed</dt>
                  <dd className="font-mono text-slate-700 text-[11px]">{formattedCompleted}</dd>
                </div>

                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Execution Duration</dt>
                  <dd className="font-mono font-semibold text-slate-900">{durationDisplay}</dd>
                </div>

                <div>
                  <dt className="text-slate-400 text-[11px] font-medium">Substantiated Citations</dt>
                  <dd className="font-mono font-bold text-emerald-700">
                    {investigation.cited_evidence_ids?.length || 0} Records
                  </dd>
                </div>
              </dl>
            </div>

            {/* Authority Boundary Banner */}
            <AuthorityBoundaryBanner />

            {/* =========================================================================
                2. INVOICE EXCEPTION + DETERMINATION
                Two-column desktop grid for immediate clarity
                ========================================================================= */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Invoice Exception Card */}
              <InvoiceExceptionCard
                investigation={investigation}
                lineage={lineage || investigation.lineage}
              />

              {/* Prominent Determination Card */}
              <DeterminationCard investigation={investigation} />
            </div>

            {/* =========================================================================
                3. LINEAGE GRAPH
                Central visual element exposing the real directional relationship graph
                ========================================================================= */}
            <LineageGraph
              lineage={lineage || investigation.lineage}
              onSelectEvidence={(ev) => setInspectedEvidence(ev)}
            />

            {/* =========================================================================
                4. VALIDATION + EVIDENCE + ACTIVITY
                Detailed evidentiary sections completing the unbroken verification chain
                ========================================================================= */}
            <div className="space-y-6">
              {/* Deterministic Validation Section */}
              <ValidationSection
                results={investigation.validation_results}
                onSelectEvidenceId={handleSelectEvidenceById}
              />

              {/* Evidentiary Records Section */}
              <EvidenceSection
                evidence={lineage?.evidence || investigation.lineage?.evidence}
                citedEvidenceIds={investigation.cited_evidence_ids}
              />

              {/* Investigation Activity & Evidence Trace */}
              <InvestigationActivityTrace
                trace={trace}
                events={investigation.events || investigation.agent_events}
              />
            </div>
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
