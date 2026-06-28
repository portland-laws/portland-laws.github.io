from pathlib import Path

from ppd.logic.guardrail_promotion_gate import PromotionCheck, run_guardrail_promotion_gate


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrail_promotion_gate" / "candidate_guardrail_bundle.json"


def test_promotion_gate_promotes_when_all_fixture_validators_pass():
    result = run_guardrail_promotion_gate(
        FIXTURE_PATH,
        {
            "has_bundle_id": lambda fixture: bool(fixture.get("guardrail_bundle_id")),
            "has_process_id": lambda fixture: (
                bool(fixture.get("process_id")),
                "candidate includes a process id",
                ["process_id"],
            ),
            "uses_source_evidence": lambda fixture: {
                "passed": bool(fixture.get("source_evidence_ids")),
                "message": "candidate has source evidence ids",
                "evidence": fixture.get("source_evidence_ids", []),
            },
        },
    )

    assert result.promoted is True
    assert result.failures == ()
    assert result.to_dict()["promoted"] is True


def test_promotion_gate_blocks_when_any_validator_fails():
    result = run_guardrail_promotion_gate(
        FIXTURE_PATH,
        [lambda fixture: PromotionCheck("manual_review_complete", False, "fixture remains candidate-only")],
    )

    assert result.promoted is False
    assert [failure.name for failure in result.failures] == ["manual_review_complete"]


def test_promotion_gate_requires_at_least_one_validator():
    result = run_guardrail_promotion_gate(FIXTURE_PATH, [])

    assert result.promoted is False
    assert result.failures[0].name == "validators_present"
