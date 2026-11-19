"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRef, useState } from "react";

import { LandscapeDiagram } from "@/components/report/landscape-diagram";
import { EditableList, EditableText } from "@/components/ui/editable";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { TextInput } from "@/components/ui/text-input";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api/client";
import { reportApi } from "@/lib/api/report";
import { IMPACT_LABELS } from "@/types/estate";
import type {
  Block,
  EditValue,
  ExecutiveFinding,
  ExecutiveRow,
  ReportPayload,
  ReportRead,
  ReportSection,
  RiskLevel,
} from "@/types/report";
import { RISK_LEVELS } from "@/types/report";
import {
  InvestmentExplain,
  ReportRiskExplain,
} from "@/components/engagement/explain";
import { InfoTip } from "@/components/ui/info-tip";

/**
 * The final report — the deliverable. docs/reference/REPORT_STRUCTURE.md.
 *
 * Every block shows exactly what the PPTX will contain, and every block is editable
 * before export (Rishi, 2026-11-18). Edits are stored against stable keys, so regenerating
 * — after more IRL responses or a re-score — keeps them. Areas and sections can be left out
 * of the export with their include toggle rather than deleted.
 */

const RISK_CLASSES: Record<RiskLevel, string> = {
  High: "bg-priority-critical",
  Medium: "bg-priority-high",
  Low: "bg-status-received",
  "Not assessed": "bg-line-strong",
};

const NAV = [
  { id: "cover", label: "Cover" },
  { id: "context", label: "Context setting" },
  { id: "glossary", label: "Glossary" },
  { id: "in_scope", label: "In-scope areas" },
  { id: "limitations", label: "Data limitations" },
  { id: "executive", label: "Executive summary" },
  { id: "supporting", label: "Supporting analysis" },
  { id: "appendix", label: "Appendix" },
];

type Edit = (key: string, value: EditValue) => Promise<void>;
type Revert = (key: string) => Promise<void>;

function Slide({
  id,
  number,
  title,
  children,
  aside,
}: {
  id: string;
  number?: string;
  title: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className="scroll-mt-24 rounded-2xl border border-line-strong bg-paper shadow-sm"
    >
      <header className="flex flex-wrap items-baseline justify-between gap-3 border-b border-line px-7 pt-6 pb-4">
        <h2 className="font-display text-[26px] leading-tight text-ink">
          {number && (
            <span className="mr-3 font-mono text-[13px] text-muted-2">
              {number}
            </span>
          )}
          {title}
        </h2>
        <div className="flex items-center gap-3">
          {aside}
          <span className="font-sans text-[12px] font-bold tracking-wide text-ink-2">
            DRAFT
          </span>
        </div>
      </header>
      <div className="px-7 py-6">{children}</div>
    </section>
  );
}

