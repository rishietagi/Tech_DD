import type { Workstream } from "@/types/engagement";

export function WorkstreamCard({ workstream }: { workstream: Workstream }) {
  return (
    <div className="border-t border-line py-6 first:border-t-0">
      <h3 className="mb-1.5 font-serif text-xl font-medium">{workstream.name}</h3>
      <p className="mb-4 font-sans text-sm text-muted">{workstream.summary}</p>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div>
          <h4 className="mb-2 font-mono text-[10.5px] tracking-[0.08em] text-muted-2 uppercase">Objectives</h4>
          <ul className="list-disc space-y-1 pl-4 font-sans text-sm text-text">
            {workstream.objectives.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-2 font-mono text-[10.5px] tracking-[0.08em] text-muted-2 uppercase">Key questions</h4>
          <ul className="list-disc space-y-1 pl-4 font-sans text-sm text-text">
            {workstream.key_questions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="mb-2 font-mono text-[10.5px] tracking-[0.08em] text-muted-2 uppercase">Evidence requested</h4>
          <ul className="list-disc space-y-1 pl-4 font-sans text-sm text-text">
            {workstream.evidence_requests.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
