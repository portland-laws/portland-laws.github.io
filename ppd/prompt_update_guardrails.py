"""Validation for PP&D agent prompt update candidate packets.

The validator is intentionally conservative: candidate packets are commit-safe
proposals, not execution ledgers or release controls. They may describe a
prompt/refusal change only when that change is cited, reviewed, and tied to
regression rerun expectations.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


_LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(?i)(?:\bfile://|\b/Users/|\b/home/|\b/private/|\b/var/folders/|\b/tmp/|\bC:\\\\Users\\|\b[A-Z]:\\\\Users\\)"
)

_LIVE_EXECUTION_RE = re.compile(
    r"(?i)\b(?:"
    r"(?:ran|run|executed|called|queried|used|invoked)\s+(?:the\s+)?(?:live\s+)?(?:llm|devhub|crawler|processor)|"
    r"(?:live\s+)?(?:llm|devhub|crawler|processor)\s+(?:run|execution|call|query|crawl|session)\s+(?:completed|succeeded|ran|executed)|"
    r"crawled\s+(?:live|production|devhub|portland)|"
    r"processed\s+(?:live|production|devhub|crawler)"
    r")\b"
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"(?i)\b(?:"
    r"guarantee(?:s|d)?\s+(?:approval|issuance|compliance|permit|legal|outcome)|"
    r"(?:permit|application|plans?)\s+(?:will|shall)\s+(?:be\s+)?(?:approved|issued|accepted)|"
    r"(?:legally|fully)\s+compliant|"
    r"ensures?\s+(?:approval|issuance|legal\s+compliance|permit\s+approval)"
    r")\b"
)

_PRIVATE_FACT_KEYS = {
    "applicant_name",
    "applicant_email",
    "applicant_phone",
    "case_fact",
    "case_facts",
    "known_facts",
    "owner_name",
    "private_case_fact",
    "private_case_facts",
    "private_fact",
    "private_facts",
    "property_address",
    "tax_account",
    "user_fact",
    "user_facts",
}

_MUTATION_FLAG_KEYS = {
    "active_prompt_mutation",
    "apply_to_active_prompt",
    "deploy_release",
    "enable_release_state_mutation",
    "mutate_active_prompt",
    "mutate_release_state",
    "publish_release",
    "release_state_mutation",
    "write_active_prompt",
    "write_release_state",
}

_CONSEQUENTIAL_ACTION_WORDS = {
    "cancel",
    "certify",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
}

_CONSEQUENTIAL_CLASSES = {"consequential", "financial", "official", "submission"}


@dataclass(frozen=True)
class PacketViolation:
    """A validation failure for an agent prompt update candidate packet."""

    code: str
    path: str
    message: str


def validate_agent_prompt_update_candidate(packet: Mapping[str, Any]) -> list[PacketViolation]:
    """Return all safety violations found in a prompt update candidate packet."""

    violations: list[PacketViolation] = []

    violations.extend(_reject_private_case_facts(packet))
    violations.extend(_reject_local_private_paths(packet))
    violations.extend(_reject_uncited_prompt_or_refusal_changes(packet))
    violations.extend(_reject_missing_regression_expectations(packet))
    violations.extend(_reject_missing_reviewer_owners(packet))
    violations.extend(_reject_live_execution_claims(packet))
    violations.extend(_reject_outcome_guarantees(packet))
    violations.extend(_reject_enabled_consequential_controls(packet))
    violations.extend(_reject_mutation_flags(packet))

    return violations


def assert_agent_prompt_update_candidate_safe(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a prompt update candidate packet is unsafe."""

    violations = validate_agent_prompt_update_candidate(packet)
    if violations:
        details = "; ".join(f"{violation.code} at {violation.path}" for violation in violations)
        raise ValueError(f"unsafe PP&D prompt update candidate packet: {details}")


