"""Fixture-first PP&D safe-action freshness regression packets.

This module consumes already-redacted packet fixtures and produces cited stale
source scenarios for agent regression review. It never calls an LLM, opens
DevHub, mutates prompts, or mutates guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


PACKET_TYPE = "ppd.safe_action_freshness_regression_packet.v1"
_REQUIRED_ATTESTATIONS = {
    "no_live_llm": True,
    "no_devhub": True,
    "no_prompt_mutation": True,
    "no_guardrail_mutation": True,
}
_STALE_STATUSES = {"stale", "stale_requires_review", "expired", "needs_review"}
_CONSEQUENTIAL_TERMS = ("submit", "upload", "pay", "payment", "schedule", "cancel", "withdraw", "certif")
_PRIVATE_KEYS = {
    "auth_state",
    "cookies",
    "credentials",
    "password",
    "payment_details",
    "raw_authenticated_values",
    "session_state",
    "token",
}
_PRIVATE_TEXT_MARKERS = ("/home/", "/Users/", "C:/Users/", "file://", "auth_state", "trace.zip", ".har")


@dataclass(frozen=True)
class FreshnessRegressionIssue:
    code: str
    path: str
    message: str


class SafeActionFreshnessRegressionPacketError(ValueError):
    def __init__(self, issues: Sequence[FreshnessRegressionIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(detail or "safe-action freshness regression packet is invalid")


def build_safe_action_freshness_regression_packet(
    safe_read_only_action_transcript_packet: Mapping[str, Any],
    evidence_freshness_watchlist_reviewer_disposition_packet: Mapping[str, Any],
    agent_prompt_regression_dry_run_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a metadata-only stale-evidence regression packet from fixtures."""

    transcript_packet_id = _packet_id(safe_read_only_action_transcript_packet, "safe-read-only-action-transcript")
    watchlist_packet_id = _packet_id(evidence_freshness_watchlist_reviewer_disposition_packet, "freshness-watchlist-reviewer-disposition")
    dry_run_packet_id = _packet_id(agent_prompt_regression_dry_run_packet, "agent-prompt-regression-dry-run")
    transcript_messages = _mapping_sequence(safe_read_only_action_transcript_packet.get("messages"))
    dry_run_expectations = _expectations_by_scenario(agent_prompt_regression_dry_run_packet)

    scenarios: list[dict[str, Any]] = []
    for index, item in enumerate(_stale_watchlist_items(evidence_freshness_watchlist_reviewer_disposition_packet), start=1):
        source_evidence_ids = _string_list(item.get("source_evidence_ids") or item.get("citations"))
        transcript_matches = _messages_for_citations(transcript_messages, source_evidence_ids)
        expected_prompts = _expected_prompts(item, transcript_matches, dry_run_expectations)
        expected_refusals = _expected_refusals(item, transcript_matches, dry_run_expectations)
        blocked_explanations = _blocked_explanations(item, transcript_matches)
        scenarios.append(
            {
                "scenario_id": str(item.get("scenario_id") or item.get("watchlist_item_id") or f"stale-evidence-scenario-{index:02d}"),
                "user_scenario": str(item.get("user_scenario") or item.get("review_summary") or "User asks the agent to continue from stale PP&D evidence."),
                "stale_evidence": [
                    {
                        "source_evidence_id": evidence_id,
                        "freshness_status": str(item.get("freshness_status") or "stale_requires_review"),
                        "reviewer_disposition": str(item.get("reviewer_disposition") or item.get("disposition") or "blocked_pending_refresh"),
                    }
                    for evidence_id in source_evidence_ids
                ],
                "source_evidence_ids": source_evidence_ids,
                "expected_missing_fact_prompts": expected_prompts,
                "expected_refusals": expected_refusals,
                "blocked_action_explanations": blocked_explanations,
                "source_packet_refs": [
                    "safe_read_only_action_transcript_packet",
                    "evidence_freshness_watchlist_reviewer_disposition_packet",
                    "agent_prompt_regression_dry_run_packet",
                ],
            }
        )

    reviewer_owner_fields = _reviewer_owner_fields(
        safe_read_only_action_transcript_packet,
        evidence_freshness_watchlist_reviewer_disposition_packet,
        agent_prompt_regression_dry_run_packet,
    )
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "safe-action-freshness-regression-for-" + watchlist_packet_id,
        "fixture_first": True,
        "metadata_only": True,
        "input_packet_refs": {
            "safe_read_only_action_transcript_packet_id": transcript_packet_id,
            "evidence_freshness_watchlist_reviewer_disposition_packet_id": watchlist_packet_id,
            "agent_prompt_regression_dry_run_packet_id": dry_run_packet_id,
        },
        "stale_evidence_user_scenarios": scenarios,
        "reviewer_owner_fields": reviewer_owner_fields,
        "attestations": {
            "no_live_llm": True,
            "no_devhub": True,
            "no_prompt_mutation": True,
            "no_guardrail_mutation": True,
            "no_private_devhub_session_files": True,
            "no_auth_state": True,
            "no_traces_or_raw_crawl_output": True,
            "no_downloaded_documents": True,
        },
    }
    require_valid_safe_action_freshness_regression_packet(packet)
    return packet


