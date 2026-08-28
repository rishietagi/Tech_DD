import { use } from "react";

import { EngagementDetail } from "./engagement-detail";

export default function EngagementDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <EngagementDetail engagementId={id} />;
}
