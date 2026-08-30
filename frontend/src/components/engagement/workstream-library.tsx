"use client";

import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { metaApi } from "@/lib/api/engagements";
import type { LibraryRow } from "@/types/engagement";

const DECK_TITLE: Record<string, string> = {
  product: "Product Due Diligence",
  enterprise: "Enterprise IT Due Diligence",
};

function Row({ row }: { row: LibraryRow }) {
  return (
    <li className="border-t border-line py-4 first:border-t-0">
      <div className="mb-1.5 flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="font-display text-[15px] font-semibold text-text">
          <span className="mr-2 font-sans text-[12.5px] font-medium text-muted-2">
            {String(row.sn).padStart(2, "0")}
          </span>
          {row.title}
        </h4>
        {row.always_in_scope && (
          <span className="rounded-full border border-steel px-2.5 py-0.5 font-sans text-[10.5px] font-semibold text-steel uppercase">
            always in scope
          </span>
        )}
      </div>
      {row.lines.map((line, index) => (
        <p key={index} className="mb-1 max-w-[68ch] font-sans text-[13.5px] leading-[1.55] text-muted">
          {line}
        </p>
      ))}
      {row.dd_master_ref && (
        <p className="mt-1 font-sans text-[12px] text-muted-2 italic">{row.dd_master_ref}</p>
      )}
    </li>
  );
}

/**
 * The scope library, rendered from /meta/workstreams.
 *
 * The methodology page reads the same data the engine uses, so documentation and
 * behaviour cannot drift apart.
 */
export function WorkstreamLibraryView() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["workstream-library"],
    queryFn: () => metaApi.workstreams(),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        title="Can't reach the API right now"
        description="Start the backend to see the scope library here."
      />
    );
  }

  return (
    <div>
      <p className="mb-8 font-sans text-[14px] leading-[1.6] text-muted">
        These are the areas the engine selects from, quoted from{" "}
        <span className="text-text">{data.source_document}</span> ({data.source_owner}). The engine decides
        which open and at what depth; it never invents an area that is not here.
      </p>

      {Object.entries(data.decks).map(([deckId, rows]) => (
        <section key={deckId} className="mb-10">
          <h3 className="mb-1 font-display text-xl font-semibold text-text">
            {DECK_TITLE[deckId] ?? deckId}
          </h3>
          <p className="mb-3 font-sans text-[13px] text-muted-2">{rows.length} areas</p>
          <ul>
            {rows.map((row) => (
              <Row key={row.id} row={row} />
            ))}
          </ul>
        </section>
      ))}

      <p className="border-t border-line pt-4 font-sans text-[12px] text-muted-2">
        Library v{data.library_version}
      </p>
    </div>
  );
}
