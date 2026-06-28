from __future__ import annotations

from ppd.devhub_readonly_drift_validation import (
    assert_valid_devhub_readonly_surface_drift_packet,
    validate_devhub_readonly_surface_drift_packet,
)


def _base_packet() -> dict[str, object]:
    return {
        "packet_type": "devhub_readonly_surface_drift_comparison",
        "reviewer_owner": "ppd-reviewer",
        "drift_claims": [
            {
                "claim": "The public permit search label changed.",
                "citations": ["https://www.portland.gov/ppd/public-source"],
            }
        ],
        "deferrals": [
            {"item": "authenticated-only account dashboard", "reason": "requires a user session and is outside read-only public scope"}
        ],
        "registry_mutation_enabled": False,
        "allow_submit": False,
    }


def _codes(packet: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_devhub_readonly_surface_drift_packet(packet)}


def test_accepts_minimal_public_readonly_packet() -> None:
    assert validate_devhub_readonly_surface_drift_packet(_base_packet()) == []
    assert_valid_devhub_readonly_surface_drift_packet(_base_packet())


def test_rejects_uncited_drift_claims() -> None:
    packet = _base_packet()
    packet["drift_claims"] = [{"claim": "A visible heading changed."}]
    assert "uncited_drift_claim" in _codes(packet)


def test_rejects_private_session_artifacts_and_raw_authenticated_values() -> None:
    packet = _base_packet()
    packet["evidence"] = {
        "storage_state": {"cookies": []},
        "Authorization": "Bearer abcdefghijklmnopqrstuvwxyz",
    }
    codes = _codes(packet)
    assert "private_or_session_artifact" in codes
    assert "raw_authenticated_value" in codes


def test_rejects_local_private_paths_and_live_browser_claims() -> None:
    packet = _base_packet()
    packet["notes"] = [
        "Saved trace to /home/alex/.config/devhub/session.zip",
        "Playwright executed a browser click against DevHub.",
    ]
    codes = _codes(packet)
    assert "local_private_path" in codes
    assert "live_browser_execution_claim" in codes


def test_rejects_registry_mutation_flags_and_consequential_actions() -> None:
    packet = _base_packet()
    packet["registry_mutation_enabled"] = True
    packet["payment_enabled"] = True
    codes = _codes(packet)
    assert "active_registry_mutation_flag" in codes
    assert "consequential_action_enabled" in codes


def test_rejects_missing_reviewer_owner_and_missing_deferral_reason() -> None:
    packet = _base_packet()
    packet["reviewer_owner"] = ""
    packet["deferrals"] = [{"item": "later review"}]
    codes = _codes(packet)
    assert "missing_reviewer_owner" in codes
    assert "missing_deferral_reason" in codes
