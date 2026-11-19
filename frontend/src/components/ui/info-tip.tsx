"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Explainability (Rishi, 2026-11-19: "wherever there is a need for explainability, add an
 * information icon"). Every number the platform computes should be arguable on stated
 * grounds, so the rule behind it sits one hover away.
 *
 * - `InfoTip` — an ⓘ button. Hover or focus shows the explanation; a click pins it open
 *   (touch screens have no hover). Portalled and positioned against the viewport, so a
 *   table's overflow or a card's border never clips it.
 * - `Formula` — a formula set apart from the prose.
 * - `HowItWorks` — a disclosure for explanations too long for a tooltip.
 */

const WIDTH = 340;
const GAP = 8;

type Position = { left: number; top?: number; bottom?: number };

export function InfoTip({
  label,
  title,
  children,
  className = "",
  tone = "default",
}: {
  /** What is being explained — read by screen readers as "How … is calculated". */
  label: string;
  title?: string;
  children: React.ReactNode;
  className?: string;
  /** `inverse` for use on KPMG-blue surfaces. */
  tone?: "default" | "inverse";
}) {
  const id = useId();
  const button = useRef<HTMLButtonElement | null>(null);
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [position, setPosition] = useState<Position | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const place = useCallback(() => {
    const rect = button.current?.getBoundingClientRect();
    if (!rect) return;
    const width = Math.min(WIDTH, window.innerWidth - 24);
    const left = Math.max(
      12,
      Math.min(
        rect.left + rect.width / 2 - width / 2,
        window.innerWidth - width - 12,
      ),
    );
    // Below by default; above when the lower half of the screen is where the icon is.
    setPosition(
      rect.top > window.innerHeight * 0.58
        ? { left, bottom: window.innerHeight - rect.top + GAP }
        : { left, top: rect.bottom + GAP },
    );
  }, []);

  const show = () => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    place();
    setOpen(true);
  };
  const hideSoon = () => {
    if (pinned) return;
    hideTimer.current = setTimeout(() => setOpen(false), 120);
  };
  const close = useCallback(() => {
    setOpen(false);
    setPinned(false);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onPointer = (e: MouseEvent) => {
      const target = e.target as Node;
      if (button.current?.contains(target)) return;
      if (document.getElementById(id)?.contains(target)) return;
      close();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [open, close, id]);

  useEffect(
    () => () => {
      if (hideTimer.current) clearTimeout(hideTimer.current);
    },
    [],
  );

  return (
    <>
      <button
        ref={button}
        type="button"
        aria-label={`How ${label} is calculated`}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onMouseEnter={show}
        onMouseLeave={hideSoon}
        onFocus={show}
        onBlur={hideSoon}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (pinned) close();
          else {
            show();
            setPinned(true);
          }
        }}
        className={`ml-1.5 inline-flex h-[17px] w-[17px] flex-none translate-y-[-1px] items-center justify-center rounded-full align-middle font-serif text-[10.5px] font-bold italic normal-case leading-none tracking-normal transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-kpmg-blue-light ${
          tone === "inverse"
            ? "bg-white/15 text-white hover:bg-white/30"
            : open
              ? "bg-kpmg-blue text-white"
              : "bg-kpmg-blue-tint-strong text-kpmg-blue hover:bg-kpmg-blue hover:text-white"
        } ${className}`}
      >
        i
      </button>
      {open &&
        position &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            id={id}
            role="tooltip"
            onMouseEnter={show}
            onMouseLeave={hideSoon}
            style={{
              left: position.left,
              top: position.top,
              bottom: position.bottom,
              width: Math.min(WIDTH, window.innerWidth - 24),
            }}
            className="fixed z-[70] max-h-[60vh] overflow-y-auto rounded-xl border border-kpmg-blue/15 bg-paper px-4 py-3.5 text-left font-sans text-[12.5px] leading-[1.55] font-normal tracking-normal text-text normal-case shadow-[0_18px_50px_-12px_rgba(0,30,90,0.35)] animate-fade-in"
          >
            <p className="mb-1.5 flex items-center gap-2 font-display text-[13px] font-semibold text-kpmg-blue">
              <span className="h-3.5 w-[3px] rounded-full bg-kpmg-blue-light" />
              {title ?? `How ${label} is calculated`}
            </p>
            <div className="space-y-2 text-muted [&_strong]:font-semibold [&_strong]:text-text">
              {children}
            </div>
          </div>,
          document.body,
        )}
    </>
  );
}

/** A formula, set in the code face on a tinted strip. */
export function Formula({ children }: { children: React.ReactNode }) {
  return (
    <code className="block rounded-lg bg-kpmg-blue-tint px-2.5 py-1.5 font-code text-[11.5px] leading-[1.5] text-kpmg-blue">
      {children}
    </code>
  );
}

/** A short ruled list for thresholds and bands inside an explanation. */
export function Scale({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[12px]">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="font-semibold text-text tabular-nums">{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** A "How this works" disclosure for explanations longer than a tooltip. */
export function HowItWorks({
  title = "How this is calculated",
  children,
  className = "",
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <details
      className={`group rounded-xl border border-kpmg-blue/15 bg-kpmg-blue-tint/60 open:bg-paper ${className}`}
    >
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-2.5 font-sans text-[13px] font-semibold text-kpmg-blue select-none [&::-webkit-details-marker]:hidden">
        <span
          aria-hidden
          className="inline-flex h-[17px] w-[17px] items-center justify-center rounded-full bg-kpmg-blue font-serif text-[10.5px] font-bold text-white italic"
        >
          i
        </span>
        {title}
        <svg
          aria-hidden
          viewBox="0 0 12 12"
          className="ml-auto h-3 w-3 text-kpmg-blue/70 transition-transform group-open:rotate-180"
        >
          <path
            d="M2.5 4.5 6 8l3.5-3.5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </summary>
      <div className="space-y-2.5 border-t border-kpmg-blue/10 px-4 py-3.5 font-sans text-[13px] leading-[1.6] text-muted [&_strong]:font-semibold [&_strong]:text-text">
        {children}
      </div>
    </details>
  );
}
