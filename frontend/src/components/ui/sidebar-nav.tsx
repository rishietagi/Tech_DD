"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { INTAKE_STEPS, INTAKE_STEP_LABELS } from "@/types/intake";

function useActiveEngagementId(): string | null {
  const pathname = usePathname();
  const match = pathname?.match(/^\/intake\/([^/]+)/);
  return match ? match[1] : null;
}

function NavSectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-7 mb-2 px-4 font-sans text-[11px] font-semibold tracking-[0.06em] text-paper-on-ink/55 uppercase first:mt-0">
      {children}
    </div>
  );
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`block rounded-xl px-4 py-2 font-sans text-[13.5px] transition-colors ${
        active
          ? "bg-white/12 font-medium text-white"
          : "text-paper-on-ink/75 hover:bg-white/8 hover:text-paper-on-ink"
      }`}
    >
      {children}
    </Link>
  );
}

export function SidebarNav() {
  const pathname = usePathname();
  const activeEngagementId = useActiveEngagementId();

  return (
    <aside className="flex h-screen w-[248px] flex-none flex-col bg-kpmg-blue text-paper-on-ink">
      <Link href="/" className="flex items-center gap-2.5 px-6 py-7">
        <Image
          src="/kpmg-logo-white.png"
          alt="KPMG"
          width={690}
          height={362}
          priority
          className="h-8 w-auto"
        />
      </Link>

      <nav aria-label="Primary" className="flex-1 overflow-y-auto px-2 pb-6">
        <NavSectionLabel>Generate Scope of Work</NavSectionLabel>
        <div className="space-y-0.5">
          <NavLink href="/intake/new" active={pathname === "/intake/new"}>
            + New intake
          </NavLink>
          {activeEngagementId &&
            INTAKE_STEPS.map((step, idx) => {
              const href = `/intake/${activeEngagementId}/${step}`;
              return (
                <NavLink key={step} href={href} active={pathname === href}>
                  <span className="mr-2 font-sans text-[12px] text-paper-on-ink/45">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  {INTAKE_STEP_LABELS[step]}
                </NavLink>
              );
            })}
          {activeEngagementId && (
            <NavLink
              href={`/intake/${activeEngagementId}/review`}
              active={pathname === `/intake/${activeEngagementId}/review`}
            >
              <span className="mr-2 font-sans text-[12px] text-paper-on-ink/45">
                {String(INTAKE_STEPS.length + 1).padStart(2, "0")}
              </span>
              Review &amp; File
            </NavLink>
          )}
        </div>

        <NavSectionLabel>Workspace</NavSectionLabel>
        <div className="space-y-0.5">
          <NavLink href="/engagements" active={pathname?.startsWith("/engagements") ?? false}>
            Engagements
          </NavLink>
          <NavLink href="/about/methodology" active={pathname?.startsWith("/about") ?? false}>
            Methodology
          </NavLink>
        </div>
      </nav>

      <div className="border-t border-white/15 px-5 py-4 font-sans text-[11px] font-medium text-paper-on-ink/45">
        KPMG Tech Diligence Tool
      </div>
    </aside>
  );
}