def _reject_private_case_facts(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for path, key, value in _walk_key_values(packet):
        normalized_key = key.lower()
        if normalized_key in _PRIVATE_FACT_KEYS and _is_nonempty(value):
            violations.append(
                PacketViolation(
                    "private_case_facts",
                    path,
                    "candidate packets must not include private case facts or applicant/property values",
                )
            )
        if normalized_key in {"privacy", "privacy_classification"} and str(value).lower() in {
            "private",
            "case_private",
            "personal",
            "pii",
        }:
            violations.append(
                PacketViolation(
                    "private_case_facts",
                    path,
                    "candidate packets must not carry privately classified facts",
                )
            )
    return violations


def _reject_local_private_paths(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for path, value in _walk_strings(packet):
        if _LOCAL_PRIVATE_PATH_RE.search(value):
            violations.append(
                PacketViolation(
                    "local_private_path",
                    path,
                    "candidate packets must not include local private filesystem paths",
                )
            )
    return violations


def _reject_uncited_prompt_or_refusal_changes(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for field in ("prompt_changes", "refusal_changes"):
        changes = packet.get(field)
        if not _is_nonempty(changes):
            continue
        for index, change in enumerate(_as_sequence(changes)):
            path = f"$.{field}[{index}]"
            if not isinstance(change, Mapping):
                violations.append(
                    PacketViolation("uncited_prompt_or_refusal_change", path, "prompt/refusal changes must be structured and cited")
                )
                continue
            if not _has_citation(change):
                violations.append(
                    PacketViolation(
                        "uncited_prompt_or_refusal_change",
                        path,
                        "prompt/refusal changes must include citations or source evidence IDs",
                    )
                )
    return violations


def _reject_missing_regression_expectations(packet: Mapping[str, Any]) -> list[PacketViolation]:
    expectations = packet.get("regression_rerun_expectations") or packet.get("regression_reruns")
    if not _is_nonempty(expectations):
        return [
            PacketViolation(
                "missing_regression_rerun_expectations",
                "$.regression_rerun_expectations",
                "candidate packets must declare regression reruns and expected outcomes",
            )
        ]
    for index, expectation in enumerate(_as_sequence(expectations)):
        if not isinstance(expectation, Mapping):
            return [
                PacketViolation(
                    "missing_regression_rerun_expectations",
                    f"$.regression_rerun_expectations[{index}]",
                    "each regression rerun expectation must be structured",
                )
            ]
        has_target = _is_nonempty(expectation.get("test")) or _is_nonempty(expectation.get("suite"))
        has_expected = _is_nonempty(expectation.get("expected")) or _is_nonempty(expectation.get("expected_result"))
        if not has_target or not has_expected:
            return [
                PacketViolation(
                    "missing_regression_rerun_expectations",
                    f"$.regression_rerun_expectations[{index}]",
                    "each regression rerun expectation must name a test or suite and expected result",
                )
            ]
    return []


def _reject_missing_reviewer_owners(packet: Mapping[str, Any]) -> list[PacketViolation]:
    reviewers = packet.get("reviewer_owners") or packet.get("reviewers")
    if not _is_nonempty(reviewers):
        return [
            PacketViolation(
                "missing_reviewer_owners",
                "$.reviewer_owners",
                "candidate packets must identify reviewer owners",
            )
        ]
    return []


def _reject_live_execution_claims(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for path, value in _walk_strings(packet):
        if _LIVE_EXECUTION_RE.search(value):
            violations.append(
                PacketViolation(
                    "live_execution_claim",
                    path,
                    "candidate packets must not claim live LLM, DevHub, crawler, or processor execution",
                )
            )
    return violations


def _reject_outcome_guarantees(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for path, value in _walk_strings(packet):
        if _OUTCOME_GUARANTEE_RE.search(value):
            violations.append(
                PacketViolation(
                    "outcome_guarantee",
                    path,
                    "candidate packets must not guarantee legal or permitting outcomes",
                )
            )
    return violations


def _reject_enabled_consequential_controls(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    controls = packet.get("controls") or packet.get("action_controls") or []
    for index, control in enumerate(_as_sequence(controls)):
        path = f"$.controls[{index}]"
        if not isinstance(control, Mapping):
            continue
        if control.get("enabled") is not True:
            continue
        classification = str(control.get("classification") or control.get("action_class") or "").lower()
        action = str(control.get("action") or control.get("name") or control.get("control") or "").lower()
        action_words = set(re.findall(r"[a-z]+", action))
        if classification in _CONSEQUENTIAL_CLASSES or action_words.intersection(_CONSEQUENTIAL_ACTION_WORDS):
            violations.append(
                PacketViolation(
                    "enabled_consequential_control",
                    path,
                    "candidate packets must not enable consequential, financial, or official action controls",
                )
            )
    return violations


def _reject_mutation_flags(packet: Mapping[str, Any]) -> list[PacketViolation]:
    violations: list[PacketViolation] = []
    for path, key, value in _walk_key_values(packet):
        if key.lower() in _MUTATION_FLAG_KEYS and value is True:
            violations.append(
                PacketViolation(
                    "active_prompt_or_release_state_mutation",
                    path,
                    "candidate packets must not set active prompt or release-state mutation flags",
                )
            )
    return violations


def _has_citation(change: Mapping[str, Any]) -> bool:
    citation_fields = (
        "citation",
        "citations",
        "source_evidence_id",
        "source_evidence_ids",
        "source_ids",
        "evidence",
    )
    return any(_is_nonempty(change.get(field)) for field in citation_fields)


def _is_nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping) or isinstance(value, Sequence):
        return bool(value)
    return True


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return value
    return [value]


def _walk_key_values(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_path = f"{path}.{child_key}"
            yield child_path, str(child_key), child_value
            yield from _walk_key_values(child_value, child_path, str(child_key))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk_key_values(child_value, f"{path}[{index}]", key)


def _walk_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield from _walk_strings(child_value, f"{path}.{child_key}")
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk_strings(child_value, f"{path}[{index}]")
