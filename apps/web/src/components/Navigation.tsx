"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { checkApiHealth } from "@/lib/api";

interface NavigationProps {
  onOpenNewModal?: () => void;
  onOpenReportModal?: () => void;
}

export function Navigation({ onOpenNewModal, onOpenReportModal }: NavigationProps) {
  const pathname = usePathname();
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [systemHealth, setSystemHealth] = useState<{ status: string; service: string; version: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    async function check() {
      try {
        const data = await checkApiHealth();
        if (mounted) {
          setApiConnected(true);
          setSystemHealth(data);
        }
      } catch {
        if (mounted) setApiConnected(false);
      }
    }
    check();
    const timer = setInterval(check, 20000);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo & Main Nav */}
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="flex items-center gap-2.5 text-slate-900 group"
            >
              <div className="h-8 w-8 rounded-md bg-slate-900 text-white flex items-center justify-center font-bold text-sm tracking-wider shadow-xs group-hover:bg-slate-800 transition">
                EL
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-base tracking-tight leading-none text-slate-900">
                  ExceptionLineage
                </span>
                <span className="text-[11px] text-slate-500 tracking-normal leading-none mt-1">
                  Invoice Investigation
                </span>
              </div>
            </Link>

            {/* Primary Navigation: Overview, Investigations, Evidence, Reports */}
            <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
              <Link
                href="/"
                className={`px-3 py-1.5 rounded-md transition ${
                  pathname === "/"
                    ? "bg-slate-100 text-slate-900 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                Overview
              </Link>
              <Link
                href="/investigations"
                className={`px-3 py-1.5 rounded-md transition ${
                  pathname?.startsWith("/investigations")
                    ? "bg-slate-100 text-slate-900 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                Investigations
              </Link>
              <Link
                href="/investigations#evidence"
                className="px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
              >
                Evidence
              </Link>
              {onOpenReportModal ? (
                <button
                  type="button"
                  onClick={onOpenReportModal}
                  className="px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
                >
                  Reports
                </button>
              ) : (
                <Link
                  href="/investigations"
                  className="px-3 py-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition"
                >
                  Reports
                </Link>
              )}
            </nav>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            {/* System Status - secondary/secondary interaction */}
            <button
              type="button"
              onClick={() => setShowSystemInfo((prev) => !prev)}
              className="flex items-center gap-2 px-2.5 py-1 rounded-full border border-slate-200 bg-slate-50 text-xs text-slate-600 hover:bg-slate-100 transition"
              title="Click to view engine connection details"
              aria-label="Engine status"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  apiConnected === true
                    ? "bg-emerald-500"
                    : apiConnected === false
                    ? "bg-rose-500"
                    : "bg-amber-400 animate-pulse"
                }`}
              />
              <span className="text-[11px] hidden sm:inline text-slate-600">
                {apiConnected === true
                  ? "System Online"
                  : apiConnected === false
                  ? "System Offline"
                  : "Connecting…"}
              </span>
            </button>

            {/* Primary Action Button: Review an invoice */}
            {onOpenNewModal ? (
              <button
                type="button"
                onClick={onOpenNewModal}
                className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3.5 py-2 text-xs sm:text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>Review an invoice</span>
              </button>
            ) : (
              <Link
                href="/investigations?action=new"
                className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3.5 py-2 text-xs sm:text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>Review an invoice</span>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Secondary System Status Popover / Drawer if clicked */}
      {showSystemInfo && (
        <div className="border-t border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-700">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-4">
              <span className="font-semibold text-slate-900">Engine Connection Details:</span>
              <span>
                Backend API:{" "}
                <strong className={apiConnected ? "text-emerald-700 font-mono" : "text-rose-700 font-mono"}>
                  {apiConnected ? "Connected" : "Offline"}
                </strong>
              </span>
              {systemHealth && (
                <>
                  <span className="text-slate-400">|</span>
                  <span>
                    Service: <span className="font-mono text-slate-800">{systemHealth.service}</span>
                  </span>
                  <span className="text-slate-400">|</span>
                  <span>
                    Version: <span className="font-mono text-slate-800">{systemHealth.version}</span>
                  </span>
                </>
              )}
            </div>
            <button
              type="button"
              onClick={() => setShowSystemInfo(false)}
              className="text-xs text-slate-500 hover:text-slate-900 font-semibold"
            >
              Close ✕
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
