"""Fixture-first local PDF draft preview packet v6.

This module assembles and validates a local-only draft preview packet from two
committed fixture inputs:

* a guarded draft preview handoff packet v6
* a synthetic fillable-PDF field fixture

It never opens DevHub, reads private documents, downloads forms, writes PDFs,
uploads, submits, certifies, pays, schedules, or makes legal/permitting
guarantees. The packet is preview metadata only: field mappings, missing user
fact prompts, source references, rendering notes, placeholders, stop gates, and
manual review notes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.agent_readiness.guarded_draft_preview_handoff_packet_v6 import (
    assert_valid_guarded_draft_preview_handoff_packet_v6,
)

PACKET_VERSION = "local-pdf-draft-preview-packet-v6"

EXACT_VALIDATION_COMMANDS: list[list[str]] = [
    [
        "python3",
        "-m",
        "py_compile",
        "ppd/agent_readiness/local_pdf_draft_preview_packet_v6.py",
        "ppd/tests/test_local_pdf_draft_preview_packet_v6.py",
    ],
    ["python3", "-m", "unittest", "ppd.tests.test_local_pdf_draft_preview_packet_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_PACKET_REF_FIELDS = (
    "handoff_packet_ref",
    "synthetic_field_fixture_ref",
)
_REQUIRED_LIST_SECTIONS = (
    "field_mapping_rows",
    "missing_user_fact_prompts",
    "source_evidence_references",
    "preview_only_rendering_notes",
    "no_private_document_placeholders",
    "stop_gates",
    "manual_review_notes",
    "validation_commands",
)
_REQUIRED_STOP_GATE_TOPICS = {"upload", "submission", "certification", "payment"}
_PRIVATE_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "C:\\Users\\",
    "file://",
    "auth_state",
    "browser_state",
    "session_state",
    "storage_state",
    "cookie",
    "csrf",
    "bearer ",
    "password",
    "PRIVATE_FACT:",
    "AUTHENTICATED_VALUE:",
    "RAW_PDF_BYTES:",
    "private_file_path",
    "trace.zip",
    ".har",
)
_FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b(?:opened|accessed|logged\s+into|used)\s+devhub\b", re.IGNORECASE),
    re.compile(r"\blive\s+devhub\s+(?:access|session|run|crawl)\b", re.IGNORECASE),
    re.compile(r"\bauthenticated\s+devhub\s+(?:session|page|value|artifact)\b", re.IGNORECASE),
    re.compile(r"\b(?:i|we|the\s+agent)\s+(?:submitted|uploaded|paid|certified|scheduled|cancelled|canceled)\b", re.IGNORECASE),
    re.compile(r"\b(?:application|permit|payment|upload|certification|inspection|cancellation)\s+(?:submitted|uploaded|paid|certified|scheduled|completed|cancelled|canceled)\b", re.IGNORECASE),
    re.compile(r"\b(?:final|official)\s+(?:submission|upload|payment|certification|scheduling|cancellation)\s+(?:completed|performed|executed)\b", re.IGNORECASE),
    re.compile(r"\bpermit\s+(?:will|shall|is\s+guaranteed\s+to)\s+(?:be\s+)?(?:approved|issued|accepted)\b", re.IGNORECASE),
    re.compile(r"\bapproval\s+(?:is\s+)?guaranteed\b", re.IGNORECASE),
    re.compile(r"\bguarantee(?:d|s)?\s+(?:permit|approval|issuance|code\s+compliance|legal\s+sufficiency)\b", re.IGNORECASE),
    re.compile(r"\blegally\s+(?:sufficient|compliant|approved|guaranteed)\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:code\s+)?(?:violation|enforcement\s+risk|permitting\s+risk)\b", re.IGNORECASE),
    re.compile(r"\b(?:click|press|select)\s+(?:submit|upload|pay|certify|schedule|cancel)\b", re.IGNORECASE),
    re.compile(r"\b(?:submit|upload|pay|certify|schedule|cancel)\s+(?:now|in\s+devhub|the\s+official|the\s+final)\b", re.IGNORECASE),
)
_NO_EFFECT_FALSE_FLAGS = (
    "live_devhub_access",
    "private_session_auth_artifacts",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
    "active_mutation_flags",
    "opens_devhub",
    "reads_private_documents",
    "downloads_forms",
    "writes_pdf",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
    "cancels",
    "uses_authenticated_session",
    "stores_auth_state",
    "stores_cookies",
    "creates_traces",
    "creates_screenshots",
    "creates_har_files",
    "makes_legal_or_permitting_guarantees",
    "mutates_release_state",
    "mutates_guardrails",
    "mutates_prompts",
)
_ACTIVE_MUTATION_KEY_TERMS = (
    "active_mutation",
    "mutation_enabled",
    "mutates_",
    "write_enabled",
    "updates_guardrail",
    "updates_prompt",
    "release_state_mutation",
)


def load_fixture_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("fixture packet must be a JSON object")
    return data


def build_local_pdf_draft_preview_packet_v6(
    *,
    guarded_handoff_packet_v6: Mapping[str, Any],
    synthetic_fillable_pdf_fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a local-only PDF draft preview packet from committed fixtures."""

    assert_valid_guarded_draft_preview_handoff_packet_v6(guarded_handoff_packet_v6)
    _validate_synthetic_field_fixture(synthetic_fillable_pdf_fields)

    handoff_id = _text(guarded_handoff_packet_v6.get("handoff_id")) or "guarded-draft-preview-handoff-v6-fixture"
    fixture_id = _require_text(synthetic_fillable_pdf_fields, "fixture_id")
    pdf_fixture_id = _require_text(synthetic_fillable_pdf_fields, "pdf_fixture_id")
    handoff_rows = _rows_by_fact_id(guarded_handoff_packet_v6.get("reversible_draft_preview_rows", []))

    mapping_rows = []
    missing_prompts_by_fact: dict[str, dict[str, Any]] = {}
    source_refs: dict[str, dict[str, Any]] = {}
    placeholders = []

    for field in _sequence(synthetic_fillable_pdf_fields.get("fields")):
        field_id = _require_text(field, "field_id")
        required_fact_ids = _strings(field.get("required_fact_ids"))
        evidence_ids = _strings(field.get("source_evidence_ids"))
        matched_row_ids = sorted({row["row_id"] for fact_id in required_fact_ids for row in handoff_rows.get(fact_id, [])})
        placeholder = {
            "placeholder_id": f"placeholder::{field_id}",
            "field_id": field_id,
            "placeholder_text": "NO_PRIVATE_DOCUMENT_VALUE_IN_FIXTURE",
            "reason": "Preview packet carries no private document values or local file paths.",
        }
        placeholders.append(placeholder)
        mapping_rows.append(
            {
                "row_id": f"mapping::{field_id}",
                "pdf_fixture_id": pdf_fixture_id,
                "field_id": field_id,
                "pdf_field_name": _require_text(field, "pdf_field_name"),
                "field_type": _require_text(field, "field_type"),
                "required_fact_ids": required_fact_ids,
                "matched_handoff_row_ids": matched_row_ids,
                "preview_value_placeholder": placeholder["placeholder_text"],
                "local_only": True,
                "preview_only": True,
                "writes_pdf": False,
                "uses_private_document": False,
                "source_evidence_ids": evidence_ids,
            }
        )
        for evidence_id in evidence_ids:
            source_refs.setdefault(
                evidence_id,
                {
                    "source_evidence_id": evidence_id,
                    "reference_kind": "fixture_public_or_guardrail_evidence",
                    "used_by_field_ids": [],
                },
            )["used_by_field_ids"].append(field_id)
        for fact_id in required_fact_ids:
            if fact_id not in handoff_rows:
                missing_prompts_by_fact.setdefault(
                    fact_id,
                    {
                        "prompt_id": f"missing-fact::{fact_id}",
                        "fact_id": fact_id,
                        "prompt": f"Ask the user for fixture-scoped provenance for {fact_id} before treating the local PDF preview row as reviewable.",
                        "blocks_field_ids": [],
                        "source_evidence_ids": evidence_ids,
                    },
                )["blocks_field_ids"].append(field_id)

    packet = {
        "packet_version": PACKET_VERSION,
        "fixture_first": True,
        "local_only": True,
        "handoff_packet_ref": handoff_id,
        "synthetic_field_fixture_ref": fixture_id,
        "field_mapping_rows": mapping_rows,
        "missing_user_fact_prompts": list(missing_prompts_by_fact.values()),
        "source_evidence_references": sorted(source_refs.values(), key=lambda item: item["source_evidence_id"]),
        "preview_only_rendering_notes": [
            {
                "note_id": "rendering::metadata-only",
                "note": "Render field labels, synthetic field names, field types, placeholders, and citations only; do not read, create, or modify a PDF file.",
                "source_evidence_ids": ["plan::local-pdf-preview", "plan::non-negotiable-boundaries"],
            },
            {
                "note_id": "rendering::fillable-field-confidence",
                "note": "Synthetic fillable-PDF fields are suitable for local mapping rehearsal only and require manual review before any attended workflow.",
                "source_evidence_ids": ["fixture::synthetic-fillable-pdf-fields"],
            },
        ],
        "no_private_document_placeholders": placeholders,
        "stop_gates": _stop_gates(),
        "manual_review_notes": [
            {
                "note_id": "manual-review::field-mapping",
                "note": "A reviewer must compare the synthetic mapping rows, missing prompts, and cited evidence before any user-facing draft guidance is promoted.",
                "source_evidence_ids": ["plan::manual-review", "fixture::guarded-handoff-v6"],
            },
            {
                "note_id": "manual-review::official-actions",
                "note": "Consequential DevHub actions remain stopped and require attended user review with action-specific confirmation outside this packet.",
                "source_evidence_ids": ["plan::authenticated-devhub-boundaries"],
            },
        ],
        "no_effect_policy": {flag: False for flag in _NO_EFFECT_FALSE_FLAGS},
        "validation_commands": EXACT_VALIDATION_COMMANDS,
    }
    validate_local_pdf_draft_preview_packet_v6(packet)
    return packet


