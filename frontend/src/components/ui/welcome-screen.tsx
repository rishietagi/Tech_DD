"use client";

import Image from "next/image";

const STEPS = [
  ["01", "Intake", "Capture the deal, the investor and the target"],
  ["02", "Scope", "Derive what the diligence must examine"],
  ["03", "Information requests", "Ask for the evidence and track what arrives"],
  ["04", "Assess", "Find what moves the value of the deal"],
  ["05", "Report", "Edit the findings and export the deck"],
] as const;

/** The first screen of a session: the KPMG brand, what the tool does, one way in. */
export function WelcomeScreen({ onContinue }: { onContinue: () => void }) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-kpmg-blue text-white">
      {/* Brand geometry: one soft light-blue glow behind the workflow column. */}
      <div
        aria-hidden
        className="pointer-events-none absolute top-1/2 right-[-12%] h-[760px] w-[760px] -translate-y-1/2 rounded-full bg-kpmg-blue-light/15 blur-3xl"
      />

      <header className="relative mx-auto w-full max-w-[1440px] px-10 pt-10 lg:px-16">
        <Image
          src="/kpmg-logo-white.png"
          alt="KPMG"
          width={751}
          height={332}
          priority
          className="h-auto w-[120px]"
        />
      </header>

      <main className="relative mx-auto grid w-full max-w-[1440px] flex-1 items-center gap-16 px-10 py-16 lg:grid-cols-[1.15fr_1fr] lg:px-16">
        <div className="animate-page-in">
          <p className="mb-5 font-sans text-[12px] font-semibold tracking-[0.18em] text-kpmg-blue-light uppercase">
            Technology Due Diligence
          </p>
          <h1 className="mb-6 font-display text-[clamp(40px,5.4vw,76px)] leading-[1.02] font-semibold text-white">
            Tech Diligence Tool
          </h1>
          <p className="mb-11 max-w-[50ch] font-sans text-[18px] leading-[1.6] text-white/80">
            One workspace from the first call to the final report — scope the
            diligence, collect the evidence, assess what moves the value of the
            deal, and export the findings.
          </p>
          <button
            type="button"
            onClick={onContinue}
            className="group inline-flex items-center gap-3 rounded-full bg-white px-8 py-4 font-sans text-[15px] font-semibold text-kpmg-blue shadow-[0_10px_30px_-10px_rgba(0,0,0,0.45)] transition-all hover:-translate-y-0.5 hover:bg-paper-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-kpmg-blue-light focus-visible:ring-offset-2 focus-visible:ring-offset-kpmg-blue"
          >
            Continue
            <span
              aria-hidden
              className="transition-transform group-hover:translate-x-1"
            >
              →
            </span>
          </button>
        </div>

        {/* The workflow, as a quiet numbered list: no boxes, a hairline between steps. */}
        <section aria-labelledby="workflow-heading" className="animate-page-in">
          <p
            id="workflow-heading"
            className="mb-4 font-sans text-[12px] font-semibold tracking-[0.18em] text-white/50 uppercase"
          >
            How it works
          </p>
          <ol className="border-t border-white/15">
            {STEPS.map(([n, title, line]) => (
              <li
                key={n}
                className="group grid grid-cols-[56px_1fr] items-baseline border-b border-white/15 py-5"
              >
                <span className="font-display text-[15px] font-semibold text-kpmg-blue-light tabular-nums">
                  {n}
                </span>
                <div>
                  <p className="font-display text-[21px] leading-tight font-semibold text-white">
                    {title}
                  </p>
                  <p className="mt-1 font-sans text-[14px] text-white/60">
                    {line}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="relative mx-auto w-full max-w-[1440px] px-10 pb-8 text-right font-sans text-[11.5px] text-white/45 lg:px-16">
        KPMG — internal use only
      </footer>
    </div>
  );
}