def validate_safe_action_freshness_regression_packet(packet: Mapping[str, Any]) -> list[FreshnessRegressionIssue]:
    issues: list[FreshnessRegressionIssue] = []
    _scan_private_or_live_claims(packet, "$", issues)
    if packet.get("packet_type") != PACKET_TYPE:
        issues.append(FreshnessRegressionIssue("invalid_packet_type", "$.packet_type", "packet type must identify the safe-action freshness regression packet"))
    if packet.get("fixture_first") is not True or packet.get("metadata_only") is not True:
        issues.append(FreshnessRegressionIssue("not_fixture_first_metadata_only", "$", "packet must be fixture-first and metadata-only"))

    refs = packet.get("input_packet_refs")
    if not isinstance(refs, Mapping):
        issues.append(FreshnessRegressionIssue("missing_input_packet_refs", "$.input_packet_refs", "packet must cite all source packet ids"))
    else:
        for key in (
            "safe_read_only_action_transcript_packet_id",
            "evidence_freshness_watchlist_reviewer_disposition_packet_id",
            "agent_prompt_regression_dry_run_packet_id",
        ):
            if not isinstance(refs.get(key), str) or not refs.get(key):
                issues.append(FreshnessRegressionIssue("missing_input_packet_ref", f"$.input_packet_refs.{key}", "source packet id is required"))

    scenarios = _mapping_sequence(packet.get("stale_evidence_user_scenarios"))
    if not scenarios:
        issues.append(FreshnessRegressionIssue("missing_stale_evidence_user_scenarios", "$.stale_evidence_user_scenarios", "at least one stale evidence scenario is required"))
    for index, scenario in enumerate(scenarios):
        _validate_scenario(scenario, f"$.stale_evidence_user_scenarios[{index}]", issues)

    owners = _mapping_sequence(packet.get("reviewer_owner_fields"))
    if not owners:
        issues.append(FreshnessRegressionIssue("missing_reviewer_owner_fields", "$.reviewer_owner_fields", "reviewer-owner fields are required"))
    for index, owner in enumerate(owners):
        for key in ("reviewer_owner_id", "reviewer_role", "reviewer_disposition", "source_evidence_ids"):
            value = owner.get(key)
            if key == "source_evidence_ids":
                if not _string_list(value):
                    issues.append(FreshnessRegressionIssue("missing_reviewer_owner_source_evidence", f"$.reviewer_owner_fields[{index}].{key}", "reviewer owner must cite evidence"))
            elif not isinstance(value, str) or not value:
                issues.append(FreshnessRegressionIssue("missing_reviewer_owner_field", f"$.reviewer_owner_fields[{index}].{key}", "reviewer owner field is required"))

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        issues.append(FreshnessRegressionIssue("missing_attestations", "$.attestations", "required no-mutation attestations are missing"))
    else:
        for key, expected in _REQUIRED_ATTESTATIONS.items():
            if attestations.get(key) is not expected:
                issues.append(FreshnessRegressionIssue("missing_no_mutation_attestation", f"$.attestations.{key}", "required attestation must be true"))
    return issues


