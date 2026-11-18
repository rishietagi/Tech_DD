"""The intelligence pipeline: skills (SKILL.md) and the one decision of rules vs LLM.

docs/phases/PHASE7_PLAN.md Part A. Every generator in the platform has a deterministic
floor that always runs; a skill describes what the model may add on top, and `use_llm`
decides — from one setting — whether it does.
"""

from app.services.intelligence.mode import ai_status, use_llm
from app.services.intelligence.skills import Skill, get_skill, list_skills, skill_text

__all__ = ["Skill", "ai_status", "get_skill", "list_skills", "skill_text", "use_llm"]
