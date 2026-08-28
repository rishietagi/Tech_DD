import Link from "next/link";

import { INTAKE_STEP_LABELS, type IntakeDraft, type IntakeStep } from "@/types/intake";

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function SectionCard({ engagementId, step, data }: { engagementId: string; step: IntakeStep; data: Record<string, unknown> | null }) {
  const entries = data ? Object.entries(data).filter(([, v]) => v !== undefined) : [];

  return (
    <div className="border-t border-line py-6 first:border-t-0">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-mono text-xs tracking-[0.08em] text-muted uppercase">{INTAKE_STEP_LABELS[step]}</h3>
        <Link href={`/intake/${engagementId}/${step}`} className="font-mono text-[11px] text-steel underline">
          Edit
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="font-serif text-sm text-muted italic">Not started</p>
      ) : (
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt className="mb-0.5 font-mono text-[10.5px] tracking-[0.08em] text-muted-2 uppercase">
                {humanizeKey(key)}
              </dt>
              <dd className="font-sans text-[14px] text-text">{formatValue(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

export function CoverSheet({ engagementId, intake }: { engagementId: string; intake: IntakeDraft }) {
  const steps: IntakeStep[] = ["context", "rationale", "structure", "investor", "target", "technology", "objectives"];

  return (
    <div className="rounded-[4px] border border-line-strong bg-paper-2 px-8 py-2 sm:px-10">
      {steps.map((step) => (
        <SectionCard key={step} engagementId={engagementId} step={step} data={intake[step] as Record<string, unknown> | null} />
      ))}
    </div>
  );
}
