"""Validation for fixture-first post-recompile readiness replay packet v1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ppd.agent_readiness.post_recompile_agent_readiness_replay_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_TYPE,
    PACKET_VERSION,
    PUBLIC_VALIDATION_COMMANDS,
    REQUIRED_NON_MUTATION_FLAGS,
    SOURCE_KIND,
)

REQUIRED_CASE_FIELDS = (
    "missing_information_prompts",
    "blocked_action_decisions",
    "reversible_draft_eligibility_decisions",
    "exact_confirmation_warnings",
    "refused_action_explanations",
    "regression_notes",
    "reviewer_holds",
    "rollback_notes",
)

FORBIDDEN_TEXT_MARKERS = (
    "opened devhub",
    "live devhub",
    "devhub session opened",
    "authenticated devhub session",
    "live crawl",
    "started crawl",
    "crawled live",
    "official action completed",
    "official action performed",
    "submitted permit",
    "uploaded correction",
    "certified acknowledgement",
    "paid fee",
    "scheduled inspection",
    "cancelled permit",
    "raw crawl output",
    "raw downloaded",
    "downloaded document",
    "downloaded artifact",
    "private artifact",
    "auth state",
    "browser state",
    "session state",
    "trace file",
    "har file",
    "cookie",
    "password",
    "credential",
    "updated active prompt",
    "mutated active prompt",
    "changed active prompt",
    "updated active guardrail",
    "mutated active guardrail",
    "changed active guardrail",
    "legal advice",
    "legal guarantee",
    "guaranteed approval",
    "guarantee approval",
    "permit guaranteed",
    "permit will be approved",
    "approval is guaranteed",
)

FORBIDDEN_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "password",
    "private_artifact",
    "raw_crawl_output",
    "raw_download",
    "downloaded_artifact",
    "downloaded_document",
    "session_state",
    "storage_state",
    "trace",
    "har",
)

FORBIDDEN_TRUE_FLAG_KEYS = (
    "active_agent_prompt_change",
    "active_prompt_change",
    "active_prompt_mutation",
    "active_guardrail_change",
    "active_guardrail_mutation",
    "active_release_state_change",
    "active_mutation",
    "devhub_opened",
    "live_devhub_opened",
    "public_crawl_started",
    "live_crawl_started",
    "private_artifact_stored",
    "raw_artifact_stored",
    "downloaded_artifact_stored",
    "official_action_performed",
    "official_action_completed",
)


def validate_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet_version must be {PACKET_VERSION}")
    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")
    if packet.get("offline_only") is not True:
        errors.append("offline_only must be true")
    if packet.get("source_kind") != SOURCE_KIND:
        errors.append(f"source_kind must be {SOURCE_KIND}")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("exact_offline_validation_commands must exactly match v1 offline validation commands")
    if packet.get("validation_commands") != PUBLIC_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the PP&D daemon self-test command")

    non_mutation_flags = packet.get("non_mutation_flags")
    if non_mutation_flags != REQUIRED_NON_MUTATION_FLAGS:
        errors.append("non_mutation_flags must exactly deny active mutations, live DevHub, crawling, private artifacts, and official actions")

    consumed_row_ids = _string_list(packet.get("consumed_row_ids"))
    if not consumed_row_ids:
        errors.append("consumed_row_ids must be non-empty")

    replay_cases = packet.get("replay_cases")
    if not isinstance(replay_cases, list) or not replay_cases:
        errors.append("replay_cases must be a non-empty list")
        replay_cases = []
    _validate_replay_cases(replay_cases, set(consumed_row_ids), errors)
    _validate_citation_coverage(packet, replay_cases, errors)
    _validate_forbidden_payload(packet, "$", errors)
    return sorted(set(errors))


def assert_valid_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_packet(packet)
    if errors:
        raise ValueError("invalid post-recompile readiness replay packet v1: " + "; ".join(errors))


def _validate_replay_cases(cases: Sequence[Any], consumed_row_ids: set[str], errors: list[str]) -> None:
    for index, case in enumerate(cases):
        prefix = f"replay_cases[{index}]"
        if not isinstance(case, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        if case.get("case_sequence") != index + 1:
            errors.append(f"{prefix}.case_sequence must be {index + 1}")
        _validate_inactive_candidate_reference(prefix, case, consumed_row_ids, errors)
        citations = _string_list(case.get("citation_placeholder_ids"))
        if not citations:
            errors.append(f"{prefix}.citation_placeholder_ids must be non-empty")
        for field in REQUIRED_CASE_FIELDS:
            rows = case.get(field)
            if not isinstance(rows, list) or not rows:
                errors.append(f"{prefix}.{field} must be non-empty")
                continue
            for child_index, row in enumerate(rows):
                child = f"{prefix}.{field}[{child_index}]"
                if not isinstance(row, Mapping):
                    errors.append(f"{child} must be an object")
                    continue
                child_citations = _string_list(row.get("citation_placeholder_ids"))
                if not child_citations:
                    errors.append(f"{child}.citation_placeholder_ids must be non-empty")
                for citation in child_citations:
                    if citation not in citations:
                        errors.append(f"{child}.citation_placeholder_ids includes unknown case citation {citation}")
        _validate_semantic_decisions(prefix, case, errors)


def _validate_inactive_candidate_reference(
    prefix: str,
    case: Mapping[str, Any],
    consumed_row_ids: set[str],
    errors: list[str],
) -> None:
    source_row_id = case.get("source_row_id")
    if source_row_id not in consumed_row_ids:
        errors.append(f"{prefix}.source_row_id must reference consumed_row_ids")
    label = _text(case.get("source_candidate_label"))
    if not label:
        errors.append(f"{prefix}.source_candidate_label must identify the inactive promotion candidate")
    elif "inactive" not in label.lower() or "candidate" not in label.lower():
        errors.append(f"{prefix}.source_candidate_label must identify an inactive promotion candidate")


def _validate_semantic_decisions(prefix: str, case: Mapping[str, Any], errors: list[str]) -> None:
    for index, prompt in enumerate(_mapping_list(case.get("missing_information_prompts"))):
        if prompt.get("prompt_kind") != "missing_information":
            errors.append(f"{prefix}.missing_information_prompts[{index}].prompt_kind must be missing_information")
        if not _text(prompt.get("expected_prompt")):
            errors.append(f"{prefix}.missing_information_prompts[{index}].expected_prompt must be non-empty")
    for index, decision in enumerate(_mapping_list(case.get("blocked_action_decisions"))):
        if decision.get("decision") != "blocked":
            errors.append(f"{prefix}.blocked_action_decisions[{index}].decision must be blocked")
        if not _text(decision.get("reason")):
            errors.append(f"{prefix}.blocked_action_decisions[{index}].reason must be non-empty")
    for index, decision in enumerate(_mapping_list(case.get("reversible_draft_eligibility_decisions"))):
        if decision.get("eligible") is not True:
            errors.append(f"{prefix}.reversible_draft_eligibility_decisions[{index}].eligible must be true")
        if decision.get("requires_user_attendance") is not False:
            errors.append(f"{prefix}.reversible_draft_eligibility_decisions[{index}].requires_user_attendance must be false")
        if not _text(decision.get("forbidden_escalation")):
            errors.append(f"{prefix}.reversible_draft_eligibility_decisions[{index}].forbidden_escalation must be non-empty")
    for index, warning in enumerate(_mapping_list(case.get("exact_confirmation_warnings"))):
        if not _text(warning.get("warning")):
            errors.append(f"{prefix}.exact_confirmation_warnings[{index}].warning must be non-empty")
    for index, explanation in enumerate(_mapping_list(case.get("refused_action_explanations"))):
        if not _text(explanation.get("expected_explanation")):
            errors.append(f"{prefix}.refused_action_explanations[{index}].expected_explanation must be non-empty")
    for index, note in enumerate(_mapping_list(case.get("regression_notes"))):
        if not _text(note.get("note")):
            errors.append(f"{prefix}.regression_notes[{index}].note must be non-empty")
    for index, hold in enumerate(_mapping_list(case.get("reviewer_holds"))):
        if hold.get("status") != "held_for_manual_review":
            errors.append(f"{prefix}.reviewer_holds[{index}].status must be held_for_manual_review")
        if not _text(hold.get("reason")):
            errors.append(f"{prefix}.reviewer_holds[{index}].reason must be non-empty")
    for index, note in enumerate(_mapping_list(case.get("rollback_notes"))):
        if not _text(note.get("note")):
            errors.append(f"{prefix}.rollback_notes[{index}].note must be non-empty")


def _validate_citation_coverage(packet: Mapping[str, Any], cases: Sequence[Any], errors: list[str]) -> None:
    coverage = packet.get("citation_placeholder_coverage")
    if not isinstance(coverage, Mapping):
        errors.append("citation_placeholder_coverage must be present")
        return
    if coverage.get("all_replay_cases_have_placeholders") is not True:
        errors.append("citation_placeholder_coverage.all_replay_cases_have_placeholders must be true")
    expected = sorted(
        {
            citation
            for case in cases
            if isinstance(case, Mapping)
            for citation in _string_list(case.get("citation_placeholder_ids"))
        }
    )
    if coverage.get("placeholder_ids") != expected:
        errors.append("citation_placeholder_coverage.placeholder_ids must exactly match replay case citation placeholders")


def _validate_forbidden_payload(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized_key in FORBIDDEN_TRUE_FLAG_KEYS and child is True:
                errors.append(f"forbidden active/live/private/official mutation flag at {child_path}")
            if any(marker in normalized_key for marker in FORBIDDEN_KEY_MARKERS) and child not in (None, False, "", [], {}):
                errors.append(f"forbidden private/session/browser/raw artifact field at {child_path}")
            _validate_forbidden_payload(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _validate_forbidden_payload(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live/private/official-action/guarantee claim at {path}: {marker}")


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _text(value: Any) -> str:
    return value if isinstance(value, str) and value else ""
