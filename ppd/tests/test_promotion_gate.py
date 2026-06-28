from __future__ import annotations

from pathlib import Path

from ppd.logic.promotion_gate import evaluate_promotion_candidate, load_promotion_fixture


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "promotion_gate" / "promotability_candidates.json"


def test_process_model_and_guardrail_bundle_with_unresolved_blockers_are_not_promotable() -> None:
    fixture = load_promotion_fixture(FIXTURE_PATH)
    expected_codes = tuple(fixture["blocked_blocker_codes"])

    for candidate in fixture["blocked_candidates"]:
        result = evaluate_promotion_candidate(candidate)

        assert candidate["promotable"] is True
        assert result.promotable is False
        assert result.blocker_codes == expected_codes
        assert result.candidate_kind in {"ProcessModel", "GuardrailBundle"}
        assert result.candidate_id != "unknown-candidate"
        assert all(blocker.message for blocker in result.blockers)


def test_resolved_process_model_and_guardrail_bundle_are_promotable() -> None:
    fixture = load_promotion_fixture(FIXTURE_PATH)

    for candidate in fixture["resolved_candidates"]:
        result = evaluate_promotion_candidate(candidate)

        assert result.promotable is True
        assert result.blockers == ()
        assert result.blocker_codes == ()
        assert result.candidate_kind in {"ProcessModel", "GuardrailBundle"}
