"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { INTAKE_STEPS, INTAKE_STEP_LABELS } from "@/types/intake";

interface LedgerRailProps {
  engagementId: string;
  visitedSteps: Set<string>;
}

export function LedgerRail({ engagementId, visitedSteps }: LedgerRailProps) {
  const pathname = usePathname();

  return (
    <nav aria-label="Intake steps" className="sticky top-[76px] hidden pt-2 md:block">
      <ol className="m-0 list-none p-0">
        {INTAKE_STEPS.map((step, idx) => {
          const href = `/intake/${engagementId}/${step}`;
          const isActive = pathname === href;
          const isFilled = visitedSteps.has(step);

          return (
            <li key={step}>
              <Link
                href={href}
                aria-current={isActive ? "step" : undefined}
                className={`flex items-center gap-2.5 border-l-2 py-[9px] pr-1 pl-3.5 font-mono text-[12.5px] transition-colors ${
                  isActive ? "border-redline text-text" : "border-transparent text-muted-2"
                }`}
              >
                <span
                  className={`h-[7px] w-[7px] flex-none rounded-full border-[1.5px] transition-colors ${
                    isFilled ? "border-redline bg-redline" : "border-muted-2 bg-transparent"
                  }`}
                  aria-hidden
                />
                <span className={`text-[11px] ${isActive ? "text-redline" : "text-muted-2"}`}>
                  {String(idx + 1).padStart(2, "0")}
                </span>
                {INTAKE_STEP_LABELS[step]}
              </Link>
            </li>
          );
        })}
        <li>
          <Link
            href={`/intake/${engagementId}/review`}
            aria-current={pathname?.endsWith("/review") ? "step" : undefined}
            className={`flex items-center gap-2.5 border-l-2 py-[9px] pr-1 pl-3.5 font-mono text-[12.5px] transition-colors ${
              pathname?.endsWith("/review") ? "border-redline text-text" : "border-transparent text-muted-2"
            }`}
          >
            <span
              className={`h-[7px] w-[7px] flex-none rounded-full border-[1.5px] transition-colors ${
                visitedSteps.size === INTAKE_STEPS.length ? "border-redline bg-redline" : "border-muted-2"
              }`}
              aria-hidden
            />
            <span className="text-[11px] text-redline">08</span>
            Review &amp; File
          </Link>
        </li>
      </ol>
      <p className="mt-3.5 pl-3.5 font-mono text-[11px] text-muted-2">Draft saved to the API as you go.</p>
    </nav>
  );
}
