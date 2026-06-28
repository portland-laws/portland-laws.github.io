"""Validation for requirement rerun work-queue packets.

The rerun queue is a planning surface only. Packets accepted here may identify
already-cited requirements, affected process models, affected guardrails, ordered
review steps, and reviewer owners. They must not claim live crawl/extraction work,
processor execution, raw artifact access, legal outcomes, permitting outcomes, or
active mutation of requirements, processes, or guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


FORBIDDEN_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|_)(raw|body|raw_body)(_ref|_refs|_url|_urls|_path|_paths)?$"),
    re.compile(r"(^|_)(download|archive|warc|snapshot)(_ref|_refs|_url|_urls|_path|_paths)?$"),
    re.compile(r"(^|_)(live|execute|processor|crawl|extract|mutate|mutation)(_.*)?$"),
)

FORBIDDEN_TEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\braw\s+(body|html|pdf|response|content)\b", re.IGNORECASE),
    re.compile(r"\b(download|archive|warc|snapshot)\s+(url|path|ref|artifact|body|file)\b", re.IGNORECASE),
    re.compile(r"\b(live\s+extraction|live\s+crawl|execute\s+processor|processor\s+execution)\b", re.IGNORECASE),
    re.compile(r"\b(will|guarantee(?:d|s)?|ensure(?:s|d)?)\s+(be\s+)?(approved|issued|accepted|permitted|legal|compliant)\b", re.IGNORECASE),
    re.compile(r"\b(approval|issuance|permit|legality|compliance)\s+(is\s+)?guaranteed\b", re.IGNORECASE),
)

ACTIVE_MUTATION_KEYS: frozenset[str] = frozenset(
    {
        "active_requirement_mutation",
        "active_process_mutation",
        "active_guardrail_mutation",
        "mutates_requirements",
        "mutates_processes",
        "mutates_guardrails",
        "write_requirements",
        "write_processes",
        "write_guardrails",
    }
)


@dataclass(frozen=True)
class RequirementRerunValidationResult:
    """Structured validation result for a rerun work-queue packet."""

    valid: bool
    errors: tuple[str, ...]

    def require_valid(self) -> None:
        if not self.valid:
            raise ValueError("; ".join(self.errors))


def validate_requirement_rerun_work_queue_packet(
    packet: Mapping[str, Any]
) -> RequirementRerunValidationResult:
    """Validate a requirement rerun work-queue packet.

    The accepted shape is intentionally plain so supervisor-generated JSON can be
    checked before any worker consumes it. Required top-level fields are:

    - requirement_ids: non-empty list of requirement identifiers
    - citations: mapping from every requirement identifier to non-empty evidence refs
    - affected_process_refs: non-empty list of process identifiers
    - affected_guardrail_refs: non-empty list of guardrail identifiers
    - rerun_steps: ordered list of step objects with integer order values starting at 1
    - reviewer_owners: non-empty list of reviewer owner identifiers
    """

    errors: list[str] = []

    if not isinstance(packet, Mapping):
        return RequirementRerunValidationResult(False, ("packet must be a mapping",))

    requirement_ids = _string_list(packet.get("requirement_ids"))
    if not requirement_ids:
        errors.append("requirement_ids must be a non-empty list of strings")

    citations = packet.get("citations")
    if not isinstance(citations, Mapping):
        errors.append("citations must map every requirement_id to source evidence")
    else:
        for requirement_id in requirement_ids:
            evidence = citations.get(requirement_id)
            if not _string_list(evidence):
                errors.append(f"requirement_id {requirement_id!r} is missing citation evidence")

    if not _string_list(packet.get("affected_process_refs")):
        errors.append("affected_process_refs must include at least one process reference")

    if not _string_list(packet.get("affected_guardrail_refs")):
        errors.append("affected_guardrail_refs must include at least one guardrail reference")

    rerun_steps = packet.get("rerun_steps")
    if not isinstance(rerun_steps, Sequence) or isinstance(rerun_steps, (str, bytes)) or not rerun_steps:
        errors.append("rerun_steps must be a non-empty ordered list")
    else:
        step_orders: list[int] = []
        for index, step in enumerate(rerun_steps, start=1):
            if not isinstance(step, Mapping):
                errors.append(f"rerun_steps[{index - 1}] must be a mapping")
                continue
            order = step.get("order")
            if not isinstance(order, int) or isinstance(order, bool):
                errors.append(f"rerun_steps[{index - 1}].order must be an integer")
                continue
            step_orders.append(order)
        expected_orders = list(range(1, len(step_orders) + 1))
        if step_orders and step_orders != expected_orders:
            errors.append(f"rerun_steps must be ordered as {expected_orders}, got {step_orders}")

    if not _string_list(packet.get("reviewer_owners")):
        errors.append("reviewer_owners must include at least one owner")

    _collect_forbidden_claim_errors(packet, errors)

    return RequirementRerunValidationResult(not errors, tuple(errors))


def require_requirement_rerun_work_queue_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the packet after validation or raise ValueError with all errors."""

    result = validate_requirement_rerun_work_queue_packet(packet)
    result.require_valid()
    return packet


def _string_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        strings = tuple(item for item in value if isinstance(item, str) and item.strip())
        if len(strings) == len(value):
            return strings
    return ()


def _collect_forbidden_claim_errors(value: Any, errors: list[str], path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in ACTIVE_MUTATION_KEYS and bool(child):
                errors.append(f"{child_path} sets an active mutation flag")
            if any(pattern.search(key_text) for pattern in FORBIDDEN_KEY_PATTERNS):
                errors.append(f"{child_path} uses a forbidden raw, live, processor, archive, download, or mutation field")
            _collect_forbidden_claim_errors(child, errors, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _collect_forbidden_claim_errors(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains a forbidden claim: {value!r}")
                break
