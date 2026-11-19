"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { intelligenceApi } from "@/lib/api/report";
import type { SkillStatus } from "@/types/report";

/**
 * The intelligence pipeline, made visible: one switch, and every skill with its status,
 * what it may and may not change, its deterministic floor, and the instructions the model
 * is given. Read-only — the switch is AI_MODE in the server's .env, and a skill is edited in
 * its SKILL.md, so the instructions shown are the instructions used.
 */

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="mb-1 font-mono text-[10px] tracking-wide text-muted uppercase">
        {title}
      </p>
      <ul className="list-disc space-y-0.5 pl-5 font-sans text-[13px] leading-[1.5] text-text">
        {items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </div>
  );
}

function SkillCard({ skill }: { skill: SkillStatus }) {
  const [open, setOpen] = useState(false);
  const llm = skill.status === "llm";
  return (
    <li className="rounded-2xl border border-line-strong bg-paper p-6">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="font-mono text-[15px] font-semibold text-ink">
          {skill.name}
        </h2>
        <span
          className={`rounded-full px-3 py-1 font-sans text-[11px] font-semibold uppercase ${
            llm
              ? "bg-status-received-tint text-status-received"
              : "bg-paper-2 text-muted"
          }`}
          title={skill.reason}
        >
          {llm ? "Model on" : "Deterministic"} · {skill.reason}
        </span>
      </div>
      <p className="mb-4 max-w-[90ch] font-sans text-[14px] leading-[1.6] text-muted">
        {skill.description}
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        <List title="May change" items={skill.may_change} />
        <List title="Must not change" items={skill.must_not_change} />
        <List title="House rules" items={skill.house_rules} />
      </div>
      <p className="mt-4 font-sans text-[12.5px] text-muted">
        <span className="font-semibold text-text">Deterministic floor:</span>{" "}
        {skill.deterministic_fallback} ·{" "}
        <span className="font-semibold text-text">Mode:</span>{" "}
        {skill.mode.replace("_", " ")} · v{skill.version}
      </p>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="mt-3 font-sans text-[12.5px] font-medium text-steel hover:underline"
      >
        {open ? "Hide" : "Show"} the instructions the model is given
      </button>
      {open && (
        <pre className="mt-3 max-h-[480px] overflow-auto rounded-xl bg-paper-2 p-4 font-code text-[12px] leading-[1.55] whitespace-pre-wrap text-text">
          {skill.body}
        </pre>
      )}
    </li>
  );
}

export function AiSkillsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["intelligence"],
    queryFn: intelligenceApi.status,
  });

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1100px] px-7 pt-14 pb-24">
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }
  if (isError || !data) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState title="Couldn't load the AI status" />
      </main>
    );
  }
  return (
    <main className="mx-auto w-full max-w-[1100px] px-7 pt-14 pb-24">
      <div className="mb-3 font-sans text-xs font-semibold tracking-[0.08em] text-kpmg-blue uppercase">
        AI &amp; skills
      </div>
      <h1 className="mb-4 font-display text-4xl font-semibold">
        Every generator, rules first
      </h1>
      <p className="mb-6 max-w-[80ch] font-sans text-[16px] leading-[1.6] text-muted">
        Every generation task in the platform has a deterministic floor that
        always runs. A skill describes what a model may add on top — and what it
        may never change. One switch decides whether it does.
      </p>
      <dl className="mb-10 grid gap-3 rounded-2xl border border-line-strong bg-paper-2 p-5 sm:grid-cols-4">
        <div>
          <dt className="font-mono text-[10px] tracking-wide text-muted uppercase">
            AI_MODE
          </dt>
          <dd className="font-sans text-[18px] font-semibold text-text">
            {data.mode}
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] tracking-wide text-muted uppercase">
            Model key
          </dt>
          <dd className="font-sans text-[18px] font-semibold text-text">
            {data.key_present ? "Present" : "None"}
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] tracking-wide text-muted uppercase">
            Model
          </dt>
          <dd className="font-sans text-[18px] font-semibold text-text">
            {data.model}
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[10px] tracking-wide text-muted uppercase">
            Status
          </dt>
          <dd className="font-sans text-[18px] font-semibold text-text">
            {data.active ? "Model on" : "Deterministic"}
          </dd>
        </div>
      </dl>
      <p className="mb-6 font-sans text-[13px] text-muted">
        To turn the model on, set{" "}
        <code className="font-mono">AI_MODE=auto</code> and a key in the
        server&apos;s <code className="font-mono">.env</code>, then restart it.
        Keep a skill deterministic under auto with{" "}
        <code className="font-mono">AI_DISABLED_SKILLS</code>.
      </p>
      <ul className="space-y-4">
        {data.skills.map((s) => (
          <SkillCard key={s.name} skill={s} />
        ))}
      </ul>
    </main>
  );
}
