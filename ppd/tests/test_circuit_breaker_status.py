from pathlib import Path

import pytest

from ppd.daemon.circuit_breaker_status import (
    load_status_fixture,
    validate_paused_circuit_breaker_status,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon"
    / "circuit_breaker_paused_status.json"
)


def test_paused_circuit_breaker_fixture_records_quarantine_and_restart_boundary():
    status = load_status_fixture(FIXTURE_PATH)

    result = validate_paused_circuit_breaker_status(status)

    assert result.task_id == "checkbox-449"
    assert result.quarantine_id == "quarantine-checkbox-449-paused-daemon-fixture"
    assert result.restart_mode == "supervised_fixture_only_restart"
    assert result.source_evidence_ids == (
        "fixture:ppd-daemon-circuit-breaker-paused-v1",
    )


def test_paused_circuit_breaker_rejects_autonomous_resume_before_recovery():
    status = dict(load_status_fixture(FIXTURE_PATH))
    restart = dict(status["restart_eligibility"])
    restart["may_resume_autonomous_work"] = True
    status["restart_eligibility"] = restart

    with pytest.raises(ValueError, match="must not resume autonomous work"):
        validate_paused_circuit_breaker_status(status)


def test_paused_circuit_breaker_rejects_private_or_raw_artifact_paths():
    status = dict(load_status_fixture(FIXTURE_PATH))
    status["recorded_artifact_paths"] = [
        "ppd/data/private/devhub-session-state.json",
    ]

    with pytest.raises(ValueError, match="forbidden boundary"):
        validate_paused_circuit_breaker_status(status)


def test_paused_circuit_breaker_requires_source_safe_boundaries():
    status = dict(load_status_fixture(FIXTURE_PATH))
    recovery = dict(status["source_safe_recovery"])
    recovery["forbidden_write_prefixes"] = ["ppd/data/private/"]
    status["source_safe_recovery"] = recovery

    with pytest.raises(ValueError, match="missing forbidden write boundaries"):
        validate_paused_circuit_breaker_status(status)
