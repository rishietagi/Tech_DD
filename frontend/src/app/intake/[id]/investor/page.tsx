import { use } from "react";

import { InvestorStepForm } from "./investor-step-form";

export default function InvestorStepPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <InvestorStepForm engagementId={id} />;
}
