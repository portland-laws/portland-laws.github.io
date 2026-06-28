from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

REQUIRED_BLOCKED_ACTION_DOMAINS = {
    "submission": ("submit", "submission"),
    "upload": ("upload",),
    "payment": ("pay", "payment", "purchase"),
    "scheduling": ("schedule", "scheduling", "inspection"),
    "certification": ("certify", "certification", "acknowledge", "acknowledgement"),
}

PRIVATE_KEYS = {
    "auth_state",
    "authorization",
    "browser_trace",
    "card_number",
    "cookie",
    "credentials",
    "cvv",
    "devhub_session",
    "email",
    "har",
    "password",
    "payment_detail",
    "payment_details",
    "phone",
    "private_case_facts",
    "private_file",
    "private_path",
    "private_value",
    "raw_private_file",
    "session_state",
    "ssn",
    "token",
    "trace",
}

PRIVATE_FACT_KEYS = {
    "applicant_name",
    "contractor_name",
    "customer_name",
    "owner_name",
    "permit_number",
    "property_address",
    "site_address",
    "tax_account",
}

LIVE_EXECUTION_KEYS = {
    "agent_enabled",
    "call_llm",
    "calls_llm",
    "devhub_enabled",
    "execute_live_devhub",
    "execute_with_agent",
    "execute_with_llm",
    "launch_devhub",
    "launches_devhub",
    "live_agent",
    "live_devhub",
    "live_execution",
    "live_llm",
    "open_browser",
    "playwright_enabled",
    "read_private_files",
    "reads_private_files",
    "run_agent",
    "run_devhub",
    "run_llm",
    "uses_authenticated_session",
    "uses_devhub",
    "uses_llm",
}

PRIVATE_VALUE_MARKERS = (
    "/home/",
    "/Users/",
    "/private/",
    "/var/folders/",
    "C:/Users/",
    "C:\\Users\\",
    "file://",
    "auth_state",
    "devhub/session",
    ".har",
    "password=",
    "trace.zip",
)

LIVE_EXECUTION_TEXT_MARKERS = (
    "agent will execute",
    "agent will open devhub",
    "agent will run devhub",
    "launch devhub",
    "live devhub",
    "open authenticated browser",
    "run the live agent",
)

OUTCOME_GUARANTEE_MARKERS = (
    "approval is guaranteed",
    "guarantee approval",
    "guarantee issuance",
    "guarantees approval",
    "permit approval is certain",
    "permit will be approved",
    "permit will be issued",
    "will pass inspection",
    "will pass plan review",
)

ENABLED_MARKERS = {"enabled", "is_enabled", "available", "clickable", "can_execute"}
DISABLED_MARKERS = {"disabled", "is_disabled", "blocked"}


@dataclass(frozen=True)
class GapAnalysisRerunRehearsalIssue:
    code: str
    path: str
    message: str