function IncludeToggle({
  included,
  onChange,
  label,
}: {
  included: boolean;
  onChange: (value: boolean) => void;
  label: string;
}) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-2 font-sans text-[12px] text-muted">
      <input
        type="checkbox"
        checked={included}
        onChange={(e) => onChange(e.target.checked)}
        className="h-3.5 w-3.5 accent-[var(--ink)]"
        aria-label={`Include ${label} in the export`}
      />
      In export
    </label>
  );
}

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5 font-sans text-[13.5px] leading-[1.55] text-text marker:text-muted-2">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function TableView({ block }: { block: Block }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line-strong">
      <table className="w-full border-collapse font-sans text-[12.5px]">
        <thead>
          <tr className="bg-ink text-left text-paper-on-ink">
            {block.columns.map((c) => (
              <th key={c} className="px-3 py-2 font-semibold">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {block.rows.map((row, r) => (
            <tr key={r} className={r % 2 ? "bg-paper-2" : "bg-paper"}>
              {row.map((cell, c) => (
                <td key={c} className="px-3 py-2 align-top text-text">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BlockView({
  block,
  prefix,
  edit,
  revert,
  edited,
  engagementId,
}: {
  block: Block;
  prefix: string;
  edit: Edit;
  revert: Revert;
  edited: Set<string>;
  engagementId: string;
}) {
  const key = (field: string) => `${prefix}.${block.id}.${field}`;
  const isEdited = (field: string) => edited.has(key(field));
  const body = (() => {
    switch (block.kind) {
      case "paragraph":
        return (
          <EditableText
            value={block.text}
            label={block.title || "paragraph"}
            edited={isEdited("text")}
            onSave={(v) => edit(key("text"), v)}
            onRevert={() => revert(key("text"))}
          >
            <p className="font-sans text-[13.5px] leading-[1.6] text-text">
              {block.text}
            </p>
          </EditableText>
        );
      case "bullets":
        return (
          <EditableList
            items={block.items}
            label={block.title || "bullets"}
            edited={isEdited("items")}
            onSave={(v) => edit(key("items"), v)}
            onRevert={() => revert(key("items"))}
          >
            <Bullets items={block.items} />
          </EditableList>
        );
      case "table":
        return (
          <EditableText
            value={block.rows.map((r) => r.join(" | ")).join("\n")}
            rows={Math.min(block.rows.length + 1, 16)}
            label={`${block.title || "table"} (one row per line, cells separated by |)`}
            edited={isEdited("rows")}
            onSave={(text) =>
              edit(
                key("rows"),
                text
                  .split("\n")
                  .filter((line) => line.trim())
                  .map((line) => line.split("|").map((c) => c.trim())),
              )
            }
            onRevert={() => revert(key("rows"))}
          >
            <TableView block={block} />
          </EditableText>
        );
      case "diagram":
        return block.diagram ? (
          <LandscapeDiagram model={block.diagram} />
        ) : null;
      case "image":
        return block.asset_id ? (
          <figure>
            {/* eslint-disable-next-line @next/next/no-img-element -- served by the API, not static */}
            <img
              src={reportApi.assetUrl(engagementId, block.asset_id)}
              alt={block.title}
              className="max-h-[520px] rounded-lg border border-line"
            />
            {block.text && (
              <figcaption className="mt-1 font-sans text-[12px] text-muted">
                {block.text}
              </figcaption>
            )}
          </figure>
        ) : null;
      default:
        return null;
    }
  })();

  return (
    <div className={block.include ? "" : "opacity-45"}>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        {block.title ? (
          <h4 className="font-sans text-[14px] font-semibold text-ink-2">
            {block.title}
          </h4>
        ) : (
          <span />
        )}
        <IncludeToggle
          included={block.include}
          label={block.title || block.id}
          onChange={(v) => void edit(key("include"), v)}
        />
      </div>
      {body}
    </div>
  );
}

function SectionView({
  section,
  prefix,
  withPanel,
  sourceLine,
  edit,
  revert,
  edited,
  engagementId,
}: {
  section: ReportSection;
  prefix: "supporting" | "appendix";
  withPanel: boolean;
  sourceLine: string;
  edit: Edit;
  revert: Revert;
  edited: Set<string>;
  engagementId: string;
}) {
  const key = (field: string) => `${prefix}.${section.id}.${field}`;
  return (
    <Slide
      id={`${prefix}-${section.id}`}
      title={section.title}
      aside={
        <IncludeToggle
          included={section.include}
          label={section.title}
          onChange={(v) => void edit(key("include"), v)}
        />
      }
    >
      <div
        className={`grid gap-6 ${withPanel ? "lg:grid-cols-[280px_minmax(0,1fr)]" : ""} ${section.include ? "" : "opacity-45"}`}
      >
        {withPanel && (
          <div className="rounded-xl bg-kpmg-blue p-4 text-paper-on-ink">
            <EditableText
              value={section.panel}
              label={`${section.title} summary`}
              rows={7}
              edited={edited.has(key("panel"))}
              onSave={(v) => edit(key("panel"), v)}
              onRevert={() => revert(key("panel"))}
            >
              <p className="font-sans text-[13.5px] leading-[1.6]">
                {section.panel}
              </p>
            </EditableText>
          </div>
        )}
        <div className="space-y-6">
          {section.blocks.map((block) => (
            <BlockView
              key={block.id}
              block={block}
              prefix={`${prefix}.${section.id}`}
              edit={edit}
              revert={revert}
              edited={edited}
              engagementId={engagementId}
            />
          ))}
          <p className="font-sans text-[11.5px] text-muted-2 italic">
            {sourceLine}
          </p>
        </div>
      </div>
    </Slide>
  );
}

function RiskPicker({
  value,
  label,
  onChange,
  edited,
  onRevert,
}: {
  value: RiskLevel;
  label: string;
  onChange: (v: RiskLevel) => void;
  edited: boolean;
  onRevert: () => void;
}) {
  return (
    <label className="flex items-center gap-2 font-sans text-[12px] text-muted">
      <span
        aria-hidden
        className={`h-3.5 w-3.5 rounded-full ${RISK_CLASSES[value]}`}
      />
      <select
        aria-label={`Risk level for ${label}`}
        value={value}
        onChange={(e) => onChange(e.target.value as RiskLevel)}
        className="rounded-md border border-line-strong bg-paper-2 px-2 py-1 font-sans text-[12.5px] text-text"
      >
        {RISK_LEVELS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      {edited && (
        <button
          type="button"
          onClick={onRevert}
          className="text-[11.5px] text-steel hover:underline"
        >
          Revert
        </button>
      )}
    </label>
  );
}

function FindingView({
  areaId,
  finding,
  edit,
  revert,
  edited,
}: {
  areaId: string;
  finding: ExecutiveFinding;
  edit: Edit;
  revert: Revert;
  edited: Set<string>;
}) {
  const key = (field: string) => `exec.${areaId}.${finding.key}.${field}`;
  const props = (field: string) => ({
    edited: edited.has(key(field)),
    onRevert: () => revert(key(field)),
  });
  return (
    <li
      className={`grid gap-5 border-t border-line pt-4 first:border-t-0 first:pt-0 lg:grid-cols-[minmax(0,1.7fr)_120px_minmax(0,1fr)_140px] ${finding.include ? "" : "opacity-45"}`}
    >
      <div>
        <EditableText
          value={finding.headline}
          rows={1}
          label="finding headline"
          onSave={(v) => edit(key("headline"), v)}
          {...props("headline")}
        >
          <h4 className="font-sans text-[14.5px] font-semibold text-text">
            {finding.headline}
          </h4>
        </EditableText>
        <div className="mt-1.5">
          <EditableList
            items={finding.bullets}
            label="finding evidence"
            onSave={(v) => edit(key("bullets"), v)}
            {...props("bullets")}
          >
            <Bullets items={finding.bullets} />
          </EditableList>
        </div>
        <div className="mt-2">
          <EditableText
            value={finding.implication}
            label="implication"
            rows={2}
            onSave={(v) => edit(key("implication"), v)}
            {...props("implication")}
          >
            <p className="font-sans text-[13px] leading-[1.55] text-text italic">
              <span className="font-semibold">Implication: </span>
              {finding.implication || "—"}
            </p>
          </EditableText>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {finding.impact.map((lens) => (
            <span
              key={lens}
              className="rounded-full bg-steel-tint px-2 py-0.5 font-sans text-[10.5px] text-steel"
            >
              {IMPACT_LABELS[lens] ?? lens}
            </span>
          ))}
          {finding.source && (
            <span className="font-mono text-[10.5px] text-muted-2">
              {finding.source}
            </span>
          )}
          <IncludeToggle
            included={finding.include}
            label={finding.headline}
            onChange={(v) => void edit(key("include"), v)}
          />
        </div>
      </div>
      <div>
        <p className="mb-1 font-mono text-[10px] tracking-wide text-muted uppercase">
          Risk
        </p>
        <RiskPicker
          value={finding.risk}
          label={finding.headline}
          onChange={(v) => void edit(key("risk"), v)}
          {...props("risk")}
        />
      </div>
      <div>
        <p className="mb-1 font-mono text-[10px] tracking-wide text-muted uppercase">
          Recommended actions
        </p>
        <EditableList
          items={finding.actions}
          label="recommended actions"
          onSave={(v) => edit(key("actions"), v)}
          {...props("actions")}
        >
          {finding.actions.length ? (
            <Bullets items={finding.actions} />
          ) : (
            <p className="font-sans text-[13px] text-muted-2">—</p>
          )}
        </EditableList>
      </div>
      <div>
        <p className="mb-1 flex items-center font-mono text-[10px] tracking-wide text-muted uppercase">
          Investment impact
          <InfoTip label="investment impact" title="Why investment is XXX">
            <InvestmentExplain />
          </InfoTip>
        </p>
        <EditableText
          value={finding.investment}
          rows={1}
          label="investment impact"
          onSave={(v) => edit(key("investment"), v)}
          {...props("investment")}
        >
          <span
            className={
              finding.investment === "XXX"
                ? "font-mono text-[13px] text-muted-2"
                : "font-sans text-[13.5px] text-text"
            }
          >
            {finding.investment}
          </span>
        </EditableText>
      </div>
    </li>
  );
}

/** A diligence area with one row per finding, each with its own risk (Phase 8). */
function ExecutiveRowView({
  row,
  edit,
  revert,
  edited,
}: {
  row: ExecutiveRow;
  edit: Edit;
  revert: Revert;
  edited: Set<string>;
}) {
  const key = (field: string) => `exec.${row.area_id}.${field}`;
  return (
    <li className={`card p-5 ${row.include ? "" : "bg-paper-2 opacity-60"}`}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[12px] text-muted-2">
            {String(row.sn).padStart(2, "0")}
          </span>
          <EditableText
            value={row.title}
            rows={1}
            label="area title"
            onSave={(v) => edit(key("title"), v)}
            edited={edited.has(key("title"))}
            onRevert={() => revert(key("title"))}
          >
            <h3 className="inline font-sans text-[16px] font-semibold text-text">
              {row.title}
            </h3>
          </EditableText>
          <span className="inline-flex items-center gap-1.5 font-sans text-[11px] text-muted">
            <span
              aria-label={`Area risk ${row.risk}`}
              className={`h-2.5 w-7 rounded-sm ${RISK_CLASSES[row.risk]}`}
            />
            {row.risk}
            <InfoTip label="the area risk" title="How risk is set">
              <ReportRiskExplain />
            </InfoTip>
          </span>
        </div>
        <IncludeToggle
          included={row.include}
          label={row.title}
          onChange={(v) => void edit(key("include"), v)}
        />
      </div>
      {row.findings.length > 0 ? (
        <ul className="space-y-4">
          {row.findings.map((finding) => (
            <FindingView
              key={finding.key}
              areaId={row.area_id}
              finding={finding}
              edit={edit}
              revert={revert}
              edited={edited}
            />
          ))}
        </ul>
      ) : null}
      {row.note && (
        <p className="mt-3 font-sans text-[13px] text-muted italic">
          {row.note}
        </p>
      )}
    </li>
  );
}

function DiagramUploads({
  engagementId,
  onChanged,
}: {
  engagementId: string;
  onChanged: () => Promise<void>;
}) {
  const { show } = useToast();
  const [title, setTitle] = useState("");
  const [caption, setCaption] = useState("");
  const file = useRef<HTMLInputElement | null>(null);
  const assets = useQuery({
    queryKey: ["report-assets", engagementId],
    queryFn: () => reportApi.listAssets(engagementId),
  });
  const upload = useMutation({
    mutationFn: (f: File) =>
      reportApi.uploadAsset(engagementId, f, title || f.name, caption),
    onSuccess: async () => {
      setTitle("");
      setCaption("");
      await assets.refetch();
      await onChanged();
      show("Diagram added to the appendix");
    },
    onError: (err: unknown) =>
      show(err instanceof ApiError ? err.message : "Upload failed", "error"),
  });
  return (
    <div className="rounded-xl border border-dashed border-line-strong bg-paper-2 p-5">
      <h3 className="mb-1 font-sans text-[14px] font-semibold text-text">
        Target-supplied diagrams
      </h3>
      <p className="mb-3 max-w-[80ch] font-sans text-[12.5px] text-muted">
        Network and infrastructure diagrams are not generated — the platform
        holds no topology. Upload the target&apos;s own and they are placed in
        the appendix as provided.
      </p>
      <div className="flex flex-wrap items-end gap-2">
        <TextInput
          aria-label="Diagram title"
          placeholder="Title, e.g. Network diagram (1/2)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="max-w-[280px] py-2 text-[13px]"
        />
        <TextInput
          aria-label="Caption"
          placeholder="Caption (optional)"
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          className="max-w-[280px] py-2 text-[13px]"
        />
        <input
          ref={file}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) upload.mutate(f);
            e.target.value = "";
          }}
        />
        <button
          type="button"
          onClick={() => file.current?.click()}
          disabled={upload.isPending}
          className="rounded-full bg-ink px-4 py-2 font-sans text-[12.5px] font-medium text-paper-on-ink disabled:opacity-50"
        >
          {upload.isPending ? "Uploading…" : "Upload image"}
        </button>
      </div>
      {(assets.data ?? []).length > 0 && (
        <ul className="mt-3 space-y-1">
          {(assets.data ?? []).map((a) => (
            <li
              key={a.id}
              className="flex items-center gap-3 font-sans text-[12.5px] text-text"
            >
              {a.title}
              <button
                type="button"
                onClick={async () => {
                  await reportApi.deleteAsset(engagementId, a.id);
                  await assets.refetch();
                  await onChanged();
                }}
                className="text-[11.5px] text-redline hover:underline"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReportBody({
  report,
  engagementId,
  edit,
  revert,
  regenerate,
}: {
  report: ReportRead;
  engagementId: string;
  edit: Edit;
  revert: Revert;
  regenerate: () => Promise<void>;
}) {
  const p: ReportPayload = report.payload;
  const edited = new Set(p.edited_keys);
  const ed = (key: string) => ({
    edited: edited.has(key),
    onRevert: () => revert(key),
  });
  const included = p.executive.filter((r) => r.include);
  const left = p.executive.filter((r) => !r.include);

  return (
    <div className="space-y-8">
      <section
        id="cover"
        className="scroll-mt-24 overflow-hidden rounded-2xl bg-ink-2 px-10 py-12 text-paper-on-ink"
      >
        <div className="max-w-[60ch] space-y-5">
          <EditableText
            value={p.cover.codename}
            rows={1}
            label="codename"
            onSave={(v) => edit("cover.codename", v)}
            {...ed("cover.codename")}
          >
            <h1 className="font-display text-[46px] leading-tight">
              {p.cover.codename}
            </h1>
          </EditableText>
          <EditableText
            value={p.cover.title}
            rows={1}
            label="cover title"
            onSave={(v) => edit("cover.title", v)}
            {...ed("cover.title")}
          >
            <p className="font-sans text-[28px]">{p.cover.title}</p>
          </EditableText>
          <EditableText
            value={p.cover.subtitle}
            rows={1}
            label="cover subtitle"
            onSave={(v) => edit("cover.subtitle", v)}
            {...ed("cover.subtitle")}
          >
            <p className="font-sans text-[16px] font-semibold">
              {p.cover.subtitle}
            </p>
          </EditableText>
          <EditableText
            value={p.cover.date_label}
            rows={1}
            label="cover date"
            onSave={(v) => edit("cover.date_label", v)}
            {...ed("cover.date_label")}
          >
            <p className="font-sans text-[16px] font-semibold">
              {p.cover.date_label}
            </p>
          </EditableText>
        </div>
      </section>

      <Slide id="context" number="01" title="Setting the context">
        <div className="space-y-4">
          {(["objective", "approach", "outcome"] as const).map((field, i) => (
            <div
              key={field}
              className="grid items-start gap-4 sm:grid-cols-[150px_minmax(0,1fr)]"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-ink-2 font-sans text-[15px] font-bold text-paper-on-ink">
                  0{i + 1}
                </span>
                <span className="font-sans text-[12.5px] font-bold tracking-wide text-ink-2 uppercase">
                  {field}
                </span>
              </div>
              <div className="rounded-lg border border-dashed border-line-strong px-4 py-3">
                <EditableText
                  value={p.context[field]}
                  label={field}
                  onSave={(v) => edit(`context.${field}`, v)}
                  {...ed(`context.${field}`)}
                >
                  <p className="font-sans text-[14px] leading-[1.6] text-text">
                    {p.context[field]}
                  </p>
                </EditableText>
              </div>
            </div>
          ))}
          <div className="grid gap-3 sm:grid-cols-[150px_minmax(0,1fr)]">
            <div className="flex items-center justify-center rounded-lg bg-ink-2 p-3 text-center font-sans text-[13px] font-bold text-paper-on-ink">
              Key assessment areas
            </div>
            <EditableList
              items={p.context.key_areas}
              label="key assessment areas"
              onSave={(v) => edit("context.key_areas", v)}
              {...ed("context.key_areas")}
            >
              <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                {p.context.key_areas.map((a) => (
                  <div
                    key={a}
                    className="rounded-md border border-line bg-paper-2 px-3 py-2.5 text-center font-sans text-[12.5px] text-text"
                  >
                    {a}
                  </div>
                ))}
              </div>
            </EditableList>
          </div>
          <EditableText
            value={p.context.cutoff}
            rows={2}
            label="information cut-off"
            onSave={(v) => edit("context.cutoff", v)}
            {...ed("context.cutoff")}
          >
            <p className="font-sans text-[12.5px] text-muted">
              * {p.context.cutoff}
            </p>
          </EditableText>
        </div>
      </Slide>

      <Slide id="glossary" number="02" title="Glossary of terms">
        <EditableText
          value={p.glossary.map((g) => `${g.term}: ${g.expansion}`).join("\n")}
          rows={Math.min(p.glossary.length + 1, 18)}
          label="glossary (one term per line, TERM: expansion)"
          edited={edited.has("glossary")}
          onRevert={() => revert("glossary")}
          onSave={(text) =>
            edit(
              "glossary",
              text
                .split("\n")
                .filter((l) => l.includes(":"))
                .map((l) => {
                  const [term, ...rest] = l.split(":");
                  return {
                    term: term.trim(),
                    expansion: rest.join(":").trim(),
                  };
                }),
            )
          }
        >
          <dl className="grid gap-x-10 gap-y-1 sm:grid-cols-2">
            {p.glossary.map((g) => (
              <div
                key={g.term}
                className="grid grid-cols-[80px_minmax(0,1fr)] font-sans text-[13px]"
              >
                <dt className="font-semibold text-ink-2">{g.term}</dt>
                <dd className="text-text">{g.expansion}</dd>
              </div>
            ))}
          </dl>
        </EditableText>
      </Slide>

      <Slide id="in_scope" number="03" title="In-scope areas">
        <ul className="divide-y divide-line">
          {p.in_scope.map((a) => (
            <li
              key={a.area_id}
              className={`grid gap-4 py-4 sm:grid-cols-[240px_minmax(0,1fr)] ${a.include ? "" : "opacity-45"}`}
            >
              <div>
                <EditableText
                  value={a.title}
                  rows={1}
                  label="focus area"
                  onSave={(v) => edit(`in_scope.${a.area_id}.title`, v)}
                  {...ed(`in_scope.${a.area_id}.title`)}
                >
                  <p className="inline font-sans text-[14px] font-semibold text-text">
                    {a.title}
                  </p>
                </EditableText>
                <div className="mt-1">
                  <IncludeToggle
                    included={a.include}
                    label={a.title}
                    onChange={(v) =>
                      void edit(`in_scope.${a.area_id}.include`, v)
                    }
                  />
                </div>
              </div>
              <EditableList
                items={a.considerations}
                label="key considerations"
                onSave={(v) => edit(`in_scope.${a.area_id}.considerations`, v)}
                {...ed(`in_scope.${a.area_id}.considerations`)}
              >
                <Bullets items={a.considerations} />
              </EditableList>
            </li>
          ))}
        </ul>
      </Slide>

      <Slide id="limitations" number="04" title="Data limitations">
        {p.limitations.length === 0 ? (
          <p className="font-sans text-[13.5px] text-muted">
            No limitations recorded.
          </p>
        ) : (
          <ul className="divide-y divide-line">
            {p.limitations.map((lim) => (
              <li
                key={lim.area_id}
                className={`grid gap-4 py-4 sm:grid-cols-[240px_minmax(0,1fr)] ${lim.include ? "" : "opacity-45"}`}
              >
                <div>
                  <p className="font-sans text-[14px] font-semibold text-text">
                    {lim.title}
                  </p>
                  <IncludeToggle
                    included={lim.include}
                    label={lim.title}
                    onChange={(v) =>
                      void edit(`limitations.${lim.area_id}.include`, v)
                    }
                  />
                </div>
                <EditableList
                  items={lim.items}
                  label="data limitations"
                  onSave={(v) => edit(`limitations.${lim.area_id}.items`, v)}
                  {...ed(`limitations.${lim.area_id}.items`)}
                >
                  <Bullets items={lim.items} />
                </EditableList>
              </li>
            ))}
          </ul>
        )}
      </Slide>

      <Slide
        id="executive"
        number="05"
        title={p.executive_title}
        aside={
          <span className="flex items-center gap-3 font-sans text-[11.5px] text-muted">
            {(["Low", "Medium", "High"] as RiskLevel[]).map((r) => (
              <span key={r} className="flex items-center gap-1.5">
                <span className={`h-2 w-6 rounded-sm ${RISK_CLASSES[r]}`} />
                {r}
              </span>
            ))}
          </span>
        }
      >
        <ol className="space-y-4">
          {included.map((row) => (
            <ExecutiveRowView
              key={row.area_id}
              row={row}
              edit={edit}
              revert={revert}
              edited={edited}
            />
          ))}
        </ol>
        {left.length > 0 && (
          <details className="mt-6">
            <summary className="cursor-pointer font-sans text-[13px] font-medium text-steel">
              {left.length} area{left.length === 1 ? "" : "s"} left out of the
              export — no findings, or not assessed
            </summary>
            <ol className="mt-3 space-y-3">
              {left.map((row) => (
                <ExecutiveRowView
                  key={row.area_id}
                  row={row}
                  edit={edit}
                  revert={revert}
                  edited={edited}
                />
              ))}
            </ol>
          </details>
        )}
        <p className="mt-5 font-sans text-[11.5px] text-muted-2 italic">
          *The investment estimate is for the engagement team to complete; XXX
          exports as XXX.
        </p>
      </Slide>

      <div id="supporting" className="scroll-mt-24 space-y-8">
        <h2 className="font-display text-[22px] text-ink">
          06 · Supporting analysis
        </h2>
        {p.supporting.map((s) => (
          <SectionView
            key={s.id}
            section={s}
            prefix="supporting"
            withPanel
            sourceLine={p.source_line}
            edit={edit}
            revert={revert}
            edited={edited}
            engagementId={engagementId}
          />
        ))}
      </div>

      <div id="appendix" className="scroll-mt-24 space-y-8">
        <h2 className="font-display text-[22px] text-ink">07 · Appendix</h2>
        <DiagramUploads engagementId={engagementId} onChanged={regenerate} />
        {p.appendix.map((s) => (
          <SectionView
            key={s.id}
            section={s}
            prefix="appendix"
            withPanel={false}
            sourceLine={p.source_line}
            edit={edit}
            revert={revert}
            edited={edited}
            engagementId={engagementId}
          />
        ))}
      </div>
    </div>
  );
}

export function ReportPage({ engagementId }: { engagementId: string }) {
  const queryClient = useQueryClient();
  const { show } = useToast();
  const key = ["report", engagementId];

  const { data, isLoading, isError, error } = useQuery({
    queryKey: key,
    queryFn: () => reportApi.get(engagementId),
    retry: false,
  });

  const generate = useMutation({
    mutationFn: () => reportApi.generate(engagementId),
    onSuccess: (fresh) => {
      queryClient.setQueryData(key, fresh);
      show(
        `Report generated — version ${fresh.version}${fresh.payload.edited_keys.length ? `, ${fresh.payload.edited_keys.length} edit${fresh.payload.edited_keys.length === 1 ? "" : "s"} kept` : ""}`,
      );
    },
    onError: (err: unknown) =>
      show(
        err instanceof ApiError ? err.message : "Could not generate the report",
        "error",
      ),
  });

  const edit: Edit = async (k, value) => {
    try {
      queryClient.setQueryData(
        key,
        await reportApi.edit(engagementId, k, value),
      );
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : "Could not save that edit",
        "error",
      );
      throw err;
    }
  };
  const revert: Revert = async (k) => {
    queryClient.setQueryData(key, await reportApi.revert(engagementId, k));
    show("Reverted to the generated text");
  };

  if (isLoading) {
    return (
      <main className="mx-auto w-full max-w-[1600px] px-7 pt-12 pb-24">
        <Skeleton className="mb-6 h-10 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </main>
    );
  }

  const notYet =
    isError && error instanceof ApiError && error.code === "no_report";
  if (
    notYet ||
    (isError && error instanceof ApiError && error.code === "not_scoped")
  ) {
    return (
      <main className="mx-auto w-full max-w-[760px] px-7 py-20">
        <EmptyState
          title="No report yet"
          description="The report is built from everything recorded so far — scope, request list, inventories, assessments and IT budget. Generate it now and regenerate as evidence arrives; your edits are kept."
          action={
            <div className="flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={() => generate.mutate()}
                disabled={generate.isPending}
                className="rounded-full border border-ink bg-ink px-5 py-3 font-sans text-[13px] font-medium text-paper-on-ink disabled:opacity-50"
              >
                {generate.isPending ? "Generating…" : "Generate report"}
              </button>
              <Link
                href={`/engagements/${engagementId}/scope`}
                className="rounded-full border border-line-strong px-5 py-3 font-sans text-[13px] text-text"
              >
                Scope of work
              </Link>
            </div>
          }
        />
      </main>
    );
  }
  if (isError || !data) {
    return (
      <main className="mx-auto w-full max-w-[720px] px-7 py-20">
        <ErrorState
          title="Couldn't load the report"
          description={error instanceof Error ? error.message : undefined}
        />
      </main>
    );
  }

  const p = data.payload;
  return (
    <main className="mx-auto w-full max-w-[1600px] px-7 pb-24">
      <div className="sticky top-0 z-20 -mx-7 mb-8 flex flex-wrap items-center justify-between gap-3 border-b border-line bg-paper/95 px-7 py-4 backdrop-blur">
        <div>
          <p className="font-mono text-[11px] tracking-wide text-muted uppercase">
            Final report · IT due diligence
          </p>
          <p className="font-sans text-[13px] text-text">
            {p.target_name || "Target"} · version {data.version} ·{" "}
            {p.generator === "llm"
              ? "narrative written by the model"
              : "deterministic"}{" "}
            · {p.edited_keys.length} edit
            {p.edited_keys.length === 1 ? "" : "s"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            title="Rebuild from the latest scope, request list, inventories, assessments and budget. Your edits are kept."
            className="rounded-full border border-line-strong px-4 py-2 font-sans text-[13px] font-medium hover:bg-paper-2 disabled:opacity-50"
          >
            {generate.isPending ? "Regenerating…" : "Regenerate"}
          </button>
          <a
            href={reportApi.exportUrl(engagementId)}
            download
            className="rounded-full bg-kpmg-blue px-4 py-2 font-sans text-[13px] font-medium text-paper-on-ink hover:bg-kpmg-blue-dark"
          >
            Export PowerPoint
          </a>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[200px_minmax(0,1fr)]">
        <nav aria-label="Report sections" className="hidden lg:block">
          <ul className="sticky top-28 space-y-1">
            {NAV.map((n) => (
              <li key={n.id}>
                <a
                  href={`#${n.id}`}
                  className="block rounded-lg px-3 py-1.5 font-sans text-[13px] text-muted hover:bg-paper-2 hover:text-text"
                >
                  {n.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <ReportBody
          report={data}
          engagementId={engagementId}
          edit={edit}
          revert={revert}
          regenerate={async () => {
            await generate.mutateAsync();
          }}
        />
      </div>
    </main>
  );
}
