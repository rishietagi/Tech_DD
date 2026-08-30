export default function MethodologyPage() {
  return (
    <main className="mx-auto max-w-[760px] px-7 pt-14 pb-24">
      <div className="mb-3 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">Methodology</div>
      <h1 className="mb-6 font-display font-semibold text-4xl">The Enterprise / Product axis</h1>
      <p className="mb-10 font-sans text-[17px] leading-[1.6] text-muted">
        Two archetypes sit at the ends of one spectrum. Real engagements are a blend; the platform expresses the
        blend as a ratio, not a binary.
      </p>

      <section className="mb-12 border-t border-line-strong pt-8">
        <h2 className="mb-3 font-display font-semibold text-2xl">Enterprise Tech DD</h2>
        <p className="mb-4 font-sans text-[15px] leading-[1.6] text-text">
          Technology is an <em>enabler of</em> the business. The question is whether the IT estate supports the
          plan, and what it will cost.
        </p>
        <p className="mb-4 font-sans text-[15px] leading-[1.6] text-muted">
          <strong className="text-text">Typical workstreams:</strong> application landscape &amp; ERP fitness;
          infrastructure, hosting and cloud cost; IT operating model, org and spend (run vs change); vendor and
          licence contracts; cyber security posture and compliance; business continuity and DR; integration /
          separation (TSA, carve-out) readiness; IT capex and run-rate normalisation; data governance; shadow IT.
        </p>
        <p className="font-sans text-[15px] leading-[1.6] text-muted">
          <strong className="text-text">Signals that pull this way:</strong> traditional or asset-heavy line of
          business; COTS/ERP-heavy estate (SAP, Oracle, Dynamics, Salesforce); small engineering headcount relative
          to total; carve-out or corporate-separation situation; cost-takeout or buy-and-build thesis with IT
          consolidation; strategic acquirer intending to integrate onto an existing platform; heavy on-prem
          footprint.
        </p>
      </section>

      <section className="mb-12 border-t border-line-strong pt-8">
        <h2 className="mb-3 font-display font-semibold text-2xl">Product Tech DD</h2>
        <p className="mb-4 font-sans text-[15px] leading-[1.6] text-text">
          Technology <em>is</em> the business. The question is whether the product and the team behind it can carry
          the growth case.
        </p>
        <p className="mb-4 font-sans text-[15px] leading-[1.6] text-muted">
          <strong className="text-text">Typical workstreams:</strong> architecture and scalability; code quality
          and technical debt; engineering velocity and delivery metrics (DORA); SDLC, testing and release practice;
          product management, roadmap credibility and PMF evidence; data and AI capability; product security and
          multi-tenancy; IP ownership, open-source licence hygiene and third-party dependencies; engineering talent,
          org design and key-person risk; unit economics of infrastructure (COGS per customer).
        </p>
        <p className="font-sans text-[15px] leading-[1.6] text-muted">
          <strong className="text-text">Signals that pull this way:</strong> digital-native target; software or
          platform is the revenue-generating asset; product-led growth motion; high engineering share of headcount;
          predominantly in-house build; growth / multiple-expansion thesis; minority growth investor backing a
          product roadmap; venture or growth-equity investor type.
        </p>
      </section>

      <section className="border-t border-line-strong pt-8">
        <h2 className="mb-4 font-display font-semibold text-2xl">Modifiers that apply to both</h2>
        <ul className="space-y-4 font-sans text-[15px] leading-[1.6] text-muted">
          <li>
            <strong className="text-text">Majority</strong> stake → deeper access, control-oriented workstreams
            (org change, cost takeout, 100-day plan) are in scope. <strong className="text-text">Minority</strong> →
            influence-oriented, lighter, more reliance on management representations.
          </li>
          <li>
            <strong className="text-text">Strategic</strong> investor → integration/interoperability, data
            migration, product overlap and rationalisation, security-posture alignment.{" "}
            <strong className="text-text">Financial</strong> investor → standalone viability, scalability headroom,
            cost curve, exit-readiness.
          </li>
          <li>
            <strong className="text-text">Regulated data</strong> (PII / PHI / PCI / financial) → mandatory
            compliance and privacy workstreams regardless of archetype.
          </li>
          <li>
            <strong className="text-text">AI/ML dependence</strong> → model governance, data rights, vendor
            lock-in, inference cost workstreams.
          </li>
          <li>
            <strong className="text-text">Deal stage &amp; access level</strong> → determine depth (red-flag vs
            confirmatory) and whether code-level review is even possible.
          </li>
        </ul>
      </section>
    </main>
  );
}
