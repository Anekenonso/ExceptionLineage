"use client";

import React, { useEffect, useState, use, useMemo } from "react";
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
import { ContractClauseDiffModal, ClauseDiffData } from "@/components/ContractClauseDiffModal";
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
  const [isDiffOpen, setIsDiffOpen] = useState<boolean>(false);
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

  // Construct ClauseDiffData from investigation and lineage
  const diffData: ClauseDiffData | null = useMemo(() => {
    if (!investigation) return null;
    const exc = lineage?.exception || investigation.lineage?.exception;
    const k = lineage?.contract || investigation.lineage?.contract;

    const billedAmt = Number(investigation.amount) || Number(exc?.actual_amount) || 0;
    const expectedAmt = exc?.expected_amount !== undefined && exc?.expected_amount !== null
      ? Number(exc.expected_amount)
      : billedAmt > 0 ? billedAmt * 0.9 : 0;

    return {
      clauseSection: "Section 4.2 (Fee Schedule)",
      clauseTitle: k?.title || "Master Professional Services Agreement",
      agreedRate: expectedAmt,
      agreedUnit: "hour",
      effectiveDate: k?.effective_from ? new Date(k.effective_from).toLocaleDateString() : undefined,
      agreedScope:
        "Standard billable hourly rate authorized under Schedule A for engineering and audit services.",
      itemCode: `ITEM-${investigation.invoice_id.replace(/\D/g, "").slice(-4) || "01"}`,
      itemDescription: "Billed Operational & Engineering Services",
      billedRate: billedAmt,
      billedQuantity: 1,
      billedTotal: billedAmt,
      currency: investigation.currency || "USD",
      invoiceDate: investigation.created_at ? new Date(investigation.created_at).toLocaleDateString() : undefined,
      ruleTriggered: investigation.failure_reason ? "Pricing Schedule Discrepancy" : "Baseline Contract Check",
      reasonNotes:
        investigation.summary ||
        "Deterministic audit checks compare contracted rate schedules against submitted invoice line items.",
    };
  }, [investigation, lineage]);

  return (
    <div className="min-h-screen bg-[var(--color-paper)] flex flex-col text-[var(--color-ink)]">
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
          <div className="rounded-xl border border-[var(--color-honey)]/30 bg-[var(--color-honey-soft)]/50 p-3.5 text-xs text-[var(--color-honey)] flex items-center justify-between font-mono">
            <span>
              Active Demo Mode: Displaying verified local sample record.
            </span>
            <button
              type="button"
              onClick={loadInvestigation}
              className="underline font-bold hover:opacity-80 transition"
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[var(--color-line)]">
              <div className="space-y-1">
                <Link
                  href="/investigations"
                  className="text-xs text-[var(--color-ink-faint)] hover:text-[var(--color-forest)] font-mono flex items-center gap-1.5 transition"
                >
                  &larr; Return to directory
                </Link>
                <div className="flex items-center gap-3 pt-1">
                  <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-[var(--color-ink)]">
                    Audit Review: {investigation.invoice_id}
                  </h1>
                  <StatusBadge status={investigation.status} size="md" />
                </div>
                <p className="text-xs text-[var(--color-ink-faint)] font-mono">
                  {customerDisplay} &middot; {amountDisplay}
                </p>
              </div>

              <div className="flex items-center gap-2.5">
                {/* Clause Diff Button */}
                <button
                  type="button"
                  onClick={() => setIsDiffOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] px-3.5 py-2 text-xs font-mono font-medium text-[var(--color-ink)] shadow-2xs hover:bg-[var(--color-paper-deep)] transition"
                >
                  <span className="text-[var(--color-clay)] font-bold">&plusmn;</span>
                  <span>Clause Diff</span>
                </button>

                {/* Export Report Button */}
                <button
                  type="button"
                  onClick={() => setIsExportOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--color-forest)] text-[var(--color-paper)] px-4 py-2 text-xs font-mono font-semibold shadow-2xs hover:opacity-90 transition"
                >
                  <svg
                    className="h-3.5 w-3.5 text-[var(--color-paper)]"
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
              </div>
            </div>

            {/* 1. INVOICE SECTION */}
            <InvoiceExceptionCard
              investigation={investigation}
              lineage={lineage || investigation.lineage}
              onOpenClauseDiff={() => setIsDiffOpen(true)}
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

      {/* Contract Clause Diff Modal */}
      <ContractClauseDiffModal
        isOpen={isDiffOpen}
        onClose={() => setIsDiffOpen(false)}
        diffData={diffData}
      />

      {/* Quick Evidence Inspector Drawer */}
      <EvidenceDrawer
        evidence={inspectedEvidence}
        onClose={() => setInspectedEvidence(null)}
      />
    </div>
  );
}
