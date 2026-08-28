interface MultiSelectProps {
  name: string;
  options: { value: string; label: string }[];
  value: string[];
  onChange: (value: string[]) => void;
}

export function MultiSelect({ name, options, value, onChange }: MultiSelectProps) {
  const toggle = (optValue: string) => {
    if (value.includes(optValue)) {
      onChange(value.filter((v) => v !== optValue));
    } else {
      onChange([...value, optValue]);
    }
  };

  return (
    <div role="group" aria-label={name} className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const checked = value.includes(opt.value);
        return (
          <label
            key={opt.value}
            className={`cursor-pointer rounded-full border px-3.5 py-1.5 font-sans text-[13px] transition-colors ${
              checked
                ? "border-redline bg-redline-tint text-text"
                : "border-line-strong bg-paper-2 text-muted hover:bg-paper-3"
            }`}
          >
            <input
              type="checkbox"
              checked={checked}
              onChange={() => toggle(opt.value)}
              className="absolute h-px w-px opacity-0"
            />
            {opt.label}
          </label>
        );
      })}
    </div>
  );
}
