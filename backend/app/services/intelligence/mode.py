"""The one decision: does this skill run the model, or only its deterministic floor?

Rishi, 2026-11-18 (D4): `AI_MODE=off` keeps every generator deterministic even when a key
is present; `auto` turns the model on for every skill that has a key, except those listed
in `AI_DISABLED_SKILLS`. An explicit generator request from a caller (a test, a developer
hitting the API with `{"generator": "llm"}`) still wins — that is a deliberate act, not a
default.
"""

from typing import Any

from app.core.config import Settings, get_settings
from app.services.intelligence.skills import get_skill, list_skills


def use_llm(skill: str, requested: str | None = None, settings: Settings | None = None) -> bool:
    get_skill(skill)  # an unknown skill is a programming error — fail loudly
    if requested == "llm":
        return True
    if requested in ("rules", "placeholder", "manual"):
        return False
    s = settings or get_settings()
    return s.llm_enabled and skill not in s.disabled_skills


def ai_status(settings: Settings | None = None) -> dict[str, Any]:
    s = settings or get_settings()
    skills = []
    for skill in list_skills():
        if s.ai_mode == "off":
            status, reason = "deterministic", "AI_MODE is off"
        elif not s.llm_key_present:
            status, reason = "deterministic", "no model key configured"
        elif skill.name in s.disabled_skills:
            status, reason = "deterministic", "disabled in AI_DISABLED_SKILLS"
        else:
            status, reason = "llm", f"model {s.gemini_model}"
        skills.append({**skill.as_dict(), "status": status, "reason": reason, "body": skill.body})
    return {
        "mode": s.ai_mode,
        "key_present": s.llm_key_present,
        "model": s.gemini_model,
        "active": s.llm_enabled,
        "skills": skills,
    }
