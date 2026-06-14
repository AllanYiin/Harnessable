import pytest

from harnessable import HarnessKernel
from harnessable.events import EventType
from harnessable.gateways import ContextAssemblyGateway, GatewayContext
from harnessable.skills import (
    DeterministicSkillRoutingReviewTool,
    SKILL_ROUTING_REVIEW_JSON_SCHEMA,
    SkillContextAssembler,
    SkillContextAssemblyRequest,
    SkillContextBudget,
    SkillHydrator,
    SkillIndex,
    SkillManifest,
    SkillResourcePolicyError,
    SkillRoutingReviewResult,
    SkillSelector,
    SkillUndertriggerAudit,
    assert_selected_skill,
    is_likely_text_resource,
    normalize_read_max_chars,
    resolve_allowed_resource,
)


def _index() -> SkillIndex:
    return SkillIndex(
        [
            SkillManifest(
                id="ethical-persuasion-strategy",
                description="設計說服策略、message house、反對點 FAQ、A/B test 與倫理護欄。",
                triggers=["說服策略", "買單", "促銷", "objection", "message house"],
                negative_triggers=["直接潤銷售文案"],
                category="strategy",
                priority=10,
            ),
            SkillManifest(
                id="humanize-text",
                description="把 AI 味、翻譯腔或過度制式文字改自然。",
                triggers=["AI 味", "翻譯腔", "改自然", "humanize", "潤稿"],
                negative_triggers=["bytes", "time formatting"],
                category="writing",
                priority=20,
            ),
            SkillManifest(
                id="harm-aware-editor",
                description="敏感歷史日期、公共記憶、創傷知情與冒犯風險文案審查。",
                triggers=["228", "敏感歷史日期", "公共記憶", "歷史傷痛", "促銷文案"],
                category="safety",
                priority=5,
            ),
        ]
    )


def test_explicit_skill_reference_always_selects():
    result = SkillSelector().select("請使用 $humanize-text 幫我處理這段文字", _index())
    assert [candidate.manifest.id for candidate in result.candidates][:1] == ["humanize-text"]
    assert result.candidates[0].explicit is True


def test_negative_trigger_excludes_near_miss():
    result = SkillSelector().select("幫我直接潤銷售文案，不需要策略。", _index())
    ids = [candidate.manifest.id for candidate in result.candidates]
    assert "ethical-persuasion-strategy" not in ids
    assert any(item["id"] == "ethical-persuasion-strategy" for item in result.excluded)


def test_cjk_phrase_and_sensitive_date_select_related_skills():
    result = SkillSelector().select("請寫 228 連假促銷文案，語氣要能促成購買。", _index(), top_n=4)
    ids = [candidate.manifest.id for candidate in result.candidates]
    assert "harm-aware-editor" in ids
    assert "ethical-persuasion-strategy" in ids


def test_duplicate_skill_roots_use_precedence_and_filter_archived():
    first = SkillManifest(id="same", description="first", root_priority=0)
    second = SkillManifest(id="same", description="second", root_priority=1)
    archived = SkillManifest(id="old", archived=True)
    index = SkillIndex([second, archived, first])
    assert index.get("same").description == "first"
    assert [manifest.id for manifest in index.list()] == ["same"]