def validate_local_pdf_draft_preview_packet_v6(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        raise ValueError("invalid local PDF draft preview packet v6: packet must be an object")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be local-pdf-draft-preview-packet-v6")
    if packet.get("fixture_first") is not True:
        errors.append("packet must be fixture_first")
    if packet.get("local_only") is not True:
        errors.append("packet must be local_only")
    for ref_field in _REQUIRED_PACKET_REF_FIELDS:
        if not _text(packet.get(ref_field)):
            errors.append(f"{ref_field} must reference the committed fixture input")
    for section in _REQUIRED_LIST_SECTIONS:
        if not _sequence(packet.get(section)):
            errors.append(f"{section} must be a non-empty list")
    for row in _sequence(packet.get("field_mapping_rows")):
        if not isinstance(row, Mapping):
            errors.append("field mapping rows must be objects")
            continue
        for key in ("row_id", "pdf_fixture_id", "field_id", "pdf_field_name", "field_type", "preview_value_placeholder"):
            if not _text(row.get(key)):
                errors.append(f"field mapping rows must include {key}")
        if not _strings(row.get("required_fact_ids")):
            errors.append("field mapping rows must include required_fact_ids")
        if row.get("local_only") is not True or row.get("preview_only") is not True:
            errors.append("field mapping rows must be local preview rows")
        if row.get("writes_pdf") is not False or row.get("uses_private_document") is not False:
            errors.append("field mapping rows must not write PDFs or use private documents")
        if not _strings(row.get("source_evidence_ids")):
            errors.append("field mapping rows must cite source evidence")
    for prompt in _sequence(packet.get("missing_user_fact_prompts")):
        if not isinstance(prompt, Mapping):
            errors.append("missing user-fact prompts must be objects")
            continue
        for key in ("prompt_id", "fact_id", "prompt"):
            if not _text(prompt.get(key)):
                errors.append(f"missing user-fact prompts must include {key}")
        if not _strings(prompt.get("blocks_field_ids")):
            errors.append("missing user-fact prompts must block field ids")
        if not _strings(prompt.get("source_evidence_ids")):
            errors.append("missing user-fact prompts must cite source evidence")
    for ref in _sequence(packet.get("source_evidence_references")):
        if not isinstance(ref, Mapping):
            errors.append("source evidence references must be objects")
            continue
        if not _text(ref.get("source_evidence_id")):
            errors.append("source evidence references must include source_evidence_id")
        if not _strings(ref.get("used_by_field_ids")):
            errors.append("source evidence references must identify used_by_field_ids")
    for section in ("preview_only_rendering_notes", "manual_review_notes"):
        for note in _sequence(packet.get(section)):
            if not isinstance(note, Mapping):
                errors.append(f"{section} entries must be objects")
                continue
            if not _text(note.get("note_id")) or not _text(note.get("note")):
                errors.append(f"{section} entries must include note_id and note")
            if not _strings(note.get("source_evidence_ids")):
                errors.append(f"{section} entries must cite source evidence")
    topics = {_text(gate.get("topic")) for gate in _sequence(packet.get("stop_gates")) if isinstance(gate, Mapping)}
    if not _REQUIRED_STOP_GATE_TOPICS.issubset(topics):
        errors.append("stop gates must cover upload, submission, certification, and payment")
    for gate in _sequence(packet.get("stop_gates")):
        if not isinstance(gate, Mapping):
            errors.append("stop gates must be objects")
            continue
        if gate.get("automated") is not False or gate.get("requires_attended_user") is not True or gate.get("requires_exact_confirmation") is not True:
            errors.append("stop gates must be non-automated and require attended exact confirmation")
        if not _strings(gate.get("source_evidence_ids")):
            errors.append("stop gates must cite source evidence")
    policy = packet.get("no_effect_policy")
    if not isinstance(policy, Mapping):
        errors.append("no_effect_policy must be an object")
    else:
        for flag in _NO_EFFECT_FALSE_FLAGS:
            if policy.get(flag) is not False:
                errors.append(f"no_effect_policy.{flag} must be false")
    if packet.get("validation_commands") != EXACT_VALIDATION_COMMANDS:
        errors.append("validation_commands must exactly match local PDF draft preview packet v6 commands")
    _scan_for_forbidden_values(packet, errors)
    if errors:
        unique_errors = sorted(set(errors))
        raise ValueError("invalid local PDF draft preview packet v6: " + "; ".join(unique_errors))
    return []


def _validate_synthetic_field_fixture(fixture: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if fixture.get("fixture_kind") != "synthetic_fillable_pdf_fields_v1":
        errors.append("fixture_kind must be synthetic_fillable_pdf_fields_v1")
    if fixture.get("fixture_first") is not True:
        errors.append("field fixture must be fixture_first")
    if fixture.get("synthetic") is not True:
        errors.append("field fixture must be synthetic")
    for flag in ("opens_devhub", "reads_private_documents", "downloads_forms", "writes_pdf"):
        if fixture.get(flag) is not False:
            errors.append(f"field fixture {flag} must be false")
    fields = _sequence(fixture.get("fields"))
    if not fields:
        errors.append("field fixture must include fields")
    for field in fields:
        if not isinstance(field, Mapping):
            errors.append("field entries must be objects")
            continue
        for key in ("field_id", "pdf_field_name", "field_type"):
            if not _text(field.get(key)):
                errors.append(f"field.{key} is required")
        if not _strings(field.get("required_fact_ids")):
            errors.append("field.required_fact_ids must be non-empty")
        if not _strings(field.get("source_evidence_ids")):
            errors.append("field.source_evidence_ids must be non-empty")
    _scan_for_forbidden_values(fixture, errors)
    if errors:
        raise ValueError("invalid synthetic fillable PDF field fixture: " + "; ".join(sorted(set(errors))))


def _rows_by_fact_id(rows: Any) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = {}
    for row in _sequence(rows):
        if not isinstance(row, Mapping):
            continue
        row_id = _text(row.get("row_id"))
        for fact_id in _strings(row.get("required_fact_ids")) + _strings(row.get("user_fact_ids")):
            if row_id:
                result.setdefault(fact_id, []).append(row)
    return result


def _stop_gates() -> list[dict[str, Any]]:
    return [
        {
            "topic": topic,
            "automated": False,
            "requires_attended_user": True,
            "requires_exact_confirmation": True,
            "disposition": "stop_and_manual_handoff",
            "source_evidence_ids": ["plan::non-negotiable-boundaries"],
        }
        for topic in ("upload", "submission", "certification", "payment")
    ]


def _scan_for_forbidden_values(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if child is True and normalized_key in _NO_EFFECT_FALSE_FLAGS:
                errors.append(f"forbidden true flag at {path}.{key}")
            if child is True and any(term in normalized_key for term in _ACTIVE_MUTATION_KEY_TERMS):
                errors.append(f"forbidden active mutation flag at {path}.{key}")
            _scan_for_forbidden_values(child, errors, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_values(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in _PRIVATE_MARKERS):
            errors.append(f"private or authenticated artifact reference at {path}")
        if any(pattern.search(value) for pattern in _FORBIDDEN_TEXT_PATTERNS):
            errors.append(f"forbidden live, official-action, or guarantee language at {path}")


def _require_text(mapping: Mapping[str, Any], key: str) -> str:
    value = _text(mapping.get(key))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _strings(value: Any) -> list[str]:
    return [_text(item) for item in _sequence(value) if _text(item)]


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []
