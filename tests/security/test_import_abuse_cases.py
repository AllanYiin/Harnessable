from harnessable import HarnessProject
from harnessable.state.import_preview import ImportPreviewStore


def test_import_preview_rejects_invalid_yaml_without_apply(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Security")
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: [", encoding="utf-8")
    preview = project.import_bundle_preview(str(bad))
    assert preview.valid is False
    result = project.apply_import(preview.preview_id)
    assert result.applied is False
    assert not (project.path / "rules" / "bad.yaml").exists()


def test_import_preview_rejects_root_escape_binary_and_oversized_sources(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Security")
    outside = tmp_path.parent / "outside.yaml"
    outside.write_text("id: x\nschema_version: '1'\n", encoding="utf-8")
    binary = tmp_path / "binary.yaml"
    binary.write_bytes(b"id: x\x00schema_version: '1'")
    large = tmp_path / "large.yaml"
    large.write_text("x" * 32, encoding="utf-8")
    store = ImportPreviewStore(project.path, max_bytes=16)

    escaped_preview = store.preview(outside)
    binary_preview = store.preview(binary)
    large_preview = store.preview(large)

    assert escaped_preview.valid is False
    assert "source path is outside allowed import roots" in escaped_preview.errors
    assert binary_preview.valid is False
    assert "source file appears to be binary" in binary_preview.errors
    assert large_preview.valid is False
    assert "source file exceeds import size limit" in large_preview.errors


def test_import_apply_rejects_source_changed_after_preview(tmp_path):
    project = HarnessProject.create(str(tmp_path / "project"), "Security")
    source = tmp_path / "rule.yaml"
    source.write_text("id: rule_1\nschema_version: '1'\nname: Rule\n", encoding="utf-8")
    preview = project.import_bundle_preview(str(source))
    assert preview.valid is True

    source.write_text("id: [", encoding="utf-8")
    result = project.apply_import(preview.preview_id)

    assert result.applied is False
    assert result.errors == ["source changed after preview; create a new preview before apply"]
    assert not (project.path / "rules" / "rule.yaml").exists()
