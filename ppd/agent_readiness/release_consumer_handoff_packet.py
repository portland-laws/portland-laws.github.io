"""Validation for PP&D release-consumer handoff packets.

The validator is deterministic and metadata-only. It rejects packet content that
would expose private case facts, imply live execution, enable consequential
controls, or hand off uncited expectations to an agent release consumer.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

PACKET_TYPE = "ppd.release_consumer_handoff_packet.v1"


@dataclass(frozen=True)
class ReleaseConsumerHandoffValidationResult:
    """Machine-readable validation result for release-consumer handoff packets."""

    ready: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "problems": list(self.problems)}


_PRIVATE_FACT_KEYS = {
    "access_token",
    "auth_state",
    "browser_state",
    "case_fact",
    "case_facts",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "devhub_session",
    "email",
    "field_value",
    "har",
    "password",
    "payment_details",
    "phone",
    "private_case_fact",
    "private_case_facts",
    "private_value",
    "raw_case_fact",
    "raw_value",
    "refresh_token",
    "screenshot",
    "secret",
    "session",
    "session_cookie",
    "session_file",
    "session_state",
    "ssn",
    "storage_state",
    "token",
    "trace",
    "user_input",
    "user_supplied_value",
}
_LOCAL_PATH_KEYS = {"file_path", "local_file_path", "local_path", "path", "private_file_path", "session_file"}
_EXPECTED_RESPONSE_KEYS = {
    "expected_agent_response",
    "expected_agent_responses",
    "expected_consumer_response",
    "expected_consumer_responses",
    "expected_response",
    "expected_responses",
    "response_expectation",
    "response_expectations",
}
_LIVE_EXECUTION_KEYS = {
    "crawler_execution_claim",
    "crawler_execution_enabled",
    "devhub_execution_claim",
    "devhub_execution_enabled",
    "execute_crawler",
    "execute_devhub",
    "execute_llm",
    "execute_processor",
    "live_crawler",
    "live_crawler_execution",
    "live_devhub",
    "live_devhub_execution",
    "live_llm",
    "live_llm_execution",
    "live_processor",
    "live_processor_execution",
    "llm_execution_enabled",
    "processor_execution_claim",
    "processor_execution_enabled",
    "ran_crawler",
    "ran_devhub",
    "ran_llm",
    "ran_processor",
}
_CONSEQUENTIAL_CONTROL_KEYS = {
    "allow_cancellation",
    "allow_certification",
    "allow_payment",
    "allow_scheduling",
    "allow_submission",
    "allow_upload",
    "cancellation_enabled",
    "certification_enabled",
    "certify_enabled",
    "consequential_controls_enabled",
    "fee_payment_enabled",
    "final_submit_enabled",
    "official_action_enabled",
    "payment_enabled",
    "purchase_enabled",
    "schedule_enabled",
    "scheduling_enabled",
    "submission_enabled",
    "submit_enabled",
    "upload_enabled",
    "withdraw_enabled",
}
_CONSUMER_STATE_MUTATION_KEYS = {
    "active_consumer_state_mutation",
    "consumer_state_mutation_active",
    "consumer_state_mutation_enabled",
    "consumer_state_write_enabled",
    "mutate_consumer_state",
    "mutates_consumer_state",
    "write_consumer_state",
    "writes_consumer_state",
}
_CONSEQUENTIAL_WORDS = {
    "cancel",
    "cancellation",
    "certification",
    "certify",
    "fee",
    "payment",
    "purchase",
    "schedule",
    "scheduling",
    "submit",
    "submission",
    "upload",
    "withdraw",
}
_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/private/)|(^/var/folders/)|(^~?/\.devhub/)|(^[A-Za-z]:[\\/]Users[\\/][^\\/]+[\\/])",
    re.IGNORECASE,
)
_LIVE_EXECUTION_RE = re.compile(
    r"\b(live\s+(llm|devhub|crawler|crawl|processor)|ran\s+(an?\s+)?(llm|devhub|crawler|crawl|processor)|executed\s+(an?\s+)?(llm|devhub|crawler|crawl|processor)|called\s+(an?\s+)?llm|invoked\s+(an?\s+)?llm|submitted\s+through\s+devhub|uploaded\s+through\s+devhub|processor\s+execution\s+completed|crawler\s+execution\s+completed)\b",
    re.IGNORECASE,
)
_GUARANTEE_RE = re.compile(
    r"\b(guarantee|guarantees|guaranteed|ensure|ensures|assure|assures|promise|promises)\b.{0,80}\b(approval|approved|issuance|issued|permit|permitting|legal|lawful|compliance|compliant|code)\b|"
    r"\b(approval|issuance|permit|permitting|legal|lawful|compliance|compliant|code)\b.{0,80}\b(guaranteed|certain|assured|will\s+be\s+(approved|issued|legal|lawful|compliant))\b",
    re.IGNORECASE,
)


def validate_release_consumer_handoff_packet(packet: Mapping[str, Any]) -> ReleaseConsumerHandoffValidationResult:
    """Return fail-closed validation for a release-consumer handoff packet."""

    evidence_ids = _evidence_ids(packet)
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    problems.extend(_private_fact_and_path_problems(packet))
    problems.extend(_expected_response_citation_problems(packet, evidence_ids))
    problems.extend(_refusal_example_problems(packet, evidence_ids))
    problems.extend(_reviewer_owner_problems(packet, evidence_ids))
    problems.extend(_live_execution_claim_problems(packet))
    problems.extend(_guarantee_claim_problems(packet))
    problems.extend(_enabled_consequential_control_problems(packet))
    problems.extend(_consumer_state_mutation_problems(packet))
    return ReleaseConsumerHandoffValidationResult(ready=not problems, problems=tuple(problems))


def require_release_consumer_handoff_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a release-consumer handoff packet is unsafe."""

    result = validate_release_consumer_handoff_packet(packet)
    if not result.ready:
        raise ValueError("invalid_release_consumer_handoff_packet: " + "; ".join(result.problems))


