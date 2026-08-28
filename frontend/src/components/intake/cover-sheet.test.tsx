import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CoverSheet } from "./cover-sheet";
import type { IntakeDraft } from "@/types/intake";

const EMPTY_INTAKE: IntakeDraft = {
  context: null,
  rationale: null,
  structure: null,
  investor: null,
  target: null,
  technology: null,
  objectives: null,
};

describe("CoverSheet", () => {
  it("shows 'Not started' for every section when the intake is empty", () => {
    render(<CoverSheet engagementId="abc-123" intake={EMPTY_INTAKE} />);
    expect(screen.getAllByText("Not started")).toHaveLength(7);
  });

  it("renders filled-in section fields and formats them for display", () => {
    const intake: IntakeDraft = {
      ...EMPTY_INTAKE,
      context: {
        deal_name: "Project Falcon",
        context_narrative: "Some narrative",
        deal_stage: "Confirmatory",
        process_type: "Bilateral",
      },
      structure: {
        investment_type: "strategic",
        stake: "majority",
        carve_out_or_tsa: false,
        post_close_intent: "Standalone",
      },
    };

    render(<CoverSheet engagementId="abc-123" intake={intake} />);

    expect(screen.getByText("Project Falcon")).toBeInTheDocument();
    // carve_out_or_tsa: false should render as "No", not "false" or blank.
    expect(screen.getByText("No")).toBeInTheDocument();
  });

  it("links each section's Edit action to its intake step route", () => {
    render(<CoverSheet engagementId="abc-123" intake={EMPTY_INTAKE} />);
    const editLinks = screen.getAllByRole("link", { name: "Edit" });
    expect(editLinks[0]).toHaveAttribute("href", "/intake/abc-123/context");
    expect(editLinks[6]).toHaveAttribute("href", "/intake/abc-123/objectives");
  });

  it("renders arrays joined with commas", () => {
    const intake: IntakeDraft = {
      ...EMPTY_INTAKE,
      rationale: {
        rationale_narrative: "Thesis",
        value_creation_levers: ["Cost takeout", "Margin expansion"],
      },
    };
    render(<CoverSheet engagementId="abc-123" intake={intake} />);
    expect(screen.getByText("Cost takeout, Margin expansion")).toBeInTheDocument();
  });
});
