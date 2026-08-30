interface StepFooterProps {
  backHref?: string;
  isSubmitting?: boolean;
  nextLabel?: string;
}

export function StepFooter({ backHref, isSubmitting, nextLabel = "Save & continue" }: StepFooterProps) {
  return (
    <div className="mt-8 flex items-center justify-between border-t border-line pt-6">
      {backHref ? (
        <a href={backHref} className="font-sans text-[14px] font-medium text-muted transition-colors hover:text-text">
          ← Back
        </a>
      ) : (
        <span />
      )}
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-full border border-ink bg-ink px-7 py-3.5 font-sans text-[14px] font-medium text-paper-on-ink transition-colors hover:border-kpmg-blue-dark hover:bg-kpmg-blue-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Saving…" : nextLabel}
      </button>
    </div>
  );
}