def _expected_response_citation_problems(value: Any, evidence_ids: set[str], path: str = "$", inherited_refs: frozenset[str] = frozenset()) -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        local_refs = inherited_refs | frozenset(_collect_direct_evidence_refs(value))
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized_key = key_text.lower()
            if normalized_key in _EXPECTED_RESPONSE_KEYS and child not in (None, "", [], {}):
                refs = local_refs | frozenset(_collect_evidence_refs(child))
                if not refs:
                    problems.append(f"expected response lacks source_evidence_ids at {child_path}")
                for ref in sorted(refs):
                    if ref not in evidence_ids:
                        problems.append(f"expected response cites unknown source evidence {ref} at {child_path}")
            problems.extend(_expected_response_citation_problems(child, evidence_ids, child_path, local_refs))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_expected_response_citation_problems(child, evidence_ids, f"{path}[{index}]", inherited_refs))
    return problems


def _refusal_example_problems(packet: Mapping[str, Any], evidence_ids: set[str]) -> list[str]:
    raw = packet.get("refusal_examples") or packet.get("refused_response_examples")
    if not isinstance(raw, list) or not raw:
        return ["release-consumer handoff packet must include refusal_examples"]

    problems: list[str] = []
    for index, example in enumerate(raw):
        path = f"$.refusal_examples[{index}]"
        if not isinstance(example, Mapping):
            problems.append(f"refusal example must be an object at {path}")
            continue
        if not _has_text(example, ("response", "message", "refusal_text", "example")):
            problems.append(f"refusal example lacks response text at {path}")
        refs = _collect_evidence_refs(example)
        if not refs:
            problems.append(f"refusal example lacks source_evidence_ids at {path}")
        for ref in sorted(refs):
            if ref not in evidence_ids:
                problems.append(f"refusal example cites unknown source evidence {ref} at {path}")
    return problems


def _reviewer_owner_problems(packet: Mapping[str, Any], evidence_ids: set[str]) -> list[str]:
    raw = packet.get("reviewer_owners") or packet.get("reviewers") or packet.get("operator_reviewers")
    if not isinstance(raw, list) or not raw:
        return ["release-consumer handoff packet must include reviewer_owners"]

    problems: list[str] = []
    for index, owner in enumerate(raw):
        path = f"$.reviewer_owners[{index}]"
        if not isinstance(owner, Mapping):
            problems.append(f"reviewer owner must be an object at {path}")
            continue
        if not _has_text(owner, ("owner_id", "reviewer_owner_id", "reviewer_id")):
            problems.append(f"reviewer owner lacks owner_id at {path}")
        if not _has_text(owner, ("role", "reviewer_role")):
            problems.append(f"reviewer owner lacks role at {path}")
        refs = _collect_evidence_refs(owner)
        if not refs:
            problems.append(f"reviewer owner lacks source_evidence_ids at {path}")
        for ref in sorted(refs):
            if ref not in evidence_ids:
                problems.append(f"reviewer owner cites unknown source evidence {ref} at {path}")
    return problems


