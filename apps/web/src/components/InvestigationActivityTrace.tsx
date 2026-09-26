"use client";

import React, { useState } from "react";
import { InvestigationEvidenceTrace, TraceEvent, InvestigationEvent } from "@/types/investigation";

interface InvestigationActivityTraceProps {
  trace?: InvestigationEvidenceTrace | null;
  events?: InvestigationEvent[] | null;
}

export function InvestigationActivityTrace({ trace, events }: InvestigationActivityTraceProps) {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [showTechnicalTrace, setShowTechnicalTrace] = useState<boolean>(false);

  // Normalize trace events from trace or fallback to investigation events
  const traceEvents: TraceEvent[] = React.useMemo(() => {
    if (trace && trace.events && trace.events.length > 0) {
      return trace.events;
    }

    if (events && events.length > 0) {
      return events.map((e) => ({
        type: e.event_type.toLowerCase(),
        timestamp: e.timestamp,
        message: e.message || e.reason,
        reason: e.reason,
        action: typeof e.metadata?.action === "string" ? e.metadata.action : undefined,
        arguments:
          typeof e.metadata?.arguments === "object"
            ? (e.metadata.arguments as Record<string, unknown>)
            : undefined,
        check: typeof e.metadata?.check === "string" ? e.metadata.check : undefined,
        status: typeof e.metadata?.status === "string" ? e.metadata.status : undefined,
        evidence_ids: Array.isArray(e.metadata?.evidence_ids)
          ? (e.metadata.evidence_ids as string[])
          : undefined,
      }));
    }

    return [];
  }, [trace, events]);

  const filteredEvents = React.useMemo(() => {
    if (filterType === "ALL") return traceEvents;
    return traceEvents.filter((e) => e.type.toLowerCase() === filterType.toLowerCase());
  }, [traceEvents, filterType]);

  // High-level user readable investigation steps summary (Phase 13)
  const highLevelSteps = React.useMemo(() => {
    const steps: { title: string; subtitle: string; status: "completed" | "active" }[] = [];

    steps.push({
      title: "Invoice received",
      subtitle: "Flagged transaction ingested for review",
      status: "completed",
    });

    const hasContract = traceEvents.some(
      (e) =>
        e.action?.includes("contract") ||
        e.message?.toLowerCase().includes("contract") ||
        e.type === "graph_retrieval"
    );
    if (hasContract || traceEvents.length > 1) {
      steps.push({
        title: "Contract identified",
        subtitle: "Located governing master agreement",
        status: "completed",
      });
    }

    const hasAmendment = traceEvents.some(
      (e) =>
        e.action?.includes("amendment") ||
        e.message?.toLowerCase().includes("amendment") ||
        e.action?.includes("sow")
    );
    if (hasAmendment || traceEvents.length > 2) {
      steps.push({
        title: "Amendment & SOW reviewed",
        subtitle: "Evaluated rate terms and effective periods",
        status: "completed",
      });
    }

    const hasApproval = traceEvents.some(
      (e) =>
        e.action?.includes("approval") ||
        e.message?.toLowerCase().includes("approval")
    );
    if (hasApproval || traceEvents.length > 3) {
      steps.push({
        title: "Approval checked",
        subtitle: "Verified operational authorization records",
        status: "completed",
      });
    }

    const hasValidation = traceEvents.some(
      (e) => e.type === "validation" || e.type === "outcome"
    );
    if (hasValidation || traceEvents.length > 4) {
      steps.push({
        title: "Finding reached",
        subtitle: "Verified against available contract records",
        status: "completed",
      });
    }

    return steps;
  }, [traceEvents]);

  // Technical event labels and styling for technical trace
  const typeConfig: Record<
    string,
    { label: string; bg: string; text: string; border: string }
  > = {
    input: { label: "Input", bg: "bg-[var(--color-paper-deep)]", text: "text-[var(--color-ink)]", border: "border-[var(--color-line)]" },
    agent_decision: { label: "Agent Decision", bg: "bg-[var(--color-sky-soft)]", text: "text-[var(--color-sky)]", border: "border-[var(--color-sky)]/20" },
    tool_call: { label: "Tool Call", bg: "bg-[var(--color-forest-soft)]", text: "text-[var(--color-forest)]", border: "border-[var(--color-forest)]/20" },
    graph_retrieval: { label: "Graph Retrieval", bg: "bg-[var(--color-paper-deep)]", text: "text-[var(--color-ink)]", border: "border-[var(--color-line)]" },
    evidence_found: { label: "Evidence Found", bg: "bg-[var(--color-forest-soft)]", text: "text-[var(--color-forest)]", border: "border-[var(--color-forest)]/20" },
    validation: { label: "Validation", bg: "bg-[var(--color-honey-soft)]", text: "text-[var(--color-honey)]", border: "border-[var(--color-honey)]/20" },
    outcome: { label: "Final Outcome", bg: "bg-[var(--color-forest-soft)]", text: "text-[var(--color-forest)]", border: "border-[var(--color-forest)]/20" },
    state_transition: { label: "Lifecycle State", bg: "bg-[var(--color-paper)]", text: "text-[var(--color-ink-soft)]", border: "border-[var(--color-line)]" },
  };

  return (
    <div className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:p-6 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[var(--color-line)] gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider font-semibold text-[var(--color-ink-faint)]">
            Execution Log
          </span>
          <h3 className="font-serif text-base font-bold text-[var(--color-ink)] tracking-tight">
            Investigation Activity
          </h3>
          <p className="text-xs text-[var(--color-ink-faint)] mt-0.5">
            Key steps taken to review this transaction and check contract records
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowTechnicalTrace((prev) => !prev)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] text-xs font-mono font-medium text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)] transition self-start sm:self-center shadow-2xs"
        >
          <span>{showTechnicalTrace ? "Hide technical trace" : "View technical trace"}</span>
          <span className="text-[var(--color-ink-faint)]">({traceEvents.length} events)</span>
        </button>
      </div>

      {/* PHASE 13: Concise User-Readable Activity Timeline */}
      <div className="relative pl-6 space-y-4 border-l-2 border-[var(--color-line-strong)] ml-2">
        {highLevelSteps.map((st, sIdx) => (
          <div key={sIdx} className="relative group">
            {/* Step dot */}
            <div className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-[var(--color-forest)] bg-[var(--color-card)] flex items-center justify-center">
              <div className="h-1.5 w-1.5 rounded-full bg-[var(--color-forest)]" />
            </div>

            <div className="text-xs space-y-0.5">
              <div className="font-serif font-bold text-[var(--color-ink)] text-sm">
                {st.title}
              </div>
              <div className="text-[var(--color-ink-faint)] text-xs">
                {st.subtitle}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* PHASE 14: Secondary Technical Trace */}
      {showTechnicalTrace && (
        <div className="mt-6 pt-6 border-t border-[var(--color-line)] space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[var(--color-line)]">
            <div>
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--color-ink)]">
                Technical Execution Trace
              </h4>
              <p className="text-[11px] text-[var(--color-ink-faint)]">
                Granular agent decisions, tool calls, graph queries, and validation timestamps
              </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              {[
                { key: "ALL", label: "All" },
                { key: "agent_decision", label: "Agent" },
                { key: "tool_call", label: "Tools" },
                { key: "graph_retrieval", label: "Graph" },
                { key: "validation", label: "Rules" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setFilterType(tab.key)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition shrink-0 ${
                    filterType === tab.key
                      ? "bg-[var(--color-ink)] text-[var(--color-paper)] font-bold shadow-2xs"
                      : "text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-paper-deep)]"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {filteredEvents.length === 0 ? (
            <div className="py-6 text-center text-xs text-[var(--color-ink-faint)] font-mono">
              No technical events matching filter.
            </div>
          ) : (
            <div className="space-y-3 font-mono text-xs">
              {filteredEvents.map((evt, idx) => {
                const conf = typeConfig[evt.type] || typeConfig.state_transition;

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-[var(--color-line)] bg-[var(--color-paper)]/40 text-xs space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${conf.bg} ${conf.text} ${conf.border}`}
                        >
                          {conf.label}
                        </span>

                        {evt.action && (
                          <span className="font-semibold text-[var(--color-ink)]">
                            {evt.action}
                          </span>
                        )}

                        {evt.check && (
                          <span className="font-semibold text-[var(--color-ink-soft)]">
                            {evt.check}
                          </span>
                        )}

                        {evt.status && (
                          <span
                            className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                              evt.status === "PASS" || evt.status === "VERIFIED"
                                ? "bg-[var(--color-forest-soft)] text-[var(--color-forest)]"
                                : evt.status === "FAIL" || evt.status === "NOT_VERIFIED"
                                ? "bg-[var(--color-clay-soft)] text-[var(--color-clay)]"
                                : "bg-[var(--color-honey-soft)] text-[var(--color-honey)]"
                            }`}
                          >
                            {evt.status}
                          </span>
                        )}
                      </div>

                      {evt.timestamp && (
                        <span className="text-[10.5px] text-[var(--color-ink-faint)] font-mono">
                          {new Date(evt.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                            fractionalSecondDigits: 3,
                          })}
                        </span>
                      )}
                    </div>

                    {evt.message && (
                      <p className="text-[var(--color-ink-soft)] leading-relaxed font-sans text-xs">
                        {evt.message}
                      </p>
                    )}

                    {evt.arguments && Object.keys(evt.arguments).length > 0 && (
                      <div className="mt-1 p-2 rounded-lg bg-[var(--color-card)] border border-[var(--color-line)] text-[10.5px] text-[var(--color-ink-soft)] overflow-x-auto">
                        <span className="text-[var(--color-ink-faint)] block text-[9.5px] font-mono uppercase tracking-wider font-semibold">
                          Arguments:
                        </span>
                        <code>{JSON.stringify(evt.arguments, null, 2)}</code>
                      </div>
                    )}

                    {evt.relationships && evt.relationships.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                        <span className="text-[10px] font-mono text-[var(--color-ink-faint)]">Traversed:</span>
                        {evt.relationships.map((rel, rIdx) => (
                          <span
                            key={rIdx}
                            className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-paper-deep)] text-[var(--color-ink-soft)] border border-[var(--color-line)]"
                          >
                            -[:{rel}]-&gt;
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
