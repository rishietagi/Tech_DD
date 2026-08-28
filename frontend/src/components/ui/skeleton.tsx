export function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-[3px] bg-paper-3 ${className ?? "h-4 w-full"}`} aria-hidden />;
}
