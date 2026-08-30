import type { ScopeOfWorkRead } from "@/types/engagement";

export function ScopeHeader({ scope }: { scope: ScopeOfWorkRead }) {
  return (
    <div className="mb-8">
      <div className="mb-1 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">Scope of Work</div>
      <h1 className="mb-3 font-display font-semibold text-3xl">Version {scope.version}</h1>

      {scope.payload.is_placeholder && (
        <div role="status" className="rounded-2xl border-2 border-redline bg-redline-tint px-5 py-4">
          <p className="font-sans text-[13px] font-semibold text-redline">
            Placeholder — generation engine not yet enabled
          </p>
          {scope.payload.placeholder_notice && (
            <p className="mt-2 font-sans text-sm text-text">{scope.payload.placeholder_notice}</p>
          )}
        </div>
      )}
    </div>
  );
}
