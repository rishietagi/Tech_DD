export function FieldCounter({ filled, total }: { filled: number; total: number }) {
  return (
    <span className="font-sans text-xs text-muted-2">
      <b className="text-paper-on-ink">{filled}</b> of {total} steps on file
    </span>
  );
}
