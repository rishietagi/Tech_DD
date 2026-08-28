interface StepFooterProps {
  backHref?: string;
  isSubmitting?: boolean;
  nextLabel?: string;
}

export function StepFooter({ backHref, isSubmitting, nextLabel = "Save & continue" }: StepFooterProps) {
  return (
    <div className="mt-8 flex items-center justify-between border-t border-line pt-6">
      {backHref ? (
        <a
          href={backHref}
          className="font-mono text-[13px] tracking-[0.06em] text-muted uppercase transition-colors hover:text-text"
        >
          ← Back
        </a>
      ) : (
        <span />
      )}
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-[3px] border border-ink bg-ink px-[26px] py-[15px] font-mono text-[13px] tracking-[0.08em] text-paper-on-ink uppercase transition-colors hover:border-redline-dark hover:bg-redline-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Saving…" : nextLabel}
      </button>
    </div>
  );
}
