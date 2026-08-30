export type StampState = "draft" | "in-progress" | "ready-to-file" | "filed";

const STAMP_LABEL: Record<StampState, string> = {
  draft: "Draft",
  "in-progress": "In Progress",
  "ready-to-file": "Ready to File",
  filed: "Filed",
};

export function Stamp({ state }: { state: StampState }) {
  const isSteel = state === "ready-to-file" || state === "filed";

  return (
    <div
      className={`pointer-events-none inline-block rounded-full border-2 px-4 py-1.5 font-sans text-[12px] font-semibold tracking-[0.04em] uppercase ${
        isSteel ? "border-steel text-steel" : "border-redline text-redline"
      }`}
    >
      {STAMP_LABEL[state]}
    </div>
  );
}
