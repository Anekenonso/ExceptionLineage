"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { checkApiHealth } from "@/lib/api";

interface NavigationProps {
  onOpenNewModal?: () => void;
}

export function Navigation({ onOpenNewModal }: NavigationProps) {
  const pathname = usePathname();
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    async function check() {
      try {
        await checkApiHealth();
        if (mounted) setApiConnected(true);
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
              href="/investigations"
              className="flex items-center gap-2.5 text-slate-900 group"
            >
              <div className="h-8 w-8 rounded-md bg-slate-900 text-white flex items-center justify-center font-mono font-bold text-sm tracking-wider shadow-xs group-hover:bg-slate-800 transition">
                EL
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-base tracking-tight leading-none text-slate-900">
                  ExceptionLineage
                </span>
                <span className="text-[11px] text-slate-500 font-mono tracking-wide leading-none mt-1">
                  Investigation Workspace
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              <Link
                href="/investigations"
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  pathname?.startsWith("/investigations")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                Investigations
              </Link>
              <Link
                href="/"
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  pathname === "/"
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                System Status
              </Link>
            </nav>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-4">
            {/* Live API indicator */}
            <div
              className="flex items-center gap-2 px-2.5 py-1 rounded-full border border-slate-200 bg-slate-50 text-xs text-slate-600"
              title={
                apiConnected === true
                  ? "API Backend: Connected (http://localhost:8000)"
                  : apiConnected === false
                  ? "API Backend: Offline (Check port 8000)"
                  : "Checking API connection..."
              }
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
              <span className="font-mono text-[11px] hidden sm:inline">
                {apiConnected === true
                  ? "API Online"
                  : apiConnected === false
                  ? "API Offline"
                  : "Connecting…"}
              </span>
            </div>

            {/* New Investigation Button */}
            {onOpenNewModal ? (
              <button
                type="button"
                onClick={onOpenNewModal}
                className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-3.5 py-2 text-xs sm:text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
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
                <span>New Investigation</span>
              </button>
            ) : (
              <Link
                href="/investigations?action=new"
                className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-3.5 py-2 text-xs sm:text-sm font-semibold text-white shadow-xs hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
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
                <span>New Investigation</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
