from copy import deepcopy
from pathlib import Path

from ppd.agent_readiness.e2e_digest import (
    E2EReadinessDigestError,
    build_e2e_readiness_digest,
    load_e2e_readiness_digest_fixture,
    validate_e2e_readiness_digest,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "e2e_readiness_digest" / "synthetic_case_status.json"
_REQUIRED_PACKET_KEYS = (
    "public_source_packet",
    "extraction_packet",
    "process_model_packet",
    "guardrail_packet",
    "user_gap_packet",
    "local_preview_packet",
    "devhub_preflight_packet",
    "journal_packet",
    "post_action_packet",
)


def _base_fixture() -> dict:
    return {
        "case_id": "synthetic-case",
        "process_id": "process-fixture",
        **{
            key: {
                "packet_id": key,
                "fixture_first": True,
                "live_services_called": False,
                "official_readiness": False,
                "status": "fixture_validated",
                "source_evidence_ids": ["ev-fixture"],
            }
            for key in _REQUIRED_PACKET_KEYS
        },
    }


def _problems_for_fixture(fixture: dict) -> tuple[str, ...]:
    try:
        build_e2e_readiness_digest(fixture)
    except E2EReadinessDigestError as exc:
        return exc.problems
    raise AssertionError("expected fixture to be rejected")


def test_e2e_readiness_digest_links_all_fixture_packets_without_official_readiness() -> None:
    digest = load_e2e_readiness_digest_fixture(FIXTURE_PATH)

    assert digest["digest_type"] == "ppd.e2e_readiness_digest.v1"
    assert digest["fixture_first"] is True
    assert digest["live_services_called"] is False
    assert digest["official_readiness"] is False
    assert digest["synthetic_case_status"] == "synthetic_blocked_pending_user_or_manual_review"

    linked_keys = {link["packet_key"] for link in digest["packet_links"]}
    assert linked_keys == set(_REQUIRED_PACKET_KEYS)
    assert "ev-ppd-devhub-application-guide" in digest["source_evidence_ids"]
    assert "resolve_missing_or_gated_items_before_official_action" in digest["next_safe_actions"]
    assert validate_e2e_readiness_digest(digest) == []


def test_e2e_readiness_digest_rejects_live_service_packet() -> None:
    fixture = _base_fixture()
    fixture["devhub_preflight_packet"]["live_services_called"] = True

    problems = _problems_for_fixture(fixture)

    assert "devhub_preflight_packet must confirm live_services_called is false" in problems


def test_validate_e2e_readiness_digest_rejects_missing_packet_links() -> None:
    digest = load_e2e_readiness_digest_fixture(FIXTURE_PATH)
    digest["packet_links"] = [
        link for link in digest["packet_links"] if link["packet_key"] != "journal_packet"
    ]

    problems = validate_e2e_readiness_digest(digest)

    assert "digest is missing packet link: journal_packet" in problems
    assert "digest must link every required packet exactly once" in problems


def test_build_e2e_readiness_digest_rejects_stale_component() -> None:
    fixture = _base_fixture()
    fixture["public_source_packet"]["freshness_status"] = "stale"

    problems = _problems_for_fixture(fixture)

    assert "fixture.public_source_packet.freshness_status is stale: stale" in problems


def test_build_e2e_readiness_digest_rejects_unreviewed_component() -> None:
    fixture = _base_fixture()
    fixture["guardrail_packet"]["human_review_status"] = "unreviewed"

    problems = _problems_for_fixture(fixture)

    assert "fixture.guardrail_packet.human_review_status is unreviewed: unreviewed" in problems


def test_build_e2e_readiness_digest_rejects_private_values() -> None:
    fixture = _base_fixture()
    fixture["devhub_preflight_packet"]["auth_state"] = {"cookie": "private-session"}

    problems = _problems_for_fixture(fixture)

    assert "fixture.devhub_preflight_packet.auth_state must not contain private values" in problems
    assert "fixture.devhub_preflight_packet.auth_state.cookie must not contain private values" in problems


def test_build_e2e_readiness_digest_rejects_raw_or_authenticated_artifacts() -> None:
    fixture = _base_fixture()
    fixture["public_source_packet"]["raw_crawl_artifact_ref"] = "raw-crawl/body.html"
    fixture["devhub_preflight_packet"]["authenticated_artifact_ref"] = "trace.zip"

    problems = _problems_for_fixture(fixture)

    assert "fixture.public_source_packet.raw_crawl_artifact_ref must not reference raw crawl or authenticated artifacts" in problems
    assert "fixture.devhub_preflight_packet.authenticated_artifact_ref must not reference raw crawl or authenticated artifacts" in problems


def test_build_e2e_readiness_digest_rejects_downloaded_document_paths() -> None:
    fixture = _base_fixture()
    fixture["local_preview_packet"]["downloaded_document_path"] = "/home/example/Downloads/site-plan.pdf"

    problems = _problems_for_fixture(fixture)

    assert "fixture.local_preview_packet.downloaded_document_path must not reference downloaded document paths" in problems
    assert "fixture.local_preview_packet.downloaded_document_path must not contain downloaded document paths" in problems


def test_build_e2e_readiness_digest_rejects_ready_to_submit_statuses() -> None:
    fixture = _base_fixture()
    fixture["post_action_packet"]["status"] = "ready_to_submit"

    problems = _problems_for_fixture(fixture)

    assert "fixture.post_action_packet.status contains unsupported ready-to-submit status" in problems


def test_build_e2e_readiness_digest_rejects_unblocked_consequential_actions() -> None:
    fixture = _base_fixture()
    fixture["journal_packet"]["actions"] = [
        {
            "action_id": "submit-application",
            "action_class": "submission",
            "status": "ready_metadata_only",
        }
    ]

    problems = _problems_for_fixture(fixture)

    assert "fixture.journal_packet.actions[0] has consequential action without blocked or manual-handoff status" in problems


def test_build_e2e_readiness_digest_allows_blocked_consequential_actions() -> None:
    fixture = _base_fixture()
    fixture["journal_packet"]["actions"] = [
        {
            "action_id": "submit-application",
            "action_class": "submission",
            "status": "manual_handoff_required",
        }
    ]

    digest = build_e2e_readiness_digest(deepcopy(fixture))

    assert digest["official_readiness"] is False
    assert validate_e2e_readiness_digest(digest) == []
