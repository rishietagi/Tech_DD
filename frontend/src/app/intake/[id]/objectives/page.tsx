import { use } from "react";

import { ObjectivesStepForm } from "./objectives-step-form";

export default function ObjectivesStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ObjectivesStepForm engagementId={id} />;
}
