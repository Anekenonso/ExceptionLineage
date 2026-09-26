import React from "react";

export function AuthorityBoundaryBanner() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3.5 sm:p-4 text-xs text-slate-700 flex items-start gap-3 shadow-2xs">
      <div className="p-1 rounded-md bg-slate-100 text-slate-600 shrink-0 mt-0.5">
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="2"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
          />
        </svg>
      </div>
      <div className="space-y-0.5">
        <h4 className="font-semibold text-slate-900 text-xs">
          How we verify
        </h4>
        <p className="text-slate-600 leading-relaxed">
          AI helps investigate the available records. Verification is performed using deterministic checks against the evidence found.
        </p>
      </div>
    </div>
  );
}
