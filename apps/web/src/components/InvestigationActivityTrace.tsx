"use client";

import React, { useState } from "react";
import { InvestigationEvidenceTrace, TraceEvent, InvestigationEvent } from "@/types/investigation";

interface InvestigationActivityTraceProps {
  trace?: InvestigationEvidenceTrace | null;
  events?: InvestigationEvent[] | null;
}

export function InvestigationActivityTrace({ trace, events }: InvestigationActivityTraceProps) {
  const [filterType, setFilterType] = useState<string>("ALL");

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
        arguments: typeof e.metadata?.arguments === "object" ? (e.metadata.arguments as Record<string, unknown>) : undefined,
        check: typeof e.metadata?.check === "string" ? e.metadata.check : undefined,
        status: typeof e.metadata?.status === "string" ? e.metadata.status : undefined,
        evidence_ids: Array.isArray(e.metadata?.evidence_ids) ? (e.metadata.evidence_ids as string[]) : undefined,
      }));
    }

    return [];
  }, [trace, events]);

  const filteredEvents = React.useMemo(() => {
    if (filterType === "ALL") return traceEvents;
    return traceEvents.filter((e) => e.type.toLowerCase() === filterType.toLowerCase());
  }, [traceEvents, filterType]);

  // Color & Badge Mapping for trace types
  const typeConfig: Record<
    string,
    { label: string; bg: string; text: string; border: string; icon: string }
  > = {
    input: {
      label: "Input",
      bg: "bg-slate-100",
      text: "text-slate-800",
      border: "border-slate-300",
      icon: "IN",
    },
    agent_decision: {
      label: "Agent Decision",
      bg: "bg-blue-50",
      text: "text-blue-800",
      border: "border-blue-200",
      icon: "AD",
    },
    tool_call: {
      label: "Tool Call",
      bg: "bg-indigo-50",
      text: "text-indigo-800",
      border: "border-indigo-200",
      icon: "TC",
    },
    graph_retrieval: {
      label: "Graph Retrieval",
      bg: "bg-purple-50",
      text: "text-purple-800",
      border: "border-purple-200",
      icon: "GR",
    },
    evidence_found: {
      label: "Evidence Found",
      bg: "bg-teal-50",
      text: "text-teal-800",
      border: "border-teal-200",
      icon: "EV",
    },
    validation: {
      label: "Validation",
      bg: "bg-amber-50",
      text: "text-amber-800",
      border: "border-amber-200",
      icon: "VR",
    },
    outcome: {
      label: "Final Outcome",
      bg: "bg-emerald-50",
      text: "text-emerald-800",
      border: "border-emerald-200",
      icon: "OUT",
    },
    state_transition: {
      label: "Lifecycle State",
      bg: "bg-slate-50",
      text: "text-slate-700",
      border: "border-slate-200",
      icon: "ST",
    },
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-slate-900 text-white flex items-center justify-center text-[10px] font-mono font-bold">
              TR
            </div>
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
              Investigation Activity & Evidence Trace
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            End-to-end execution chronology from initial invoice trigger to final determination.
          </p>
        </div>

        {trace?.chain_verified !== undefined && (
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-md border ${
                trace.chain_verified
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                  : "bg-amber-50 text-amber-800 border-amber-200"
              }`}
            >
              {trace.chain_verified ? "✓ Unbroken Evidence Chain Verified" : "Chain Incomplete"}
            </span>
          </div>
        )}
      </div>

      {/* Visual Pipeline Sequence Banner */}
      <div className="mb-5 overflow-x-auto pb-2">
        <div className="flex items-center gap-2 text-[10.5px] font-mono min-w-[700px]">
          <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-800 font-bold border border-slate-200">
            INPUT
          </span>
          <span className="text-slate-400 font-bold">→</span>
          <span className="px-2.5 py-1 rounded bg-blue-50 text-blue-800 font-bold border border-blue-200">
            AGENT DECISION
          </span>
          <span className="text-slate-400 font-bold">→</span>
          <span className="px-2.5 py-1 rounded bg-indigo-50 text-indigo-800 font-bold border border-indigo-200">
            TOOL CALL
          </span>
          <span className="text-slate-400 font-bold">→</span>
          <span className="px-2.5 py-1 rounded bg-purple-50 text-purple-800 font-bold border border-purple-200">
            GRAPH RETRIEVAL
          </span>
          <span className="text-slate-400 font-bold">→</span>
          <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-800 font-bold border border-amber-200">
            VALIDATION
          </span>
          <span className="text-slate-400 font-bold">→</span>
          <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
            RESULT
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-3 mb-4 text-xs border-b border-slate-100">
        {[
          { key: "ALL", label: "All Events" },
          { key: "agent_decision", label: "Agent Decisions" },
          { key: "tool_call", label: "Tool Calls" },
          { key: "graph_retrieval", label: "Graph Retrieval" },
          { key: "validation", label: "Validation" },
          { key: "outcome", label: "Outcome" },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setFilterType(tab.key)}
            className={`px-3 py-1 rounded-md font-mono text-[11px] transition shrink-0 ${
              filterType === tab.key
                ? "bg-slate-900 text-white font-semibold shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Trace Timeline */}
      {filteredEvents.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          No trace events found matching the active filter.
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 border-l-2 border-slate-200 ml-3">
          {filteredEvents.map((evt, idx) => {
            const conf = typeConfig[evt.type] || typeConfig.state_transition;

            return (
              <div key={idx} className="relative group">
                {/* Timeline node pip */}
                <div
                  className={`absolute -left-[31px] top-1.5 h-4 w-4 rounded-full border-2 bg-white flex items-center justify-center ${
                    evt.type === "outcome"
                      ? "border-emerald-600"
                      : evt.type === "validation"
                      ? "border-amber-500"
                      : evt.type === "tool_call"
                      ? "border-indigo-500"
                      : "border-slate-400"
                  }`}
                >
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                </div>

                {/* Event Card */}
                <div className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-2xs hover:border-slate-300 transition text-xs space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${conf.bg} ${conf.text} ${conf.border}`}
                      >
                        {conf.label}
                      </span>

                      {evt.step !== undefined && evt.step !== null && (
                        <span className="text-[10px] font-mono text-slate-500">
                          Step #{evt.step}
                        </span>
                      )}

                      {evt.action && (
                        <span className="font-mono font-semibold text-slate-900 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                          {evt.action}
                        </span>
                      )}

                      {evt.check && (
                        <span className="font-mono font-semibold text-slate-900 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                          Rule: {evt.check}
                        </span>
                      )}

                      {evt.status && (
                        <span
                          className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded ${
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
                      <span className="font-mono text-[10.5px] text-slate-400">
                        {new Date(evt.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                          fractionalSecondDigits: 3,
                        })}
                      </span>
                    )}
                  </div>

                  {/* Message / Reason */}
                  {evt.message && (
                    <p className="text-slate-800 leading-relaxed font-normal">
                      {evt.message}
                    </p>
                  )}

                  {evt.reason && evt.reason !== evt.message && (
                    <p className="text-slate-500 text-[11px] italic">
                      Rationale: {evt.reason}
                    </p>
                  )}

                  {/* Tool Arguments */}
                  {evt.arguments && Object.keys(evt.arguments).length > 0 && (
                    <div className="mt-2 p-2 rounded bg-slate-50 border border-slate-200 font-mono text-[10.5px] text-slate-700 overflow-x-auto">
                      <span className="text-slate-400 block text-[9.5px] uppercase font-semibold">
                        Arguments (Sanitized):
                      </span>
                      <code>{JSON.stringify(evt.arguments, null, 2)}</code>
                    </div>
                  )}

                  {/* Relationships traversed */}
                  {evt.relationships && evt.relationships.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      <span className="text-[10px] font-mono text-slate-400">Traversed:</span>
                      {evt.relationships.map((rel, rIdx) => (
                        <span
                          key={rIdx}
                          className="font-mono text-[9.5px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200"
                        >
                          -[:{rel}]-&gt;
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Evidence IDs returned / referenced */}
                  {evt.evidence_ids && evt.evidence_ids.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      <span className="text-[10px] font-mono text-slate-400">Evidence Citations:</span>
                      {evt.evidence_ids.map((evId, evIdx) => (
                        <span
                          key={evIdx}
                          className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200 font-semibold"
                        >
                          {evId}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
