from __future__ import annotations

import json
from pathlib import Path

from ppd.archive.artifact_retention import validate_archive_artifact_retention


_FIXTURES = Path(__file__).parent / "fixtures" / "archive_retention"


def _load_fixture(name: str) -> list[dict[str, object]]:
    with (_FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_commit_safe_archive_artifacts_are_accepted() -> None:
    result = validate_archive_artifact_retention(_load_fixture("commit_safe_artifacts.json"))

    assert result.ok is True
    assert result.findings == ()
    assert result.as_dict() == {"ok": True, "findings": []}


def test_raw_private_and_unknown_artifacts_are_rejected_deterministically() -> None:
    result = validate_archive_artifact_retention(_load_fixture("rejected_artifacts.json"))

    assert result.ok is False
    assert result.as_dict() == {
        "ok": False,
        "findings": [
            {
                "artifact_id": "devhub-session",
                "code": "authenticated_scope_retained",
                "message": "authenticated scoped artifacts must not be retained by the public archive helper",
            },
            {
                "artifact_id": "devhub-session",
                "code": "forbidden_artifact_type",
                "message": "auth_state artifacts must not be retained by PP&D archive helpers",
            },
            {
                "artifact_id": "devhub-session",
                "code": "forbidden_path_fragment",
                "message": "artifact path contains non-retained location fragment /auth/",
            },
            {
                "artifact_id": "devhub-session",
                "code": "private_privacy_classification",
                "message": "session_secret artifacts are not commit-safe archive retention outputs",
            },
            {
                "artifact_id": "raw-html-body",
                "code": "forbidden_artifact_type",
                "message": "raw_html artifacts must not be retained by PP&D archive helpers",
            },
            {
                "artifact_id": "raw-html-body",
                "code": "forbidden_path_fragment",
                "message": "artifact path contains non-retained location fragment /raw/",
            },
            {
                "artifact_id": "raw-html-body",
                "code": "raw_body_not_excluded",
                "message": "no_raw_body_persisted must not be false for retained archive artifacts",
            },
            {
                "artifact_id": "raw-html-body",
                "code": "raw_body_retained",
                "message": "artifact descriptor says a raw response body would be retained",
            },
            {
                "artifact_id": "unknown-export",
                "code": "unsupported_artifact_type",
                "message": "zip_export is not in the allowed retention artifact set",
            },
        ],
    }


def test_missing_artifact_type_uses_stable_fallback_identifier() -> None:
    result = validate_archive_artifact_retention([{"path": "ppd/archive/manifests/missing-type.json"}])

    assert result.as_dict() == {
        "ok": False,
        "findings": [
            {
                "artifact_id": "artifact[0]",
                "code": "missing_artifact_type",
                "message": "artifact descriptor must include an artifact_type/type/kind/role",
            }
        ],
    }
