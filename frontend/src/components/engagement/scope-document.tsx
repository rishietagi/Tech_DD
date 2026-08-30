import { ScopeHeader } from "@/components/engagement/scope-header";
import { WorkstreamCard } from "@/components/engagement/workstream-card";
import type { ScopeOfWorkPayloadV1 } from "@/types/engagement";

/**
 * The Phase 1 placeholder scope. Retained so scope rows generated before the engine
 * existed still render; new scopes use ScopeDocumentV2.
 */
export function ScopeDocument({
  payload,
  version,
}: {
  payload: ScopeOfWorkPayloadV1;
  version: number;
}) {
  return (
    <div>
      <ScopeHeader payload={payload} version={version} />
      <div className="rounded-2xl border border-line-strong bg-paper-2 px-8 py-2 sm:px-10">
        {payload.workstreams.map((workstream) => (
          <WorkstreamCard key={workstream.name} workstream={workstream} />
        ))}
      </div>
    </div>
  );
}
