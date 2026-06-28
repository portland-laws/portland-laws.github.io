"""Fixture-first candidate and dry-run packets for PP&D agent prompt updates.

This module is intentionally deterministic: it models reviewer packets without
calling live agents, reading private case files, or mutating prompt/release
state. The dry-run validator rejects packet shapes that would leak private case
material, imply live execution, omit reviewer accountability, or overstate legal
or permitting outcomes.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

REQUIRED_SOURCE_PACKET_IDS = (
    "agent_consumer_feedback_triage_packet",
    "guardrail_explanation_regression_packet",
    "missing_information_prompt_corpus",
)

NO_LIVE_AGENT_ATTESTATION = {
    "live_agent_invoked": False,
    "llm_consumer_invoked": False,
    "private_case_files_read": False,
    "prompt_state_mutated": False,
    "release_state_mutated": False,
}

_PRIVATE_FACT_KEYS = {
    "applicant_name",
    "case_fact",
    "case_facts",
    "devhub_private_value",
    "email_address",
    "known_private_fact",
    "known_private_facts",
    "observed_private_values",
    "owner_name",
    "permit_number",
    "phone_number",
    "private_case_fact",
    "private_case_facts",
    "private_values",
    "project_address",
    "tax_account_number",
}
_PRIVATE_PATH_KEYS = {
    "auth_state_path",
    "downloaded_document_path",
    "har_path",
    "local_private_path",
    "private_case_file",
    "private_case_path",
    "raw_crawl_output_path",
    "screenshot_path",
    "session_state_path",
    "trace_path",
}
_PRIVATE_CLASSIFICATIONS = {
    "case_private",
    "confidential",
    "devhub_authenticated_private",
    "private",
    "restricted",
    "user_private",
}
_LOCAL_PATH_PREFIXES = ("/home/", "/Users/", "/private/", "/tmp/", "file://", "C:\\", "D:\\")
_LIVE_EXECUTION_KEYS = {
    "agent_consumer_invoked",
    "agent_consumers_invoked",
    "browser_automation_executed",
    "crawler_executed",
    "devhub_browser_executed",
    "devhub_executed",
    "llm_executed",
    "llm_execution_allowed",
    "live_crawler_executed",
    "live_devhub_executed",
    "live_llm_executed",
    "live_processor_executed",
    "processor_executed",
}
_LIVE_EXECUTION_PHRASES = (
    "agent consumer executed",
    "agent consumer invoked",
    "called the llm",
    "crawler executed",
    "devhub browser ran",
    "devhub executed",
    "llm executed",
    "llm execution completed",
    "live crawler",
    "live devhub",
    "live llm",
    "live processor",
    "opened devhub",
    "processor executed",
    "ran the crawler",
    "ran the processor",
)
_OUTCOME_GUARANTEE_PHRASES = (
    "application will be approved",
    "approval is guaranteed",
    "cannot be denied",
    "guarantee approval",
    "guaranteed approval",
    "legally valid",
    "no legal risk",
    "permit issuance guaranteed",
    "permit will be approved",
    "permit will issue",
    "will receive the permit",
)
_CONSEQUENTIAL_CONTROL_WORDS = (
    "acknowledge",
    "certification",
    "certify",
    "inspection",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "scheduling",
    "submit",
    "submission",
    "upload",
)
_MUTATION_FLAG_KEYS = {
    "active_prompt_mutation",
    "active_prompt_mutation_flag",
    "active_release_state_mutation",
    "active_release_state_mutation_flag",
    "mutate_prompt_state",
    "mutate_release_state",
    "prompt_state_mutated",
    "prompt_state_mutation_enabled",
    "release_state_mutated",
    "release_state_mutation_enabled",
}


@dataclass(frozen=True)
class PromptRegressionPacketError(ValueError):
    """Raised when a prompt regression packet violates PP&D dry-run rules."""

    message: str

    def __str__(self) -> str:
        return self.message


_CANDIDATE_PACKET: dict[str, Any] = {
    "packet_id": "agent_prompt_update_candidate_packet_fixture_first_v1",
    "packet_kind": "fixture_first_agent_prompt_update_candidate",
    "source_packet_ids": list(REQUIRED_SOURCE_PACKET_IDS),
    "reviewer_owner_fields": {
        "review_owner": "ppd_policy_review",
        "engineering_owner": "ppd_guardrails",
        "release_owner": "ppd_release_manager",
        "requires_human_review": True,
    },
    "citations": [
        {
            "citation_id": "triage-001",
            "source_packet_id": "agent_consumer_feedback_triage_packet",
            "claim": "Consumers need refusals to explain the specific PP&D automation boundary that applies.",
        },
        {
            "citation_id": "guardrail-001",
            "source_packet_id": "guardrail_explanation_regression_packet",
            "claim": "Refusal wording must preserve prohibitions on CAPTCHA, MFA, payment, submission, upload, and certification actions.",
        },
        {
            "citation_id": "missing-info-001",
            "source_packet_id": "missing_information_prompt_corpus",
            "claim": "Missing-information prompts should ask for public, non-secret inputs and offer fixture-only next steps.",
        },
    ],
    "proposed_prompt_wording_changes": [
        {
            "change_id": "prompt-boundary-001",
            "status": "candidate_only",
            "proposed_wording": "Use committed PP&D fixtures and public documentation references first. Do not invoke live agent consumers, read private case files, or mutate prompt or release state while preparing review packets.",
            "citation_ids": ["triage-001", "guardrail-001"],
        },
        {
            "change_id": "prompt-missing-info-001",
            "status": "candidate_only",
            "proposed_wording": "When required information is missing, ask only for the narrow public or user-provided fields needed to continue, and describe the fixture-based validation that can run before any authenticated or live automation.",
            "citation_ids": ["missing-info-001"],
        },
    ],
    "proposed_refusal_wording_changes": [
        {
            "change_id": "refusal-live-action-001",
            "status": "candidate_only",
            "proposed_wording": "I cannot perform live PP&D actions such as CAPTCHA, MFA, payment, submission, upload, certification, cancellation, or account creation. I can prepare fixture-backed review material and validation expectations instead.",
            "citation_ids": ["guardrail-001"],
        }
    ],
    "regression_rerun_expectations": [
        {
            "expectation_id": "rerun-guardrail-explanations",
            "must_pass": True,
            "description": "Re-run guardrail explanation regressions against the candidate wording and verify each refusal names the prohibited live action boundary.",
        },
        {
            "expectation_id": "rerun-missing-info-prompts",
            "must_pass": True,
            "description": "Re-run missing-information prompt corpus checks and verify prompts request only public or user-provided fields.",
        },
        {
            "expectation_id": "rerun-consumer-feedback-triage",
            "must_pass": True,
            "description": "Re-run consumer feedback triage packet checks and verify every proposed change has at least one citation.",
        },
    ],
    "attestations": dict(NO_LIVE_AGENT_ATTESTATION),
}

_PROMPT_REGRESSION_DRY_RUN_PACKET: dict[str, Any] = {
    "packet_id": "agent_prompt_regression_dry_run_fixture_first_v1",
    "packet_kind": "fixture_first_agent_prompt_regression_dry_run",
    "dry_run_only": True,
    "source_packet_ids": list(REQUIRED_SOURCE_PACKET_IDS),
    "reviewer_owner_fields": {
        "review_owner": "ppd_policy_review",
        "engineering_owner": "ppd_guardrails",
        "release_owner": "ppd_release_manager",
        "requires_human_review": True,
    },
    "citations": deepcopy(_CANDIDATE_PACKET["citations"]),
    "execution_policy": {
        "fixtures_only": True,
        "llm_execution_allowed": False,
        "live_llm_executed": False,
        "live_devhub_executed": False,
        "live_crawler_executed": False,
        "live_processor_executed": False,
        "agent_consumers_invoked": False,
        "private_case_files_read": False,
    },
    "state_mutation_flags": {
        "prompt_state_mutation_enabled": False,
        "release_state_mutation_enabled": False,
        "active_prompt_mutation": False,
        "active_release_state_mutation": False,
    },
    "prompt_expectations": [
        {
            "expectation_id": "prompt-missing-info-public-only",
            "before_outcome": "Prompt could ask broadly for missing facts without restating the public-only boundary.",
            "after_outcome": "Prompt asks only for narrow public or user-provided facts and points to fixture-only validation.",
            "citation_ids": ["missing-info-001"],
        }
    ],
    "refusal_expectations": [
        {
            "expectation_id": "refusal-live-action-boundary",
            "before_outcome": "Refusal names the blocked action category without identifying safe fixture alternatives.",
            "after_outcome": "Refusal blocks live PP&D actions and offers fixture-backed review material instead.",
            "citation_ids": ["guardrail-001"],
        }
    ],
    "regression_rerun_expectations": deepcopy(_CANDIDATE_PACKET["regression_rerun_expectations"]),
    "consequential_controls": [
        {"control": "submit permit request", "enabled": False},
        {"control": "upload correction", "enabled": False},
        {"control": "submit payment", "enabled": False},
        {"control": "schedule inspection", "enabled": False},
        {"control": "certify acknowledgement", "enabled": False},
    ],
    "attestations": dict(NO_LIVE_AGENT_ATTESTATION),
}


def build_candidate_packet() -> dict[str, Any]:
    """Return a defensive copy of the deterministic candidate packet."""
    return deepcopy(_CANDIDATE_PACKET)


def build_prompt_regression_dry_run_packet() -> dict[str, Any]:
    """Return a defensive copy of the deterministic dry-run packet."""
    return deepcopy(_PROMPT_REGRESSION_DRY_RUN_PACKET)


def validate_candidate_packet(packet: dict[str, Any]) -> list[str]:
    """Return validation errors for a candidate packet fixture."""
    errors: list[str] = []
    source_ids = set(packet.get("source_packet_ids", []))
    for required_id in REQUIRED_SOURCE_PACKET_IDS:
        if required_id not in source_ids:
            errors.append(f"missing source packet: {required_id}")

    citations = packet.get("citations", [])
    citation_ids = {item.get("citation_id") for item in citations if isinstance(item, Mapping)}
    for item in citations:
        if not isinstance(item, Mapping):
            errors.append("citation entries must be mappings")
            continue
        source_packet_id = item.get("source_packet_id")
        if source_packet_id not in source_ids:
            errors.append(f"citation references unknown source packet: {source_packet_id}")

    for section in ("proposed_prompt_wording_changes", "proposed_refusal_wording_changes"):
        for change in packet.get(section, []):
            if change.get("status") != "candidate_only":
                errors.append(f"{section} change is not candidate_only: {change.get('change_id')}")
            if not change.get("proposed_wording"):
                errors.append(f"{section} change lacks proposed wording: {change.get('change_id')}")
            for citation_id in change.get("citation_ids", []):
                if citation_id not in citation_ids:
                    errors.append(f"{section} references unknown citation: {citation_id}")

    attestations = packet.get("attestations", {})
    for field, expected in NO_LIVE_AGENT_ATTESTATION.items():
        if attestations.get(field) is not expected:
            errors.append(f"attestation {field} must be {expected}")

    owners = packet.get("reviewer_owner_fields", {})
    for field in ("review_owner", "engineering_owner", "release_owner"):
        if not owners.get(field):
            errors.append(f"missing reviewer owner field: {field}")

    if not packet.get("regression_rerun_expectations"):
        errors.append("missing regression rerun expectations")

    errors.extend(_format_findings(validate_prompt_regression_packet_safety(packet)))
    return errors


def validate_prompt_regression_dry_run_packet(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return deterministic rejection findings for a prompt regression dry-run packet."""

    findings: list[dict[str, str]] = []
    _validate_reviewer_owners(packet, findings)
    _validate_rerun_expectations(packet, findings)
    _validate_prompt_and_refusal_expectations(packet, findings)
    _validate_recursive_safety(packet, findings)
    return findings


