from __future__ import annotations

from dataclasses import dataclass, field

from .index import SkillIndex
from .selector import SkillSelector


@dataclass(slots=True)
class SkillUndertriggerAuditResult:
    warning: bool
    severity: str = "info"
    mode: str = "observe"
    suggested_skill_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "warning": self.warning,
            "severity": self.severity,
            "mode": self.mode,
            "suggested_skill_ids": list(self.suggested_skill_ids),
            "reasons": list(self.reasons),
        }


class SkillUndertriggerAudit:
    def __init__(self, selector: SkillSelector | None = None) -> None:
        self.selector = selector or SkillSelector()

    def audit(
        self,
        task_text: str,
        selected_skill_ids: list[str] | None,
        index: SkillIndex,
        runtime_mode: str = "harness",
    ) -> SkillUndertriggerAuditResult:
        if selected_skill_ids:
            return SkillUndertriggerAuditResult(warning=False)
        reasons = _risk_reasons(task_text)
        if not reasons:
            return SkillUndertriggerAuditResult(warning=False)
        suggestions = [candidate.manifest.id for candidate in self.selector.select(task_text, index, top_n=4).candidates]
        harness_mode = runtime_mode.strip().lower() not in {"noharness", "llm-only", "llm_only"}
        return SkillUndertriggerAuditResult(
            warning=True,
            severity="warn" if harness_mode else "info",
            mode="warn" if harness_mode else "observe",
            suggested_skill_ids=suggestions,
            reasons=reasons,
        )


def _risk_reasons(task_text: str) -> list[str]:
    normalized = str(task_text or "").lower()
    checks = {
        "copywriting": ["文案", "貼文", "廣告", "email", "landing page"],
        "public_release": ["發布", "對外", "公開", "社群", "促銷", "優惠", "活動"],
        "persuasion": ["說服", "買單", "轉換", "cta", "objection", "faq", "促購"],
        "sensitive_date": ["228", "紀念日", "歷史傷痛", "公共記憶", "敏感日期"],
        "humanize": ["ai 味", "ai味", "機器感", "翻譯腔", "改自然", "humanize"],
    }
    return [reason for reason, terms in checks.items() if any(term in normalized for term in terms)]