def test_selector_does_not_read_full_skill_until_hydration(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: humanize-text
description: 把 AI 味文字改自然。
---

# Humanize

## Scope

Full scope content.

## Workflow overview

Full workflow content.

## Routing boundaries

Full routing content.
""",
        encoding="utf-8",
    )
    manifest = SkillManifest(
        id="humanize-text",
        description="把 AI 味文字改自然。",
        triggers=["AI 味"],
        path=str(skill_file),
    )
    result = SkillSelector().select("這段 AI 味太重，改自然一點。", SkillIndex([manifest]))
    assert result.candidates[0].manifest.id == "humanize-text"

    hydrated = SkillHydrator().hydrate_summary(result.candidates[0].manifest)
    assert "Full scope content." in hydrated.content
    assert "Full workflow content." in hydrated.content
    assert "Full routing content." in hydrated.content
    assert hydrated.mode == "summary"


def test_budget_trims_metadata_candidates():
    index = SkillIndex(
        [
            SkillManifest(id="a", description="促銷", triggers=["促銷"], token_cost_estimate=900),
            SkillManifest(id="b", description="促銷", triggers=["促銷"], token_cost_estimate=900),
        ]
    )
    result = SkillSelector(metadata_token_budget=1000).select("促銷", index, top_n=2)
    assert [candidate.manifest.id for candidate in result.candidates] == ["a"]
    assert result.budget_exceeded is True


def test_undertrigger_audit_warns_in_harness_mode_and_observes_in_noharness():
    audit = SkillUndertriggerAudit()
    harness = audit.audit("請寫 228 連假促銷文案。", [], _index(), runtime_mode="harness")
    noharness = audit.audit("請寫 228 連假促銷文案。", [], _index(), runtime_mode="noharness")
    assert harness.warning is True
    assert harness.mode == "warn"
    assert "harm-aware-editor" in harness.suggested_skill_ids
    assert noharness.warning is True
    assert noharness.mode == "observe"


def test_manifest_exports_skill_capability_metadata():
    capability = SkillManifest(id="humanize-text", description="改自然").to_capability()
    assert capability.compatibility_class == "skill"
    assert capability.contracts["skill_manifest"]["id"] == "humanize-text"


@pytest.mark.asyncio
async def test_context_assembly_gateway_emits_budget_event():
    index = SkillIndex([SkillManifest(id="humanize-text", description="AI 味", triggers=["AI 味"], token_cost_estimate=999)])
    assembler = SkillContextAssembler(index, budget=SkillContextBudget(metadata_token_budget=10))
    kernel = HarnessKernel()
    gateway = ContextAssemblyGateway(kernel, assembler)

    context = await gateway.assemble(SkillContextAssemblyRequest("AI 味很重", hydrate=False), GatewayContext(run_id="run_skill"))

    assert context.selection.budget_exceeded is True
    assert any(event.event_type == EventType.CONTEXT_BUDGET_EXCEEDED for event in kernel.events.events)


def test_skill_routing_review_schema_is_fixed_json_contract():
    assert SKILL_ROUTING_REVIEW_JSON_SCHEMA["additionalProperties"] is False
    result = SkillRoutingReviewResult(
        decision="add",
        selected_skill_ids=["humanize-text"],
        confidence=0.8,
        reasons=["undertrigger"],
        should_hydrate=True,
    )
    assert result.to_dict()["selected_skill_ids"] == ["humanize-text"]


def test_undertrigger_calls_skill_routing_review_tool_and_applies_selection():
    class FakeReviewTool:
        name = "skill_routing_review"

        def __init__(self):
            self.calls = []

        def review(self, request):
            self.calls.append(request)
            return {
                "decision": "add",
                "selected_skill_ids": ["ethical-persuasion-strategy"],
                "confidence": 0.9,
                "reasons": ["public copywriting needs strategy review"],
                "should_hydrate": True,
            }

    tool = FakeReviewTool()
    index = _index()
    assembler = SkillContextAssembler(index, review_tool=tool)

    context = assembler.assemble(SkillContextAssemblyRequest("請幫我寫一篇對外社群貼文", hydrate=False, selected_skill_ids=[]))

    assert len(tool.calls) == 1
    assert tool.calls[0].trigger == "undertrigger"
    assert context.routing_review["output"]["decision"] == "add"
    assert [candidate.manifest.id for candidate in context.selection.candidates] == ["ethical-persuasion-strategy"]


def test_close_score_calls_skill_routing_review_tool():
    class FakeReviewTool:
        name = "skill_routing_review"

        def __init__(self):
            self.triggers = []

        def review(self, request):
            self.triggers.append(request.trigger)
            return SkillRoutingReviewResult(
                decision="add",
                selected_skill_ids=[candidate.manifest.id for candidate in request.candidates[:2]],
                confidence=0.75,
                reasons=["close score"],
                should_hydrate=True,
            )

    index = SkillIndex(
        [
            SkillManifest(id="a", description="促銷", triggers=["促銷"], priority=10),
            SkillManifest(id="b", description="促銷", triggers=["促銷"], priority=11),
        ]
    )
    tool = FakeReviewTool()
    context = SkillContextAssembler(index, review_tool=tool, close_score_delta=100).assemble(SkillContextAssemblyRequest("促銷", hydrate=False))

    assert tool.triggers == ["close_score"]
    assert [candidate.manifest.id for candidate in context.selection.candidates] == ["a", "b"]


def test_deterministic_review_tool_returns_fixed_json_result_for_close_scores():
    index = SkillIndex(
        [
            SkillManifest(id="a", description="促銷", triggers=["促銷"], priority=10),
            SkillManifest(id="b", description="促銷", triggers=["促銷"], priority=11),
        ]
    )
    context = SkillContextAssembler(index, review_tool=DeterministicSkillRoutingReviewTool(), close_score_delta=100).assemble(
        SkillContextAssemblyRequest("促銷", hydrate=False)
    )

    assert context.routing_review["tool"] == "skill_routing_review"
    assert context.routing_review["output"]["should_hydrate"] is True


def test_skill_resource_policy_restricts_paths_and_selected_skills(tmp_path):
    root = tmp_path / "skill"
    (root / "references").mkdir(parents=True)
    allowed = root / "references" / "guide.md"
    allowed.write_text("guide", encoding="utf-8")

    assert_selected_skill("humanize-text", ("humanize-text",))
    assert resolve_allowed_resource(root, "references/guide.md") == allowed.resolve()
    with pytest.raises(SkillResourcePolicyError):
        assert_selected_skill("other", ("humanize-text",))
    with pytest.raises(SkillResourcePolicyError):
        resolve_allowed_resource(root, "../secret.txt")
    with pytest.raises(SkillResourcePolicyError):
        resolve_allowed_resource(root, "tmp/cache.txt")


def test_skill_resource_policy_limits_text_reads():
    assert normalize_read_max_chars(None) == 6000
    assert normalize_read_max_chars(999999) == 20000
    assert is_likely_text_resource(b"plain text", size_bytes=10) is True
    assert is_likely_text_resource(b"a\x00b", size_bytes=3) is False
