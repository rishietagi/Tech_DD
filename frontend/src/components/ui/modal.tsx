"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

const SIZES = {
  sm: "max-w-[460px]",
  md: "max-w-[640px]",
  lg: "max-w-[820px]",
} as const;

/**
 * A centred dialog (Rishi, 2026-11-19: editors open "as a pop-up in the middle", not a
 * side drawer).
 *
 * Portalled to `<body>` so no transformed or overflow-clipped ancestor can trap it, with
 * the usual dialog behaviour: Escape and a backdrop click close it, the page behind stops
 * scrolling, the first field takes focus, and focus returns to whatever opened it.
 */
export function Modal({
  label,
  labelledBy,
  onClose,
  size = "md",
  dismissable = true,
  children,
}: {
  /** Accessible name, when there is no visible heading to point at. */
  label?: string;
  labelledBy?: string;
  onClose: () => void;
  size?: keyof typeof SIZES;
  /** False while something is in flight that closing would orphan. */
  dismissable?: boolean;
  children: React.ReactNode;
}) {
  const panel = useRef<HTMLDivElement | null>(null);
  const close = useRef(onClose);
  close.current = onClose;
  const canDismiss = useRef(dismissable);
  canDismiss.current = dismissable;

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && canDismiss.current) close.current();
    };
    window.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const first = panel.current?.querySelector<HTMLElement>(
      "input:not([type=hidden]), textarea, select, button[data-autofocus]",
    );
    (first ?? panel.current)?.focus();
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      opener?.focus?.();
    };
  }, []);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-kpmg-blue-dark/45 p-4 backdrop-blur-[3px] animate-fade-in sm:p-8"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && canDismiss.current) close.current();
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={label}
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className={`flex max-h-[calc(100dvh-2rem)] w-full flex-col overflow-hidden rounded-2xl bg-paper shadow-[0_30px_80px_-20px_rgba(0,20,60,0.55)] outline-none animate-modal-in sm:max-h-[calc(100dvh-4rem)] ${SIZES[size]}`}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
