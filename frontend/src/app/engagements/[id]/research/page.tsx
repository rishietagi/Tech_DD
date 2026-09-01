import { use } from "react";

import { ResearchPage } from "./research-page";

export default function EngagementResearchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ResearchPage engagementId={id} />;
}
