import { use } from "react";

import { ProcessAssessPage } from "./process-assess-page";

export default function EngagementProcessAssessPage({
  params,
}: {
  params: Promise<{ id: string; processKey: string }>;
}) {
  const { id, processKey } = use(params);
  return <ProcessAssessPage engagementId={id} processKey={processKey} />;
}
