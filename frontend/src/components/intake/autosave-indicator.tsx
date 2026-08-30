"use client";

import type { SaveStatus } from "@/lib/store/intake-store";

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function AutosaveIndicator({ status, lastSavedAt }: { status: SaveStatus; lastSavedAt: Date | null }) {
  let text = "Not saved yet";
  if (status === "saving") text = "Saving…";
  else if (status === "saved" && lastSavedAt) text = `Saved ${formatTime(lastSavedAt)}`;
  else if (status === "error") text = "Save failed — retrying";

  return (
    <span
      role="status"
      aria-live="polite"
      className={`font-sans text-xs ${status === "error" ? "text-redline" : "text-muted-2"}`}
    >
      {text}
    </span>
  );
}
