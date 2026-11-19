"use client";

import { useLinkStatus } from "next/link";
import { createPortal } from "react-dom";

/**
 * Loading motifs (Rishi, 2026-11-19: "loading animations between screens").
 *
 * - `TopProgress` — a thin KPMG-blue bar sliding across the top of the viewport.
 * - `LinkPending` — placed inside a `<Link>`; shows the top bar while that link's
 *   navigation is in flight, so a click always gets immediate feedback.
 * - `PageLoader` — what a route segment shows while it loads (`loading.tsx`).
 * - `Spinner` — inline, for buttons and small regions.
 *
 * All animations are CSS and switch off under `prefers-reduced-motion` (globals.css).
 */

export function TopProgress() {
  return (
    <div
      role="progressbar"
      aria-label="Loading"
      className="pointer-events-none fixed inset-x-0 top-0 z-[60] h-[3px] overflow-hidden bg-kpmg-blue-tint"
    >
      <div className="h-full w-full origin-left animate-progress bg-gradient-to-r from-kpmg-blue via-kpmg-blue-light to-kpmg-blue" />
    </div>
  );
}

export function LinkPending() {
  const { pending } = useLinkStatus();
  // Portalled to <body>: a transformed ancestor (a link's hover nudge, the page-in
  // animation) makes `position: fixed` relative to itself, which drew the bar inside
  // the sidebar link instead of across the window (seen 2026-11-19).
  if (!pending || typeof document === "undefined") return null;
  return createPortal(<TopProgress />, document.body);
}

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={`inline-block animate-spin-slow rounded-full border-2 border-current border-r-transparent ${className}`}
    />
  );
}

/** A route segment loading: top bar, a branded mark, and the page's rough shape. */
export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24" aria-busy>
      <TopProgress />
      <div className="mb-8 flex items-center gap-3 text-kpmg-blue">
        <Spinner className="h-5 w-5" />
        <span className="font-sans text-[13px] font-medium tracking-wide text-muted">
          {label}…
        </span>
      </div>
      <div className="mb-3 h-3 w-24 rounded-full shimmer" />
      <div className="mb-4 h-9 w-2/5 rounded-lg shimmer" />
      <div className="mb-10 h-4 w-3/5 rounded-full shimmer" />
      <div className="grid gap-5 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-6">
            <div className="mb-3 h-3 w-1/3 rounded-full shimmer" />
            <div className="mb-2 h-7 w-1/2 rounded-md shimmer" />
            <div className="h-3 w-4/5 rounded-full shimmer" />
          </div>
        ))}
      </div>
      <div className="card mt-6 space-y-3 p-6">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-4 rounded-full shimmer"
            style={{ width: `${92 - i * 12}%` }}
          />
        ))}
      </div>
    </main>
  );
}
