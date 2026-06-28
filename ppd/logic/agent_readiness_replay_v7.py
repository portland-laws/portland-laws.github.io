"""Fixture-first post-recompile agent readiness replay v7.

This module is intentionally side-effect free. It consumes committed PP&D test
fixtures only and returns deterministic agent-facing readiness responses for the
post-recompile guardrail reviewer packet flow.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

_ALLOWED_FIXTURE_KINDS = {
    "guardrail_recompile_reviewer_packet_v7",
    "inactive_guardrail_staging_v7",
}

_REQUIRED_SCENARIOS = (
    "missing_information",
    "stale_evidence_stop",
    "reversible_draft",
    "local_pdf_preview",
    "exact_confirmation_checkpoint",
    "refused_consequential_action",
    "refused_financial_action",
    "rollback_visibility",
    "source_citation_explanation",
    "manual_handoff",
)

_PROHIBITED_EFFECTS = (
    "activate_guardrails",
    "open_devhub",
    "crawl_live_sites",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantee",
)

_EXPECTED_ACTIONS = {
    "missing_information": "ask_missing_information",
    "stale_evidence_stop": "stop_for_stale_evidence",
    "reversible_draft": "prepare_reversible_draft",
    "local_pdf_preview": "show_local_pdf_preview",
    "exact_confirmation_checkpoint": "request_exact_confirmation",
    "refused_consequential_action": "refuse_consequential_action",
    "refused_financial_action": "refuse_financial_action",
    "rollback_visibility": "explain_rollback_visibility",
    "source_citation_explanation": "explain_with_source_citations",
    "manual_handoff": "manual_handoff",
}


class ReplayFixtureError(ValueError):
    """Raised when replay fixtures are incomplete or unsafe."""


@dataclass(frozen=True)
class ReplayCaseResult:
    scenario: str
    action: str
    status: str
    message: str
    citations: List[str]
    validation_command: List[str]


@dataclass(frozen=True)
class ReplayReport:
    replay_id: str
    offline_only: bool
    guardrails_activated: bool
    cases: List[ReplayCaseResult]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "offline_only": self.offline_only,
            "guardrails_activated": self.guardrails_activated,
            "cases": [case.__dict__ for case in self.cases],
        }


def load_replay_fixtures(paths: Sequence[Path]) -> List[Dict[str, Any]]:
    """Load replay fixtures from explicit local paths.

    The caller supplies committed fixture paths. No network, browser, DevHub,
    private-document, upload, payment, or scheduling side effects are performed.
    """

    fixtures: List[Dict[str, Any]] = []
    for path in paths:
        fixture_path = Path(path)
        with fixture_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ReplayFixtureError(f"fixture must be an object: {fixture_path}")
        loaded["_fixture_path"] = str(fixture_path)
        fixtures.append(loaded)
    return fixtures


def replay_agent_readiness_v7(fixtures: Sequence[Mapping[str, Any]]) -> ReplayReport:
    """Replay agent readiness responses from v7 fixtures only."""

    _validate_fixture_set(fixtures)
    cases_by_scenario: Dict[str, Mapping[str, Any]] = {}
    for fixture in fixtures:
        for case in _iter_cases(fixture):
            scenario = _required_string(case, "scenario")
            cases_by_scenario[scenario] = case

    results = [_evaluate_case(cases_by_scenario[scenario]) for scenario in _REQUIRED_SCENARIOS]
    return ReplayReport(
        replay_id="post-recompile-agent-readiness-replay-v7",
        offline_only=True,
        guardrails_activated=False,
        cases=results,
    )


def _validate_fixture_set(fixtures: Sequence[Mapping[str, Any]]) -> None:
    if not fixtures:
        raise ReplayFixtureError("at least one replay fixture is required")

    fixture_kinds = {_required_string(fixture, "fixture_kind") for fixture in fixtures}
    disallowed_kinds = sorted(fixture_kinds - _ALLOWED_FIXTURE_KINDS)
    if disallowed_kinds:
        raise ReplayFixtureError(f"disallowed fixture kinds: {disallowed_kinds}")

    for fixture in fixtures:
        effects = fixture.get("prohibited_effects", [])
        if not isinstance(effects, list):
            raise ReplayFixtureError("prohibited_effects must be a list")
        missing_effects = sorted(set(_PROHIBITED_EFFECTS) - set(effects))
        if missing_effects:
            raise ReplayFixtureError(f"fixture is missing prohibited effects: {missing_effects}")
        if fixture.get("guardrails_active") is not False:
            raise ReplayFixtureError("replay requires inactive guardrail fixtures")
        if fixture.get("offline_only") is not True:
            raise ReplayFixtureError("replay fixtures must be marked offline_only")

    scenarios = {case.get("scenario") for fixture in fixtures for case in _iter_cases(fixture)}
    missing_scenarios = [scenario for scenario in _REQUIRED_SCENARIOS if scenario not in scenarios]
    if missing_scenarios:
        raise ReplayFixtureError(f"missing replay scenarios: {missing_scenarios}")


def _iter_cases(fixture: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    cases = fixture.get("cases", [])
    if not isinstance(cases, list):
        raise ReplayFixtureError("fixture cases must be a list")
    for case in cases:
        if not isinstance(case, dict):
            raise ReplayFixtureError("each replay case must be an object")
        yield case


def _evaluate_case(case: Mapping[str, Any]) -> ReplayCaseResult:
    scenario = _required_string(case, "scenario")
    expected_action = _EXPECTED_ACTIONS[scenario]
    action = _required_string(case, "agent_action")
    if action != expected_action:
        raise ReplayFixtureError(f"{scenario} expected {expected_action}, got {action}")

    blocked_effects = case.get("blocked_effects", [])
    if not isinstance(blocked_effects, list):
        raise ReplayFixtureError(f"{scenario} blocked_effects must be a list")
    unexpected_effects = sorted(set(blocked_effects) - set(_PROHIBITED_EFFECTS))
    if unexpected_effects:
        raise ReplayFixtureError(f"{scenario} has unknown blocked effects: {unexpected_effects}")

    citations = case.get("citations", [])
    if not isinstance(citations, list) or not citations:
        raise ReplayFixtureError(f"{scenario} requires at least one source citation")
    citation_strings = [_require_string_value(citation, f"{scenario} citation") for citation in citations]

    validation_command = case.get("validation_command")
    if not _is_offline_validation_command(validation_command):
        raise ReplayFixtureError(f"{scenario} requires an exact offline validation command")

    return ReplayCaseResult(
        scenario=scenario,
        action=action,
        status=_required_string(case, "status"),
        message=_required_string(case, "agent_response"),
        citations=citation_strings,
        validation_command=list(validation_command),
    )


def _is_offline_validation_command(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not all(isinstance(part, str) and part for part in value):
        return False
    forbidden_tokens = {
        "curl",
        "wget",
        "playwright",
        "npm",
        "pnpm",
        "devhub",
        "upload",
        "submit",
        "pay",
        "schedule",
    }
    lowered = {part.lower() for part in value}
    return lowered.isdisjoint(forbidden_tokens)


def _required_string(mapping: Mapping[str, Any], key: str) -> str:
    return _require_string_value(mapping.get(key), key)


def _require_string_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReplayFixtureError(f"{label} must be a non-empty string")
    return value
