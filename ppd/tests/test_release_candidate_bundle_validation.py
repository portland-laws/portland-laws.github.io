from pathlib import Path

import pytest

from ppd.validation.release_candidate_bundle import assert_release_candidate_bundle, validate_release_candidate_bundle


def _codes(root: Path) -> set[str]:
    return {finding.code for finding in validate_release_candidate_bundle(root)}


def test_release_candidate_bundle_accepts_cited_offline_fixture(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "README.md").write_text(
        "Prerequisite: confirm parcel identifier mapping [ppd/prereq-parcel-map].\n"
        "Readiness validated against deterministic fixture [ppd/readiness-fixture].\n"
        "Rollback: restore previous fixture snapshot [ppd/rollback-fixture].\n"
        "payment capability disabled\n"
        "upload capability disabled\n"
        "submission capability disabled\n"
        "scheduling capability disabled\n"
        "cancellation capability disabled\n"
        "certification capability disabled\n",
        encoding="utf-8",
    )

    assert validate_release_candidate_bundle(bundle) == []
    assert_release_candidate_bundle(bundle)


def test_release_candidate_bundle_rejects_uncited_and_live_claims(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.md").write_text(
        "Prerequisite: permit account access.\n"
        "This release candidate is production-ready and fully validated.\n"
        "Run with --live and devhub_execute=true.\n"
        "submission capability enabled\n",
        encoding="utf-8",
    )

    codes = _codes(bundle)

    assert "missing_prerequisite_link" in codes
    assert "uncited_readiness_claim" in codes
    assert "production_ready_label" in codes
    assert "live_execution_flag" in codes
    assert "enabled_high_risk_capability" in codes
    assert "missing_rollback_reference" in codes


def test_release_candidate_bundle_rejects_private_and_raw_artifacts(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    (bundle / "sessions").mkdir(parents=True)
    (bundle / "raw" / "downloads").mkdir(parents=True)
    (bundle / "sessions" / "storage_state.json").write_text("{}", encoding="utf-8")
    (bundle / "raw" / "downloads" / "permit.html").write_text(
        "Rollback: restore snapshot [ppd/rollback-fixture].\n"
        "raw crawl output from archive.org\n",
        encoding="utf-8",
    )

    codes = _codes(bundle)

    assert "private_or_session_artifact" in codes
    assert "raw_artifact_path" in codes
    assert "raw_reference" in codes


def test_assert_release_candidate_bundle_raises_with_findings(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "README.md").write_text("ready\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        assert_release_candidate_bundle(bundle)

    assert "uncited_readiness_claim" in str(excinfo.value)
