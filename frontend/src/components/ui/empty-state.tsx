export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-[3px] border border-dashed border-line-strong bg-paper-2 px-8 py-14 text-center">
      <p className="font-serif text-lg text-text">{title}</p>
      {description && <p className="mx-auto mt-2 max-w-[48ch] font-sans text-sm text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
