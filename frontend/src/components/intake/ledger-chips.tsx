"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { INTAKE_STEPS, INTAKE_STEP_LABELS } from "@/types/intake";

export function LedgerChips({ engagementId }: { engagementId: string }) {
  const pathname = usePathname();
  const allStops = [...INTAKE_STEPS, "review"] as const;

  return (
    <div className="sticky top-[53px] z-30 flex gap-2 overflow-x-auto border-b border-line bg-paper px-5 py-3.5 md:hidden">
      {allStops.map((step) => {
        const href = `/intake/${engagementId}/${step}`;
        const isActive = pathname === href;
        const label = step === "review" ? "Review" : INTAKE_STEP_LABELS[step];
        return (
          <Link
            key={step}
            href={href}
            className={`flex-none rounded-full border px-3 py-1.5 font-mono text-[11.5px] whitespace-nowrap transition-colors ${
              isActive ? "border-redline text-text" : "border-line-strong text-muted"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </div>
  );
}
