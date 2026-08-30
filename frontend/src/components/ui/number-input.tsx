import { forwardRef } from "react";

type NumberInputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "onChange" | "value"> & {
  invalid?: boolean;
  value?: number;
  onValueChange: (value: number | undefined) => void;
};

export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(function NumberInput(
  { invalid, className, value, onValueChange, ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      type="number"
      value={value ?? ""}
      onChange={(e) => onValueChange(e.target.value === "" ? undefined : Number(e.target.value))}
      aria-invalid={invalid || undefined}
      className={`w-full rounded-xl border bg-paper-2 px-3.5 py-3 font-sans text-[15px] text-text transition-colors focus:bg-paper focus:border-steel focus:outline-none ${
        invalid ? "border-redline" : "border-line-strong"
      } ${className ?? ""}`}
      {...props}
    />
  );
});
