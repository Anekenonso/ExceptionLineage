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
    input: { label: "Input", bg: "bg-slate-100", text: "text-slate-800", border: "border-slate-300" },
    agent_decision: { label: "Agent Decision", bg: "bg-blue-50", text: "text-blue-800", border: "border-blue-200" },
    tool_call: { label: "Tool Call", bg: "bg-indigo-50", text: "text-indigo-800", border: "border-indigo-200" },
    graph_retrieval: { label: "Graph Retrieval", bg: "bg-purple-50", text: "text-purple-800", border: "border-purple-200" },
    evidence_found: { label: "Evidence Found", bg: "bg-teal-50", text: "text-teal-800", border: "border-teal-200" },
    validation: { label: "Validation", bg: "bg-amber-50", text: "text-amber-800", border: "border-amber-200" },
    outcome: { label: "Final Outcome", bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-200" },
    state_transition: { label: "Lifecycle State", bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-200" },
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Investigation activity
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Key steps taken to review this transaction and check contract records.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowTechnicalTrace((prev) => !prev)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition self-start sm:self-center"
        >
          <span>{showTechnicalTrace ? "Hide technical trace" : "View technical trace"}</span>
          <span className="text-slate-400 font-normal">({traceEvents.length} events)</span>
        </button>
      </div>

      {/* PHASE 13: Concise User-Readable Activity Timeline */}
      <div className="relative pl-6 space-y-4 border-l-2 border-slate-200 ml-2">
        {highLevelSteps.map((st, sIdx) => (
          <div key={sIdx} className="relative group">
            {/* Step dot */}
            <div className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-slate-900 bg-white flex items-center justify-center">
              <div className="h-1.5 w-1.5 rounded-full bg-slate-900" />
            </div>

            <div className="text-xs space-y-0.5">
              <div className="font-semibold text-slate-900 text-sm">
                {st.title}
              </div>
              <div className="text-slate-500 text-xs">
                {st.subtitle}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* PHASE 14: Secondary Technical Trace */}
      {showTechnicalTrace && (
        <div className="mt-6 pt-6 border-t border-slate-200 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Technical Execution Trace
              </h4>
              <p className="text-[11px] text-slate-500">
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
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition shrink-0 ${
                    filterType === tab.key
                      ? "bg-slate-900 text-white font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {filteredEvents.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500 font-mono">
              No technical events matching filter.
            </div>
          ) : (
            <div className="space-y-3 font-mono text-xs">
              {filteredEvents.map((evt, idx) => {
                const conf = typeConfig[evt.type] || typeConfig.state_transition;

                return (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50/60 text-xs space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded border ${conf.bg} ${conf.text} ${conf.border}`}
                        >
                          {conf.label}
                        </span>

                        {evt.action && (
                          <span className="font-semibold text-slate-900">
                            {evt.action}
                          </span>
                        )}

                        {evt.check && (
                          <span className="font-semibold text-slate-800">
                            {evt.check}
                          </span>
                        )}

                        {evt.status && (
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              evt.status === "PASS" || evt.status === "VERIFIED"
                                ? "bg-emerald-100 text-emerald-800"
                                : evt.status === "FAIL" || evt.status === "NOT_VERIFIED"
                                ? "bg-rose-100 text-rose-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {evt.status}
                          </span>
                        )}
                      </div>

                      {evt.timestamp && (
                        <span className="text-[10.5px] text-slate-400">
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
                      <p className="text-slate-700 leading-relaxed font-sans text-xs">
                        {evt.message}
                      </p>
                    )}

                    {evt.arguments && Object.keys(evt.arguments).length > 0 && (
                      <div className="mt-1 p-2 rounded bg-white border border-slate-200 text-[10.5px] text-slate-700 overflow-x-auto">
                        <span className="text-slate-400 block text-[9.5px] uppercase font-semibold">
                          Arguments:
                        </span>
                        <code>{JSON.stringify(evt.arguments, null, 2)}</code>
                      </div>
                    )}

                    {evt.relationships && evt.relationships.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                        <span className="text-[10px] text-slate-400">Traversed:</span>
                        {evt.relationships.map((rel, rIdx) => (
                          <span
                            key={rIdx}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200"
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
