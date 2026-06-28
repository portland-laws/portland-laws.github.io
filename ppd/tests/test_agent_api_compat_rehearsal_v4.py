from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.agent_api_compat_rehearsal_v4 import (
    assert_valid_agent_api_compatibility_rehearsal_v4,
    load_rehearsal_fixture,
    validate_agent_api_compatibility_rehearsal_v4,
)


FIXTURE = Path(__file__).parent / "fixtures" / "agent_api_compat_rehearsal_v4_valid.json"


def valid_payload() -> dict:
    return load_rehearsal_fixture(FIXTURE)


def assert_rejected(payload: dict, expected: str) -> None:
    errors = validate_agent_api_compatibility_rehearsal_v4(payload)
    assert any(expected in error for error in errors), errors


def test_valid_rehearsal_fixture_is_accepted() -> None:
    assert validate_agent_api_compatibility_rehearsal_v4(valid_payload()) == []
    assert_valid_agent_api_compatibility_rehearsal_v4(valid_payload())


@pytest.mark.parametrize(
    "key, expected",
    [
        ("monitoring_rehearsal_references", "missing non-empty monitoring_rehearsal_references"),
        ("synthetic_agent_request_fixtures", "missing non-empty synthetic_agent_request_fixtures"),
        ("expected_api_response_rows", "missing non-empty expected_api_response_rows"),
        ("source_citation_payloads", "missing non-empty source_citation_payloads"),
        ("validation_commands", "missing non-empty validation_commands"),
    ],
)
def test_rejects_missing_required_fixture_sections(key: str, expected: str) -> None:
    payload = valid_payload()
    payload[key] = []
    assert_rejected(payload, expected)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_fact",
        "stale_evidence",
        "reversible_draft_only",
        "manual_handoff",
        "refusal_explanation",
    ],
)
def test_rejects_missing_required_response_handling(kind: str) -> None:
    payload = valid_payload()
    payload["response_scenarios"] = [item for item in payload["response_scenarios"] if item["kind"] != kind]
    assert_rejected(payload, f"missing {kind} response handling")


def test_rejects_malformed_validation_command_rows() -> None:
    payload = valid_payload()
    payload["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]
    assert_rejected(payload, "validation_commands[0] must be a non-empty list of strings")


@pytest.mark.parametrize(
    "patch, expected",
    [
        ({"session_file": "devhub.json"}, "private/session/auth artifact"),
        ({"auth_token": "secret"}, "private/session/auth artifact"),
        ({"trace_path": "trace.zip"}, "private/session/auth artifact"),
        ({"raw_crawl_output": "crawl.ndjson"}, "private/session/auth artifact"),
        ({"safety": {"mutates_live_systems": True}}, "active mutation flag"),
        ({"safety": {"live_submit": True}}, "active mutation flag"),
        ({"safety": {"autonomous_official_action": True}}, "autonomous official-action claim"),
        ({"safety": {"legal_guarantee": True}}, "legal or permitting guarantee"),
        ({"safety": {"permitting_guarantee": True}}, "legal or permitting guarantee"),
        ({"note": "This permit will be approved."}, "legal or permitting guarantee"),
        ({"note": "I filed the permit for you."}, "autonomous official-action claim"),
    ],
)
def test_rejects_prohibited_artifacts_claims_guarantees_and_mutations(patch: dict, expected: str) -> None:
    payload = valid_payload()
    merged = copy.deepcopy(payload)
    _deep_update(merged, patch)
    assert_rejected(merged, expected)


def test_assert_valid_raises_with_actionable_message() -> None:
    payload = valid_payload()
    payload["source_citation_payloads"] = []
    with pytest.raises(ValueError, match="source_citation_payloads"):
        assert_valid_agent_api_compatibility_rehearsal_v4(payload)


def _deep_update(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
