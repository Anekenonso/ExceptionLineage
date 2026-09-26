"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { checkApiHealth } from "@/lib/api";
import { Navigation } from "@/components/Navigation";
import { AuthorityBoundaryBanner } from "@/components/AuthorityBoundaryBanner";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

type ConnectionStatus = "checking" | "connected" | "error";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("checking");

  useEffect(() => {
    async function check() {
      try {
        const data = await checkApiHealth();
        setHealth(data);
        setConnectionStatus("connected");
      } catch {
        setConnectionStatus("error");
      }
    }

    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <Navigation />

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">
        {/* Hero Section */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-slate-200 bg-white text-xs font-mono text-slate-600 shadow-2xs">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Stage 19 — Investigation Workspace</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900">
            ExceptionLineage
          </h1>
          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Evidence-backed transaction exception investigation for enterprise SaaS.
            Follow the evidence across contracts, amendments, SOWs, and approvals.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/investigations"
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition"
            >
              <span>Launch Investigation Workspace</span>
              <span aria-hidden="true">→</span>
            </Link>

            <Link
              href="/investigations?action=new"
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
            >
              <span>Run New Investigation</span>
            </Link>
          </div>
        </div>

        {/* Authority Boundary Banner */}
        <AuthorityBoundaryBanner />

        {/* 3 Core Architectural Pillars (Proven in Stage 18.5) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Pillar 1 */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-blue-50 text-blue-700 flex items-center justify-center font-mono font-bold text-xs">
              01
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              Agent Necessity
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Autonomous reasoning over non-linear branching paths, dead-end backtracking, and dynamic early stop to minimize wasted queries.
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-purple-50 text-purple-700 flex items-center justify-center font-mono font-bold text-xs">
              02
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              Neo4j Load-Bearing Role
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Directional graph relationships (<code className="font-mono text-slate-700">-[:AMENDED_BY]-&gt;</code>) eliminate customer-wide context pollution that degrades flat retrieval to 20% completeness.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-2">
            <div className="h-8 w-8 rounded-md bg-emerald-50 text-emerald-700 flex items-center justify-center font-mono font-bold text-xs">
              03
            </div>
            <h3 className="font-semibold text-slate-900 text-sm tracking-tight">
              End-to-End Evidence Chain
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Auditable provenance trace from input trigger through tool execution, graph traversal, and deterministic rule evaluation to final outcome.
            </p>
          </div>
        </div>

        {/* System & Architecture Status */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
                System Infrastructure Status
              </h2>
              <p className="text-xs text-slate-500">Live operational runtime metrics</p>
            </div>
            <div className="text-xs font-mono">
              <span className="text-slate-400">Environment: </span>
              <span className="font-semibold text-slate-700">production / evaluation</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">FastAPI Backend</span>
                <span className="font-mono font-semibold text-slate-900">
                  {health?.service || "ExceptionLineage API"}
                </span>
              </div>
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  connectionStatus === "connected"
                    ? "bg-emerald-500"
                    : connectionStatus === "checking"
                    ? "bg-amber-400 animate-pulse"
                    : "bg-rose-500"
                }`}
              />
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 text-[11px] block">API Version</span>
              <span className="font-mono font-semibold text-slate-900">
                {health?.version || "0.1.0"}
              </span>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-500 text-[11px] block">Authority Model</span>
              <span className="font-semibold text-slate-900">
                Deterministic Validation Engine
              </span>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 font-mono">
        ExceptionLineage — Evidence-backed investigation for enterprise transaction exceptions.
      </footer>
    </div>
  );
}
