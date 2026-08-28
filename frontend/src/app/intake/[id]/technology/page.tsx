import { use } from "react";

import { TechnologyStepForm } from "./technology-step-form";

export default function TechnologyStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <TechnologyStepForm engagementId={id} />;
}
