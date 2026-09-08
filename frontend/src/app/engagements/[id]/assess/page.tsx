import { use } from "react";

import { AssessIndexPage } from "./assess-index-page";

export default function EngagementAssessPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <AssessIndexPage engagementId={id} />;
}
