import { Badge } from "@/components/ui/badge";
import type { EngagementStatus } from "@/types/engagement";

const TONE: Record<EngagementStatus, "neutral" | "redline" | "steel"> = {
  draft: "redline",
  filed: "steel",
  scoped: "steel",
  archived: "neutral",
};

export function EngagementStatusBadge({ status }: { status: EngagementStatus }) {
  return <Badge tone={TONE[status]}>{status}</Badge>;
}
