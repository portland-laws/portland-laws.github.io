from pathlib import Path
from typing import Any

import pytest

from ppd.agent_api_compatibility_matrix_v6 import (
    CompatibilityMatrixError,
    build_matrix,
    default_fixture_paths,
    default_matrix,
    load_fixture,
    validate_matrix,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_api_compatibility_matrix_v6"


def test_default_matrix_uses_only_inactive_committed_fixtures() -> None:
    matrix = default_matrix()

    assert matrix["matrix_id"] == "ppd_agent_api_compatibility_matrix_v6"
    assert matrix["version"] == 6
    assert matrix["source_policy"] == "fixture_first_committed_inactive_replay_only"
    assert matrix["fixture_ids"] == [
        "inactive-rollback-drill-agent-api-v6",
        "inactive-smoke-replay-agent-api-v6",
    ]
    assert matrix["smoke_replay_fixture_refs"] == ["inactive-smoke-replay-agent-api-v6"]
    assert matrix["rollback_drill_fixture_refs"] == ["inactive-rollback-drill-agent-api-v6"]
    assert matrix["validation_commands"] == matrix["offline_validation_commands"]
    assert "open_devhub" in matrix["prohibited_runtime_behaviors"]
    assert "crawl_live_sites" in matrix["prohibited_runtime_behaviors"]
    assert "submit_certify_or_upload" in matrix["prohibited_runtime_behaviors"]


def test_matrix_summarizes_required_agent_compatibility_categories() -> None:
    matrix = build_matrix(default_fixture_paths())

    assert "List missing user facts before drafting any PP&D form values." in matrix["supported_agent_queries"]
    assert "official_submission" in matrix["blocked_action_classes"]
    assert "fee_payment" in matrix["blocked_action_classes"]
    assert any("stale" in item for item in matrix["stale_evidence_behavior"])
    assert any("permit type" in item for item in matrix["missing_information_prompts"])
    assert any("Must stop before certification" in item for item in matrix["reversible_draft_boundaries"])
    assert any("Must not upload" in item for item in matrix["local_pdf_preview_boundaries"])
    assert any("Before certification" in item for item in matrix["exact_confirmation_checkpoints"])
    assert any("DevHub login" in item for item in matrix["manual_handoff_surfaces"])
    assert ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"] in matrix["offline_validation_commands"]


@pytest.mark.parametrize(
    "key",
    [
        "smoke_replay_fixture_refs",
        "rollback_drill_fixture_refs",
        "supported_agent_queries",
        "blocked_action_classes",
        "stale_evidence_behavior",
        "missing_information_prompts",
        "reversible_draft_boundaries",
        "local_pdf_preview_boundaries",
        "exact_confirmation_checkpoints",
        "manual_handoff_surfaces",
        "offline_validation_commands",
        "validation_commands",
    ],
)
def test_matrix_validation_rejects_missing_required_sections(key: str) -> None:
    matrix = default_matrix()
    matrix[key] = []

    with pytest.raises(CompatibilityMatrixError):
        validate_matrix(matrix)


@pytest.mark.parametrize(
    "key,value",
    [
        ("active_activation", True),
        ("live_crawl_executed", True),
        ("devhub_session", "redacted-session-value"),
        ("official_action_completed", True),
        ("mutates_active_guardrails", True),
    ],
)
def test_matrix_validation_rejects_active_live_private_official_and_mutation_flags(key: str, value: Any) -> None:
    matrix = default_matrix()
    matrix[key] = value

    with pytest.raises(CompatibilityMatrixError):
        validate_matrix(matrix)


@pytest.mark.parametrize(
    "claim",
    [
        "active activation complete",
        "executed live crawl",
        "submitted to DevHub",
        "uploaded to official record",
        "permit guaranteed",
        "legal guarantee",
    ],
)
def test_matrix_validation_rejects_prohibited_claim_text(claim: str) -> None:
    matrix = default_matrix()
    matrix["reviewer_notes"] = [claim]

    with pytest.raises(CompatibilityMatrixError):
        validate_matrix(matrix)


def test_fixture_loader_rejects_active_or_live_fixture_markers(tmp_path: Path) -> None:
    fixture_path = tmp_path / "active_fixture.json"
    fixture_path.write_text(
        """
        {
          "fixture_id": "bad-active-fixture",
          "fixture_class": "inactive_smoke_replay",
          "status": "active",
          "source_scope": "committed_offline_fixture_only",
          "agent_queries": ["Open DevHub with a devhub_session."],
          "blocked_action_classes": ["official_submission"],
          "stale_evidence_behavior": ["Hold stale evidence."],
          "missing_information_prompts": ["Ask for permit type."],
          "reversible_draft_boundaries": ["Stop before submission."],
          "local_pdf_preview_boundaries": ["Do not upload."],
          "exact_confirmation_checkpoints": ["Before official action."],
          "manual_handoff_surfaces": ["DevHub login."],
          "offline_validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(CompatibilityMatrixError):
        load_fixture(fixture_path)


def test_fixture_loader_rejects_empty_required_rows(tmp_path: Path) -> None:
    fixture_path = tmp_path / "empty_rows_fixture.json"
    fixture_path.write_text(
        """
        {
          "fixture_id": "bad-empty-fixture",
          "fixture_class": "inactive_smoke_replay",
          "status": "inactive",
          "source_scope": "committed_offline_fixture_only",
          "agent_queries": [],
          "blocked_action_classes": ["official_submission"],
          "stale_evidence_behavior": ["Hold stale evidence."],
          "missing_information_prompts": ["Ask for permit type."],
          "reversible_draft_boundaries": ["Stop before submission."],
          "local_pdf_preview_boundaries": ["Do not upload."],
          "exact_confirmation_checkpoints": ["Before official action."],
          "manual_handoff_surfaces": ["DevHub login."],
          "offline_validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(CompatibilityMatrixError):
        load_fixture(fixture_path)


def test_matrix_requires_both_fixture_classes() -> None:
    with pytest.raises(CompatibilityMatrixError):
        build_matrix([FIXTURE_DIR / "inactive_smoke_replay.json"])
