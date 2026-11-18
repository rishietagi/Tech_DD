"""Gathers every earlier module's output, builds the report, stores it, applies edits.

The report needs a scope (it is organised by the scope's areas). Everything else is
optional: a report generated on day one says what was not received, and gets better as the
IRL, the inventories and the assessments fill in.
"""

import logging
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.estate import InventoryItem
from app.models.irl import IrlDocumentStatus, IrlResponse
from app.models.report import Report, ReportAsset, ReportEdit
from app.schemas.assess import BAND_LABELS
from app.schemas.report import ReportConfig, ReportPayload, ReportRead
from app.services.assess.service import list_processes
from app.services.engagements import assemble_intake_full, get_engagement
from app.services.estate import budget as budget_service
from app.services.estate import service as estate_service
from app.services.estate.inventory import items_of, process_refs
from app.services.intelligence.mode import use_llm
from app.services.irl import service as irl_service
from app.services.report import edits as edit_rules
from app.services.report.builder import build
from app.services.report.inputs import IrlRequest, Item, ProcessResult, ReportInputs
from app.services.report.llm import ReportWriter, skill_versions
from app.services.report.sections import BUILDERS
from app.services.research.service import find_latest_research
from app.services.scope import service as scope_service

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parents[2] / "reference" / "report" / "report.yaml"
ALLOWED_MIME = {"image/png", "image/jpeg", "image/gif", "image/webp"}
MAX_ASSET_BYTES = 8 * 1024 * 1024


@lru_cache(maxsize=1)
def get_report_config() -> ReportConfig:
    with CONFIG_FILE.open(encoding="utf-8") as handle:
        config = ReportConfig.model_validate(yaml.safe_load(handle))
    unknown = {s for ids in config.supporting.values() for s in ids} - set(BUILDERS)
    if unknown:
        raise RuntimeError(f"report.yaml names supporting sections with no builder: {sorted(unknown)}")
    missing_titles = {s for ids in config.supporting.values() for s in ids} - set(config.sections)
    if missing_titles:
        raise RuntimeError(f"report.yaml: sections without a title: {sorted(missing_titles)}")
    for category, rule in config.routing.items():
        if category not in config.implications or category not in config.actions:
            raise RuntimeError(f"report.yaml: {category!r} needs an implication and an action")
        if not rule.fallback:
            raise RuntimeError(f"report.yaml: {category!r} needs a fallback area")
    return config


# ------------------------------------------------------------------ inputs


def _cutoff(db: Session, engagement_id: str, irl_id: str | None) -> datetime | None:
    stamps = [db.scalar(select(func.max(InventoryItem.updated_at)).where(InventoryItem.engagement_id == engagement_id))]
    if irl_id:
        stamps.append(db.scalar(select(func.max(IrlResponse.updated_at)).where(IrlResponse.irl_id == irl_id)))
        stamps.append(
            db.scalar(select(func.max(IrlDocumentStatus.updated_at)).where(IrlDocumentStatus.irl_id == irl_id))
        )
    known = [s for s in stamps if s is not None]
    return max(known) if known else None


def gather(db: Session, engagement_id: str) -> ReportInputs:
    engagement = get_engagement(db, engagement_id)
    intake = assemble_intake_full(engagement)
    try:
        scope = scope_service.get_latest_scope(db, engagement_id)
    except AppError as exc:
        raise AppError(
            code="not_scoped",
            message="The report is organised by the scope of work's areas — generate a scope first.",
            status_code=409,
        ) from exc
    scope_payload = scope.payload_json
    if scope_payload.get("schema_version") != 2:
        raise AppError(code="unsupported_scope_version", message="Regenerate the scope of work first.", status_code=409)
    classification = scope_payload.get("classification") or {}

    irl = irl_service._latest_irl(db, engagement_id)
    requests: list[IrlRequest] = []
    if irl is not None:
        tracking = irl_service.tracking_for(db, engagement_id, irl)
        for q in irl.payload_json.get("questions", []):
            t = tracking.get(q["id"])
            requests.append(
                IrlRequest(
                    id=q["id"],
                    question=q["question"],
                    scope_area=q.get("scope_area") or "",
                    source_row_id=q.get("source_row_id"),
                    kind=q.get("kind", "document"),
                    status=t.status if t else "not_received",
                    follow_ups=list(getattr(t, "follow_up_questions", None) or []) if t else [],
                )
            )

    research = find_latest_research(db, engagement_id)
    brief = (research.payload_json.get("business_brief") or {}) if research else {}

    def score_payload(domain: str) -> dict[str, Any] | None:
        row = estate_service.find_latest(db, engagement_id, domain)  # type: ignore[arg-type]
        return estate_service.to_read(db, row).payload if row is not None else None

    processes = [
        ProcessResult(
            key=p.key,
            name=p.name,
            short_name=p.short_name,
            index=p.index or 0.0,
            band=p.band or "manual",
            band_label=BAND_LABELS.get(p.band or "manual", ""),
        )
        for p in list_processes(db, engagement_id).processes
        if p.defined and p.has_score and p.index is not None
    ]
    budget = budget_service.get_budget(db, engagement_id)
    inventory: dict[str, list[Item]] = {}
    for item in items_of(db, engagement_id):
        inventory.setdefault(item.kind, []).append(Item(ref=item.ref, fields=dict(item.fields or {})))
    assets = [
        {"id": a.id, "title": a.title, "caption": a.caption}
        for a in db.scalars(
            select(ReportAsset).where(ReportAsset.engagement_id == engagement_id).order_by(ReportAsset.created_at)
        )
    ]
    cutoff = _cutoff(db, engagement_id, irl.id if irl else None)

    return ReportInputs(
        deal_name=engagement.deal_name,
        target_name=intake.target.company_name or "",
        investor_name=intake.context.investor_firm_name or "",
        dd_type=str(classification.get("dd_type") or "enterprise"),
        dd_mix=classification.get("dd_mix"),
        access_level=intake.objectives.access_level or "",
        today=datetime.now(UTC).date(),
        cutoff=cutoff.date() if cutoff else None,
        scope_rows=scope_payload.get("rows", []),
        irl=requests,
        research_summary=(research.payload_json.get("summary", "") if research else ""),
        research_what_they_do=((brief.get("what_they_do") or {}).get("text", "") if brief else ""),
        applications_score=score_payload("applications"),
        data_tech_score=score_payload("data_tech"),
        processes=processes,
        budget=budget.model_dump(mode="json"),
        budget_saved=budget.saved,
        inventory=inventory,
        process_names={p.key: p.name for p in process_refs()},
        assets=assets,
    )


