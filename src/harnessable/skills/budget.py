from __future__ import annotations

from dataclasses import dataclass

from .schemas import HydratedSkill


@dataclass(slots=True)
class SkillContextBudget:
    metadata_token_budget: int = 1500
    summary_token_budget: int = 4000
    full_skill_token_budget: int = 8000
    max_primary: int = 2
    max_secondary: int = 2

    @property
    def max_selected_skills(self) -> int:
        return self.max_primary + self.max_secondary

    def trim_hydrated(self, skills: list[HydratedSkill], full: bool = False) -> tuple[list[HydratedSkill], bool]:
        budget = self.full_skill_token_budget if full else self.summary_token_budget
        used = 0
        kept: list[HydratedSkill] = []
        exceeded = False
        for skill in skills:
            if kept and used + skill.estimated_tokens > budget:
                exceeded = True
                continue
            kept.append(skill)
            used += skill.estimated_tokens
        return kept, exceeded
