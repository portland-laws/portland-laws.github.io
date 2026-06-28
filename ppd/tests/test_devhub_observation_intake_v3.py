from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub_observation_intake_v3 import (
    IntakeError,
    build_observation_rows,
    validate_observation_rows,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_observation_intake_v3"


def _load_fixture(name: str):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_builds_expected_redacted_observation_rows_from_synthetic_checklist_rows() -> None:
    checklist_rows = _load_fixture("synthetic_checklist_rows.json")
    expected_rows = _load_fixture("expected_observation_rows_v3.json")

    observation_rows = build_observation_rows(checklist_rows)

    assert observation_rows == expected_rows
    validate_observation_rows(observation_rows)


def test_rejects_non_synthetic_rows() -> None:
    checklist_rows = _load_fixture("synthetic_checklist_rows.json")
    checklist_rows[0]["synthetic"] = False

    with pytest.raises(IntakeError, match="must be synthetic"):
        build_observation_rows(checklist_rows)


def test_rejects_private_or_live_artifact_fields() -> None:
    checklist_rows = _load_fixture("synthetic_checklist_rows.json")
    checklist_rows[0]["session_cookie"] = "redacted session artifact still forbidden"

    with pytest.raises(IntakeError, match="forbidden fields"):
        build_observation_rows(checklist_rows)


def test_rejects_live_action_language_inside_hints() -> None:
    checklist_rows = _load_fixture("synthetic_checklist_rows.json")
    checklist_rows[0]["read_only_action_label_hints"] = ["submit now"]

    with pytest.raises(IntakeError, match="private or live-action"):
        build_observation_rows(checklist_rows)
