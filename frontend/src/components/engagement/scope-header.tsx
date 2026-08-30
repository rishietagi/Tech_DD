import type { ScopeOfWorkPayloadV1 } from "@/types/engagement";

export function ScopeHeader({
  payload,
  version,
}: {
  payload: ScopeOfWorkPayloadV1;
  version: number;
}) {
  return (
    <div className="mb-8">
      <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
        Scope of Work
      </div>
      <h1 className="mb-3 font-display text-3xl font-semibold">Version {version}</h1>

      {payload.is_placeholder && (
        <div role="status" className="rounded-2xl border-2 border-redline bg-redline-tint px-5 py-4">
          <p className="font-sans text-[13px] font-semibold text-redline">
            Placeholder — generated before the scope engine existed
          </p>
          {payload.placeholder_notice && (
            <p className="mt-2 font-sans text-sm text-text">{payload.placeholder_notice}</p>
          )}
          <p className="mt-2 font-sans text-[13px] text-text">
            Regenerate to produce a scope from the current engine.
          </p>
        </div>
      )}
    </div>
  );
}
