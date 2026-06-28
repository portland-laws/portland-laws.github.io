from pathlib import Path

import pytest

from ppd.contracts.devhub_attended_login import (
    AttendedDevHubLoginContract,
    DevHubLoginState,
)


def fixture_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "devhub_attended_login" / name


def test_manual_login_detection_uses_local_fixture() -> None:
    contract = AttendedDevHubLoginContract()
    html = fixture_path("manual_sign_in.html").read_text(encoding="utf-8")

    state = contract.state_from_observation(
        "https://www.portlandoregon.gov/DevHub/Account/Login",
        html,
        200,
    )

    assert state is DevHubLoginState.MANUAL_SIGN_IN_REQUIRED
    assert not contract.can_save_resume(state)


def test_authenticated_save_resume_detection_uses_local_fixture() -> None:
    contract = AttendedDevHubLoginContract()
    html = fixture_path("save_resume.html").read_text(encoding="utf-8")

    state = contract.state_from_observation(
        "https://www.portlandoregon.gov/DevHub/Permits/Draft?id=123",
        html,
        200,
    )

    assert state is DevHubLoginState.SAVE_RESUME_READY
    assert contract.can_save_resume(state)


def test_route_snapshot_redacts_query_values_and_fragments() -> None:
    contract = AttendedDevHubLoginContract()

    snapshot = contract.redacted_route_snapshot(
        "https://www.portlandoregon.gov/DevHub/Callback?code=abc123&recordId=RSW-1#token=hidden",
        method="post",
        html_text="My Account Save and Resume",
        status_code=200,
    )

    assert snapshot.method == "POST"
    assert snapshot.status_code == 200
    assert snapshot.state is DevHubLoginState.SAVE_RESUME_READY
    assert snapshot.url == "https://www.portlandoregon.gov/DevHub/Callback?code=REDACTED&recordId=VALUE"


def test_external_routes_are_blocked_and_not_snapshotted() -> None:
    contract = AttendedDevHubLoginContract()

    snapshot = contract.redacted_route_snapshot("https://example.com/login?token=abc")

    assert snapshot.state is DevHubLoginState.BLOCKED
    assert snapshot.url == "blocked://external-route"


def test_unsafe_metadata_fields_are_rejected() -> None:
    contract = AttendedDevHubLoginContract()

    with pytest.raises(ValueError):
        contract.assert_safe_metadata({"storage_state": "never-write-this"})


def test_safe_route_metadata_is_allowed() -> None:
    contract = AttendedDevHubLoginContract()

    contract.assert_safe_metadata(
        {
            "route": "/DevHub/Permits/Draft",
            "status_code": 200,
            "login_state": DevHubLoginState.AUTHENTICATED.value,
        }
    )
