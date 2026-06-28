from __future__ import annotations

import json
from pathlib import Path

from ppd.fixture_first_requirement_rerun import build_requirement_rerun_work_queue_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_rerun"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_build_requirement_rerun_work_queue_packet_is_metadata_only() -> None:
    packet = build_requirement_rerun_work_queue_packet(
        _fixture("source_freshness_drift_escalation.json"),
        _fixture("requirement_rerun_disposition.json"),
        _fixture("guardrail_bundle_update_candidate.json"),
    )

    assert packet["packet_type"] == "fixture_first_requirement_rerun_work_queue"
    assert packet["cited_requirement_ids"] == ["PCC-33.110.265", "PCC-33.445.320"]
    assert packet["affected_process_refs"] == ["ppd-process:source-freshness-review", "ppd-process:requirement-rerun-review"]
    assert packet["affected_guardrail_refs"] == ["guardrail:no-live-extraction", "guardrail:no-requirement-mutation"]
    assert packet["reviewer_owner_fields"] == {
        "reviewer_owner": "requirements-review",
        "escalation_owner": "freshness-review",
        "guardrail_owner": "guardrail-review",
    }
    assert [step["step"] for step in packet["ordered_rerun_steps"]] == [1, 2, 3]
    assert all(step["live_extraction_allowed"] is False for step in packet["ordered_rerun_steps"])
    assert all(step["processor_invocation_allowed"] is False for step in packet["ordered_rerun_steps"])
    assert all(step["requirement_mutation_allowed"] is False for step in packet["ordered_rerun_steps"])
    assert packet["attestations"] == {
        "no_live_extraction": True,
        "no_source_fetching": True,
        "no_processor_invocation": True,
        "no_raw_archive_reads": True,
        "no_requirement_record_mutation": True,
        "metadata_only_outputs": True,
    }
    assert packet["expected_outputs"] == [
        "metadata_only_requirement_rerun_packet",
        "metadata_only_reviewer_disposition",
        "metadata_only_guardrail_reference_update_candidate",
    ]