class GapAnalysisRerunRehearsalError(ValueError):
    def __init__(self, issues: Sequence[GapAnalysisRerunRehearsalIssue]) -> None:
        self.issues = tuple(issues)
        details = "; ".join(f"{issue.path}: {issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(details or "gap-analysis rerun rehearsal packet is invalid")


def build_gap_analysis_rerun_rehearsal_packet(
    process_model_impact_packet: Mapping[str, Any],
    missing_information_prompt_corpus: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a fixture-only user gap-analysis rerun rehearsal packet."""

    _raise_for_disallowed_inputs(process_model_impact_packet)
    _raise_for_disallowed_inputs(missing_information_prompt_corpus)

    impacts = _accepted_impacts(process_model_impact_packet)
    process_models = _process_models_by_id(process_model_impact_packet)
    prompt_cases = _prompt_cases(missing_information_prompt_corpus) or [{"case_id": "synthetic-rerun-case-1"}]

    case_deltas: list[dict[str, Any]] = []
    missing_fact_prompts: list[dict[str, Any]] = []
    stale_conflicting_notes: list[dict[str, Any]] = []
    blocked_action_expectations: list[dict[str, Any]] = []
    next_safe_action_candidates: list[dict[str, Any]] = []

    for index, case in enumerate(prompt_cases):
        impact = impacts[index % len(impacts)] if impacts else {}
        process_id = _choose_process_id(case, impact, process_models)
        citations = _merge_citations(_citation_ids(impact), _case_source_ids(case))
        required_facts_added = _required_facts_added(impact)
        document_rule_deltas = _document_rule_deltas(impact)
        unsupported_notes = _string_list(impact.get("unsupported_path_notes"))
        case_id = str(case.get("case_id") or f"synthetic-rerun-case-{index + 1}")

        case_deltas.append({
            "case_id": case_id,
            "process_id": process_id,
            "requirement_id": str(impact.get("requirement_id") or "synthetic-requirement-impact"),
            "candidate_id": str(impact.get("candidate_id") or "synthetic-candidate-impact"),
            "source_evidence_ids": citations,
            "synthetic_case_delta": {
                "known_fact_keys": sorted(_mapping(case.get("known_facts")).keys()),
                "required_facts_added": required_facts_added,
                "document_rule_deltas": document_rule_deltas,
                "unsupported_path_notes": unsupported_notes,
            },
        })

        fact_prompt = _missing_fact_prompt(case_id, process_id, required_facts_added, _expected_prompts(case), citations)
        if fact_prompt:
            missing_fact_prompts.append(fact_prompt)
        notes = _evidence_notes(case_id, process_id, case, impact, citations)
        stale_conflicting_notes.extend(notes)
        blocked_action_expectations.extend(_blocked_actions(case_id, process_id, case, citations))
        next_safe_action_candidates.append(_next_safe_action(case_id, process_id, fact_prompt, notes, citations))

    _ensure_required_blocked_action_expectations(blocked_action_expectations, case_deltas)

    packet = {
        "packet_id": "fixture-first-user-gap-analysis-rerun-rehearsal",
        "packet_status": "fixture_only_no_private_files_no_devhub_no_agent_consumers",
        "source_packets": {
            "process_model_impact_rehearsal_packet_id": str(process_model_impact_packet.get("packet_id") or "unknown-process-impact-packet"),
            "missing_information_prompt_corpus_id": str(missing_information_prompt_corpus.get("corpus_id") or "unknown-prompt-corpus"),
        },
        "execution_boundaries": {
            "calls_llm": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "reads_private_files": False,
            "runs_agent_consumers": False,
            "writes_private_artifacts": False,
        },
        "synthetic_case_deltas": case_deltas,
        "missing_fact_prompts": missing_fact_prompts,
        "stale_conflicting_evidence_notes": stale_conflicting_notes,
        "blocked_action_expectations": blocked_action_expectations,
        "next_safe_action_candidates": next_safe_action_candidates,
    }
    assert_valid_gap_analysis_rerun_rehearsal_packet(packet)
    return packet


def assert_valid_gap_analysis_rerun_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    issues = validate_gap_analysis_rerun_rehearsal_packet(packet)
    if issues:
        raise GapAnalysisRerunRehearsalError(issues)


def validate_gap_analysis_rerun_rehearsal_packet(packet: Mapping[str, Any]) -> list[GapAnalysisRerunRehearsalIssue]:
    issues: list[GapAnalysisRerunRehearsalIssue] = []
    if not isinstance(packet, Mapping):
        return [GapAnalysisRerunRehearsalIssue("invalid_packet", "$", "packet must be an object")]

    issues.extend(_scan_disallowed_inputs(packet))

    if packet.get("packet_status") != "fixture_only_no_private_files_no_devhub_no_agent_consumers":
        issues.append(GapAnalysisRerunRehearsalIssue("unsafe_packet_status", "packet_status", "packet must be fixture-only"))

    boundaries = _mapping(packet.get("execution_boundaries"))
    for key in ("calls_llm", "launches_devhub", "uses_authenticated_session", "reads_private_files", "runs_agent_consumers", "writes_private_artifacts"):
        if boundaries.get(key) is not False:
            issues.append(GapAnalysisRerunRehearsalIssue("unsafe_execution_boundary", f"execution_boundaries.{key}", "boundary must be explicitly false"))

    for group_name in ("synthetic_case_deltas", "missing_fact_prompts", "stale_conflicting_evidence_notes", "blocked_action_expectations", "next_safe_action_candidates"):
        values = _sequence_of_mappings(packet.get(group_name))
        if group_name in {"synthetic_case_deltas", "blocked_action_expectations", "next_safe_action_candidates"} and not values:
            issues.append(GapAnalysisRerunRehearsalIssue("missing_rehearsal_section", group_name, "section must contain cited fixture rows"))
        for index, row in enumerate(values):
            if not _string_list(row.get("source_evidence_ids")):
                issues.append(GapAnalysisRerunRehearsalIssue("uncited_rehearsal_row", f"{group_name}[{index}]", "row must cite source evidence ids"))

    for index, prompt in enumerate(_sequence_of_mappings(packet.get("missing_fact_prompts"))):
        if not str(prompt.get("prompt") or "").strip():
            issues.append(GapAnalysisRerunRehearsalIssue("uncited_or_empty_prompt", f"missing_fact_prompts[{index}]", "prompt text must be present and cited"))

    blocked_actions = _sequence_of_mappings(packet.get("blocked_action_expectations"))
    covered_domains = set()
    for index, action in enumerate(blocked_actions):
        path = f"blocked_action_expectations[{index}]"
        action_text = _row_text(action)
        covered_domains.update(_domains_for_text(action_text))
        if action.get("blocked") is not True:
            issues.append(GapAnalysisRerunRehearsalIssue("blocked_action_not_blocked", path, "blocked action expectation must stay blocked"))
        if action.get("requires_attendance") is not True or action.get("requires_exact_confirmation") is not True:
            issues.append(GapAnalysisRerunRehearsalIssue("missing_confirmation_gate", path, "blocked action must require attendance and exact confirmation"))
        if not _domains_for_text(action_text):
            issues.append(GapAnalysisRerunRehearsalIssue("non_consequential_blocked_action", path, "blocked action must be an official or consequential action"))

    missing_domains = sorted(set(REQUIRED_BLOCKED_ACTION_DOMAINS) - covered_domains)
    if missing_domains:
        issues.append(GapAnalysisRerunRehearsalIssue("missing_blocked_action_expectation", "blocked_action_expectations", "missing blocked expectations for: " + ", ".join(missing_domains)))

    for index, action in enumerate(_sequence_of_mappings(packet.get("next_safe_action_candidates"))):
        path = f"next_safe_action_candidates[{index}]"
        if action.get("requires_devhub") is not False or action.get("reads_private_files") is not False or action.get("runs_agent_consumer") is not False:
            issues.append(GapAnalysisRerunRehearsalIssue("unsafe_next_action", path, "next safe action must remain local and fixture-only"))
        if _domains_for_text(_row_text(action)):
            issues.append(GapAnalysisRerunRehearsalIssue("consequential_next_action", path, "next safe action must not be an official consequential action"))

    return issues


def _accepted_impacts(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates = _sequence_of_mappings(packet.get("reviewed_synthetic_requirement_candidates"))
    accepted = [candidate for candidate in candidates if str(candidate.get("review_status") or "").startswith("accepted")]
    if accepted:
        return accepted
    rehearsal = _mapping(packet.get("guardrail_recompilation_rehearsal_packet"))
    return _sequence_of_mappings(rehearsal.get("predicate_impacts"))


def _process_models_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(model.get("process_id")): model for model in _sequence_of_mappings(packet.get("process_model_fixtures")) if model.get("process_id")}


def _prompt_cases(corpus: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return _sequence_of_mappings(corpus.get("synthetic_user_cases") or corpus.get("cases"))


def _choose_process_id(case: Mapping[str, Any], impact: Mapping[str, Any], process_models: Mapping[str, Mapping[str, Any]]) -> str:
    impact_process_id = str(impact.get("process_id") or "")
    if impact_process_id:
        return impact_process_id
    scenario = str(case.get("scenario") or _mapping(case.get("known_facts")).get("permit_family") or "").lower()
    for process_id, process_model in process_models.items():
        permit_type = str(process_model.get("permit_type") or "").lower()
        if permit_type and any(word in scenario for word in permit_type.split()[:3]):
            return process_id
    return next(iter(process_models), "synthetic-process")


def _citation_ids(impact: Mapping[str, Any]) -> list[str]:
    return _string_list(impact.get("source_evidence_ids")) + _string_list(impact.get("citation_ids"))


def _case_source_ids(case: Mapping[str, Any]) -> list[str]:
    source_ids: list[str] = []
    for citation in _sequence_of_mappings(case.get("citations")):
        source_id = citation.get("source_id")
        section = citation.get("section")
        if source_id and section:
            source_ids.append(f"{source_id}#{section}")
        elif source_id:
            source_ids.append(str(source_id))
    for prompt in _sequence_of_mappings(case.get("expected_prompts")):
        for citation in _sequence_of_mappings(prompt.get("citations")):
            source_id = citation.get("source_id")
            section = citation.get("section")
            if source_id and section:
                source_ids.append(f"{source_id}#{section}")
            elif source_id:
                source_ids.append(str(source_id))
    return source_ids


def _required_facts_added(impact: Mapping[str, Any]) -> list[str]:
    changes = _mapping(impact.get("required_fact_changes"))
    return sorted(set(_string_list(changes.get("add")) + _string_list(impact.get("required_facts_added"))))


def _document_rule_deltas(impact: Mapping[str, Any]) -> list[dict[str, str]]:
    deltas: list[dict[str, str]] = []
    for key, impact_type in (("document_rule_impacts", "change"), ("document_rules_added", "add"), ("document_rules_changed", "change")):
        for row in _sequence_of_mappings(impact.get(key)):
            deltas.append({
                "document": str(row.get("document") or "synthetic_document"),
                "impact_type": str(row.get("impact_type") or impact_type),
                "rule": str(row.get("rule") or "review cited document rule before relying on readiness"),
            })
    return deltas


def _expected_prompts(case: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return _sequence_of_mappings(case.get("expected_prompts"))


def _missing_fact_prompt(case_id: str, process_id: str, required_facts_added: Sequence[str], expected_prompts: Sequence[Mapping[str, Any]], citations: Sequence[str]) -> dict[str, Any] | None:
    prompt_text = ""
    for prompt in expected_prompts:
        if "missing_fact" in str(prompt.get("category") or ""):
            prompt_text = str(prompt.get("text") or "")
            break
    if not prompt_text and required_facts_added:
        prompt_text = "Please confirm these PP&D case facts before I rerun the gap analysis: " + ", ".join(required_facts_added) + "."
    if not prompt_text:
        return None
    return {
        "case_id": case_id,
        "process_id": process_id,
        "prompt_id": f"{case_id}.missing_fact_prompt",
        "missing_fact_keys": list(required_facts_added),
        "prompt": prompt_text,
        "agent_state": "blocked_until_user_supplies_required_case_facts",
        "source_evidence_ids": list(citations),
    }


def _evidence_notes(case_id: str, process_id: str, case: Mapping[str, Any], impact: Mapping[str, Any], citations: Sequence[str]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    scenario = str(case.get("scenario") or "").lower()
    known = _mapping(case.get("known_facts"))
    if "stale" in scenario or "stale" in str(known).lower():
        notes.append({"case_id": case_id, "process_id": process_id, "note_id": f"{case_id}.stale_evidence", "kind": "stale_evidence", "note": "Cached or stale evidence must be refreshed or confirmed before the rerun can rely on it.", "source_evidence_ids": list(citations)})
    if _string_list(impact.get("unsupported_path_notes")):
        notes.append({"case_id": case_id, "process_id": process_id, "note_id": f"{case_id}.conflicting_or_unsupported_path", "kind": "conflicting_evidence", "note": "The process impact packet flags a possible unsupported DevHub path, so the rerun must not assume portal eligibility.", "source_evidence_ids": list(citations)})
    return notes


def _blocked_actions(case_id: str, process_id: str, case: Mapping[str, Any], citations: Sequence[str]) -> list[dict[str, Any]]:
    texts = [str(case.get("scenario") or ""), str(_mapping(case.get("known_facts")).get("requested_action") or "")]
    for prompt in _expected_prompts(case):
        texts.append(str(prompt.get("text") or ""))
    combined = " ".join(texts).lower()
    actions: list[str] = []
    for domain, words in REQUIRED_BLOCKED_ACTION_DOMAINS.items():
        if any(word in combined for word in words):
            actions.append(f"{domain}_requires_attended_confirmation")
    return [_blocked_action(case_id, process_id, action, citations) for action in sorted(set(actions))]


def _blocked_action(case_id: str, process_id: str, action: str, citations: Sequence[str]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "process_id": process_id,
        "action_id": action,
        "blocked": True,
        "requires_attendance": True,
        "requires_exact_confirmation": True,
        "reason_code": "fixture_gap_analysis_blocks_consequential_action",
        "source_evidence_ids": list(citations),
    }


def _ensure_required_blocked_action_expectations(actions: list[dict[str, Any]], case_deltas: Sequence[Mapping[str, Any]]) -> None:
    if case_deltas:
        first = case_deltas[0]
        case_id = str(first.get("case_id") or "synthetic-rerun-case-1")
        process_id = str(first.get("process_id") or "synthetic-process")
        citations = _string_list(first.get("source_evidence_ids"))
    else:
        case_id = "synthetic-rerun-case-1"
        process_id = "synthetic-process"
        citations = ["synthetic-fixture-source-required"]
    covered = set()
    for action in actions:
        covered.update(_domains_for_text(_row_text(action)))
    for domain in sorted(set(REQUIRED_BLOCKED_ACTION_DOMAINS) - covered):
        actions.append(_blocked_action(case_id, process_id, f"{domain}_requires_attended_confirmation", citations))


def _next_safe_action(case_id: str, process_id: str, fact_prompt: Mapping[str, Any] | None, notes: Sequence[Mapping[str, Any]], citations: Sequence[str]) -> dict[str, Any]:
    if fact_prompt:
        action_id = "ask_cited_missing_fact_prompt"
    elif notes:
        action_id = "review_stale_or_conflicting_evidence_note"
    else:
        action_id = "prepare_reversible_local_gap_analysis_preview"
    return {"case_id": case_id, "process_id": process_id, "action_id": action_id, "requires_devhub": False, "reads_private_files": False, "runs_agent_consumer": False, "source_evidence_ids": list(citations)}


def _raise_for_disallowed_inputs(value: Any) -> None:
    issues = _scan_disallowed_inputs(value)
    if issues:
        raise GapAnalysisRerunRehearsalError(issues)


def _scan_disallowed_inputs(value: Any, path: str = "$", key: str = "") -> list[GapAnalysisRerunRehearsalIssue]:
    issues: list[GapAnalysisRerunRehearsalIssue] = []
    normalized_key = key.lower()

    if normalized_key in PRIVATE_KEYS and value not in (None, "", [], {}):
        code = "private_case_fact_present" if normalized_key == "private_case_facts" else "private_input_present"
        issues.append(GapAnalysisRerunRehearsalIssue(code, path, "packet must not include private case facts, files, credentials, sessions, or payment data"))
    if normalized_key == "known_facts" and _mapping(value) and any(fact_key.lower() in PRIVATE_FACT_KEYS for fact_key in _mapping(value)):
        issues.append(GapAnalysisRerunRehearsalIssue("private_case_fact_present", path, "known facts must list synthetic keys only, not private case fact values"))
    if normalized_key in LIVE_EXECUTION_KEYS and value not in (False, None, "", [], {}):
        issues.append(GapAnalysisRerunRehearsalIssue("live_execution_claim", path, "packet must not claim live agent, LLM, DevHub, browser, or private-file execution"))
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in PRIVATE_VALUE_MARKERS):
            issues.append(GapAnalysisRerunRehearsalIssue("private_value_present", path, "packet must not include private paths or runtime artifacts"))
        if any(marker in lowered for marker in LIVE_EXECUTION_TEXT_MARKERS):
            issues.append(GapAnalysisRerunRehearsalIssue("live_execution_claim", path, "packet must not claim live agent or DevHub execution"))
        if any(marker in lowered for marker in OUTCOME_GUARANTEE_MARKERS):
            issues.append(GapAnalysisRerunRehearsalIssue("outcome_guarantee_present", path, "packet must not guarantee legal, permitting, inspection, review, approval, or issuance outcomes"))

    if isinstance(value, Mapping):
        if _is_enabled_consequential_control(value):
            issues.append(GapAnalysisRerunRehearsalIssue("enabled_consequential_control", path, "submission, upload, payment, scheduling, and certification controls must be blocked or disabled"))
        for child_key, child_value in value.items():
            issues.extend(_scan_disallowed_inputs(child_value, f"{path}.{child_key}", str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_scan_disallowed_inputs(child, f"{path}[{index}]", key))
    return issues


def _is_enabled_consequential_control(row: Mapping[str, Any]) -> bool:
    text = _row_text(row)
    if not _domains_for_text(text):
        return False
    if any(row.get(key) is True for key in ENABLED_MARKERS):
        return True
    if any(row.get(key) is False for key in DISABLED_MARKERS):
        return True
    state = str(row.get("state") or row.get("status") or "").lower()
    return state in {"enabled", "available", "clickable", "ready"}


def _domains_for_text(text: str) -> set[str]:
    lowered = text.lower().replace("-", "_").replace(" ", "_")
    return {domain for domain, words in REQUIRED_BLOCKED_ACTION_DOMAINS.items() if any(word in lowered for word in words)}


def _row_text(row: Mapping[str, Any]) -> str:
    return " ".join(str(row.get(key) or "") for key in ("action_id", "action", "control_id", "label", "name", "reason_code", "description", "title"))


def _merge_citations(*groups: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in merged:
                merged.append(str(item))
    return merged or ["synthetic-fixture-source-required"]


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


__all__ = [
    "GapAnalysisRerunRehearsalError",
    "GapAnalysisRerunRehearsalIssue",
    "REQUIRED_BLOCKED_ACTION_DOMAINS",
    "assert_valid_gap_analysis_rerun_rehearsal_packet",
    "build_gap_analysis_rerun_rehearsal_packet",
    "validate_gap_analysis_rerun_rehearsal_packet",
]
