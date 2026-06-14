import json

from harnessable import (
    HarnessProject,
    VerticalHarnessPack,
    VerticalPackStore,
    build_eu_ai_act_support_export,
    build_iso42001_support_export,
    build_nist_ai_rmf_export,
    builtin_vertical_packs,
)


def test_compliance_support_exports_include_evidence_refs_and_limitations():
    refs = ["audit:run_1", "replay:case_1"]
    exports = [
        build_nist_ai_rmf_export(refs),
        build_iso42001_support_export(refs),
        build_eu_ai_act_support_export(refs),
    ]

    for export in exports:
        payload = export.to_dict()
        rendered = json.dumps(payload).lower()
        assert payload["entries"]
        assert payload["limitations"]
        assert "supports_evidence_for" in rendered
        assert "not legal advice" in rendered or "not legal advice" in payload["disclaimer"].lower()
        assert "certified" not in rendered
        assert "guaranteed compliant" not in rendered


def test_builtin_vertical_packs_keep_claims_within_evidence_support_language():
    packs = builtin_vertical_packs()

    assert set(packs) == {"coding", "research", "ops"}
    for pack in packs.values():
        payload = pack.to_dict()
        rendered = json.dumps(payload).lower()
        assert payload["supports_evidence_for"]
        assert payload["limitations"]
        assert "certified" not in rendered
        assert "guaranteed compliant" not in rendered


def test_vertical_pack_preview_apply_installs_pack_after_preview(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Demo")
    pack = builtin_vertical_packs()["coding"]

    preview = project.vertical_packs.preview(pack)
    result = project.vertical_packs.apply(preview.preview_id)

    assert result.applied is True
    assert result.pack_id == "coding"
    installed = json.loads((project.path / "packs" / "coding.json").read_text(encoding="utf-8"))
    assert installed["pack_id"] == "coding"


def test_vertical_pack_preview_warns_when_claims_exceed_evidence(tmp_path):
    store = VerticalPackStore(tmp_path)
    pack = VerticalHarnessPack(
        pack_id="bad",
        name="Certified Pack",
        profile="bad",
        supports_evidence_for=("legal compliance",),
    )

    preview = store.preview(pack)

    assert "claim_exceeds_evidence" in preview.warnings
