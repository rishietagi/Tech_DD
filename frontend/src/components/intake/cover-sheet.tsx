import Link from "next/link";

import { INTAKE_STEP_LABELS, INTAKE_STEPS, type IntakeDraft, type IntakeStep } from "@/types/intake";

const NOT_ENTERED = "No information entered";

/** `null` means the field is empty, so the caller can render it as muted italics
 *  rather than printing a bare dash the reader has to interpret. */
function formatValue(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (Array.isArray(value)) return value.length ? value.join(", ") : null;
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
        <h3 className="font-display text-[15px] font-semibold text-text">{INTAKE_STEP_LABELS[step]}</h3>
        <Link href={`/intake/${engagementId}/${step}`} className="font-sans text-[13px] font-medium text-steel">
          Edit
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="font-sans text-sm text-muted italic">Not started</p>
      ) : (
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          {entries.map(([key, value]) => {
            const formatted = formatValue(value);
            return (
              <div key={key}>
                <dt className="mb-0.5 font-sans text-[11px] font-medium text-muted-2 uppercase">
                  {humanizeKey(key)}
                </dt>
                <dd
                  className={
                    formatted === null
                      ? "font-sans text-[14px] text-muted-2 italic"
                      : "font-sans text-[14px] text-text"
                  }
                >
                  {formatted ?? NOT_ENTERED}
                </dd>
              </div>
            );
          })}
        </dl>
      )}
    </div>
  );
}

export function CoverSheet({ engagementId, intake }: { engagementId: string; intake: IntakeDraft }) {
  return (
    <div className="rounded-2xl border border-line-strong bg-paper-2 px-8 py-2 sm:px-10">
      {INTAKE_STEPS.map((step) => (
        <SectionCard key={step} engagementId={engagementId} step={step} data={intake[step] as Record<string, unknown> | null} />
      ))}
    </div>
  );
}
