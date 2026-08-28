export type StampState = "draft" | "in-progress" | "ready-to-file" | "filed";

const STAMP_LABEL: Record<StampState, string> = {
  draft: "Draft",
  "in-progress": "In Progress",
  "ready-to-file": "Ready to File",
  filed: "Filed",
};

export function Stamp({ state }: { state: StampState }) {
  const isSteel = state === "ready-to-file" || state === "filed";
  const rotate = state === "filed" ? "rotate(-7deg) scale(1.08)" : "rotate(-7deg)";

  return (
    <div
      className={`pointer-events-none relative inline-block rounded-[2px] border-2 px-4 py-2.5 font-mono text-xs tracking-[0.12em] uppercase opacity-85 [mix-blend-mode:multiply] ${
        isSteel ? "border-steel text-steel" : "border-redline text-redline"
      }`}
      style={{ transform: rotate }}
    >
      <span
        className={`pointer-events-none absolute inset-[3px] rounded-[1px] border ${
          isSteel ? "border-steel" : "border-redline"
        }`}
        aria-hidden
      />
      {STAMP_LABEL[state]}
    </div>
  );
}
