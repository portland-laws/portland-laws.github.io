from pathlib import Path

import pytest

from ppd.devhub.exact_confirmation_checkpoints import (
    EXPECTED_BOUNDARIES,
    load_checkpoint_fixtures,
    validate_checkpoint_fixtures,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "exact_confirmation_checkpoints.json"


def test_exact_confirmation_fixture_covers_required_boundaries() -> None:
    checkpoints = load_checkpoint_fixtures(FIXTURE_PATH)

    assert {checkpoint.boundary for checkpoint in checkpoints} == set(EXPECTED_BOUNDARIES)
    assert len(checkpoints) == len(EXPECTED_BOUNDARIES)


def test_exact_confirmation_checkpoints_are_manual_and_non_automating() -> None:
    checkpoints = load_checkpoint_fixtures(FIXTURE_PATH)

    for checkpoint in checkpoints:
        assert checkpoint.manual_handoff is True
        assert checkpoint.required_confirmation_text.startswith("CONFIRM ")
        assert checkpoint.accepts_confirmation(checkpoint.required_confirmation_text)
        assert not checkpoint.accepts_confirmation(checkpoint.required_confirmation_text.lower())
        assert checkpoint.allowed_before_confirmation
        assert "manual_handoff" in checkpoint.allowed_before_confirmation
        assert checkpoint.blocked_without_confirmation
        assert checkpoint.prohibited_automation
        assert not any(action.startswith("auto_") for action in checkpoint.allowed_before_confirmation)


def test_boundary_specific_blocked_actions_are_declared() -> None:
    checkpoints = {checkpoint.boundary: checkpoint for checkpoint in load_checkpoint_fixtures(FIXTURE_PATH)}

    assert checkpoints["acknowledgement_certification"].blocks("check certification box")
    assert checkpoints["official_upload"].blocks("click_upload")
    assert checkpoints["submission"].blocks("click-submit-application")
    assert checkpoints["scheduling"].blocks("submit inspection request")
    assert checkpoints["cancellation"].blocks("confirm_cancellation")
    assert checkpoints["extension_reactivation"].blocks("submit-reactivation-request")
    assert checkpoints["payment"].blocks("enter payment details")


def test_fixture_validation_rejects_missing_boundary() -> None:
    checkpoints = list(load_checkpoint_fixtures(FIXTURE_PATH))
    incomplete = [checkpoint for checkpoint in checkpoints if checkpoint.boundary != "payment"]

    with pytest.raises(ValueError, match="unexpected checkpoint boundaries"):
        validate_checkpoint_fixtures(incomplete)
