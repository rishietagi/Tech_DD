import { use } from "react";

import { ContextStepForm } from "./context-step-form";

export default function ContextStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ContextStepForm engagementId={id} />;
}
