import { use } from "react";

import { RationaleStepForm } from "./rationale-step-form";

export default function RationaleStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <RationaleStepForm engagementId={id} />;
}