def require_valid_safe_action_freshness_regression_packet(packet: Mapping[str, Any]) -> None:
    issues = validate_safe_action_freshness_regression_packet(packet)
    if issues:
        raise SafeActionFreshnessRegressionPacketError(issues)


def _validate_scenario(scenario: Mapping[str, Any], path: str, issues: list[FreshnessRegressionIssue]) -> None:
    if not isinstance(scenario.get("scenario_id"), str) or not scenario.get("scenario_id"):
        issues.append(FreshnessRegressionIssue("missing_scenario_id", f"{path}.scenario_id", "scenario id is required"))
    if not isinstance(scenario.get("user_scenario"), str) or not scenario.get("user_scenario"):
        issues.append(FreshnessRegressionIssue("missing_user_scenario", f"{path}.user_scenario", "user scenario text is required"))
    if not _string_list(scenario.get("source_evidence_ids")):
        issues.append(FreshnessRegressionIssue("uncited_stale_scenario", f"{path}.source_evidence_ids", "scenario must cite stale source evidence"))
    stale = _mapping_sequence(scenario.get("stale_evidence"))
    if not stale:
        issues.append(FreshnessRegressionIssue("missing_stale_evidence", f"{path}.stale_evidence", "scenario must name stale evidence"))
    for index, item in enumerate(stale):
        status = str(item.get("freshness_status") or "").lower()
        if status not in _STALE_STATUSES:
            issues.append(FreshnessRegressionIssue("stale_evidence_not_marked_stale", f"{path}.stale_evidence[{index}].freshness_status", "stale evidence must carry a stale review status"))
        if not item.get("reviewer_disposition"):
            issues.append(FreshnessRegressionIssue("missing_reviewer_disposition", f"{path}.stale_evidence[{index}].reviewer_disposition", "reviewer disposition is required"))
    prompts = _mapping_sequence(scenario.get("expected_missing_fact_prompts"))
    refusals = _mapping_sequence(scenario.get("expected_refusals"))
    if not prompts and not refusals:
        issues.append(FreshnessRegressionIssue("missing_expected_prompt_or_refusal", path, "scenario must include expected missing-fact prompts or refusals"))
    for index, prompt in enumerate(prompts):
        if not prompt.get("fact_id") or not prompt.get("prompt") or not _string_list(prompt.get("source_evidence_ids")):
            issues.append(FreshnessRegressionIssue("invalid_missing_fact_prompt", f"{path}.expected_missing_fact_prompts[{index}]", "missing-fact prompts require fact id, prompt text, and citations"))
    for index, refusal in enumerate(refusals):
        if not refusal.get("action") or not refusal.get("refusal") or not _string_list(refusal.get("source_evidence_ids")):
            issues.append(FreshnessRegressionIssue("invalid_refusal", f"{path}.expected_refusals[{index}]", "refusals require action, refusal text, and citations"))
    explanations = _mapping_sequence(scenario.get("blocked_action_explanations"))
    if not explanations:
        issues.append(FreshnessRegressionIssue("missing_blocked_action_explanations", f"{path}.blocked_action_explanations", "blocked-action explanations are required"))
    for index, explanation in enumerate(explanations):
        if not explanation.get("action") or not explanation.get("explanation") or not _string_list(explanation.get("source_evidence_ids")):
            issues.append(FreshnessRegressionIssue("invalid_blocked_action_explanation", f"{path}.blocked_action_explanations[{index}]", "blocked explanations require action, text, and citations"))


