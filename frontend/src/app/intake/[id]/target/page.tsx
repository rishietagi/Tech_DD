import { use } from "react";

import { TargetStepForm } from "./target-step-form";

export default function TargetStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <TargetStepForm engagementId={id} />;
}