def _private_fact_and_path_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _PRIVATE_FACT_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"private case fact or session field is not allowed at {child_path}")
            if normalized_key in _LOCAL_PATH_KEYS and _contains_local_private_path(child):
                problems.append(f"local private path is not allowed at {child_path}")
            problems.extend(_private_fact_and_path_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_private_fact_and_path_problems(child, f"{path}[{index}]", key_name))
    elif isinstance(value, str) and _LOCAL_PRIVATE_PATH_RE.search(value):
        problems.append(f"local private path is not allowed at {path}")
    return problems


def _live_execution_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _LIVE_EXECUTION_KEYS and child not in (None, False, "", [], {}):
                problems.append(f"live LLM/DevHub/crawler/processor execution claim is not allowed at {child_path}")
            problems.extend(_live_execution_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_live_execution_claim_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _LIVE_EXECUTION_RE.search(value):
        problems.append(f"live LLM/DevHub/crawler/processor execution claim is not allowed at {path}")
    return problems


def _guarantee_claim_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in {"guarantee", "guarantees", "outcome_guarantee", "legal_guarantee", "permitting_guarantee"} and child not in (None, False, "", [], {}):
                problems.append(f"legal or permitting outcome guarantee is not allowed at {child_path}")
            problems.extend(_guarantee_claim_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_guarantee_claim_problems(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _GUARANTEE_RE.search(value):
        problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
    return problems


def _enabled_consequential_control_problems(value: Any, path: str = "$", key_name: str = "") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _CONSEQUENTIAL_CONTROL_KEYS and child is True:
                problems.append(f"enabled consequential control is not allowed at {child_path}")
            if normalized_key in {"control", "controls", "action", "actions", "capability", "capabilities"} and _contains_enabled_consequential_control(child):
                problems.append(f"enabled consequential control is not allowed at {child_path}")
            problems.extend(_enabled_consequential_control_problems(child, child_path, normalized_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_enabled_consequential_control_problems(child, f"{path}[{index}]", key_name))
    return problems


def _consumer_state_mutation_problems(value: Any, path: str = "$") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in _CONSUMER_STATE_MUTATION_KEYS and child is True:
                problems.append(f"active consumer-state mutation flag is not allowed at {child_path}")
            problems.extend(_consumer_state_mutation_problems(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            problems.extend(_consumer_state_mutation_problems(child, f"{path}[{index}]"))
    return problems


def _contains_enabled_consequential_control(value: Any) -> bool:
    if isinstance(value, Mapping):
        enabled = value.get("enabled") is True or value.get("allowed") is True or str(value.get("state") or value.get("status") or "").lower() in {"enabled", "allowed", "ready"}
        descriptor = " ".join(str(value.get(key, "")) for key in ("id", "name", "type", "action", "label", "category", "control_id"))
        return enabled and _mentions_consequential_action(descriptor)
    if isinstance(value, list):
        return any(_contains_enabled_consequential_control(item) for item in value)
    return False


def _mentions_consequential_action(value: str) -> bool:
    normalized = re.sub(r"[^a-z]+", " ", value.lower())
    return bool(set(normalized.split()) & _CONSEQUENTIAL_WORDS)


def _evidence_ids(packet: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("normalized_source_evidence", "citations", "sources", "source_registry"):
        raw = packet.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            for id_key in ("evidence_id", "source_evidence_id", "citation_id", "source_id"):
                value = item.get(id_key)
                if isinstance(value, str) and value:
                    ids.add(value)
    return ids


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        refs.update(_collect_direct_evidence_refs(value))
        for child in value.values():
            refs.update(_collect_evidence_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_collect_evidence_refs(child))
    return refs


def _collect_direct_evidence_refs(value: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("source_evidence_ids", "citation_ids", "evidence_ids"):
        raw = value.get(key)
        if isinstance(raw, list):
            refs.update(item for item in raw if isinstance(item, str) and item)
    for key in ("source_evidence_id", "citation_id", "evidence_id"):
        raw = value.get(key)
        if isinstance(raw, str) and raw:
            refs.add(raw)
    return refs


def _contains_local_private_path(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_LOCAL_PRIVATE_PATH_RE.search(value))
    if isinstance(value, list):
        return any(_contains_local_private_path(item) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_local_private_path(item) for item in value.values())
    return False


def _has_text(value: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        raw = value.get(key)
        if isinstance(raw, str) and raw.strip():
            return True
    return False
