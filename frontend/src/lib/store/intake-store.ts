import { create } from "zustand";

import type { IntakeDraft } from "@/types/intake";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface IntakeStoreState {
  engagementId: string | null;
  draft: IntakeDraft | null;
  visitedSteps: Set<string>;
  saveStatus: SaveStatus;
  lastSavedAt: Date | null;
  setEngagement: (id: string, draft: IntakeDraft) => void;
  updateSection: (section: keyof IntakeDraft, values: unknown) => void;
  markVisited: (step: string) => void;
  setSaveStatus: (status: SaveStatus) => void;
  reset: () => void;
}

export const useIntakeStore = create<IntakeStoreState>((set) => ({
  engagementId: null,
  draft: null,
  visitedSteps: new Set(),
  saveStatus: "idle",
  lastSavedAt: null,

  setEngagement: (id, draft) =>
    set({
      engagementId: id,
      draft,
      visitedSteps: new Set(Object.entries(draft).filter(([, v]) => v != null).map(([k]) => k)),
    }),

  updateSection: (section, values) =>
    set((state) => ({
      draft: state.draft ? { ...state.draft, [section]: values } : state.draft,
    })),

  markVisited: (step) =>
    set((state) => {
      const next = new Set(state.visitedSteps);
      next.add(step);
      return { visitedSteps: next };
    }),

  setSaveStatus: (status) =>
    set((state) => ({
      saveStatus: status,
      lastSavedAt: status === "saved" ? new Date() : state.lastSavedAt,
    })),

  reset: () => set({ engagementId: null, draft: null, visitedSteps: new Set(), saveStatus: "idle", lastSavedAt: null }),
}));
