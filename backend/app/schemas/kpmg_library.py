"""Validation models for the KPMG scope library YAML.

The library is domain content, not logic: a practitioner edits the YAML in
`app/reference/kpmg_scope/` without touching Python. These models are what make that
safe — the loader validates every file at startup and fails fast on a malformed one,
so a typo surfaces as a clear error at boot rather than a broken scope at generation
time.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

DeckId = Literal["product", "enterprise"]


class ScopeRow(BaseModel):
    """One client-facing row.

    Product rows carry `objective` + `scope_of_work`; enterprise rows carry
    `focus_area` + `considerations`. Exactly one of those shapes must be present —
    the validator below enforces it so a half-filled row cannot reach generation.
    """

    model_config = {"extra": "forbid"}

    sn: int
    id: str

    # Product shape
    objective: str | None = None
    scope_of_work: str | None = None

    # Enterprise shape
    focus_area: str | None = None
    considerations: list[str] | None = None

    # Internal rule layer — never shown to the client verbatim.
    workstreams: list[str] = Field(default_factory=list)
    submodules: list[str] = Field(default_factory=list)
    always_in_scope: bool = False
    base_tier: int = Field(default=1, ge=0, le=3)
    triggers: list[str] = Field(default_factory=list)
    escalate_when: str | None = None
    evidence: list[str] = Field(default_factory=list)
    dd_master_ref: str | None = None

    @model_validator(mode="after")
    def _exactly_one_shape(self) -> "ScopeRow":
        is_product = self.objective is not None and self.scope_of_work is not None
        is_enterprise = self.focus_area is not None and self.considerations is not None
        if is_product == is_enterprise:
            raise ValueError(
                f"row {self.id!r} must have either (objective + scope_of_work) "
                "or (focus_area + considerations), not both and not neither"
            )
        if is_enterprise and not self.considerations:
            raise ValueError(f"row {self.id!r} has an empty considerations list")
        return self

    @property
    def title(self) -> str:
        """The row's client-facing heading, whichever shape it uses."""
        return self.objective or self.focus_area or self.id

    @property
    def body_lines(self) -> list[str]:
        """The row's client-facing detail, normalised to a list."""
        if self.considerations is not None:
            return self.considerations
        return [self.scope_of_work] if self.scope_of_work else []


class ScopeDeck(BaseModel):
    model_config = {"extra": "forbid"}

    deck: DeckId
    deck_title: str
    deck_subtitle: str
    library_version: str
    source: str
    rows: list[ScopeRow] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_ids_and_sns(self) -> "ScopeDeck":
        ids = [r.id for r in self.rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"deck {self.deck!r} has duplicate row ids")
        sns = [r.sn for r in self.rows]
        if len(sns) != len(set(sns)):
            raise ValueError(f"deck {self.deck!r} has duplicate row numbers")
        return self


class DeckRef(BaseModel):
    model_config = {"extra": "forbid"}

    id: DeckId
    file: str
    title: str
    applies_when: str


class BlendedConfig(BaseModel):
    model_config = {"extra": "forbid"}

    lead_threshold: int = Field(ge=0, le=100)


class ScopeLibraryManifest(BaseModel):
    model_config = {"extra": "forbid"}

    library_version: str
    source_document: str
    source_owner: str
    source_year: int
    decks: list[DeckRef] = Field(min_length=1)
    blended: BlendedConfig


class ScopeLibrary(BaseModel):
    """The loaded, validated library."""

    manifest: ScopeLibraryManifest
    decks: dict[str, ScopeDeck]

    def deck(self, deck_id: str) -> ScopeDeck:
        try:
            return self.decks[deck_id]
        except KeyError as exc:
            raise KeyError(f"unknown deck {deck_id!r}; have {sorted(self.decks)}") from exc
