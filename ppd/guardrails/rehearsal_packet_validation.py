"""Validation for guardrail recompilation rehearsal packets.

The validator is intentionally schema-tolerant because rehearsal packets are assembled
from multiple daemon stages. It fails closed on the guardrail hazards that must never
ship in a rehearsal packet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

REQUIRED_REFUSAL_DOMAINS = (
    "payment",
    "upload",
    "submission",
    "scheduling",
    "cancellation",
    "certification",
)

PRIVATE_FACT_MARKERS = (
    "ssn",
    "social_security",
    "date_of_birth",
    "dob",
    "password",
    "passphrase",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "session_cookie",
    "auth_cookie",
    "private_fact",
    "private_facts",
)

PRODUCTION_FLAG_KEYS = (
    "activate_production",
    "production_activation",
    "production_enabled",
    "deploy_to_production",
    "live_mode",
    "enable_live_guardrails",
)

ACTIVE_BUNDLE_KEYS = (
    "active_guardrail_bundle",
    "current_guardrail_bundle",
    "live_guardrail_bundle",
)

MUTATING_OPERATIONS = ("mutate", "mutation", "update", "replace", "write", "patch")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str


def validate_rehearsal_packet(packet: dict[str, Any]) -> list[ValidationIssue]:
    """Return all guardrail rehearsal packet validation issues."""

    issues: list[ValidationIssue] = []
    issues.extend(_validate_predicate_citations(packet))
    issues.extend(_validate_refusal_coverage(packet))
    issues.extend(_validate_exact_confirmation_gates(packet))
    issues.extend(_validate_private_facts(packet))
    issues.extend(_validate_reviewer_prompts(packet))
    issues.extend(_validate_production_activation(packet))
    issues.extend(_validate_active_bundle_mutation(packet))
    return issues


def assert_valid_rehearsal_packet(packet: dict[str, Any]) -> None:
    """Raise ValueError when a rehearsal packet violates guardrail requirements."""

    issues = validate_rehearsal_packet(packet)
    if issues:
        details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(details)


def _validate_predicate_citations(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, change in _iter_dicts(packet):
        kind = str(change.get("kind") or change.get("type") or change.get("change_type") or "").lower()
        name = str(change.get("name") or change.get("predicate") or change.get("target") or "").lower()
        is_predicate_change = "predicate" in kind or "predicate" in name or "predicate_delta" in change
        if is_predicate_change and not _has_citation(change):
            issues.append(
                ValidationIssue(
                    "uncited_predicate_change",
                    "predicate changes must include source citations",
                    path,
                )
            )
    return issues


def _validate_refusal_coverage(packet: dict[str, Any]) -> list[ValidationIssue]:
    covered = _covered_domains(packet.get("refusal_coverage"))
    missing = [domain for domain in REQUIRED_REFUSAL_DOMAINS if domain not in covered]
    if not missing:
        return []
    return [
        ValidationIssue(
            "missing_refusal_coverage",
            "missing refusal coverage for: " + ", ".join(missing),
            "refusal_coverage",
        )
    ]


def _validate_exact_confirmation_gates(packet: dict[str, Any]) -> list[ValidationIssue]:
    gates = _covered_domains(packet.get("exact_confirmation_gates"))
    missing = [domain for domain in REQUIRED_REFUSAL_DOMAINS if domain not in gates]
    if not missing:
        return []
    return [
        ValidationIssue(
            "missing_exact_confirmation_gate",
            "missing exact-confirmation gates for: " + ", ".join(missing),
            "exact_confirmation_gates",
        )
    ]


def _validate_private_facts(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, value in _walk(packet):
        marker = _private_marker(path, value)
        if marker:
            issues.append(
                ValidationIssue(
                    "private_fact_present",
                    f"private fact marker is not allowed in rehearsal packets: {marker}",
                    path,
                )
            )
    return issues


def _validate_reviewer_prompts(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    prompts = packet.get("reviewer_prompts") or packet.get("review_prompts") or []
    if isinstance(prompts, dict):
        prompts = list(prompts.values())
    if not isinstance(prompts, list):
        return issues
    for index, prompt in enumerate(prompts):
        if not isinstance(prompt, dict):
            continue
        path = f"reviewer_prompts[{index}]"
        status = str(prompt.get("status") or "").lower()
        marked_resolved = prompt.get("resolved") is True or status == "resolved"
        unresolved = prompt.get("unresolved") is True or str(prompt.get("state") or "").lower() == "unresolved"
        resolution = str(prompt.get("resolution") or prompt.get("answer") or "").strip().lower()
        if marked_resolved and (unresolved or not resolution or resolution in {"todo", "tbd", "unresolved"}):
            issues.append(
                ValidationIssue(
                    "unresolved_reviewer_prompt_marked_resolved",
                    "reviewer prompts cannot be marked resolved without a concrete resolution",
                    path,
                )
            )
    return issues


def _validate_production_activation(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].lower().replace("-", "_")
        if key in PRODUCTION_FLAG_KEYS and value is True:
            issues.append(
                ValidationIssue(
                    "production_activation_flag",
                    "rehearsal packets cannot enable production activation",
                    path,
                )
            )
        if key in {"environment", "target_environment"} and str(value).lower() in {"prod", "production"}:
            issues.append(
                ValidationIssue(
                    "production_activation_flag",
                    "rehearsal packets cannot target production",
                    path,
                )
            )
    return issues


def _validate_active_bundle_mutation(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, value in _iter_dicts(packet):
        normalized_keys = {str(key).lower().replace("-", "_") for key in value}
        touches_active = bool(normalized_keys.intersection(ACTIVE_BUNDLE_KEYS))
        target = str(value.get("target") or value.get("bundle") or value.get("bundle_state") or "").lower()
        operation = str(value.get("operation") or value.get("op") or value.get("action") or "").lower()
        mutates = any(word in operation for word in MUTATING_OPERATIONS)
        if (touches_active or target in {"active", "current", "live"}) and mutates:
            issues.append(
                ValidationIssue(
                    "active_guardrail_bundle_mutation",
                    "rehearsal packets cannot mutate the active guardrail bundle",
                    path,
                )
            )
    return issues


def _covered_domains(value: Any) -> set[str]:
    covered: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            domain = str(key).lower().replace("_", "-")
            if item is True or (isinstance(item, dict) and item.get("covered") is True):
                covered.add(domain.replace("-", "_"))
            if isinstance(item, (dict, list, tuple, set)):
                covered.update(_covered_domains(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str):
                covered.add(item.lower().replace("-", "_"))
            else:
                covered.update(_covered_domains(item))
    return covered


def _has_citation(change: dict[str, Any]) -> bool:
    for key in ("citations", "source_citations", "sources", "evidence", "citation"):
        value = change.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(bool(str(item).strip()) for item in value):
            return True
    return False


def _private_marker(path: str, value: Any) -> str | None:
    lowered_path = path.lower().replace("-", "_")
    for marker in PRIVATE_FACT_MARKERS:
        if marker in lowered_path:
            return marker
    if isinstance(value, str):
        lowered_value = value.lower().replace("-", "_")
        for marker in PRIVATE_FACT_MARKERS:
            if marker in lowered_value:
                return marker
    return None


def _iter_dicts(value: Any, path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from _iter_dicts(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_dicts(item, f"{path}[{index}]")


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")