def validate_prompt_regression_packet_safety(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return safety-only findings that also apply to candidate packets."""

    findings: list[dict[str, str]] = []
    _validate_recursive_safety(packet, findings)
    return findings


def assert_valid_prompt_regression_dry_run_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a prompt regression dry-run packet violates PP&D rules."""

    findings = validate_prompt_regression_dry_run_packet(packet)
    if findings:
        details = "; ".join(f"{item['code']} at {item['path']}" for item in findings)
        raise PromptRegressionPacketError(details)


def _validate_reviewer_owners(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    owners = packet.get("reviewer_owner_fields") or packet.get("reviewer_owners")
    if not isinstance(owners, Mapping):
        findings.append(_finding("missing_reviewer_owners", "Prompt regression dry-run packets require reviewer owners.", "$.reviewer_owner_fields"))
        return
    for field in ("review_owner", "engineering_owner", "release_owner"):
        if not str(owners.get(field) or "").strip():
            findings.append(_finding("missing_reviewer_owner", "Prompt regression dry-run packets require review, engineering, and release owners.", f"$.reviewer_owner_fields.{field}"))


def _validate_rerun_expectations(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    expectations = packet.get("regression_rerun_expectations")
    if not _non_empty_sequence(expectations):
        findings.append(_finding("missing_rerun_expectations", "Prompt regression dry-run packets require rerun expectations.", "$.regression_rerun_expectations"))


def _validate_prompt_and_refusal_expectations(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    citations = _citation_ids(packet.get("citations"))
    for section in ("prompt_expectations", "refusal_expectations"):
        expectations = packet.get(section)
        section_path = f"$.{section}"
        if not _non_empty_sequence(expectations):
            findings.append(_finding(f"missing_{section}", "Prompt regression dry-run packets require prompt and refusal expectations.", section_path))
            continue
        for index, expectation in enumerate(expectations):
            path = f"{section_path}[{index}]"
            if not isinstance(expectation, Mapping):
                findings.append(_finding("invalid_expectation", "Prompt and refusal expectations must be mappings.", path))
                continue
            if not str(expectation.get("before_outcome") or "").strip():
                findings.append(_finding("missing_before_outcome", "Prompt and refusal expectations require before_outcome.", f"{path}.before_outcome"))
            if not str(expectation.get("after_outcome") or "").strip():
                findings.append(_finding("missing_after_outcome", "Prompt and refusal expectations require after_outcome.", f"{path}.after_outcome"))
            if not _has_citation_ids(expectation, citations):
                findings.append(_finding("uncited_expectation", "Prompt and refusal expectations require cited source evidence.", path))


def _validate_recursive_safety(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    for path, key, value in _walk(packet):
        key_text = key.lower()
        if key_text in _PRIVATE_FACT_KEYS and _non_empty(value):
            findings.append(_finding("private_case_facts", "Dry-run packets must not carry private case facts.", path))
        if key_text in _PRIVATE_PATH_KEYS and _non_empty(value):
            findings.append(_finding("local_private_path", "Dry-run packets must not reference private local paths or artifacts.", path))
        if key_text in {"privacy", "privacy_classification", "case_fact_privacy"} and str(value).lower() in _PRIVATE_CLASSIFICATIONS:
            findings.append(_finding("private_case_facts", "Dry-run packets must not include private or authenticated case material.", path))
        if key_text in _LIVE_EXECUTION_KEYS and value not in (False, None, "", "not_run", "fixture_only"):
            findings.append(_finding("live_execution_claim", "Dry-run packets must not claim live LLM, DevHub, crawler, or processor execution.", path))
        if key_text in _MUTATION_FLAG_KEYS and value not in (False, None, "", "disabled", "not_enabled"):
            findings.append(_finding("active_mutation_flag", "Dry-run packets must not enable prompt or release-state mutation flags.", path))
        if _is_enabled_consequential_control(key_text, value):
            findings.append(_finding("enabled_consequential_control", "Submission, upload, payment, scheduling, and certification controls must be disabled.", path))
        if isinstance(value, str):
            lowered = value.lower()
            if _looks_like_local_private_path(value):
                findings.append(_finding("local_private_path", "Dry-run packets must not reference private local paths or artifacts.", path))
            if any(phrase in lowered for phrase in _LIVE_EXECUTION_PHRASES):
                findings.append(_finding("live_execution_claim", "Dry-run packets must not claim live LLM, DevHub, crawler, or processor execution.", path))
            if any(phrase in lowered for phrase in _OUTCOME_GUARANTEE_PHRASES):
                findings.append(_finding("outcome_guarantee", "Dry-run packets must not guarantee legal or permitting outcomes.", path))


def _citation_ids(value: Any) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return set()
    ids: set[str] = set()
    for item in value:
        if isinstance(item, Mapping):
            citation_id = item.get("citation_id") or item.get("source_evidence_id")
            if isinstance(citation_id, str) and citation_id.strip():
                ids.add(citation_id)
        elif isinstance(item, str) and item.strip():
            ids.add(item)
    return ids


def _has_citation_ids(expectation: Mapping[str, Any], known_citations: set[str]) -> bool:
    citation_ids = _string_list(expectation.get("citation_ids") or expectation.get("source_evidence_ids"))
    if not citation_ids:
        return False
    if not known_citations:
        return True
    return all(citation_id in known_citations for citation_id in citation_ids)


def _finding(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _format_findings(findings: Sequence[Mapping[str, str]]) -> list[str]:
    return [f"{item.get('code', 'validation_error')} at {item.get('path', '$')}: {item.get('message', '')}" for item in findings]


def _non_empty(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(_non_empty(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_non_empty(item) for item in value)
    return True


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _walk(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]", key))
    return rows


def _looks_like_local_private_path(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(_LOCAL_PATH_PREFIXES):
        return True
    if "\\" in stripped and len(stripped) > 2 and stripped[1:3] == ":\\":
        return True
    return False


def _is_enabled_consequential_control(key_text: str, value: Any) -> bool:
    if "enabled" in key_text and any(word in key_text for word in _CONSEQUENTIAL_CONTROL_WORDS):
        return value not in (False, None, "", "false", "disabled", "not_enabled")
    if not isinstance(value, Mapping):
        return False
    enabled = value.get("enabled", False) is True or str(value.get("status") or "").lower() in {"enabled", "active", "allowed"}
    if not enabled:
        return False
    label = " ".join(str(value.get(item, "")) for item in ("id", "name", "label", "action", "description", "control"))
    return any(word in label.lower() for word in _CONSEQUENTIAL_CONTROL_WORDS)


__all__ = [
    "NO_LIVE_AGENT_ATTESTATION",
    "PromptRegressionPacketError",
    "REQUIRED_SOURCE_PACKET_IDS",
    "assert_valid_prompt_regression_dry_run_packet",
    "build_candidate_packet",
    "build_prompt_regression_dry_run_packet",
    "validate_candidate_packet",
    "validate_prompt_regression_dry_run_packet",
    "validate_prompt_regression_packet_safety",
]
