from __future__ import annotations

from dataclasses import dataclass

from .budget import SkillContextBudget
from .hydrator import SkillHydrator
from .index import SkillIndex
from .audit import SkillUndertriggerAudit
from .review import SkillRoutingReviewRequest, SkillRoutingReviewTool, normalize_review_result
from .schemas import SkillCandidate, SkillContext, SkillSelectionResult
from .selector import SkillSelector


@dataclass(slots=True)
class SkillContextAssemblyRequest:
    task_text: str
    top_n: int = 5
    hydrate: bool = True
    include_full: bool = False
    selected_skill_ids: list[str] | None = None
    runtime_mode: str = "harness"


class SkillContextAssembler:
    def __init__(
        self,
        index: SkillIndex,
        selector: SkillSelector | None = None,
        hydrator: SkillHydrator | None = None,
        budget: SkillContextBudget | None = None,
        review_tool: SkillRoutingReviewTool | None = None,
        close_score_delta: float = 5.0,
    ) -> None:
        self.index = index
        self.budget = budget or SkillContextBudget()
        self.selector = selector or SkillSelector(metadata_token_budget=self.budget.metadata_token_budget)
        self.hydrator = hydrator or SkillHydrator()
        self.review_tool = review_tool
        self.close_score_delta = close_score_delta
        self.undertrigger_audit = SkillUndertriggerAudit(self.selector)

    def assemble(self, request: SkillContextAssemblyRequest) -> SkillContext:
        top_n = min(request.top_n, self.budget.max_selected_skills)
        selection = self.selector.select(request.task_text, self.index, top_n=top_n)
        context = SkillContext(selection=selection, cache_key_hint=self.cache_key_hint(selection.manifests))
        if selection.budget_exceeded:
            context.warnings.append({"type": "metadata_budget_exceeded", "budget": self.budget.metadata_token_budget})
        self._maybe_review_routing(request, context)
        if not request.hydrate:
            return context
        hydrated = [
            self.hydrator.hydrate_full(manifest) if request.include_full else self.hydrator.hydrate_summary(manifest)
            for manifest in selection.manifests
        ]
        hydrated, exceeded = self.budget.trim_hydrated(hydrated, full=request.include_full)
        context.hydrated = hydrated
        if exceeded:
            context.warnings.append(
                {
                    "type": "hydration_budget_exceeded",
                    "budget": self.budget.full_skill_token_budget if request.include_full else self.budget.summary_token_budget,
                    "mode": "full" if request.include_full else "summary",
                }
            )
        return context

    def cache_key_hint(self, manifests: list) -> str:
        ids = ",".join(manifest.id for manifest in manifests)
        return f"skill-manifest-prefix:{ids}"

    def _maybe_review_routing(self, request: SkillContextAssemblyRequest, context: SkillContext) -> None:
        if self.review_tool is None:
            return
        trigger = self._review_trigger(request, context.selection)
        if trigger is None:
            return
        audit = self.undertrigger_audit.audit(request.task_text, request.selected_skill_ids or [], self.index, runtime_mode=request.runtime_mode)
        review_request = SkillRoutingReviewRequest(
            task_text=request.task_text,
            trigger=trigger,
            selected_skill_ids=request.selected_skill_ids or [candidate.manifest.id for candidate in context.selection.candidates],
            candidates=context.selection.candidates,
            available_manifests=self.index.list(),
            audit_reasons=audit.reasons,
        )
        review = normalize_review_result(self.review_tool.review(review_request))
        context.routing_review = {
            "tool": getattr(self.review_tool, "name", "skill_routing_review"),
            "trigger": trigger,
            "input": review_request.to_tool_input(),
            "output": review.to_dict(),
        }
        if review.decision in {"add", "replace"} and review.should_hydrate:
            context.selection = self._apply_review_selection(context.selection, review.selected_skill_ids)

    def _review_trigger(self, request: SkillContextAssemblyRequest, selection: SkillSelectionResult) -> str | None:
        explicit_empty_selection = request.selected_skill_ids is not None and not request.selected_skill_ids
        if explicit_empty_selection or not selection.candidates:
            audit = self.undertrigger_audit.audit(request.task_text, request.selected_skill_ids or [], self.index, runtime_mode=request.runtime_mode)
            if audit.warning:
                return "undertrigger"
        if len(selection.candidates) >= 2:
            delta = abs(selection.candidates[0].score - selection.candidates[1].score)
            if delta <= self.close_score_delta:
                return "close_score"
        return None

    def _apply_review_selection(self, selection: SkillSelectionResult, selected_skill_ids: list[str]) -> SkillSelectionResult:
        existing = {candidate.manifest.id: candidate for candidate in selection.candidates}
        candidates: list[SkillCandidate] = []
        for skill_id in selected_skill_ids:
            if skill_id in existing:
                candidates.append(existing[skill_id])
                continue
            manifest = self.index.get(skill_id)
            if manifest is None:
                continue
            candidates.append(SkillCandidate(manifest=manifest, score=50, reasons=["skill_routing_review"], explicit=False))
        if not candidates:
            candidates = selection.candidates
        candidates = candidates[: self.budget.max_selected_skills]
        return SkillSelectionResult(
            candidates=candidates,
            excluded=selection.excluded,
            metadata_tokens=selection.metadata_tokens,
            budget_exceeded=selection.budget_exceeded,
        )