def _stale_watchlist_items(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates = packet.get("watchlist_reviewer_dispositions") or packet.get("reviewer_dispositions") or packet.get("watchlist_items") or []
    items = []
    for item in _mapping_sequence(candidates):
        status = str(item.get("freshness_status") or item.get("status") or "").lower()
        disposition = str(item.get("reviewer_disposition") or item.get("disposition") or "").lower()
        if status in _STALE_STATUSES or "stale" in disposition or "refresh" in disposition:
            items.append(item)
    return items


def _messages_for_citations(messages: Sequence[Mapping[str, Any]], source_evidence_ids: Sequence[str]) -> list[Mapping[str, Any]]:
    citations = set(source_evidence_ids)
    result = []
    for message in messages:
        if citations.intersection(_string_list(message.get("citations"))):
            result.append(message)
    return result


def _expected_prompts(item: Mapping[str, Any], messages: Sequence[Mapping[str, Any]], dry_run_expectations: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    citations = _string_list(item.get("source_evidence_ids") or item.get("citations"))
    prompts: list[dict[str, Any]] = []
    for fact in _mapping_sequence(item.get("expected_missing_fact_prompts")):
        prompts.append(
            {
                "fact_id": str(fact.get("fact_id") or fact.get("id") or "stale_source_confirmation"),
                "prompt": str(fact.get("prompt") or "Please confirm the stale PP&D evidence before relying on it."),
                "expected_status": str(fact.get("expected_status") or "stale"),
                "source_evidence_ids": _string_list(fact.get("source_evidence_ids")) or citations,
            }
        )
    for message in messages:
        for fact in _mapping_sequence(message.get("asked_facts")):
            prompts.append(
                {
                    "fact_id": str(fact.get("fact_id") or "stale_source_confirmation"),
                    "prompt": str(fact.get("prompt") or "Please confirm the stale PP&D evidence before relying on it."),
                    "expected_status": str(fact.get("status") or "stale"),
                    "source_evidence_ids": _string_list(fact.get("citations")) or citations,
                }
            )
    dry_run = dry_run_expectations.get(str(item.get("scenario_id") or item.get("watchlist_item_id") or ""))
    for fact in _mapping_sequence((dry_run or {}).get("expected_missing_fact_prompts")):
        prompts.append(
            {
                "fact_id": str(fact.get("fact_id") or "dry_run_missing_fact"),
                "prompt": str(fact.get("prompt") or "Ask for the cited stale fact before proceeding."),
                "expected_status": str(fact.get("expected_status") or "stale"),
                "source_evidence_ids": _string_list(fact.get("source_evidence_ids")) or citations,
            }
        )
    return _dedupe_dicts(prompts, "fact_id")


def _expected_refusals(item: Mapping[str, Any], messages: Sequence[Mapping[str, Any]], dry_run_expectations: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    citations = _string_list(item.get("source_evidence_ids") or item.get("citations"))
    refusals: list[dict[str, Any]] = []
    for action in _string_list(item.get("expected_refused_actions") or item.get("blocked_actions")):
        refusals.append(
            {
                "action": action,
                "refusal": "Refuse the official action until cited stale evidence is refreshed or reviewed by the user.",
                "source_evidence_ids": citations,
            }
        )
    for message in messages:
        for action in _string_list(message.get("blocked_official_actions")):
            if _is_consequential(action):
                refusals.append(
                    {
                        "action": action,
                        "refusal": str(message.get("text") or "Refuse the consequential action while evidence is stale."),
                        "source_evidence_ids": _string_list(message.get("citations")) or citations,
                    }
                )
    dry_run = dry_run_expectations.get(str(item.get("scenario_id") or item.get("watchlist_item_id") or ""))
    for refusal in _mapping_sequence((dry_run or {}).get("expected_refusals")):
        refusals.append(
            {
                "action": str(refusal.get("action") or "official_action"),
                "refusal": str(refusal.get("refusal") or refusal.get("expected_refusal") or "Refuse pending stale evidence review."),
                "source_evidence_ids": _string_list(refusal.get("source_evidence_ids")) or citations,
            }
        )
    return _dedupe_dicts(refusals, "action")


def _blocked_explanations(item: Mapping[str, Any], messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    citations = _string_list(item.get("source_evidence_ids") or item.get("citations"))
    explanations: list[dict[str, Any]] = []
    for explanation in _mapping_sequence(item.get("blocked_action_explanations")):
        explanations.append(
            {
                "action": str(explanation.get("action") or "official_action"),
                "explanation": str(explanation.get("explanation") or explanation.get("reason") or "Blocked by stale cited evidence."),
                "source_evidence_ids": _string_list(explanation.get("source_evidence_ids") or explanation.get("citations")) or citations,
            }
        )
    for message in messages:
        for explanation in _mapping_sequence(message.get("blocked_action_explanations")):
            explanations.append(
                {
                    "action": str(explanation.get("action") or "official_action"),
                    "explanation": str(explanation.get("explanation") or explanation.get("reason") or "Blocked pending exact user confirmation."),
                    "source_evidence_ids": _string_list(explanation.get("source_evidence_ids") or explanation.get("citations")) or citations,
                }
            )
    if explanations:
        return _dedupe_dicts(explanations, "action")
    return [
        {
            "action": "continue_with_official_action",
            "explanation": "The action is blocked until the stale cited evidence is refreshed or a reviewer disposition permits a safe read-only response.",
            "source_evidence_ids": citations,
        }
    ]


def _reviewer_owner_fields(*packets: Mapping[str, Any]) -> list[dict[str, Any]]:
    owners: list[dict[str, Any]] = []
    for packet in packets:
        source_ids = _packet_evidence_ids(packet)
        candidates = []
        reviewer_owner = packet.get("reviewer_owner")
        if isinstance(reviewer_owner, Mapping):
            candidates.append(reviewer_owner)
        candidates.extend(_mapping_sequence(packet.get("reviewer_owner_fields")))
        candidates.extend(_mapping_sequence(packet.get("reviewer_owners")))
        candidates.extend(_mapping_sequence(packet.get("reviewer_signoffs")))
        for index, owner in enumerate(candidates):
            owners.append(
                {
                    "reviewer_owner_id": str(owner.get("reviewer_owner_id") or owner.get("owner_id") or owner.get("reviewer_id") or owner.get("owner") or f"fixture-reviewer-{index + 1}"),
                    "reviewer_role": str(owner.get("reviewer_role") or owner.get("role") or "ppd_fixture_reviewer"),
                    "reviewer_disposition": str(owner.get("reviewer_disposition") or owner.get("review_status") or owner.get("approval_status") or "review_required"),
                    "source_evidence_ids": _string_list(owner.get("source_evidence_ids")) or source_ids,
                }
            )
    return _dedupe_dicts([owner for owner in owners if owner["source_evidence_ids"]], "reviewer_owner_id")


def _expectations_by_scenario(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in _mapping_sequence(packet.get("stale_evidence_expectations") or packet.get("scenario_expectations") or packet.get("regression_expectations")):
        key = str(item.get("scenario_id") or item.get("watchlist_item_id") or "")
        if key:
            result[key] = item
    return result


def _packet_id(packet: Mapping[str, Any], fallback: str) -> str:
    return str(packet.get("packet_id") or packet.get("transcript_id") or fallback)


def _packet_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    ids = _string_list(packet.get("source_evidence_ids") or packet.get("citation_ids"))
    for key in ("messages", "watchlist_reviewer_dispositions", "reviewer_dispositions", "reviewer_owners", "reviewer_signoffs"):
        for item in _mapping_sequence(packet.get(key)):
            ids.extend(_string_list(item.get("source_evidence_ids") or item.get("citations")))
    return sorted(set(ids))


def _is_consequential(action: str) -> bool:
    lowered = action.lower()
    return any(term in lowered for term in _CONSEQUENTIAL_TERMS)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _dedupe_dicts(items: Sequence[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        marker = str(item.get(key) or repr(sorted(item.items())))
        if marker not in seen:
            seen.add(marker)
            result.append(item)
    return result


def _scan_private_or_live_claims(value: Any, path: str, issues: list[FreshnessRegressionIssue]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _PRIVATE_KEYS and item not in (None, "", [], {}):
                issues.append(FreshnessRegressionIssue("private_or_auth_field_present", f"{path}.{key_text}", "packet must not include private DevHub or auth fields"))
            _scan_private_or_live_claims(item, f"{path}.{key_text}", issues)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_private_or_live_claims(item, f"{path}[{index}]", issues)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in _PRIVATE_TEXT_MARKERS):
            issues.append(FreshnessRegressionIssue("private_artifact_reference", path, "packet must not reference private paths, traces, HARs, or auth artifacts"))
        if "launched devhub" in lowered or "called the llm" in lowered or "mutated prompt" in lowered or "compiled guardrail" in lowered:
            issues.append(FreshnessRegressionIssue("live_or_mutation_claim", path, "packet must not claim live execution or prompt/guardrail mutation"))
