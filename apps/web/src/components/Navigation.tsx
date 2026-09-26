"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { checkApiHealth } from "@/lib/api";
import { BrandLogo } from "@/components/BrandLogo";

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
    <header className="border-b border-[#e6dccb] bg-[#fffdf9] sticky top-0 z-30 shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo & Main Nav */}
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="flex items-center gap-3 text-[#1c2621] group transition"
            >
              <BrandLogo size={34} />
              <div className="flex flex-col">
                <span className="font-serif font-bold text-lg tracking-tight leading-none text-[#1c2621]">
                  ExceptionLineage
                </span>
                <span className="text-[10px] uppercase font-semibold tracking-[0.14em] text-[#5b7f6a] leading-none mt-1">
                  Invoice Investigation
                </span>
              </div>
            </Link>

            {/* Primary Navigation: Overview, Investigations, Evidence, Reports */}
            <nav className="hidden md:flex items-center gap-1.5 text-sm font-medium">
              <Link
                href="/"
                className={`px-3 py-1.5 rounded-lg transition ${
                  pathname === "/"
                    ? "bg-[#faf6ef] text-[#1c2621] font-semibold border border-[#e6dccb]"
                    : "text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef]"
                }`}
              >
                Overview
              </Link>
              <Link
                href="/investigations"
                className={`px-3 py-1.5 rounded-lg transition ${
                  pathname?.startsWith("/investigations")
                    ? "bg-[#faf6ef] text-[#1c2621] font-semibold border border-[#e6dccb]"
                    : "text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef]"
                }`}
              >
                Investigations
              </Link>
              <Link
                href="/investigations#evidence"
                className="px-3 py-1.5 rounded-lg text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef] transition"
              >
                Evidence
              </Link>
              {onOpenReportModal ? (
                <button
                  type="button"
                  onClick={onOpenReportModal}
                  className="px-3 py-1.5 rounded-lg text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef] transition cursor-pointer"
                >
                  Reports
                </button>
              ) : (
                <Link
                  href="/investigations"
                  className="px-3 py-1.5 rounded-lg text-[#4a564f] hover:text-[#1c2621] hover:bg-[#faf6ef] transition"
                >
                  Reports
                </Link>
              )}
            </nav>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            {/* System Status */}
            <button
              type="button"
              onClick={() => setShowSystemInfo((prev) => !prev)}
              className="flex items-center gap-2 px-3 py-1 rounded-full border border-[#e6dccb] bg-[#faf6ef] text-xs text-[#4a564f] hover:border-[#cfc2ab] transition cursor-pointer"
              title="Click to view engine connection details"
              aria-label="Engine status"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  apiConnected === true
                    ? "bg-[#1f4d3a]"
                    : apiConnected === false
                    ? "bg-[#c2512f]"
                    : "bg-[#b97d10] animate-pulse"
                }`}
              />
              <span className="text-[11px] hidden sm:inline text-[#4a564f] font-medium">
                {apiConnected === true
                  ? "Engine Online"
                  : apiConnected === false
                  ? "Engine Offline"
                  : "Connecting…"}
              </span>
            </button>

            {/* Primary Action Button: Review an invoice */}
            {onOpenNewModal ? (
              <button
                type="button"
                onClick={onOpenNewModal}
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#1f4d3a] px-4 py-2 text-xs sm:text-sm font-semibold text-[#faf6ef] shadow-xs hover:bg-[#163828] transition focus:outline-none focus:ring-2 focus:ring-[#1f4d3a] focus:ring-offset-2 cursor-pointer"
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
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#1f4d3a] px-4 py-2 text-xs sm:text-sm font-semibold text-[#faf6ef] shadow-xs hover:bg-[#163828] transition focus:outline-none focus:ring-2 focus:ring-[#1f4d3a] focus:ring-offset-2"
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