# ------------------------------------------------------------------ generate and read


def generate(
    db: Session, engagement_id: str, generator: str | None = None, writer: ReportWriter | None = None
) -> Report:
    inputs = gather(db, engagement_id)
    payload = build(inputs, get_report_config())

    used: list[str] = []
    writer = writer or ReportWriter()
    if use_llm("report-executive-summary", generator) and writer.executive(payload):
        used.append("report-executive-summary")
    if use_llm("report-narrative", generator) and writer.narrative(payload):
        used.append("report-narrative")
    if use_llm("budget-commentary", generator) and writer.budget(payload):
        used.append("budget-commentary")
    payload.generator = "llm" if used else "rules"
    payload.skill_versions = skill_versions(used)

    last = db.scalar(select(func.max(Report.version)).where(Report.engagement_id == engagement_id)) or 0
    row = Report(
        engagement_id=engagement_id,
        version=last + 1,
        generator=payload.generator,
        payload_json=payload.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def latest(db: Session, engagement_id: str) -> Report:
    get_engagement(db, engagement_id)
    row = db.scalar(
        select(Report).where(Report.engagement_id == engagement_id).order_by(Report.version.desc()).limit(1)
    )
    if row is None:
        raise AppError(code="no_report", message="No report has been generated yet.", status_code=404)
    return row


def _edits(db: Session, engagement_id: str) -> dict[str, Any]:
    return {
        e.key: e.value_json for e in db.scalars(select(ReportEdit).where(ReportEdit.engagement_id == engagement_id))
    }


def with_edits(db: Session, row: Report) -> ReportPayload:
    data = dict(row.payload_json)
    import copy

    data = copy.deepcopy(data)
    applied = edit_rules.apply(data, _edits(db, row.engagement_id))
    data["edited_keys"] = applied
    return ReportPayload.model_validate(data)


def to_read(db: Session, row: Report) -> ReportRead:
    return ReportRead(
        id=row.id,
        engagement_id=row.engagement_id,
        version=row.version,
        generator=row.generator,
        payload=with_edits(db, row),
        created_at=row.created_at,
    )


def save_edit(db: Session, engagement_id: str, key: str, value: Any) -> ReportRead:
    row = latest(db, engagement_id)
    clean = edit_rules.validate(row.payload_json, key, value)
    existing = db.scalar(select(ReportEdit).where(ReportEdit.engagement_id == engagement_id, ReportEdit.key == key))
    if existing is None:
        db.add(ReportEdit(engagement_id=engagement_id, key=key, value_json=clean))
    else:
        existing.value_json = clean
    db.commit()
    return to_read(db, row)


def revert_edit(db: Session, engagement_id: str, key: str) -> ReportRead:
    row = latest(db, engagement_id)
    existing = db.scalar(select(ReportEdit).where(ReportEdit.engagement_id == engagement_id, ReportEdit.key == key))
    if existing is not None:
        db.delete(existing)
        db.commit()
    return to_read(db, row)


# ------------------------------------------------------------------ assets


def add_asset(db: Session, engagement_id: str, title: str, caption: str, mime: str, data: bytes) -> ReportAsset:
    get_engagement(db, engagement_id)
    if mime not in ALLOWED_MIME:
        raise AppError(code="unsupported_file", message="Upload a PNG, JPEG, GIF or WebP image.", status_code=415)
    if not data or len(data) > MAX_ASSET_BYTES:
        raise AppError(code="file_too_large", message="Images must be between 1 byte and 8 MB.", status_code=413)
    asset = ReportAsset(
        engagement_id=engagement_id, title=title.strip() or "Diagram", caption=caption.strip(), mime=mime, data=data
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def list_assets(db: Session, engagement_id: str) -> list[ReportAsset]:
    get_engagement(db, engagement_id)
    return list(
        db.scalars(
            select(ReportAsset).where(ReportAsset.engagement_id == engagement_id).order_by(ReportAsset.created_at)
        )
    )


def get_asset(db: Session, engagement_id: str, asset_id: str) -> ReportAsset:
    asset = db.get(ReportAsset, asset_id)
    if asset is None or asset.engagement_id != engagement_id:
        raise AppError(code="not_found", message="Diagram not found.", status_code=404)
    return asset


def delete_asset(db: Session, engagement_id: str, asset_id: str) -> None:
    db.delete(get_asset(db, engagement_id, asset_id))
    db.commit()
