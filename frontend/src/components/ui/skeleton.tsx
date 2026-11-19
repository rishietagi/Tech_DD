export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`shimmer rounded-xl ${className ?? "h-4 w-full"}`}
      aria-hidden
    />
  );
}
