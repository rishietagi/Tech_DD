import { use } from "react";

import { ItBudgetPage } from "./it-budget-page";

export default function EngagementItBudgetPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <ItBudgetPage engagementId={id} />;
}
