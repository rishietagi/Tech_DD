import { use } from "react";

import { ScopePage } from "./scope-page";

export default function EngagementScopePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ScopePage engagementId={id} />;
}
