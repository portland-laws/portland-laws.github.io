from __future__ import annotations

from pathlib import Path

from ppd.public_crawl_dry_run_promotion import assert_valid_manifest, validate_manifest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_crawl_dry_run_promotion_manifest.json"


def test_public_crawl_dry_run_promotion_manifest_is_valid() -> None:
    manifest = assert_valid_manifest(FIXTURE_PATH)

    assert manifest["mode"] == "fixture_first_public_crawl_dry_run_promotion"
    assert manifest["rate_limit_notes"]["live_fetches_performed"] == 0
    assert manifest["raw_body_persistence"]["allowed"] is False


def test_public_crawl_dry_run_promotion_manifest_rejects_raw_body_handoff() -> None:
    manifest = assert_valid_manifest(FIXTURE_PATH)
    manifest["processor_handoffs"][0]["raw_body_allowed"] = True

    errors = validate_manifest(manifest)

    assert any("must forbid raw body input" in error for error in errors)


def test_public_crawl_dry_run_promotion_manifest_requires_policy_evidence() -> None:
    manifest = assert_valid_manifest(FIXTURE_PATH)
    manifest["robots_policy_prerequisites"] = manifest["robots_policy_prerequisites"][:1]

    errors = validate_manifest(manifest)

    assert any("has no robots/policy prerequisite evidence" in error for error in errors)
