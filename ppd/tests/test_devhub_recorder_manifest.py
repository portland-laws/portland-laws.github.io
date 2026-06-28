from pathlib import Path

from ppd.devhub.recorder_manifest import (
    validate_recorder_manifest,
    validate_recorder_manifest_file,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_recorder"


def test_safe_recorder_manifest_fixture_is_valid() -> None:
    result = validate_recorder_manifest_file(FIXTURES / "safe_manifest.json")

    assert result.ok is True
    assert result.errors == ()


def test_unsafe_recorder_manifest_fixture_rejects_private_artifacts() -> None:
    result = validate_recorder_manifest_file(FIXTURES / "unsafe_manifest.json")

    assert result.ok is False
    codes = {error.code for error in result.errors}
    assert "playwright_launch_not_allowed" in codes
    assert "auth_state_not_allowed" in codes
    assert "artifacts_not_allowed" in codes
    assert "private_values_not_allowed" in codes
    assert "forbidden_key" in codes
    assert "unredacted_private_value" in codes
    assert "forbidden_artifact_reference" in codes


def test_manifest_requires_metadata_only_recorder_shape() -> None:
    result = validate_recorder_manifest(
        {
            "manifest_version": "devhub-recorder-manifest/v1",
            "recorded_at": "2026-05-12T00:00:00Z",
            "recorder": {
                "mode": "manifest_only",
                "playwright_launched": False,
                "auth_state_saved": False,
                "artifacts_saved": False,
            },
            "privacy": {
                "classification": "metadata_only",
                "private_values_persisted": False,
            },
            "surface": {
                "surface_id": "devhub-public-help",
                "auth_scope": "public",
                "url_pattern": "https://www.portland.gov/ppd/devhub-faqs",
            },
        }
    )

    assert result.ok is True


def test_manifest_rejects_unredacted_field_values() -> None:
    result = validate_recorder_manifest(
        {
            "manifest_version": "devhub-recorder-manifest/v1",
            "recorded_at": "2026-05-12T00:00:00Z",
            "recorder": {
                "mode": "manifest_only",
                "playwright_launched": False,
                "auth_state_saved": False,
                "artifacts_saved": False,
            },
            "privacy": {
                "classification": "metadata_only",
                "private_values_persisted": False,
            },
            "surface": {
                "surface_id": "devhub-private-form",
                "auth_scope": "authenticated_attended",
                "url_pattern": "https://devhub.portlandoregon.gov/**",
                "fields": [
                    {
                        "field_id": "applicant-name",
                        "label": "Applicant name",
                        "value": "Jane Applicant",
                    }
                ],
            },
        }
    )

    assert result.ok is False
    assert any(error.code == "unredacted_private_value" for error in result.errors)
