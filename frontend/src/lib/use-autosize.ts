"use client";

import { useCallback, useLayoutEffect, useRef } from "react";

/**
 * Grow a textarea to fit its content.
 *
 * The request list holds a client response and the team's remarks against every one of
 * ninety requests, and a fixed `rows={2}` clipped both: a three-line answer read as
 * "Last refreshed March…" with no indication there was more, which is worse than a long
 * row because the reader cannot tell something is missing.
 *
 * Bounded rather than unbounded — one pasted email must not push the next request off
 * the screen — and it re-measures on value change, so text arriving from a workbook
 * import or a scan sizes correctly without anyone typing.
 */
export function useAutosize(value: string, maxPx = 320) {
  const ref = useRef<HTMLTextAreaElement | null>(null);

  const resize = useCallback(() => {
    const element = ref.current;
    if (!element) return;
    // Collapse first: scrollHeight only shrinks if the box is smaller than the content.
    element.style.height = "auto";
    const next = Math.min(element.scrollHeight, maxPx);
    element.style.height = `${next}px`;
    element.style.overflowY = element.scrollHeight > maxPx ? "auto" : "hidden";
  }, [maxPx]);

  useLayoutEffect(resize, [value, resize]);

  return { ref, resize };
}
