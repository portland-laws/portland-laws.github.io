from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.pilot_runbook_validation import (
    assert_devhub_attended_read_only_pilot_runbook,
    validate_devhub_attended_read_only_pilot_runbook,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_pilot_runbooks"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_attended_read_only_pilot_packet_allows_explicit_refusals() -> None:
    packet = _load_fixture("valid_attended_read_only_packet.json")

    result = validate_devhub_attended_read_only_pilot_runbook(packet)

    assert result.ok, result.issues
    assert_devhub_attended_read_only_pilot_runbook(packet)


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ({"steps": ["Use Playwright to automate login after opening DevHub."]}, "automated login"),
        ({"steps": ["Solve MFA prompts with the worker when they appear."]}, "MFA automation"),
        ({"steps": ["Bypass CAPTCHA before recording the surface map."]}, "CAPTCHA automation"),
        ({"steps": ["Create an account for the pilot user if sign in fails."]}, "account creation"),
        ({"steps": ["Prompt the user for their password and enter it."]}, "credential prompts"),
        ({"cookies": [{"name": "sid", "value": "abc"}]}, "cookies"),
        ({"auth_state_path": "state/devhub.json"}, "auth state"),
        ({"screenshots": ["devhub-home.png"]}, "screenshots"),
        ({"trace_path": "trace.zip"}, "traces"),
        ({"har_path": "network.har"}, "HAR data"),
        ({"fields": {"applicant_email": "person@example.test"}}, "private field values"),
        ({"steps": ["Click submit payment to finish the permit purchase."]}, "consequential controls"),
        ({"claims": ["Live authenticated capture already completed successfully."]}, "claims live authenticated capture occurred"),
    ],
)
def test_rejects_forbidden_pilot_packet_content(mutation: dict[str, object], category: str) -> None:
    packet = _load_fixture("valid_attended_read_only_packet.json")
    packet.update(mutation)

    result = validate_devhub_attended_read_only_pilot_runbook(packet)

    assert not result.ok
    assert category in {issue.category for issue in result.issues}
    with pytest.raises(ValueError):
        assert_devhub_attended_read_only_pilot_runbook(packet)


def test_rejects_wrong_packet_kind_and_mode() -> None:
    packet = _load_fixture("valid_attended_read_only_packet.json")
    packet["packet_kind"] = "devhub_authenticated_capture"
    packet["mode"] = "unattended_live_capture"

    result = validate_devhub_attended_read_only_pilot_runbook(packet)

    assert not result.ok
    assert {issue.path for issue in result.issues} >= {"packet_kind", "mode"}
