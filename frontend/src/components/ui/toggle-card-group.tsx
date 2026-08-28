interface ToggleCardOption {
  value: string;
  title: string;
  description: string;
}

interface ToggleCardGroupProps {
  name: string;
  options: ToggleCardOption[];
  value: string | undefined;
  onChange: (value: string) => void;
  columns?: 1 | 2;
}

export function ToggleCardGroup({ name, options, value, onChange, columns = 2 }: ToggleCardGroupProps) {
  return (
    <div className={`grid gap-3 ${columns === 2 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1"}`}>
      {options.map((opt) => {
        const checked = value === opt.value;
        return (
          <label
            key={opt.value}
            className={`relative block cursor-pointer rounded-[3px] border px-[18px] py-4 transition-colors ${
              checked ? "border-redline bg-redline-tint" : "border-line-strong bg-paper-2 hover:bg-paper-3"
            }`}
          >
            <input
              type="radio"
              name={name}
              value={opt.value}
              checked={checked}
              onChange={() => onChange(opt.value)}
              className="absolute h-px w-px opacity-0"
            />
            <span className="mb-1.5 block text-[15px] font-semibold">{opt.title}</span>
            <span className="block text-[13px] leading-[1.5] text-muted">{opt.description}</span>
            <span
              className={`absolute top-[15px] right-4 h-3.5 w-3.5 rounded-full border-[1.5px] transition-colors ${
                checked ? "border-redline bg-redline shadow-[inset_0_0_0_3px_var(--redline-tint)]" : "border-muted-2"
              }`}
              aria-hidden
            />
          </label>
        );
      })}
    </div>
  );
}
