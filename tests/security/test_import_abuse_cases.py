from harnessable import HarnessProject


def test_import_preview_rejects_invalid_yaml_without_apply(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Security")
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: [", encoding="utf-8")
    preview = project.import_bundle_preview(str(bad))
    assert preview.valid is False
    result = project.apply_import(preview.preview_id)
    assert result.applied is False
    assert not (project.path / "rules" / "bad.yaml").exists()
