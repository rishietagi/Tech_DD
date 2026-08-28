import { use } from "react";

import { StructureStepForm } from "./structure-step-form";

export default function StructureStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <StructureStepForm engagementId={id} />;
}
