import { useId } from "react";

interface FieldProps {
  label: string;
  optional?: boolean;
  hint?: string;
  error?: string;
  children: (id: string, describedBy: string | undefined) => React.ReactNode;
}

export function Field({ label, optional, hint, error, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="mb-5">
      <label htmlFor={id} className="mb-1.5 block font-sans text-[13px] font-semibold text-text">
        {label}
        {optional && <span className="ml-1 font-sans text-muted-2 italic">optional</span>}
      </label>
      {hint && (
        <p id={hintId} className="mb-2 font-sans text-[13px] text-muted italic">
          {hint}
        </p>
      )}
      {children(id, describedBy)}
      {error && (
        <p id={errorId} role="alert" className="mt-1.5 font-sans text-[12px] font-medium text-redline">
          {error}
        </p>
      )}
    </div>
  );
}
