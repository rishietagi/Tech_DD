import { forwardRef } from "react";

type TextInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
};

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(function TextInput(
  { invalid, className, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={`w-full rounded-[3px] border bg-paper-2 px-3.5 py-3 font-sans text-[15px] text-text transition-colors focus:bg-paper focus:border-steel focus:outline-none ${
        invalid ? "border-redline" : "border-line-strong"
      } ${className ?? ""}`}
      {...props}
    />
  );
});
