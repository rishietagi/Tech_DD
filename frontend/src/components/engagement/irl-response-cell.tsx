"use client";

import { useEffect, useRef, useState } from "react";

import { irlApi } from "@/lib/api/irl";

type SaveStatus = "idle" | "saving" | "saved" | "error";

const DEBOUNCE_MS = 800;

/** One autosaving answer field.
 *
 * The smallest possible client component: the table around it stays a pure server
 * component, and only this leaf holds state. Modelled on `use-autosave-section.ts` —
 * same 800 ms debounce and same saving/saved/error vocabulary — but deliberately not
 * sharing it, because that hook is hard-typed to intake sections.
 */
export function IrlResponseCell({
  engagementId,
  questionId,
  initialValue,
}: {
  engagementId: string;
  questionId: string;
  initialValue: string;
}) {
  const [value, setValue] = useState(initialValue);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // The last value actually persisted, so an unchanged blur does not re-save.
  const saved = useRef(initialValue);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const persist = async (next: string) => {
    if (next === saved.current) return;
    setStatus("saving");
    try {
      await irlApi.saveResponse(engagementId, questionId, next);
      saved.current = next;
      setStatus("saved");
    } catch {
      // Left on screen rather than reverted: the user's typing is the thing worth
      // keeping, and a failed save should be visible, not silently discarded.
      setStatus("error");
    }
  };

  const onChange = (next: string) => {
    setValue(next);
    setStatus("idle");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => void persist(next), DEBOUNCE_MS);
  };

  const onBlur = () => {
    if (timer.current) clearTimeout(timer.current);
    void persist(value);
  };

  return (
    <div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
        rows={2}
        aria-label="Response"
        placeholder="Leave blank for the client to complete…"
        className="w-full resize-y rounded-lg border border-line-strong bg-paper px-2.5 py-1.5 font-sans text-[13px] leading-[1.5] text-text placeholder:text-muted-2 focus:border-steel focus:outline-none"
      />
      <span
        aria-live="polite"
        className={`mt-0.5 block font-sans text-[11px] ${
          status === "error" ? "text-redline" : "text-muted-2"
        }`}
      >
        {status === "saving" && "Saving…"}
        {status === "saved" && "Saved"}
        {status === "error" && "Not saved — check your connection"}
      </span>
    </div>
  );
}
