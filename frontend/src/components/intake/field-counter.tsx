export function FieldCounter({
  filled,
  total,
}: {
  filled: number;
  total: number;
}) {
  return (
    <span className="font-sans text-xs text-muted-2">
      <b className="font-semibold text-text">{filled}</b> of {total} steps on
      file
    </span>
  );
}
