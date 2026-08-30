"""Loads and validates the KPMG scope library from YAML.

Loaded once and cached. A malformed file raises at first access with the offending
file named, so the failure is loud and early rather than a silently degraded scope.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.schemas.kpmg_library import ScopeDeck, ScopeLibrary, ScopeLibraryManifest

logger = logging.getLogger(__name__)

LIBRARY_DIR = Path(__file__).resolve().parents[2] / "reference" / "kpmg_scope"
MANIFEST_FILE = "_library.yaml"


class ScopeLibraryError(RuntimeError):
    """Raised when the library on disk is missing or malformed."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ScopeLibraryError(f"scope library file not found: {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ScopeLibraryError(f"{path.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ScopeLibraryError(f"{path.name} must contain a YAML mapping at the top level")
    return data


@lru_cache(maxsize=1)
def get_scope_library() -> ScopeLibrary:
    manifest_data = _read_yaml(LIBRARY_DIR / MANIFEST_FILE)
    try:
        manifest = ScopeLibraryManifest.model_validate(manifest_data)
    except Exception as exc:
        raise ScopeLibraryError(f"{MANIFEST_FILE} failed validation: {exc}") from exc

    decks: dict[str, ScopeDeck] = {}
    for ref in manifest.decks:
        deck_data = _read_yaml(LIBRARY_DIR / ref.file)
        try:
            deck = ScopeDeck.model_validate(deck_data)
        except Exception as exc:
            raise ScopeLibraryError(f"{ref.file} failed validation: {exc}") from exc
        if deck.deck != ref.id:
            raise ScopeLibraryError(
                f"{ref.file} declares deck={deck.deck!r} but the manifest lists it as {ref.id!r}"
            )
        decks[ref.id] = deck

    logger.info(
        "Loaded KPMG scope library v%s: %s",
        manifest.library_version,
        ", ".join(f"{d}({len(decks[d].rows)} rows)" for d in sorted(decks)),
    )
    return ScopeLibrary(manifest=manifest, decks=decks)


def reload_scope_library() -> ScopeLibrary:
    """Drop the cache and re-read from disk. For tests and local iteration."""
    get_scope_library.cache_clear()
    return get_scope_library()
