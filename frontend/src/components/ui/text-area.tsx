import { forwardRef } from "react";

type TextAreaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { invalid, className, ...props },
  ref,
) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={`min-h-[104px] w-full resize-y rounded-xl border bg-paper-2 px-3.5 py-3 font-sans text-[15px] leading-[1.55] text-text transition-colors focus:bg-paper focus:border-steel focus:outline-none ${
        invalid ? "border-redline" : "border-line-strong"
      } ${className ?? ""}`}
      {...props}
    />
  );
});
