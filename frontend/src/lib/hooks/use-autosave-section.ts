"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { engagementsApi } from "@/lib/api/engagements";
import { useIntakeStore } from "@/lib/store/intake-store";
import type { IntakeSectionPayload, IntakeStep } from "@/types/intake";

const AUTOSAVE_DEBOUNCE_MS = 800;
const SESSION_STORAGE_PREFIX = "techdd-intake-crashguard";

/**
 * Uncontrolled inputs (native <select>, <input type="date">) send "" for an
 * untouched optional field. The backend's optional enum/date fields expect
 * null or absence, not "" — so blank strings are stripped before every save.
 */
function stripEmptyStrings<T extends Record<string, unknown>>(values: T): T {
  const cleaned = { ...values };
  for (const key of Object.keys(cleaned)) {
    if (cleaned[key] === "") {
      delete cleaned[key];
    }
  }
  return cleaned;
}

/**
 * Debounced autosave for one intake section (docs/phases/PHASE1_PLAN.md §7). Saves on
 * change (debounced), on demand (step navigation), and mirrors to
 * sessionStorage purely as a crash guard — the API stays the source of truth
 * (CLAUDE.md §3).
 */
export function useAutosaveSection(engagementId: string, section: IntakeStep) {
  const queryClient = useQueryClient();
  const setSaveStatus = useIntakeStore((s) => s.setSaveStatus);
  const updateSection = useIntakeStore((s) => s.updateSection);
  const markVisited = useIntakeStore((s) => s.markVisited);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: IntakeSectionPayload) => engagementsApi.patchSection(engagementId, section, payload),
    onMutate: () => setSaveStatus("saving"),
    onSuccess: (engagement) => {
      setSaveStatus("saved");
      markVisited(section);
      queryClient.setQueryData(["engagement", engagementId], engagement);
    },
    onError: () => setSaveStatus("error"),
  });

  const mirrorToSessionStorage = (values: IntakeSectionPayload) => {
    try {
      sessionStorage.setItem(`${SESSION_STORAGE_PREFIX}-${engagementId}-${section}`, JSON.stringify(values));
    } catch {
      // sessionStorage is a crash guard only; ignore quota/availability errors.
    }
  };

  const saveNow = async (values: IntakeSectionPayload) => {
    const cleaned = stripEmptyStrings(values as Record<string, unknown>) as IntakeSectionPayload;
    updateSection(section, cleaned);
    mirrorToSessionStorage(cleaned);
    if (timerRef.current) clearTimeout(timerRef.current);
    await mutation.mutateAsync(cleaned);
  };

  const saveDebounced = (values: IntakeSectionPayload) => {
    const cleaned = stripEmptyStrings(values as Record<string, unknown>) as IntakeSectionPayload;
    updateSection(section, cleaned);
    mirrorToSessionStorage(cleaned);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => mutation.mutate(cleaned), AUTOSAVE_DEBOUNCE_MS);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { saveDebounced, saveNow, isSaving: mutation.isPending };
}
