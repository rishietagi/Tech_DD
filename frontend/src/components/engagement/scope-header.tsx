import type { ScopeOfWorkRead } from "@/types/engagement";

export function ScopeHeader({ scope }: { scope: ScopeOfWorkRead }) {
  return (
    <div className="mb-8">
      <div className="mb-1 font-mono text-xs tracking-[0.16em] text-redline uppercase">Scope of Work</div>
      <h1 className="mb-3 font-serif text-3xl font-medium">Version {scope.version}</h1>

      {scope.payload.is_placeholder && (
        <div role="status" className="rounded-[3px] border-2 border-redline bg-redline-tint px-5 py-4">
          <p className="font-mono text-xs tracking-[0.06em] text-redline uppercase">
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
