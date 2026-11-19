"""Business-process findings: up to three themes per process, from its step scores.

Rishi, 2026-11-19: the business-process tab reports findings "in the same format as the
other assess tabs". The rules are process-agnostic, like the scoring:

1. **process_manual** — the process sits in a Manual or Emerging band. Evidence names the
   weakest heavy steps; severity comes from the band.
2. **process_broken_cycle** — one end of the cycle is a full ladder point or more ahead of
   the other. The implication is the questionnaire's own `shape` reading, because what a
   front-loaded P2P means is not what a front-loaded O2C means.
3. **process_weak_step** — a process that is otherwise system-supported (not in a manual
   band) still has steps at 2/5 or below. Medium when one carries 15% of the weight.

Computed from a stored score payload on read, so it needs no re-score and reads the
refined step scores where the model moved one.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.schemas.assess import AssessmentScorePayload, ProcessQuestionnaire, StepScore
from app.schemas.estate import Gap, GapObservation, Severity, ThemeDef
from app.schemas.process_findings import PROCESS_THEME_IDS, ProcessFindingsConfig
from app.services.estate.gaps import order

FINDINGS_FILE = Path(__file__).resolve().parents[2] / "reference" / "processes" / "_findings.yaml"


@lru_cache(maxsize=1)
def get_process_findings_config() -> ProcessFindingsConfig:
    with FINDINGS_FILE.open(encoding="utf-8") as handle:
        data: dict[str, Any] = yaml.safe_load(handle) or {}
    config = ProcessFindingsConfig.model_validate(data)
    ids = [t.id for t in config.themes]
    if sorted(ids) != sorted(PROCESS_THEME_IDS):
        raise RuntimeError(f"_findings.yaml must define exactly the themes {PROCESS_THEME_IDS}, found {ids}")
    return config


def _fmt(template: str, **values: str) -> str:
    return " ".join(template.format(**values).split())


def _step_line(step: StepScore) -> str:
    return f"{step.title} scores {step.score}/5 ({step.level_label}) and carries {step.weight}% of the process."


def _names(steps: list[StepScore]) -> str:
    titles = [s.title for s in steps]
    if len(titles) == 1:
        return titles[0]
    return ", ".join(titles[:-1]) + f" and {titles[-1]}"


def _gap(
    theme: ThemeDef,
    position: int,
    short_name: str,
    *,
    severity: Severity,
    evidence: list[str],
    values: dict[str, str],
    subjects: list[str],
    implication: str | None = None,
) -> Gap:
    return Gap(
        key=f"theme:{theme.id}",
        display_id=f"{short_name}-{position:02d}",
        theme=theme.id,
        area=theme.area,
        headline=_fmt(theme.headline, **values),
        evidence=evidence,
        implication=" ".join((implication or theme.implication).split()),
        impact=list(theme.impact),
        action=_fmt(theme.action, **values),
        severity=severity,
        subjects=subjects,
        observations=[
            GapObservation(text=line, severity=severity, subjects=subjects, source="process:step") for line in evidence
        ],
    )


def process_gaps(
    payload: AssessmentScorePayload,
    questionnaire: ProcessQuestionnaire,
    config: ProcessFindingsConfig | None = None,
) -> list[Gap]:
    """The findings one process score raises, most severe first."""
    config = config or get_process_findings_config()
    rules = config.rules
    themes = {t.id: (i + 1, t) for i, t in enumerate(config.themes)}
    assessed = [s for s in payload.steps if s.assessed and s.score is not None]
    if not assessed:
        return []

    weak = sorted(
        [s for s in assessed if (s.score or 0) <= rules.weak_step_max],
        key=lambda s: (-s.weight, s.score or 0),
    )
    weakest_first = sorted(assessed, key=lambda s: (s.score or 0, -s.weight))
    named = weak[: rules.named_steps] or weakest_first[: rules.named_steps]
    base = {
        "process": payload.process_name,
        "index": f"{payload.index:.0f}",
        "band": payload.band_label,
        # Step titles read as names, so they keep their case mid-sentence.
        "steps": _names(named) if named else "the manual steps",
        "weak_end": "",
    }
    gaps: list[Gap] = []
    short = questionnaire.short_name

    manual_severity = rules.manual_bands.get(payload.band)
    if manual_severity is not None:
        position, theme = themes["process_manual"]
        evidence = [
            f"{payload.process_name} scores {payload.index:.0f}/100 ({payload.band_label}) "
            "on the automation assessment."
        ]
        evidence += [_step_line(s) for s in named[:2]]
        gaps.append(
            _gap(
                theme,
                position,
                short,
                severity=manual_severity,
                evidence=evidence,
                values=base,
                subjects=[payload.process_name],
            )
        )

    # The cycle shape: the same split the shape note uses.
    if len(assessed) >= 4:
        shape = questionnaire.shape
        front_sn = set(shape.front_steps) if shape else {1, 2, 3}
        back_sn = set(shape.back_steps) if shape else {s.sn for s in assessed if s.sn >= 7}
        front = [s for s in assessed if s.sn in front_sn]
        back = [s for s in assessed if s.sn in back_sn]
        if front and back:
            front_mean = sum(s.score or 0 for s in front) / len(front)
            back_mean = sum(s.score or 0 for s in back) / len(back)
            gap_points = front_mean - back_mean
            if abs(gap_points) >= rules.cycle_gap:
                front_label = shape.front_label if shape else "the early steps"
                back_label = shape.back_label if shape else "the later steps"
                weak_end, strong_end = (back_label, front_label) if gap_points > 0 else (front_label, back_label)
                weak_mean, strong_mean = (back_mean, front_mean) if gap_points > 0 else (front_mean, back_mean)
                reading = (shape.front_loaded if gap_points > 0 else shape.back_loaded) if shape else None
                position, theme = themes["process_broken_cycle"]
                gaps.append(
                    _gap(
                        theme,
                        position,
                        short,
                        severity=theme.severity,
                        evidence=[
                            f"Average step score: {strong_mean:.1f}/5 at {strong_end}, "
                            f"{weak_mean:.1f}/5 at {weak_end}.",
                        ],
                        values={**base, "weak_end": weak_end},
                        subjects=[payload.process_name],
                        implication=reading,
                    )
                )

    if manual_severity is None and weak:
        position, theme = themes["process_weak_step"]
        heavy = any(s.weight >= rules.heavy_weight for s in weak)
        gaps.append(
            _gap(
                theme,
                position,
                short,
                severity="Medium" if heavy else theme.severity,
                evidence=[_step_line(s) for s in weak[: rules.named_steps]],
                values=base,
                subjects=[s.title for s in weak],
            )
        )
    return order(gaps)
