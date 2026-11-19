import { redirect } from "next/navigation";

/** The IT budget moved into Assess as a tab (Phase 8, Rishi 2026-11-18). */
export default async function EngagementItBudgetPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/engagements/${id}/assess?tab=budget`);
}
