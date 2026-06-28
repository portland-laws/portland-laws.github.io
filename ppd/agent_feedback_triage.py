"""Fixture-first PP&D agent consumer feedback triage.

This module intentionally consumes committed handoff fixtures only. It does not call
LLM consumers, read private case files, mutate prompts, or change release state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


_REQUIRED_PACKET_NAMES = (
    "release_consumer_handoff",
    "safe_action_regression",
    "post_promotion_smoke_test_plan",
)

_PRIVATE_FACT_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_fact",
    "case_facts",
    "known_private_fact",
    "known_private_facts",
    "observed_private_values",
    "private_values",
    "applicant_name",
    "owner_name",
    "email_address",
    "phone_number",
    "permit_number",
    "project_address",
    "tax_account_number",
}
_PRIVATE_PATH_KEYS = {
    "private_case_file",
    "private_case_path",
    "auth_state_path",
    "trace_path",
    "har_path",
    "screenshot_path",
    "downloaded_document_path",
    "local_private_path",
    "local_path",
}
_PRIVATE_CLASSIFICATIONS = {
    "private",
    "confidential",
    "restricted",
    "user_private",
    "case_private",
    "devhub_authenticated_private",
}
_LOCAL_PATH_PREFIXES = ("/home/", "/Users/", "/private/", "/tmp/", "file://", "C:\\", "D:\\")
_LIVE_EXECUTION_KEYS = {
    "llm_execution_allowed",
    "llm_executed",
    "live_llm_executed",
    "agent_consumer_invoked",
    "agent_consumers_invoked",
    "devhub_executed",
    "devhub_browser_executed",
    "live_devhub_executed",
    "browser_automation_executed",
    "crawler_executed",
    "live_crawler_executed",
    "processor_executed",
    "live_processor_executed",
}
_LIVE_EXECUTION_PHRASES = (
    "live llm",
    "llm executed",
    "llm execution completed",
    "called the llm",
    "agent consumer invoked",
    "agent consumer executed",
    "live devhub",
    "devhub executed",
    "devhub browser ran",
    "opened devhub",
    "browser automation ran",
    "live crawler",
    "crawler executed",
    "crawler ran",
    "live processor",
    "processor executed",
    "processor ran",
)
_OUTCOME_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "permit will be approved",
    "application will be approved",
    "approval is guaranteed",
    "permit will issue",
    "permit issuance guaranteed",
    "will receive the permit",
    "legally valid",
    "no legal risk",
    "cannot be denied",
)
_CONSEQUENTIAL_CONTROL_WORDS = (
    "submit",
    "submission",
    "upload",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "scheduling",
    "inspection",
    "certify",
    "certification",
    "acknowledge",
    "cancellation",
    "cancel",
)
_ACTIVE_MUTATION_KEYS = {
    "prompt_mutation_active",
    "prompt_mutations_active",
    "prompt_mutation_enabled",
    "prompt_mutations_enabled",
    "prompt_mutations_performed",
    "active_prompt_mutation",
    "release_state_mutation_active",
    "release_state_mutations_active",
    "release_state_mutation_enabled",
    "release_state_mutations_enabled",
    "release_state_mutations_performed",
    "active_release_state_mutation",
}


@dataclass(frozen=True)
class TriageSource:
    """A cited upstream packet entry used by a triage category."""

    packet: str
    citation_id: str
    title: str
    owner: str

    def to_dict(self) -> dict[str, str]:
        return {
            "packet": self.packet,
            "citation_id": self.citation_id,
            "title": self.title,
            "owner": self.owner,
        }


class FeedbackTriageError(ValueError):
    """Raised when fixture packets cannot produce a complete triage packet."""


def build_agent_consumer_feedback_triage(
    packets: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a deterministic fixture-first feedback triage packet."""

    missing = [name for name in _REQUIRED_PACKET_NAMES if name not in packets]
    if missing:
        raise FeedbackTriageError("missing required packets: " + ", ".join(missing))

    _assert_no_unsafe_packet_inputs(packets)

    release_packet = packets["release_consumer_handoff"]
    regression_packet = packets["safe_action_regression"]
    smoke_packet = packets["post_promotion_smoke_test_plan"]

    categories = [
        _release_readiness_category(release_packet),
        _safe_action_boundary_category(regression_packet),
        _smoke_promotion_category(smoke_packet),
        _cross_packet_refusal_category(release_packet, regression_packet, smoke_packet),
    ]

    packet = {
        "packet_id": "fixture-agent-consumer-feedback-triage-v1",
        "packet_type": "agent_consumer_feedback_triage",
        "mode": "fixture_first",
        "input_packets": [
            _packet_summary("release_consumer_handoff", release_packet),
            _packet_summary("safe_action_regression", regression_packet),
            _packet_summary("post_promotion_smoke_test_plan", smoke_packet),
        ],
        "feedback_categories": categories,
        "reviewer_owner_fields": _reviewer_owner_fields(categories),
        "regression_rerun_triggers": _regression_rerun_triggers(categories),
        "attestations": {
            "no_live_agent_consumers_invoked": True,
            "no_live_llm_execution": True,
            "no_live_devhub_execution": True,
            "no_live_crawler_execution": True,
            "no_live_processor_execution": True,
            "no_private_case_files_read": True,
            "no_prompt_mutations_performed": True,
            "no_release_state_mutations_performed": True,
            "fixtures_only": True,
        },
    }
    assert_valid_agent_consumer_feedback_triage(packet)
    return packet


