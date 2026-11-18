import { use } from "react";

import { ReportPage } from "./report-page";

export default function EngagementReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <ReportPage engagementId={id} />;
}
