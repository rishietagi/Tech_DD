"""Loads the sourced investigation questions from YAML.

An Initial Request List is not only a document request. `DD_master.md` §6 gives every
workstream **both** "areas of investigation (sourced questions where available)" **and**
"evidence requests" — two distinct outputs. Until 2026-09-02 the engine seeded from the
evidence lists alone, so the list asked for artefacts and never asked management to
explain anything.

Same contract as the other reference loaders: content lives in YAML so a practitioner can
add a question without touching Python, and a malformed file fails loudly at load rather
than producing a quietly incomplete request list.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

QUESTIONS_FILE = (
    Path(__file__).resolve().parents[2] / "reference" / "investigation_questions.yaml"
)


class InvestigationLibraryError(RuntimeError):
    """Raised when the questions file is missing or malformed."""


class SourcedQuestion(BaseModel):
    """One question, and the topic label the source grouped it under (where it had one)."""

    model_config = {"extra": "forbid"}

    text: str
    # DD_master packs several questions under a bold label ("Commercial applications").
    # The questions are split one per entry so each can be answered separately; the label
    # is kept so the grouping the book intended is not lost.
    topic: str = ""


class WorkstreamQuestions(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    citation: str = ""
    # "dd_master" for sourced questions, "none" where the book gives none for that
    # workstream and the model writes them instead.
    source: str = "dd_master"
    questions: list[SourcedQuestion] = []


class InvestigationLibrary(BaseModel):
    model_config = {"extra": "forbid"}

    version: str
    source: str
    workstreams: dict[str, WorkstreamQuestions]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise InvestigationLibraryError(f"investigation questions file not found: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise InvestigationLibraryError(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise InvestigationLibraryError(f"{path.name} must contain a YAML mapping at the top")
    return data


@lru_cache(maxsize=1)
def get_investigation_library() -> InvestigationLibrary:
    data = _read_yaml(QUESTIONS_FILE)
    try:
        library = InvestigationLibrary.model_validate(data)
    except Exception as exc:
        raise InvestigationLibraryError(
            f"{QUESTIONS_FILE.name} failed validation: {exc}"
        ) from exc

    sourced = sum(
        len(w.questions) for w in library.workstreams.values() if w.source == "dd_master"
    )
    gaps = [code for code, w in library.workstreams.items() if not w.questions]
    logger.info(
        "Loaded investigation questions v%s: %d sourced across %d workstreams; %d unsourced (%s)",
        library.version,
        sourced,
        len([w for w in library.workstreams.values() if w.questions]),
        len(gaps),
        ", ".join(sorted(gaps)) or "none",
    )
    return library


def questions_for(workstreams: list[str]) -> list[tuple[str, str, str]]:
    """Sourced questions for a set of workstream codes.

    Returns `(workstream_code, question, citation)`, de-duplicated and order-stable: a row
    can carry two workstreams, and a question must not be asked twice because of it.
    """
    library = get_investigation_library()

    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for code in workstreams:
        entry = library.workstreams.get(code)
        if entry is None:
            continue
        for question in entry.questions:
            text = question.text.strip()
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((code, text, entry.citation))
    return out


def unsourced_workstreams() -> set[str]:
    """Workstreams the book gives no questions for.

    The model writes questions for these, marked as generated. Exposed so the prompt can
    name them rather than the model guessing where it is needed.
    """
    library = get_investigation_library()
    return {code for code, entry in library.workstreams.items() if not entry.questions}


def reload_investigation_library() -> None:
    """Drop the cache and re-read from disk. For tests and local iteration."""
    get_investigation_library.cache_clear()
