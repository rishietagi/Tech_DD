import { describe, expect, it } from "vitest";

import {
  dealContextSchema,
  dealStructureSchema,
  diligenceObjectivesSchema,
  investorSchema,
  targetCompanySchema,
} from "./intake";

describe("dealContextSchema", () => {
  const valid = {
    deal_name: "Project Falcon",
    context_narrative: "A".repeat(40),
    deal_stage: "Confirmatory",
    process_type: "Bilateral",
  };

  it("accepts a fully valid payload", () => {
    expect(dealContextSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects a context narrative shorter than 40 characters", () => {
    const result = dealContextSchema.safeParse({ ...valid, context_narrative: "too short" });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown deal stage", () => {
    const result = dealContextSchema.safeParse({ ...valid, deal_stage: "Not a real stage" });
    expect(result.success).toBe(false);
  });

  it("rejects a missing deal name", () => {
    const withoutName: Record<string, unknown> = { ...valid };
    delete withoutName.deal_name;
    const result = dealContextSchema.safeParse(withoutName);
    expect(result.success).toBe(false);
  });
});

describe("investorSchema", () => {
  const valid = {
    firm_name: "Northbridge Capital",
    investor_type: "PE",
    deal_lead_name: "Jordan Lee",
    deal_lead_email: "jordan.lee@northbridge.example",
  };

  it("accepts a valid investor payload", () => {
    expect(investorSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects an invalid email", () => {
    const result = investorSchema.safeParse({ ...valid, deal_lead_email: "not-an-email" });
    expect(result.success).toBe(false);
  });
});

describe("dealStructureSchema", () => {
  it("rejects a stake_percent outside 0-100", () => {
    const result = dealStructureSchema.safeParse({
      investment_type: "strategic",
      stake: "majority",
      stake_percent: 150,
      post_close_intent: "Standalone",
      carve_out_or_tsa: false,
    });
    expect(result.success).toBe(false);
  });

  it("accepts a valid structure without the optional stake_percent", () => {
    const result = dealStructureSchema.safeParse({
      investment_type: "financial",
      stake: "minority",
      post_close_intent: "Undecided",
      carve_out_or_tsa: true,
    });
    expect(result.success).toBe(true);
  });
});

describe("targetCompanySchema", () => {
  it("rejects a line_of_business shorter than 30 characters", () => {
    const result = targetCompanySchema.safeParse({
      company_name: "Acme Analytics",
      sector: "SaaS",
      line_of_business: "too short",
      business_model: "B2B SaaS",
      revenue_model: ["Subscription"],
      digital_maturity: "Digital native",
      headcount: 120,
      revenue_stage: "Growth",
      hq_location: "Austin, TX",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty revenue_model array", () => {
    const result = targetCompanySchema.safeParse({
      company_name: "Acme Analytics",
      sector: "SaaS",
      line_of_business: "A".repeat(30),
      business_model: "B2B SaaS",
      revenue_model: [],
      digital_maturity: "Digital native",
      headcount: 120,
      revenue_stage: "Growth",
      hq_location: "Austin, TX",
    });
    expect(result.success).toBe(false);
  });
});

describe("diligenceObjectivesSchema", () => {
  const base = {
    dd_objectives: ["Validate scalability"],
    access_level: "Full (data room, management sessions, code access)",
    code_access: "Full repository access",
    deliverable_format: ["Full diligence report"],
    timeline_weeks: 4,
  };

  it("accepts 'Let the platform decide' without an override reason", () => {
    const result = diligenceObjectivesSchema.safeParse({
      ...base,
      dd_type_preference: "Let the platform decide",
    });
    expect(result.success).toBe(true);
  });

  it("rejects an explicit override without a reason", () => {
    const result = diligenceObjectivesSchema.safeParse({
      ...base,
      dd_type_preference: "Enterprise Tech DD",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].path).toContain("dd_type_override_reason");
    }
  });

  it("accepts an explicit override when a reason is given", () => {
    const result = diligenceObjectivesSchema.safeParse({
      ...base,
      dd_type_preference: "Product Tech DD",
      dd_type_override_reason: "Engineering is 80% of headcount and the product is the revenue driver.",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a timeline of zero weeks", () => {
    const result = diligenceObjectivesSchema.safeParse({
      ...base,
      timeline_weeks: 0,
      dd_type_preference: "Let the platform decide",
    });
    expect(result.success).toBe(false);
  });
});
