import { forwardRef } from "react";

type DateInputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type">;

export const DateInput = forwardRef<HTMLInputElement, DateInputProps>(function DateInput(
  { className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      type="date"
      className={`w-full rounded-xl border border-line-strong bg-paper-2 px-3.5 py-3 font-sans text-[15px] text-text transition-colors focus:bg-paper focus:border-steel focus:outline-none ${className ?? ""}`}
      {...props}
    />
  );
});
