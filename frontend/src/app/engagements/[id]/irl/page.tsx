import { use } from "react";

import { IrlPage } from "./irl-page";

export default function EngagementIrlPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <IrlPage engagementId={id} />;
}
