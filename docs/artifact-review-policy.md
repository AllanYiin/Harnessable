# Artifact Review Policy

Artifact review is the runtime-neutral policy for proposed canvas updates. It
does not store artifacts and does not know about HarnessDiff routes. Storage
adapters pass the proposed update plus the current artifact identity/version and
receive a versioned result with review issues.

## Contract

`ArtifactUpdateReviewRequest` includes:

- `schema_version`
- `artifact_id`
- `profile_id`
- `base_version`
- `content_type`
- `content`
- optional current `artifact_id`, `profile_id`, and version facts
- optional `verification_claimed` and `execution_evidence_refs`
- optional `allow_external_scripts`

`review_artifact_update(...)` returns `ArtifactReviewResult` with `ok` and a
list of structured issues. All current issues are errors.

## Policy

Artifact updates must identify the exact artifact, owning profile, and base
version they are editing. This mirrors conditional update behavior: stale base
versions are rejected instead of overwriting a newer artifact.

For `single_page_html`, content must be a complete HTML document with an
`<html>` root and closing `</html>`. External script dependencies are rejected
by default. An adapter may set `allow_external_scripts=True` only when the user
or product flow has explicitly allowed that risk and can apply additional
controls such as integrity metadata.

Verification claims are not accepted as text alone. If an update claims that
HTML or code was verified, it must include execution evidence references from
the execution evidence policy.

## Compatibility

Legacy payloads that use `kind` instead of `content_type` are accepted by
`ArtifactUpdateReviewRequest.from_dict(...)`. Adapters should keep public APIs
stable and add stricter fields in preview before making them mandatory.
