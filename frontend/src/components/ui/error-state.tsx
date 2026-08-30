export function ErrorState({
  title = "Something went wrong",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div role="alert" className="rounded-2xl border border-redline bg-redline-tint px-8 py-10 text-center">
      <p className="font-sans text-lg text-text">{title}</p>
      {description && <p className="mx-auto mt-2 max-w-[48ch] font-sans text-sm text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
