"""Fixture-first RequirementNode candidate queue v5.

This module consumes only committed public citation span inventory v5 fixtures. It
rejects incomplete RequirementNode candidate rows, missing citation/source fields,
live extraction claims, private/session/auth artifacts, raw bodies, downloaded
document claims, legal/permitting guarantees, and active mutation flags.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

QUEUE_VERSION = "requirement_candidate_queue_v5"
PUBLIC_INVENTORY_VERSION = "public_citation_span_inventory_v5"

REQUIREMENT_TYPES = frozenset(
    {
        "obligation",
        "prohibition",
        "permission",
        "precondition",
        "exception",
        "deadline",
        "fee_trigger",
        "license_requirement",
        "document_requirement",
        "action_gate",
    }
)

CONFIDENCE_LABELS = frozenset({"high", "medium", "low"})
HUMAN_REVIEW_STATUSES = frozenset({"pending_human_review", "needs_human_review", "held_for_review"})
FORMALIZATION_STATUSES = frozenset({"not_formalized", "blocked_from_formalization", "pending_formalization_review"})
REVIEWER_HOLDS = frozenset({"hold_for_human_review", "hold_for_citation_trace", "hold_for_formalization_review"})

EXPECTED_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/requirement_candidate_queue_v5.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_requirement_candidate_queue_v5.py"),
)

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_artifact",
        "auth_state",
        "body",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "document_text",
        "downloaded_document",
        "downloaded_documents",
        "downloaded_document_path",
        "downloaded_path",
        "downloaded_url",
        "html",
        "html_body",
        "local_private_path",
        "page_source",
        "password",
        "private_artifact",
        "raw_body",
        "raw_crawl_output",
        "raw_html",
        "raw_public_body",
        "raw_text",
        "session_artifact",
        "session_state",
        "screenshot",
        "storage_state",
        "trace",
    }
)

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active",
        "active_mutation",
        "active_requirement_mutation",
        "active_process_model_mutation",
        "active_guardrail_mutation",
    }
)

PROHIBITED_PHRASES = frozenset(
    {
        "active mutation",
        "authenticated artifact",
        "auth state",
        "downloaded document",
        "downloaded pdf",
        "guaranteed approval",
        "guaranteed permit",
        "legal advice",
        "live extraction",
        "permit guaranteed",
        "private artifact",
        "raw body",
        "raw crawl output",
        "session artifact",
    }
)


@dataclass(frozen=True)
class CandidateRow:
    candidate_id: str
    queue_version: str
    requirement_node_candidate: bool
    active: bool
    active_mutation: bool
    citation_span_inventory_ref: str
    citation_span_id: str
    requirement_type: str
    source_evidence_id: str
    citation: str
    normalized_text: str
    confidence_label: str
    human_review_status: str
    formalization_status: str
    reviewer_holds: tuple[str, ...]
    rollback_notes: str
    validation_commands_exact: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "queue_version": self.queue_version,
            "requirement_node_candidate": self.requirement_node_candidate,
            "active": self.active,
            "active_mutation": self.active_mutation,
            "citation_span_inventory_ref": self.citation_span_inventory_ref,
            "citation_span_id": self.citation_span_id,
            "requirement_type": self.requirement_type,
            "source_evidence_id": self.source_evidence_id,
            "citation": self.citation,
            "normalized_text": self.normalized_text,
            "confidence_label": self.confidence_label,
            "human_review_status": self.human_review_status,
            "formalization_status": self.formalization_status,
            "reviewer_holds": list(self.reviewer_holds),
            "rollback_notes": self.rollback_notes,
            "validation_commands_exact": [list(command) for command in self.validation_commands_exact],
        }


def load_public_citation_span_inventory_v5(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    _reject_prohibited_content(payload)
    version = payload.get("fixture_version") or payload.get("inventory_version") or payload.get("version")
    if version != PUBLIC_INVENTORY_VERSION:
        raise ValueError(f"expected {PUBLIC_INVENTORY_VERSION}, got {version!r}")
    _required_text(payload, "inventory_reference")
    return payload


def build_candidate_queue_from_fixture(path: Path) -> list[dict[str, Any]]:
    inventory = load_public_citation_span_inventory_v5(path)
    inventory_ref = _required_text(inventory, "inventory_reference")
    spans = list(_iter_spans(inventory))
    if not spans:
        raise ValueError("missing RequirementNode candidate rows")
    candidates = [_candidate_from_span(index, inventory_ref, span) for index, span in enumerate(spans, start=1)]
    rows = [candidate.to_dict() for candidate in candidates]
    for row in rows:
        validate_candidate_row_v5(row)
    return rows


def validate_candidate_row_v5(row: Mapping[str, Any]) -> None:
    _reject_prohibited_content(row)
    if row.get("queue_version") != QUEUE_VERSION:
        raise ValueError("candidate row must declare requirement_candidate_queue_v5")
    if row.get("requirement_node_candidate") is not True:
        raise ValueError("missing RequirementNode candidate row marker")
    if row.get("active") is not False:
        raise ValueError("candidate row must remain inactive")
    if row.get("active_mutation") is not False:
        raise ValueError("active mutation flags are not allowed")
    _required_text(row, "candidate_id")
    _required_text(row, "citation_span_inventory_ref")
    _required_text(row, "citation_span_id")
    requirement_type = _required_text(row, "requirement_type")
    if requirement_type not in REQUIREMENT_TYPES:
        raise ValueError(f"unsupported requirement_type: {requirement_type}")
    _required_text(row, "source_evidence_id")
    _required_text(row, "citation")
    _required_text(row, "normalized_text")
    confidence_label = _required_text(row, "confidence_label")
    if confidence_label not in CONFIDENCE_LABELS:
        raise ValueError(f"unsupported confidence_label: {confidence_label}")
    human_review_status = _required_text(row, "human_review_status")
    if human_review_status not in HUMAN_REVIEW_STATUSES:
        raise ValueError(f"unsupported human_review_status: {human_review_status}")
    formalization_status = _required_text(row, "formalization_status")
    if formalization_status not in FORMALIZATION_STATUSES:
        raise ValueError(f"unsupported formalization_status: {formalization_status}")
    _required_allowed_text_list(row, "reviewer_holds", REVIEWER_HOLDS)
    _required_text(row, "rollback_notes")
    if row.get("validation_commands_exact") != [list(command) for command in EXPECTED_VALIDATION_COMMANDS]:
        raise ValueError("missing validation commands")


def _iter_spans(inventory: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    spans = inventory.get("citation_spans")
    if not isinstance(spans, list):
        raise ValueError("citation_spans must be a list")
    for span in spans:
        if not isinstance(span, Mapping):
            raise ValueError("each citation span must be an object")
        yield span


def _candidate_from_span(index: int, inventory_ref: str, span: Mapping[str, Any]) -> CandidateRow:
    _reject_prohibited_content(span)
    if span.get("requirement_node_candidate") is not True:
        raise ValueError("missing RequirementNode candidate row marker")
    if span.get("active_mutation") is not False:
        raise ValueError("active mutation flags are not allowed")
    citation_span_ref = _required_text(span, "citation_span_inventory_ref")
    if citation_span_ref != inventory_ref:
        raise ValueError("citation span inventory reference does not match fixture inventory_reference")
    requirement_type = _required_text(span, "requirement_type")
    if requirement_type not in REQUIREMENT_TYPES:
        raise ValueError(f"unsupported requirement_type: {requirement_type}")
    confidence_label = _required_text(span, "confidence_label")
    if confidence_label not in CONFIDENCE_LABELS:
        raise ValueError(f"unsupported confidence_label: {confidence_label}")
    human_review_status = _required_text(span, "human_review_status")
    if human_review_status not in HUMAN_REVIEW_STATUSES:
        raise ValueError(f"unsupported human_review_status: {human_review_status}")
    formalization_status = _required_text(span, "formalization_status")
    if formalization_status not in FORMALIZATION_STATUSES:
        raise ValueError(f"unsupported formalization_status: {formalization_status}")
    reviewer_holds = _required_allowed_text_list(span, "reviewer_holds", REVIEWER_HOLDS)
    validation_commands = _required_validation_commands(span)
    evidence_id = _required_text(span, "source_evidence_id")
    citation_span_id = _required_text(span, "citation_span_id")
    text = _required_text(span, "normalized_text")
    return CandidateRow(
        candidate_id=f"rcqv5-{index:04d}-{_slug(evidence_id)}",
        queue_version=QUEUE_VERSION,
        requirement_node_candidate=True,
        active=False,
        active_mutation=False,
        citation_span_inventory_ref=citation_span_ref,
        citation_span_id=citation_span_id,
        requirement_type=requirement_type,
        source_evidence_id=evidence_id,
        citation=_required_text(span, "citation"),
        normalized_text=" ".join(text.split()),
        confidence_label=confidence_label,
        human_review_status=human_review_status,
        formalization_status=formalization_status,
        reviewer_holds=reviewer_holds,
        rollback_notes=_required_text(span, "rollback_notes"),
        validation_commands_exact=validation_commands,
    )


def _required_text(source: Mapping[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required {key}")
    return value.strip()


def _required_allowed_text_list(source: Mapping[str, Any], key: str, allowed: frozenset[str]) -> tuple[str, ...]:
    value = source.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        raise ValueError(f"missing required {key}")
    output = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    for item in output:
        if item not in allowed:
            raise ValueError(f"unsupported {key}: {item}")
    return output


def _required_validation_commands(source: Mapping[str, Any]) -> tuple[tuple[str, ...], ...]:
    value = source.get("validation_commands_exact")
    expected = tuple(tuple(command) for command in EXPECTED_VALIDATION_COMMANDS)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("missing validation commands")
    commands: list[tuple[str, ...]] = []
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes, bytearray)):
            raise ValueError("validation commands must be argv rows")
        commands.append(tuple(str(part) for part in command))
    if tuple(commands) != expected:
        raise ValueError("missing validation commands")
    return tuple(commands)


def _reject_prohibited_content(value: Any, path: str = "fixture") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in PROHIBITED_KEYS:
                raise ValueError(f"{path} contains prohibited artifact key: {key}")
            if key_text in ACTIVE_MUTATION_KEYS and child is not False:
                raise ValueError("active mutation flags are not allowed")
            _reject_prohibited_content(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
        for phrase in PROHIBITED_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "evidence"
