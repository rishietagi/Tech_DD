import { forwardRef } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-ink text-paper-on-ink border-ink hover:bg-kpmg-blue-dark hover:border-kpmg-blue-dark",
  secondary: "bg-transparent text-text border-line-strong hover:bg-paper-2",
  ghost: "bg-transparent text-muted border-transparent hover:text-text",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", className, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={`rounded-full border px-7 py-3.5 font-sans text-[14px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${className ?? ""}`}
      {...props}
    />
  );
});
