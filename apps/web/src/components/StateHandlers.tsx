import React from "react";

export function LoadingSkeleton({ title = "Loading invoice review…" }: { title?: string }) {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Top Invoice Card skeleton */}
      <div className="h-44 rounded-xl bg-slate-200/70 border border-slate-200" />

      {/* Finding Card skeleton */}
      <div className="h-56 rounded-xl bg-slate-200/80 border border-slate-200" />

      {/* Verification checks skeleton */}
      <div className="h-60 rounded-xl bg-slate-200/60 border border-slate-200" />

      {/* Contract history skeleton */}
      <div className="h-72 rounded-xl bg-slate-200/50 border border-slate-200 flex items-center justify-center">
        <span className="text-xs text-slate-400 font-medium">{title}</span>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
}: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-xs">
      <div className="h-12 w-12 mx-auto rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-4">
        <svg
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="1.5"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Zm3.75 11.625a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z"
          />
        </svg>
      </div>

      <h3 className="text-base font-bold text-slate-900 tracking-tight">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
        {description}
      </p>

      {(onAction || onSecondaryAction) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {onAction && actionLabel && (
            <button
              type="button"
              onClick={onAction}
              className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-slate-800 transition"
            >
              <span>{actionLabel}</span>
            </button>
          )}

          {onSecondaryAction && secondaryActionLabel && (
            <button
              type="button"
              onClick={onSecondaryAction}
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
            >
              <span>{secondaryActionLabel}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}

interface ApiErrorBannerProps {
  error: string;
  onRetry?: () => void;
  onUseFixtures?: () => void;
}

export function ApiErrorBanner({ error, onRetry, onUseFixtures }: ApiErrorBannerProps) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-5 text-xs text-rose-900 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-start gap-3">
        <div className="p-1 rounded-md bg-rose-200 text-rose-800 shrink-0 mt-0.5">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
        </div>
        <div>
          <span className="font-bold text-rose-950 block text-xs">
            Engine Connection Notice
          </span>
          <p className="text-rose-800 mt-0.5">{error}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-3 py-1.5 rounded-md border border-rose-300 bg-white font-semibold text-rose-900 hover:bg-rose-50 transition shadow-2xs"
          >
            Retry Connection
          </button>
        )}
        {onUseFixtures && (
          <button
            type="button"
            onClick={onUseFixtures}
            className="px-3 py-1.5 rounded-md bg-rose-800 text-white font-semibold hover:bg-rose-900 transition shadow-xs"
          >
            Load Sample Cases
          </button>
        )}
      </div>
    </div>
  );
}
