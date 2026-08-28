import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MultiSelect } from "./multi-select";

const OPTIONS = [
  { value: "a", label: "Option A" },
  { value: "b", label: "Option B" },
  { value: "c", label: "Option C" },
];

describe("MultiSelect", () => {
  it("renders every option unchecked when value is empty", () => {
    render(<MultiSelect name="test" options={OPTIONS} value={[]} onChange={vi.fn()} />);
    for (const opt of OPTIONS) {
      expect(screen.getByRole("checkbox", { name: opt.label })).not.toBeChecked();
    }
  });

  it("marks options in value as checked", () => {
    render(<MultiSelect name="test" options={OPTIONS} value={["b"]} onChange={vi.fn()} />);
    expect(screen.getByRole("checkbox", { name: "Option B" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Option A" })).not.toBeChecked();
  });

  it("adds a value when an unchecked option is clicked", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MultiSelect name="test" options={OPTIONS} value={["a"]} onChange={onChange} />);

    await user.click(screen.getByRole("checkbox", { name: "Option C" }));

    expect(onChange).toHaveBeenCalledWith(["a", "c"]);
  });

  it("removes a value when a checked option is clicked", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MultiSelect name="test" options={OPTIONS} value={["a", "b"]} onChange={onChange} />);

    await user.click(screen.getByRole("checkbox", { name: "Option A" }));

    expect(onChange).toHaveBeenCalledWith(["b"]);
  });
});
