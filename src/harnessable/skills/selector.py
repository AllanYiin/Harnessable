from __future__ import annotations

import re
from collections.abc import Callable

from .index import SkillIndex
from .schemas import SkillCandidate, SkillManifest, SkillSelectionResult, estimate_tokens

Reranker = Callable[[str, list[SkillCandidate]], list[SkillCandidate]]


class SkillSelector:
    def __init__(
        self,
        metadata_token_budget: int = 1500,
        reranker: Reranker | None = None,
    ) -> None:
        self.metadata_token_budget = metadata_token_budget
        self.reranker = reranker

    def select(self, task_text: str, index: SkillIndex, top_n: int = 5) -> SkillSelectionResult:
        explicit_ids = _explicit_skill_ids(task_text)
        candidates: list[SkillCandidate] = []
        excluded: list[dict] = []
        for manifest in index.list():
            score, reasons, explicit = self._score(task_text, manifest, explicit_ids)
            negative_hits = _matching_terms(task_text, manifest.negative_triggers)
            if negative_hits and not explicit:
                excluded.append({"id": manifest.id, "reason": "negative_trigger", "matches": negative_hits})
                continue
            if score > 0 or explicit:
                candidates.append(SkillCandidate(manifest=manifest, score=score, reasons=reasons, explicit=explicit))
        candidates.sort(key=lambda item: (-item.score, item.manifest.priority, item.manifest.id))
        if self.reranker:
            candidates = self.reranker(task_text, candidates)
        candidates = candidates[:top_n]
        candidates, used_tokens, exceeded = self._apply_metadata_budget(candidates)
        return SkillSelectionResult(candidates=candidates, excluded=excluded, metadata_tokens=used_tokens, budget_exceeded=exceeded)

    def _score(self, task_text: str, manifest: SkillManifest, explicit_ids: set[str]) -> tuple[float, list[str], bool]:
        normalized = _normalize(task_text)
        manifest_names = {manifest.id.lower(), str(manifest.name or "").lower()}
        explicit = bool(explicit_ids & manifest_names)
        score = 0.0
        reasons: list[str] = []
        if explicit:
            score += 1000
            reasons.append("explicit_skill_reference")
        trigger_hits = _matching_terms(task_text, manifest.triggers)
        for hit in trigger_hits:
            score += 25
            reasons.append(f"trigger:{hit}")
        description_score = _description_score(normalized, manifest.description)
        if description_score:
            score += description_score
            reasons.append("description_match")
        cjk_score = _cjk_overlap_score(normalized, _skill_text(manifest))
        if cjk_score:
            score += cjk_score
            reasons.append("cjk_ngram_match")
        if _looks_like_public_persuasion(normalized, manifest):
            score += 12
            reasons.append("public_persuasion_context")
        if _looks_like_humanize_request(normalized, manifest):
            score += 18
            reasons.append("humanize_context")
        return score, reasons, explicit

    def _apply_metadata_budget(self, candidates: list[SkillCandidate]) -> tuple[list[SkillCandidate], int, bool]:
        used = 0
        kept: list[SkillCandidate] = []
        exceeded = False
        for candidate in candidates:
            cost = candidate.manifest.token_cost_estimate or estimate_tokens(str(candidate.manifest.to_prompt_metadata()))
            if cost > self.metadata_token_budget:
                exceeded = True
            if kept and used + cost > self.metadata_token_budget:
                exceeded = True
                continue
            kept.append(candidate)
            used += cost
        return kept, used, exceeded


def _explicit_skill_ids(task_text: str) -> set[str]:
    values = {match.group(1).strip().lower() for match in re.finditer(r"\$([A-Za-z0-9_.-]+)", task_text)}
    values.update(match.group(1).strip().lower() for match in re.finditer(r"<name>\s*([^<]+?)\s*</name>", task_text, flags=re.IGNORECASE))
    return values


def _matching_terms(task_text: str, terms: list[str]) -> list[str]:
    normalized = _normalize(task_text)
    hits = []
    for term in terms:
        clean = _normalize(term)
        if clean and clean in normalized:
            hits.append(term)
    return hits


def _description_score(task_text: str, description: str) -> float:
    description = _normalize(description)
    if not description:
        return 0
    score = 0.0
    for term in _split_terms(task_text):
        if len(term) >= 2 and term in description:
            score += 2
    return min(score, 12)


def _cjk_overlap_score(task_text: str, skill_text: str) -> float:
    task_grams = _cjk_ngrams(task_text)
    skill_grams = _cjk_ngrams(skill_text)
    if not task_grams or not skill_grams:
        return 0
    overlap = task_grams & skill_grams
    if not overlap:
        return 0
    ratio = len(overlap) / max(1, len(task_grams))
    if ratio < 0.12:
        return 0
    return min(18.0, 6 + ratio * 24)


def _cjk_ngrams(text: str, size: int = 2) -> set[str]:
    chars = [char for char in text if "\u4e00" <= char <= "\u9fff" or char.isdigit()]
    return {"".join(chars[index : index + size]) for index in range(0, max(0, len(chars) - size + 1))}


def _split_terms(text: str) -> set[str]:
    return {item for item in re.split(r"[^0-9a-zA-Z\u4e00-\u9fff]+", _normalize(text)) if item}


def _normalize(text: str) -> str:
    return str(text or "").strip().lower()


def _skill_text(manifest: SkillManifest) -> str:
    return " ".join(
        item
        for item in [
            manifest.id,
            str(manifest.name or ""),
            manifest.description,
            " ".join(manifest.triggers),
            str(manifest.category or ""),
            str(manifest.language or ""),
        ]
        if item
    ).lower()


def _looks_like_public_persuasion(task_text: str, manifest: SkillManifest) -> bool:
    if manifest.id not in {"ethical-persuasion-strategy", "harm-aware-editor"}:
        return False
    public_terms = ["促銷", "文案", "發布", "對外", "活動", "優惠", "連假", "cta", "客戶", "買單"]
    sensitive_terms = ["228", "歷史", "公共記憶", "敏感日期", "紀念日"]
    return any(term in task_text for term in public_terms) and (
        manifest.id == "ethical-persuasion-strategy" or any(term in task_text for term in sensitive_terms)
    )


def _looks_like_humanize_request(task_text: str, manifest: SkillManifest) -> bool:
    if manifest.id != "humanize-text":
        return False
    terms = ["ai 味", "ai味", "機器感", "翻譯腔", "改自然", "humanize", "潤稿", "順一下"]
    return any(term in task_text for term in terms)
