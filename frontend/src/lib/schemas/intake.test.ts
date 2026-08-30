import { describe, expect, it } from "vitest";

import { dealContextSchema, dealStructureSchema, diligenceObjectivesSchema, targetCompanySchema } from "./intake";

describe("dealContextSchema", () => {
  const valid = {
    deal_name: "Project Falcon",
    context_narrative: "A".repeat(40),
    deal_stage: "Exclusivity",
    process_type: "Bilateral",
    investor_firm_name: "Northbridge Capital",
  };

  it("accepts a fully valid payload", () => {
    expect(dealContextSchema.safeParse(valid).success).toBe(true);
  });

  it("accepts an empty payload — every field is optional", () => {
    expect(dealContextSchema.safeParse({}).success).toBe(true);
  });

  it("rejects an unknown deal stage", () => {
    const result = dealContextSchema.safeParse({ ...valid, deal_stage: "Not a real stage" });
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
    });
    expect(result.success).toBe(false);
  });

  it("accepts an empty payload — every field is optional", () => {
    expect(dealStructureSchema.safeParse({}).success).toBe(true);
  });
});

describe("targetCompanySchema", () => {
  it("rejects a line_of_business shorter than 30 characters", () => {
    const result = targetCompanySchema.safeParse({
      sector: "SaaS",
      line_of_business: "too short",
    });
    expect(result.success).toBe(false);
  });

  it("requires sector and line_of_business but nothing else", () => {
    const result = targetCompanySchema.safeParse({
      sector: "SaaS",
      line_of_business: "A".repeat(30),
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing sector", () => {
    const result = targetCompanySchema.safeParse({
      line_of_business: "A".repeat(30),
    });
    expect(result.success).toBe(false);
  });
});

describe("diligenceObjectivesSchema", () => {
  it("accepts an empty payload — every field is optional", () => {
    expect(diligenceObjectivesSchema.safeParse({}).success).toBe(true);
  });

  it("rejects a timeline of zero weeks", () => {
    const result = diligenceObjectivesSchema.safeParse({ timeline_weeks: 0 });
    expect(result.success).toBe(false);
  });

  it("accepts a fully valid payload", () => {
    const result = diligenceObjectivesSchema.safeParse({
      dd_objectives: ["Validate scalability"],
      access_level: "Full (data room and management sessions)",
      deliverable_format: ["Full diligence report"],
      timeline_weeks: 4,
    });
    expect(result.success).toBe(true);
  });
});
