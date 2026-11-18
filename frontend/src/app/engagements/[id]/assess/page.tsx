import { Suspense, use } from "react";

import { AssessIndexPage } from "./assess-index-page";

export default function EngagementAssessPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  // The tab is read from the search params, which needs a Suspense boundary.
  return (
    <Suspense>
      <AssessIndexPage engagementId={id} />
    </Suspense>
  );
}
