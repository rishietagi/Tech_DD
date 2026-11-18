"""Skills — the instructions for every AI-assisted generation task, one SKILL.md each.

A skill lives at `app/skills/<name>/SKILL.md`: YAML frontmatter that says what the task
is and what the model may and may not change, then the prompt body the model is given.
The body is the single source of truth for the prompt — the modules that call the model
read it from here, so the instructions a reviewer reads are the instructions the model
gets.

Validated at startup: a skill with missing frontmatter or no version fails the boot.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

SkillMode = Literal["prose_only", "bounded_refinement", "grounded_search", "judgement"]
_MODES = {"prose_only", "bounded_refinement", "grounded_search", "judgement"}
_REQUIRED = (
    "name",
    "description",
    "version",
    "mode",
    "deterministic_fallback",
    "inputs",
    "outputs",
    "may_change",
    "must_not_change",
)


class SkillError(RuntimeError):
    """A SKILL.md is missing or malformed."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    version: str
    mode: SkillMode
    deterministic_fallback: str
    inputs: list[str]
    outputs: list[str]
    may_change: list[str]
    must_not_change: list[str]
    house_rules: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)
    body: str = ""
    path: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "mode": self.mode,
            "deterministic_fallback": self.deterministic_fallback,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "may_change": self.may_change,
            "must_not_change": self.must_not_change,
            "house_rules": self.house_rules,
            "used_by": self.used_by,
        }


def _parse(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SkillError(f"{path}: must start with a '---' YAML frontmatter block")
    try:
        _, front, body = text.split("---", 2)
    except ValueError as exc:
        raise SkillError(f"{path}: frontmatter is not closed with '---'") from exc
    try:
        meta = yaml.safe_load(front) or {}
    except yaml.YAMLError as exc:
        raise SkillError(f"{path}: frontmatter is not valid YAML: {exc}") from exc
    missing = [k for k in _REQUIRED if k not in meta]
    if missing:
        raise SkillError(f"{path}: frontmatter lacks {missing}")
    if meta["mode"] not in _MODES:
        raise SkillError(f"{path}: mode {meta['mode']!r} is not one of {sorted(_MODES)}")
    if meta["name"] != path.parent.name:
        raise SkillError(f"{path}: name {meta['name']!r} must match its folder")
    if not body.strip():
        raise SkillError(f"{path}: the prompt body is empty")

    def as_list(key: str) -> list[str]:
        value = meta.get(key) or []
        return [str(v) for v in value] if isinstance(value, list) else [str(value)]

    return Skill(
        name=meta["name"],
        description=str(meta["description"]).strip(),
        version=str(meta["version"]),
        mode=meta["mode"],
        deterministic_fallback=str(meta["deterministic_fallback"]),
        inputs=as_list("inputs"),
        outputs=as_list("outputs"),
        may_change=as_list("may_change"),
        must_not_change=as_list("must_not_change"),
        house_rules=as_list("house_rules"),
        used_by=as_list("used_by"),
        body=body.lstrip("\n"),
        path=str(path),
    )


@lru_cache(maxsize=1)
def _registry() -> dict[str, Skill]:
    if not SKILLS_DIR.exists():
        raise SkillError(f"skills directory not found: {SKILLS_DIR}")
    skills = {}
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skill = _parse(path)
        skills[skill.name] = skill
    return skills


def list_skills() -> list[Skill]:
    return list(_registry().values())


def get_skill(name: str) -> Skill:
    try:
        return _registry()[name]
    except KeyError as exc:
        raise SkillError(f"no skill named {name!r} in {SKILLS_DIR}") from exc


def skill_text(name: str) -> str:
    """The prompt body the model is given."""
    return get_skill(name).body


def validate_all() -> None:
    _registry()
