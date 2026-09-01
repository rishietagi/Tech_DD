import { use } from "react";

import { ChecklistPage } from "./checklist-page";

export default function EngagementChecklistPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ChecklistPage engagementId={id} />;
}