def validate_agent_consumer_feedback_triage(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return deterministic rejection findings for a feedback triage packet."""

    findings: list[dict[str, str]] = []
    _validate_feedback_categories(packet, findings)
    _validate_reviewer_owner_fields(packet, findings)
    _validate_regression_rerun_triggers(packet, findings)
    _validate_recursive_safety(packet, findings)
    return findings


def assert_valid_agent_consumer_feedback_triage(packet: Mapping[str, Any]) -> None:
    """Raise when a feedback triage packet violates PP&D safety rules."""

    findings = validate_agent_consumer_feedback_triage(packet)
    if findings:
        details = "; ".join(f"{item['code']} at {item['path']}" for item in findings)
        raise FeedbackTriageError(details)


def _release_readiness_category(packet: Mapping[str, Any]) -> dict[str, Any]:
    source = _first_source(packet, "release_consumer_handoff")
    return {
        "category_id": "release-consumer-readiness",
        "category": "release consumer readiness",
        "feedback": "Release-consumer handoff must preserve the cited scope, owner, and acceptance evidence before agent-facing promotion.",
        "citations": [source.to_dict()],
        "expected_prompt_or_refusal_updates": [
            {
                "update_type": "prompt_update",
                "expectation": "Prompt copy should ask for missing release evidence instead of inferring readiness from an unchecked handoff.",
            }
        ],
        "reviewer_owner": source.owner,
        "reviewer_owner_field": "release_consumer_reviewer_owner",
        "regression_rerun_triggers": [
            "release handoff scope changes",
            "release consumer owner changes",
            "acceptance evidence citation changes",
        ],
    }


def _safe_action_boundary_category(packet: Mapping[str, Any]) -> dict[str, Any]:
    source = _first_source(packet, "safe_action_regression")
    return {
        "category_id": "safe-action-boundary",
        "category": "safe action and refusal boundary",
        "feedback": "Safe-action regression feedback must distinguish read-only or reversible assistance from consequential, financial, upload, certification, submission, scheduling, cancellation, and account actions.",
        "citations": [source.to_dict()],
        "expected_prompt_or_refusal_updates": [
            {
                "update_type": "refusal_update",
                "expectation": "Refusals should be explicit when a requested action crosses into payment, certification, upload, submission, scheduling, cancellation, or account/security changes.",
            },
            {
                "update_type": "prompt_update",
                "expectation": "Prompts should steer the agent toward cited read-only review or reversible draft preparation when available.",
            },
        ],
        "reviewer_owner": source.owner,
        "reviewer_owner_field": "safe_action_regression_reviewer_owner",
        "regression_rerun_triggers": [
            "safe-action classifier fixture changes",
            "refusal text changes",
            "new consequential action category appears",
        ],
    }


def _smoke_promotion_category(packet: Mapping[str, Any]) -> dict[str, Any]:
    source = _first_source(packet, "post_promotion_smoke_test_plan")
    return {
        "category_id": "post-promotion-smoke-coverage",
        "category": "post-promotion smoke coverage",
        "feedback": "Post-promotion smoke feedback must cite the plan checks that prove promoted artifacts still block unsafe agent actions and preserve review ownership.",
        "citations": [source.to_dict()],
        "expected_prompt_or_refusal_updates": [
            {
                "update_type": "prompt_update",
                "expectation": "Prompt release notes should mention the smoke checks that must rerun after promotion-sensitive fixture changes.",
            }
        ],
        "reviewer_owner": source.owner,
        "reviewer_owner_field": "post_promotion_smoke_reviewer_owner",
        "regression_rerun_triggers": [
            "promotion smoke plan changes",
            "guardrail bundle fixture changes",
            "post-promotion acceptance criteria changes",
        ],
    }


def _cross_packet_refusal_category(
    release_packet: Mapping[str, Any],
    regression_packet: Mapping[str, Any],
    smoke_packet: Mapping[str, Any],
) -> dict[str, Any]:
    sources = [
        _first_source(release_packet, "release_consumer_handoff"),
        _first_source(regression_packet, "safe_action_regression"),
        _first_source(smoke_packet, "post_promotion_smoke_test_plan"),
    ]
    return {
        "category_id": "cross-packet-consumer-feedback",
        "category": "cross-packet consumer feedback",
        "feedback": "Reviewer feedback must stay citation-backed across release handoff, regression, and smoke packets before any prompt or refusal update is proposed for human review.",
        "citations": [source.to_dict() for source in sources],
        "expected_prompt_or_refusal_updates": [
            {
                "update_type": "refusal_update",
                "expectation": "Refusal changes require citations from both boundary regression and post-promotion smoke coverage.",
            },
            {
                "update_type": "prompt_update",
                "expectation": "Prompt changes require a release-consumer citation and an assigned reviewer owner.",
            },
        ],
        "reviewer_owner": "ppd-release-reviewer",
        "reviewer_owner_field": "cross_packet_reviewer_owner",
        "regression_rerun_triggers": [
            "any consumed packet citation changes",
            "review owner mapping changes",
            "expected prompt or refusal update changes",
        ],
    }


def _packet_summary(packet_name: str, packet: Mapping[str, Any]) -> dict[str, Any]:
    source = _first_source(packet, packet_name)
    return {
        "packet": packet_name,
        "packet_id": str(packet.get("packet_id", packet_name)),
        "citation_id": source.citation_id,
        "reviewer_owner": source.owner,
    }


def _first_source(packet: Mapping[str, Any], packet_name: str) -> TriageSource:
    citations = packet.get("citations")
    if not isinstance(citations, list) or not citations:
        raise FeedbackTriageError(f"{packet_name} must include at least one citation")

    first = citations[0]
    if not isinstance(first, Mapping):
        raise FeedbackTriageError(f"{packet_name} citation must be an object")

    citation_id = _required_text(first, "citation_id", packet_name)
    title = _required_text(first, "title", packet_name)
    owner = str(packet.get("reviewer_owner") or first.get("owner") or "ppd-reviewer")
    if not owner.strip():
        raise FeedbackTriageError(f"{packet_name} missing reviewer owner")
    return TriageSource(packet=packet_name, citation_id=citation_id, title=title, owner=owner)


def _required_text(mapping: Mapping[str, Any], field: str, packet_name: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FeedbackTriageError(f"{packet_name} citation missing text field: {field}")
    return value


def _reviewer_owner_fields(categories: list[Mapping[str, Any]]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for category in categories:
        field = str(category["reviewer_owner_field"])
        owner = str(category["reviewer_owner"])
        fields[field] = owner
    return fields


def _regression_rerun_triggers(categories: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    for category in categories:
        triggers.append(
            {
                "category_id": category["category_id"],
                "triggers": list(category["regression_rerun_triggers"]),
            }
        )
    return triggers


def _validate_feedback_categories(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    categories = packet.get("feedback_categories")
    if not isinstance(categories, Sequence) or isinstance(categories, (str, bytes)) or not categories:
        findings.append(_finding("missing_feedback_categories", "Feedback triage packets require feedback categories.", "$.feedback_categories"))
        return
    for index, category in enumerate(categories):
        path = f"$.feedback_categories[{index}]"
        if not isinstance(category, Mapping):
            findings.append(_finding("invalid_feedback_category", "Feedback categories must be mappings.", path))
            continue
        if str(category.get("feedback") or "").strip() and not _has_citation(category.get("citations")):
            findings.append(_finding("uncited_feedback_item", "Feedback items require at least one citation.", f"{path}.citations"))
        if not str(category.get("reviewer_owner") or "").strip():
            findings.append(_finding("missing_reviewer_owner", "Feedback items require reviewer owners.", f"{path}.reviewer_owner"))
        if not _string_list(category.get("regression_rerun_triggers")):
            findings.append(_finding("missing_regression_rerun_trigger", "Feedback items require regression rerun triggers.", f"{path}.regression_rerun_triggers"))


def _validate_reviewer_owner_fields(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    owners = packet.get("reviewer_owner_fields")
    if not isinstance(owners, Mapping) or not owners:
        findings.append(_finding("missing_reviewer_owner", "Feedback triage packets require reviewer owner fields.", "$.reviewer_owner_fields"))
        return
    for field, owner in owners.items():
        if not str(field).strip() or not str(owner).strip():
            findings.append(_finding("missing_reviewer_owner", "Reviewer owner fields must name an owner.", f"$.reviewer_owner_fields.{field}"))


def _validate_regression_rerun_triggers(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    triggers = packet.get("regression_rerun_triggers")
    if not isinstance(triggers, Sequence) or isinstance(triggers, (str, bytes)) or not triggers:
        findings.append(_finding("missing_regression_rerun_trigger", "Feedback triage packets require regression rerun triggers.", "$.regression_rerun_triggers"))
        return
    for index, trigger_group in enumerate(triggers):
        path = f"$.regression_rerun_triggers[{index}]"
        if not isinstance(trigger_group, Mapping):
            findings.append(_finding("missing_regression_rerun_trigger", "Regression rerun trigger groups must be mappings.", path))
            continue
        if not _string_list(trigger_group.get("triggers")):
            findings.append(_finding("missing_regression_rerun_trigger", "Regression rerun trigger groups require triggers.", f"{path}.triggers"))


def _validate_recursive_safety(packet: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    for path, key, value in _walk(packet):
        key_text = key.lower()
        if key_text in _PRIVATE_FACT_KEYS and _non_empty(value):
            findings.append(_finding("private_case_facts", "Feedback triage packets must not carry private case facts.", path))
        if key_text in _PRIVATE_PATH_KEYS and _non_empty(value):
            findings.append(_finding("local_private_path", "Feedback triage packets must not reference private local paths or artifacts.", path))
        if key_text in {"privacy", "privacy_classification", "case_fact_privacy"} and str(value).lower() in _PRIVATE_CLASSIFICATIONS:
            findings.append(_finding("private_case_facts", "Feedback triage packets must not include private or authenticated case material.", path))
        if key_text in _LIVE_EXECUTION_KEYS and value not in (False, None, "", "not_run", "fixture_only"):
            findings.append(_finding("live_execution_claim", "Feedback triage packets must not claim live LLM, DevHub, crawler, or processor execution.", path))
        if key_text in _ACTIVE_MUTATION_KEYS and value not in (False, None, "", "false", "not_performed", "proposed_only"):
            findings.append(_finding("active_mutation_flag", "Feedback triage packets must not carry active prompt or release-state mutation flags.", path))
        if _is_enabled_consequential_control(key_text, value):
            findings.append(_finding("enabled_consequential_control", "Submission, upload, payment, scheduling, certification, cancellation, and account controls must be disabled.", path))
        if isinstance(value, str):
            lowered = value.lower()
            if _looks_like_local_private_path(value):
                findings.append(_finding("local_private_path", "Feedback triage packets must not reference private local paths or artifacts.", path))
            if any(phrase in lowered for phrase in _LIVE_EXECUTION_PHRASES):
                findings.append(_finding("live_execution_claim", "Feedback triage packets must not claim live LLM, DevHub, crawler, or processor execution.", path))
            if any(phrase in lowered for phrase in _OUTCOME_GUARANTEE_PHRASES):
                findings.append(_finding("outcome_guarantee", "Feedback triage packets must not guarantee legal or permitting outcomes.", path))


def _assert_no_unsafe_packet_inputs(packets: Mapping[str, Mapping[str, Any]]) -> None:
    findings: list[dict[str, str]] = []
    _validate_recursive_safety(packets, findings)
    if findings:
        details = "; ".join(f"{item['code']} at {item['path']}" for item in findings)
        raise FeedbackTriageError(details)


def _finding(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _has_citation(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    for item in value:
        if isinstance(item, Mapping):
            if str(item.get("citation_id") or item.get("source_evidence_id") or "").strip():
                return True
        elif str(item).strip():
            return True
    return False


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _non_empty(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(_non_empty(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_non_empty(item) for item in value)
    return True


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
    "FeedbackTriageError",
    "TriageSource",
    "assert_valid_agent_consumer_feedback_triage",
    "build_agent_consumer_feedback_triage",
    "validate_agent_consumer_feedback_triage",
]
