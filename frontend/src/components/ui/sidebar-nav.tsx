"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { LinkPending } from "@/components/ui/loading";
import { INTAKE_STEPS, INTAKE_STEP_LABELS } from "@/types/intake";

/** The engagement currently being worked on, from either the intake wizard or one of
 *  the engagement modules. `/intake/new` and the `/engagements` list route have no id,
 *  so both are excluded. */
function useActiveEngagementId(): string | null {
  const pathname = usePathname();
  const match = pathname?.match(/^\/(?:intake|engagements)\/([^/]+)/);
  if (!match) return null;
  return match[1] === "new" ? null : match[1];
}

function NavSectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 mb-1.5 px-4 font-sans text-[11px] font-semibold tracking-[0.06em] text-paper-on-ink/55 uppercase first:mt-0">
      {children}
    </div>
  );
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`relative block rounded-lg px-4 py-[7px] font-sans text-[13.5px] transition-all duration-150 ${
        active
          ? "bg-white/14 font-semibold text-white before:absolute before:top-1.5 before:bottom-1.5 before:left-0 before:w-[3px] before:rounded-full before:bg-kpmg-blue-light"
          : "text-paper-on-ink/72 hover:translate-x-0.5 hover:bg-white/8 hover:text-paper-on-ink"
      }`}
    >
      {children}
      <LinkPending />
    </Link>
  );
}

export function SidebarNav() {
  const pathname = usePathname();
  const activeEngagementId = useActiveEngagementId();

  // Sticky, not static: the rail has to span the viewport at any scroll depth, so it
  // pins to the top and scrolls its own nav list rather than leaving with the page.
  return (
    <aside className="sticky top-0 flex h-screen w-[248px] flex-none flex-col self-start bg-kpmg-blue text-paper-on-ink">
      <Link href="/" className="flex flex-none items-center px-6 py-7">
        <Image
          src="/kpmg-logo-white.png"
          alt="KPMG"
          width={336}
          height={140}
          priority
          className="h-9 w-auto"
        />
      </Link>

      <nav
        aria-label="Primary"
        className="min-h-0 flex-1 overflow-y-auto px-2 pb-6"
      >
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

        {activeEngagementId && (
          <>
            <NavSectionLabel>Engagement</NavSectionLabel>
            <div className="space-y-0.5">
              <NavLink
                href={`/engagements/${activeEngagementId}`}
                active={pathname === `/engagements/${activeEngagementId}`}
              >
                Overview
              </NavLink>
              <NavLink
                href={`/engagements/${activeEngagementId}/scope`}
                active={pathname === `/engagements/${activeEngagementId}/scope`}
              >
                Scope of work
              </NavLink>
              <NavLink
                href={`/engagements/${activeEngagementId}/research`}
                active={
                  pathname === `/engagements/${activeEngagementId}/research`
                }
              >
                Company research
              </NavLink>
              <NavLink
                href={`/engagements/${activeEngagementId}/irl`}
                active={pathname === `/engagements/${activeEngagementId}/irl`}
              >
                Information requests
              </NavLink>
              {/* Prefix match, not exact: Assess has a sub-route per business process,
                  and the section should stay lit while the user is inside one. */}
              <NavLink
                href={`/engagements/${activeEngagementId}/assess`}
                active={
                  pathname?.startsWith(
                    `/engagements/${activeEngagementId}/assess`,
                  ) ?? false
                }
              >
                Assess
              </NavLink>

              <NavLink
                href={`/engagements/${activeEngagementId}/report`}
                active={
                  pathname === `/engagements/${activeEngagementId}/report`
                }
              >
                Report
              </NavLink>
            </div>
          </>
        )}

        <NavSectionLabel>Workspace</NavSectionLabel>
        <div className="space-y-0.5">
          {/* Exact match: this is the list route, and it should not stay lit while the
              user is inside one engagement's modules. */}
          <NavLink href="/engagements" active={pathname === "/engagements"}>
            Engagements
          </NavLink>
          <NavLink
            href="/about/methodology"
            active={pathname?.startsWith("/about") ?? false}
          >
            Methodology
          </NavLink>
          <NavLink href="/about/ai" active={pathname === "/about/ai"}>
            AI &amp; skills
          </NavLink>
        </div>
      </nav>

      <div className="flex-none border-t border-white/15 px-5 py-4 font-sans text-[11px] font-medium text-paper-on-ink/45">
        KPMG Tech Diligence Tool
      </div>
    </aside>
  );
}
