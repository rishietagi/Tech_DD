import Link from "next/link";

import type { FieldError } from "@/lib/api/client";
import { INTAKE_STEP_LABELS, type IntakeStep } from "@/types/intake";

export function ValidationSummary({ engagementId, fieldErrors }: { engagementId: string; fieldErrors: FieldError[] }) {
  if (fieldErrors.length === 0) return null;

  return (
    <div role="alert" className="mb-8 rounded-2xl border border-redline bg-redline-tint px-6 py-5">
      <p className="mb-3 font-sans text-[13px] font-semibold text-redline">
        {fieldErrors.length} field{fieldErrors.length === 1 ? "" : "s"} need attention before filing
      </p>
      <ul className="space-y-1.5">
        {fieldErrors.map((error) => {
          const [section] = error.field.split(".");
          const label = INTAKE_STEP_LABELS[section as IntakeStep] ?? section;
          return (
            <li key={error.field} className="font-sans text-sm">
              <Link href={`/intake/${engagementId}/${section}`} className="text-redline-dark underline">
                {label}
              </Link>
              <span className="text-muted"> — {error.message}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
