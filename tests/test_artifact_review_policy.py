from harnessable.state import ArtifactUpdateReviewRequest, review_artifact_update


def _request(**overrides):
    payload = {
        "artifact_id": "art_1",
        "profile_id": "harness",
        "base_version": 2,
        "content": "<!doctype html><html><body>ok</body></html>",
        "content_type": "single_page_html",
        "current_artifact_id": "art_1",
        "current_profile_id": "harness",
        "current_version": 2,
    }
    payload.update(overrides)
    return ArtifactUpdateReviewRequest(**payload)


def _codes(result):
    return {issue.code for issue in result.issues}


def test_valid_artifact_update_review_passes():
    result = review_artifact_update(_request())

    assert result.ok is True
    assert result.to_dict()["schema_version"] == 1


def test_artifact_review_requires_identity_and_base_version():
    result = review_artifact_update(
        _request(artifact_id="", profile_id="", base_version=-1, current_artifact_id=None, current_profile_id=None, current_version=None)
    )

    assert result.ok is False
    assert {"missing_artifact_id", "missing_profile_id", "missing_base_version"} <= _codes(result)


def test_artifact_review_rejects_wrong_identity_and_stale_version():
    result = review_artifact_update(
        _request(artifact_id="art_other", profile_id="baseline", base_version=1)
    )

    assert result.ok is False
    assert {"wrong_artifact_id", "wrong_profile_id", "stale_base_version"} <= _codes(result)


def test_artifact_review_rejects_incomplete_single_page_html():
    result = review_artifact_update(_request(content="<main>not a full document</main>"))

    assert result.ok is False
    assert "incomplete_single_page_html" in _codes(result)


def test_artifact_review_rejects_external_scripts_by_default():
    result = review_artifact_update(
        _request(content='<!doctype html><html><body><script src="https://cdn.example/app.js"></script></body></html>')
    )

    assert result.ok is False
    assert "external_script_not_allowed" in _codes(result)


def test_artifact_review_allows_external_scripts_when_explicit():
    result = review_artifact_update(
        _request(
            content='<!doctype html><html><body><script src="https://cdn.example/app.js"></script></body></html>',
            allow_external_scripts=True,
        )
    )

    assert result.ok is True


def test_artifact_review_requires_evidence_for_verification_claims():
    missing = review_artifact_update(_request(verification_claimed=True))
    present = review_artifact_update(
        _request(verification_claimed=True, execution_evidence_refs=["tool://standard.code.container_exec/run_1"])
    )

    assert missing.ok is False
    assert "missing_execution_evidence" in _codes(missing)
    assert present.ok is True


def test_artifact_review_accepts_legacy_kind_payload():
    request = ArtifactUpdateReviewRequest.from_dict(
        {
            "artifact_id": "art_1",
            "profile_id": "harness",
            "base_version": 2,
            "kind": "single_page_html",
            "content": "<!doctype html><html><body>legacy</body></html>",
            "current_artifact_id": "art_1",
            "current_profile_id": "harness",
            "current_version": 2,
        }
    )

    assert request.content_type == "single_page_html"
    assert review_artifact_update(request).ok is True
