export function FieldCounter({ filled, total }: { filled: number; total: number }) {
  return (
    <span className="font-mono text-xs text-paper-on-ink/60">
      <b className="text-paper-on-ink">{filled}</b> of {total} steps on file
    </span>
  );
}
