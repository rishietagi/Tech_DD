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
      <label htmlFor={id} className="mb-1.5 block font-mono text-[11px] tracking-[0.06em] text-muted uppercase">
        {label}
        {optional && <span className="ml-1 font-serif text-muted-2 italic normal-case">optional</span>}
      </label>
      {hint && (
        <p id={hintId} className="mb-2 font-serif text-[13px] text-muted italic">
          {hint}
        </p>
      )}
      {children(id, describedBy)}
      {error && (
        <p id={errorId} role="alert" className="mt-1.5 font-mono text-[11px] text-redline">
          {error}
        </p>
      )}
    </div>
  );
}
