"""Loads and validates the process questionnaires from YAML.

Same contract as the KPMG scope library: content lives in YAML so a practitioner can add
a question or retune a weight without touching Python, and a malformed file fails loudly
at load rather than producing a quietly wrong score.

Some of the five processes are declared in the registry with `defined: false` — named in
the product, no questionnaire behind them. They are listed rather than hidden so the
shape of the module is visible; asking for one raises `ProcessNotDefinedError`, which the
API turns into an honest 409 rather than a 404 that would imply the process does not
exist.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from app.core.errors import AppError
from app.schemas.assess import ProcessQuestionnaire

logger = logging.getLogger(__name__)

PROCESS_DIR = Path(__file__).resolve().parents[2] / "reference" / "processes"
REGISTRY_FILE = "_registry.yaml"


class ProcessLibraryError(RuntimeError):
    """Raised when the process library on disk is missing or malformed."""


class ProcessNotDefinedError(AppError):
    """A process that exists in the registry but has no questionnaire yet."""

    def __init__(self, key: str, name: str) -> None:
        super().__init__(
            code="process_not_defined",
            message=(
                f"{name} is not yet defined for assessment. It is named in the product "
                f"because the process exists, but its step decomposition, weights and "
                f"questions have not been written."
            ),
            status_code=409,
        )
        self.key = key


class RegistryEntry(BaseModel):
    model_config = {"extra": "forbid"}

    key: str
    name: str
    short_name: str
    defined: bool
    description: str


class ProcessRegistry(BaseModel):
    model_config = {"extra": "forbid"}

    processes: list[RegistryEntry]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProcessLibraryError(f"process library file not found: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ProcessLibraryError(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ProcessLibraryError(f"{path.name} must contain a YAML mapping at the top level")
    return data


def _assign_nudge_ids(data: dict[str, Any]) -> dict[str, Any]:
    """Give every nudge a stable id derived from its parent question.

    Ids are not written in the YAML because a practitioner adding a follow-up should not
    have to invent one, and a hand-typed id is a chance to create a duplicate. Derived
    positionally: `P2P-07-01` gains `P2P-07-01-N1`, `-N2`. Inserting a nudge in the
    middle therefore renumbers those after it — acceptable because nudge answers are
    keyed by id and a renumber would orphan one, which is why nudges are appended in
    practice. Recorded here so the constraint is known rather than discovered.
    """
    for step in data.get("steps", []):
        for question in step.get("questions", []):
            qid = question.get("id", "")
            for position, nudge in enumerate(question.get("nudges", []) or [], start=1):
                nudge.setdefault("id", f"{qid}-N{position}")
    return data


def _validate_weights(questionnaire: ProcessQuestionnaire) -> None:
    total = sum(step.weight for step in questionnaire.steps)
    if total != 100:
        raise ProcessLibraryError(
            f"{questionnaire.process_key}: step weights must sum to 100, got {total}. "
            f"See {questionnaire.model_ref} §3."
        )


def _validate_unique_ids(questionnaire: ProcessQuestionnaire) -> None:
    """Question and nudge ids must be unique across the whole questionnaire.

    They key the answer table. A duplicate would make two questions share one answer,
    which is the kind of fault that shows up as a mysteriously pre-filled field rather
    than as an error.
    """
    seen: set[str] = set()
    for step in questionnaire.steps:
        for question in step.questions:
            for candidate in [question.id, *[n.id for n in question.nudges]]:
                if candidate in seen:
                    raise ProcessLibraryError(
                        f"{questionnaire.process_key}: duplicate question or nudge id {candidate!r}"
                    )
                seen.add(candidate)


def _validate_nudge_targets(questionnaire: ProcessQuestionnaire) -> None:
    """A nudge condition naming an option that does not exist can never fire.

    Silent dead weight otherwise: the follow-up simply never appears and nobody notices
    the evidence is not being gathered.
    """
    for step in questionnaire.steps:
        for question in step.questions:
            labels = {option.label for option in question.options}
            for nudge in question.nudges:
                wanted: list[str] = []
                if nudge.when.equals is not None:
                    wanted.append(nudge.when.equals)
                if nudge.when.in_ is not None:
                    wanted.extend(nudge.when.in_)
                for label in wanted:
                    if label not in labels:
                        raise ProcessLibraryError(
                            f"{questionnaire.process_key}: nudge {nudge.id} fires on "
                            f"{label!r}, which is not an option of {question.id}"
                        )


@lru_cache(maxsize=1)
def get_process_registry() -> ProcessRegistry:
    data = _read_yaml(PROCESS_DIR / REGISTRY_FILE)
    try:
        registry = ProcessRegistry.model_validate(data)
    except Exception as exc:
        raise ProcessLibraryError(f"{REGISTRY_FILE} failed validation: {exc}") from exc

    keys = [entry.key for entry in registry.processes]
    if len(keys) != len(set(keys)):
        raise ProcessLibraryError(f"{REGISTRY_FILE} contains duplicate process keys")
    return registry


@lru_cache(maxsize=8)
def get_questionnaire(process_key: str) -> ProcessQuestionnaire:
    """Load one process's questionnaire, validated.

    Raises `ProcessNotDefinedError` for a registered-but-undefined process and
    `ProcessLibraryError` for a key that is not in the registry at all — the two are
    different failures and a caller should be able to tell them apart.
    """
    registry = get_process_registry()
    entry = next((e for e in registry.processes if e.key == process_key), None)
    if entry is None:
        raise ProcessLibraryError(f"unknown process key: {process_key!r}")
    if not entry.defined:
        raise ProcessNotDefinedError(entry.key, entry.name)

    data = _assign_nudge_ids(_read_yaml(PROCESS_DIR / f"{process_key}.yaml"))
    try:
        questionnaire = ProcessQuestionnaire.model_validate(data)
    except Exception as exc:
        raise ProcessLibraryError(f"{process_key}.yaml failed validation: {exc}") from exc

    if questionnaire.process_key != entry.key:
        raise ProcessLibraryError(
            f"{process_key}.yaml declares process_key={questionnaire.process_key!r} "
            f"but the registry lists it as {entry.key!r}"
        )

    _validate_weights(questionnaire)
    _validate_unique_ids(questionnaire)
    _validate_nudge_targets(questionnaire)

    logger.info(
        "Loaded process questionnaire %s v%s: %d steps, %d questions",
        questionnaire.process_key,
        questionnaire.version,
        len(questionnaire.steps),
        sum(len(s.questions) for s in questionnaire.steps),
    )
    return questionnaire


def reload_process_library() -> None:
    """Drop the caches and re-read from disk. For tests and local iteration."""
    get_process_registry.cache_clear()
    get_questionnaire.cache_clear()
