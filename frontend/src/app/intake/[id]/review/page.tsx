import { use } from "react";

import { ReviewStep } from "./review-step";

export default function ReviewStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ReviewStep engagementId={id} />;
}
