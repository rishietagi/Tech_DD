import { ScopeHeader } from "@/components/engagement/scope-header";
import { WorkstreamCard } from "@/components/engagement/workstream-card";
import type { ScopeOfWorkRead } from "@/types/engagement";

export function ScopeDocument({ scope }: { scope: ScopeOfWorkRead }) {
  return (
    <div>
      <ScopeHeader scope={scope} />
      <div className="rounded-2xl border border-line-strong bg-paper-2 px-8 py-2 sm:px-10">
        {scope.payload.workstreams.map((workstream) => (
          <WorkstreamCard key={workstream.name} workstream={workstream} />
        ))}
      </div>
    </div>
  );
}
