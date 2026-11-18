import type { LandscapeModel } from "@/types/report";

/**
 * The "current IT landscape" picture, drawn from the same model the PPTX export draws —
 * applications on the left (ERP-managed functions, then grouped systems), infrastructure on
 * the right (backup targets, then platforms by location with what each hosts). Nothing is
 * drawn that the inventories do not contain.
 */
export function LandscapeDiagram({ model }: { model: LandscapeModel }) {
  if (model.empty) {
    return (
      <p className="font-sans text-[13px] text-muted">
        No applications or platforms have been inventoried, so there is nothing
        to draw.
      </p>
    );
  }
  return (
    <div
      role="img"
      aria-label="Current IT landscape: applications and infrastructure"
      className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]"
    >
      <div>
        <div className="mb-2 rounded-md bg-ink-2 px-3 py-1.5 text-center font-sans text-[12.5px] font-semibold text-paper-on-ink">
          IT Applications
        </div>
        {model.erp && (
          <div className="mb-3">
            <div className="mb-1.5 rounded-md border border-line bg-paper-2 px-3 py-1 text-center font-sans text-[11.5px] font-semibold text-ink">
              Functions managed in ERP: {model.erp.name}
            </div>
            <div className="flex gap-1.5">
              {(model.erp.functions.length ? model.erp.functions : ["—"]).map(
                (fn) => (
                  <div
                    key={fn}
                    className="flex-1 rounded-md border border-kpmg-blue bg-paper px-2 py-2 text-center font-sans text-[11.5px] font-semibold text-text"
                  >
                    {fn}
                  </div>
                ),
              )}
            </div>
          </div>
        )}
        <div className="space-y-1.5">
          {model.app_groups.map((group) => (
            <div
              key={group.label}
              className="grid grid-cols-[150px_minmax(0,1fr)] gap-1.5"
            >
              <div className="flex items-center rounded-md bg-kpmg-blue px-2 py-1.5 font-sans text-[11px] font-semibold text-paper-on-ink">
                {group.label}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {group.items.map((item) => (
                  <div
                    key={item.name}
                    title={item.detail}
                    className="flex-1 rounded-md border border-line bg-paper-2 px-2 py-1.5 text-center font-sans text-[11.5px] text-text"
                  >
                    {item.name}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div>
        <div className="mb-2 rounded-md bg-ink-2 px-3 py-1.5 text-center font-sans text-[12.5px] font-semibold text-paper-on-ink">
          IT Infrastructure
        </div>
        {model.backup.length > 0 && (
          <div className="mb-3 grid grid-cols-[110px_minmax(0,1fr)] gap-1.5">
            <div className="flex items-center rounded-md border border-line bg-paper-2 px-2 py-1 font-sans text-[11px] font-semibold text-ink">
              Backup and restoration
            </div>
            <div className="space-y-1">
              {model.backup.map((name) => (
                <div
                  key={name}
                  className="rounded-md border border-line bg-paper px-2 py-1 text-center font-sans text-[11.5px]"
                >
                  {name}
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="space-y-2">
          {model.infra_groups.map((group) => (
            <div key={group.label}>
              <div className="mb-1 rounded-md border border-line bg-paper-2 px-2 py-1 text-center font-sans text-[11.5px] font-semibold text-ink">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <div
                    key={item.name}
                    className="rounded-md border border-line bg-paper px-2 py-1.5 font-sans text-[11.5px] text-text"
                  >
                    <span className="font-medium">{item.name}</span>
                    {item.detail && (
                      <span className="ml-1.5 text-muted-2">
                        · {item.detail}
                      </span>
                    )}
                    {item.hosts && item.hosts.length > 0 && (
                      <span className="block text-[11px] text-muted">
                        hosts {item.hosts.join(", ")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
