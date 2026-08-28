import type { Config } from "tailwindcss";

// Tailwind v4 is CSS-first: the canonical token definitions live in
// src/app/globals.css (`@theme inline`), sourced from src/styles/tokens.css.
// This file exists so tooling that still expects a config file (editor
// plugins, `content` globs) has one; it intentionally does not redefine
// colors so nothing can drift from the CSS source of truth (CLAUDE.md §8).
const config: Config = {
  content: ["./src/**/*.{ts,tsx,mdx}"],
};

export default config;
