import json
from pathlib import Path

import pytest

from ppd.logic.evidence_packet import assemble_evidence_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "evidence_pack" / "fixture_first_records.json"
FORBIDDEN_STRINGS = (
    "BEGIN PRIVATE DEVHUB VALUE",
    "devhub_private_value",
    "raw body that must never appear",
    "storageState",
    "Set-Cookie",
    "Authorization:",
    "trace.zip",
    "screenshot.png",
    "capture.har",
    "/home/barberb/private",
    "C:\\Users\\Owner\\private",
)
FORBIDDEN_KEYS = {
    "raw_body",
    "raw_html",
    "raw_text",
    "body",
    "html",
    "devhub_private_values",
    "auth_state",
    "storage_state",
    "cookies",
    "token",
    "authorization",
    "screenshot",
    "trace",
    "har",
    "local_path",
    "download_path",
}


def test_fixture_first_agent_evidence_packet_is_complete_and_sanitized():
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    packet = assemble_evidence_packet(records)
    encoded = json.dumps(packet, sort_keys=True)

    assert packet["schema_version"] == "ppd.agent_evidence_packet.v1"
    assert packet["source_registry"] == [
        {
            "source_id": "src-devhub-guide-submit-application",
            "canonical_url": "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
            "source_type": "devhub_public",
            "owning_surface": "Portland PP&D",
            "allowlist_policy": "allowed_official_public_source",
            "robots_policy": "respect_robots_before_live_fetch",
            "privacy_classification": "public",
            "freshness_status": "fixture-current",
        }
    ]
    assert packet["archive_manifests"][0]["manifest_id"] == "arc-devhub-guide-submit-application-20260508"
    assert packet["archive_manifests"][0]["no_raw_body_persisted"] is True

    requirement = packet["requirements"][0]
    assert requirement["requirement_id"] == "req-upload-staging-before-certification"
    assert requirement["source_evidence_ids"] == ["ev-devhub-guide-upload-staging", "ev-devhub-guide-certification-gate"]
    assert [citation["citation_span_id"] for citation in requirement["citations"]] == [
        "span-upload-staging",
        "span-certification-gate",
    ]
    assert all("quote" not in citation for citation in requirement["citations"])

    process = packet["process_models"][0]
    assert process["process_id"] == "proc-building-permit-devhub-plan-review"
    assert process["guardrail_bundle_id"] == "grd-building-permit-devhub-plan-review"

    guardrail = packet["guardrail_bundles"][0]
    assert guardrail["guardrail_bundle_id"] == "grd-building-permit-devhub-plan-review"
    assert guardrail["process_id"] == process["process_id"]
    assert guardrail["exact_confirmation_predicate_ids"] == ["pred-certification-requires-exact-confirmation"]

    action = packet["next_safe_actions"][0]
    assert action == {
        "action_id": "nsa-review-upload-checklist",
        "process_id": "proc-building-permit-devhub-plan-review",
        "guardrail_bundle_id": "grd-building-permit-devhub-plan-review",
        "label": "Review missing upload checklist facts before any DevHub submission step",
        "action_class": "safe_read_only",
        "allowed": True,
        "requires_attendance": False,
        "requires_exact_confirmation": False,
        "blocked_reason": "",
        "supporting_requirement_ids": ["req-upload-staging-before-certification"],
    }

    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in encoded
    assert not _contains_forbidden_key(packet)


def test_assembler_rejects_forbidden_material_if_present_in_output_shaped_data():
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    records["next_safe_actions"][0]["label"] = "Open /home/barberb/private/devhub-capture.har"

    with pytest.raises(ValueError, match="forbidden material"):
        assemble_evidence_packet(records)


def _contains_forbidden_key(value):
    if isinstance(value, dict):
        return any(key.lower() in FORBIDDEN_KEYS or _contains_forbidden_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(child) for child in value)
    return False
