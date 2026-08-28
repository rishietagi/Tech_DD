import { expect, test } from "@playwright/test";

test("full intake flow: create, fill every step, review, file", async ({ page }) => {
  await page.goto("/intake/new");
  await page.waitForURL(/\/intake\/[^/]+\/context/);
  const engagementId = page.url().match(/\/intake\/([^/]+)\//)?.[1];
  expect(engagementId).toBeTruthy();

  // Step 1 — Context
  await page.getByLabel("Deal codename").fill("Project Falcon");
  await page
    .getByRole("textbox", { name: "Context" })
    .fill("Target received an inbound approach from a strategic acquirer exploring platform consolidation.");
  await page.getByLabel("Deal stage").selectOption("Confirmatory");
  await page.getByLabel("Process type").selectOption("Bilateral");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/rationale/);

  // Step 2 — Rationale
  await page
    .getByRole("textbox", { name: "Rationale" })
    .fill("Buyer believes the product can be cross-sold into its existing enterprise customer base.");
  await page.getByRole("group", { name: "value_creation_levers" }).getByText("Product expansion").click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/structure/);

  // Step 3 — Deal Structure
  await page.getByText("Strategic", { exact: true }).click();
  await page.getByText("Majority", { exact: true }).click();
  await page.getByLabel("Post-close intent").selectOption("Integrate into existing platform");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/investor/);

  // Step 4 — Investor
  await page.getByLabel("Firm name").fill("Northbridge Capital");
  await page.getByLabel("Investor type").selectOption("PE");
  await page.getByLabel("Deal lead name").fill("Jordan Lee");
  await page.getByLabel("Deal lead email").fill("jordan.lee@northbridge.example");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/target/);

  // Step 5 — Target Company
  await page.getByLabel("Company name").fill("Acme Analytics");
  await page
    .getByLabel("Line of business")
    .fill("Sells usage-based analytics tooling to mid-market e-commerce companies.");
  await page.getByLabel("Sector").selectOption("SaaS");
  await page.getByLabel("Business model").selectOption("B2B SaaS");
  await page.getByRole("group", { name: "revenue_model" }).getByText("Subscription", { exact: true }).click();
  await page.getByLabel("Digital maturity").selectOption("Digital native");
  await page.getByLabel("Headcount").fill("120");
  await page.getByLabel("Revenue stage").selectOption("Growth");
  await page.getByLabel("HQ location").fill("Austin, TX");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/technology/);

  // Step 6 — Technology Profile
  await page.getByText("Yes — it's the product").click();
  await page.getByLabel("Build vs buy").selectOption("Predominantly in-house build");
  await page.getByLabel("Hosting model").selectOption("Public cloud");
  await page.getByLabel("AI/ML dependence").selectOption("Embedded in the product");
  await page.getByRole("group", { name: "data_sensitivity" }).getByText("Personal data (PII)").click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.waitForURL(/\/objectives/);

  // Step 7 — Objectives & Logistics
  await page.getByRole("group", { name: "dd_objectives" }).getByText("Validate scalability").click();
  await page.getByLabel("Access level").selectOption("Full (data room, management sessions, code access)");
  await page.getByLabel("Code access").selectOption("Full repository access");
  await page.getByRole("group", { name: "deliverable_format" }).getByText("Full diligence report").click();
  await page.getByLabel("Timeline (weeks)").fill("4");
  await page.getByRole("button", { name: "Continue to review" }).click();
  await page.waitForURL(/\/review/);

  // Step 8 — Review & File
  await expect(page.getByText("Project Falcon").first()).toBeVisible();
  await expect(page.getByText("Acme Analytics").first()).toBeVisible();
  await page.getByRole("button", { name: "File engagement" }).click();
  await page.waitForURL(/\/engagements\/[^/]+$/);
  await expect(page.getByText("filed", { exact: true })).toBeVisible();

  // Reload from URL to prove persistence (the API is the source of truth).
  await page.reload();
  await expect(page.getByText("Project Falcon").first()).toBeVisible();

  // Scope route renders the labelled placeholder.
  await page.getByRole("link", { name: "View scope of work" }).click();
  await page.waitForURL(/\/scope$/);
  const generateButton = page.getByRole("button", { name: /Generate scope/i });
  if (await generateButton.isVisible().catch(() => false)) {
    await generateButton.click();
  }
  await expect(page.getByText("Placeholder — generation engine not yet enabled")).toBeVisible();

  // Engagements list shows the filed engagement.
  await page.goto("/engagements");
  await expect(page.getByText("Project Falcon").first()).toBeVisible();
});
