from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ppd.user_gap_analysis_packet_v6 import validate_user_gap_analysis_packet_v6

PACKET_TYPE = "fixture_first_action_journal_dry_run_packet_v6"
VERSION = 6

CONSUMED_PACKET_TYPES = [
    "fixture_first_user_gap_analysis_packet_v6",
    "guarded_draft_preview_handoff_packet_v6",
]

REQUIRED_EVENT_TYPES = [
    "reversible_draft_plan",
    "local_pdf_preview",
    "refused_action",
    "manual_handoff",
    "exact_confirmation_checkpoint",
    "completion_evidence_placeholder",
    "redaction_policy",
    "retention_note",
    "offline_validation_commands",
]

REQUIRED_ROW_EVIDENCE = {
    "reversible_draft_plan": {"gap::synthetic_case_fact_inventory", "gap::missing_fact_rows"},
    "local_pdf_preview": {"gap::source_packet_types", "gap::missing_document_labels"},
    "refused_action": {"gap::blocked_action_rows"},
    "manual_handoff": {"gap::manual_handoff_notes", "handoff::manual_handoff_notes"},
    "exact_confirmation_checkpoint": {"handoff::required_facts", "gap::blocked_action_rows"},
    "completion_evidence_placeholder": {"gap::citation_payloads"},
    "redaction_policy": {"policy::commit_safe_action_journal_v6"},
    "retention_note": {"policy::fixture_retention_v6"},
    "offline_validation_commands": {"policy::offline_validation_v6"},
}

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

REQUIRED_ATTESTATIONS = {
    "no_credentials",
    "no_cookies",
    "no_auth_state",
    "no_screenshots",
    "no_traces",
    "no_har_data",
    "no_private_values",
    "no_payment_details",
    "no_local_private_file_paths",
    "no_official_action_completion_claims",
    "offline_fixture_only",
}

PROHIBITED_KEYS = {
    "absolute_path",
    "account_number",
    "auth",
    "auth_state",
    "bank",
    "browser_state",
    "card",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "csrf",
    "cvv",
    "field_value",
    "field_values",
    "form_value",
    "form_values",
    "har",
    "har_data",
    "local_path",
    "local_private_path",
    "page_value",
    "page_values",
    "password",
    "payment_detail",
    "payment_details",
    "private_file_path",
    "private_path",
    "private_value",
    "private_values",
    "raw_authenticated_value",
    "raw_crawl_output",
    "raw_document_value",
    "raw_private_value",
    "screenshot",
    "screenshots",
    "secret",
    "session",
    "session_state",
    "storage_state",
    "token",
    "trace",
    "traces",
}

FALSE_SIDE_EFFECT_FLAGS = {
    "credentials_stored",
    "cookies_stored",
    "auth_state_stored",
    "screenshots_stored",
    "traces_stored",
    "har_data_stored",
    "private_values_stored",
    "payment_details_stored",
    "local_private_file_paths_stored",
    "official_action_completed",
    "devhub_opened",
    "pdf_written",
    "upload_performed",
    "submission_performed",
    "payment_performed",
    "certification_performed",
    "scheduling_performed",
}

ACTIVE_MUTATION_FLAGS = {
    "active_mutation",
    "active_mutation_flag",
    "active_mutation_flags",
    "mutation_active",
    "mutation_enabled",
    "mutates_live_state",
    "live_mutation",
    "live_mutation_enabled",
}

PROHIBITED_TEXT_PATTERNS = {
    "browser artifact": re.compile(r"\.(?:har|trace|png|jpe?g|webp|zip)\b", re.IGNORECASE),
    "credential material": re.compile(
        r"\b(?:bearer\s+[A-Za-z0-9._~-]+|password|set-cookie|sessionid|xsrf|csrf|api[_ -]?key)\b",
        re.IGNORECASE,
    ),
    "local private path": re.compile(r"(?:file://|/(?:home|Users|private|tmp|var/folders)/[^\s]+|[A-Za-z]:\\\\[^\s]+)"),
    "payment number": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "private value": re.compile(r"\b(?:actual user value|private field value|unredacted field value|applicant ssn|PRIVATE_FACT:)\b", re.IGNORECASE),
    "official completion claim": re.compile(
        r"\b(?:submitted|uploaded|paid|receipt issued|official action completed|payment completed|certified acknowledgement|scheduled inspection)\b",
        re.IGNORECASE,
    ),
    "live DevHub claim": re.compile(r"\b(?:opened DevHub|live DevHub access|authenticated DevHub session|DevHub session captured)\b", re.IGNORECASE),
    "legal or permitting guarantee": re.compile(
        r"\b(?:guarantee(?:d|s)?\s+(?:permit|approval|issuance)|(?:permit|approval|issuance)\s+(?:is|will be)\s+guaranteed|legal advice|binding legal conclusion|permitting guarantee)\b",
        re.IGNORECASE,
    ),
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object fixture: {path}")
    return value


def assemble_action_journal_dry_run_packet_v6(
    user_gap_analysis_packet_v6: dict[str, Any],
    guarded_draft_preview_handoff_packet_v6: dict[str, Any],
) -> dict[str, Any]:
    gap_errors = validate_user_gap_analysis_packet_v6(user_gap_analysis_packet_v6)
    if gap_errors:
        raise ValueError("invalid user gap analysis packet v6: " + "; ".join(gap_errors))
    _require_handoff_packet(guarded_draft_preview_handoff_packet_v6)

    known_fact_ids = [str(row.get("fact_id", "")) for row in user_gap_analysis_packet_v6.get("synthetic_case_fact_inventory", []) if isinstance(row, dict) and row.get("fact_id")]
    missing_fact_ids = [str(row.get("fact_id", "")) for row in user_gap_analysis_packet_v6.get("missing_fact_rows", []) if isinstance(row, dict) and row.get("fact_id")]
    refused_actions = [str(row.get("action", "")) for row in user_gap_analysis_packet_v6.get("blocked_action_rows", []) if isinstance(row, dict) and row.get("action")]
    citation_ids = [str(row.get("citation_id", "")) for row in user_gap_analysis_packet_v6.get("citation_payloads", []) if isinstance(row, dict) and row.get("citation_id")]

    source_packet_refs = [
        {
            "packet_type": "fixture_first_user_gap_analysis_packet_v6",
            "version": user_gap_analysis_packet_v6.get("version"),
            "source_packet_types": list(user_gap_analysis_packet_v6.get("source_packet_types", [])),
        },
        {
            "packet_type": "guarded_draft_preview_handoff_packet_v6",
            "version": guarded_draft_preview_handoff_packet_v6.get("version"),
        },
    ]

    rows = [
        _row(
            "aj-v6-001",
            "reversible_draft_plan",
            ["gap::synthetic_case_fact_inventory", "gap::missing_fact_rows"],
            "Record a reversible draft plan using fact identifiers only; known fact ids are " + ", ".join(known_fact_ids) + "; unresolved fact ids are " + ", ".join(missing_fact_ids) + ".",
            "The row stores identifiers and review status only, not user-supplied values.",
        ),
        _row(
            "aj-v6-002",
            "local_pdf_preview",
            ["gap::source_packet_types", "gap::missing_document_labels"],
            "Record the local PDF preview as placeholder-only metadata for " + str(len(user_gap_analysis_packet_v6.get("missing_document_labels", []))) + " missing document labels.",
            "The row records no document bytes, no PDF writes, and no local private file paths.",
        ),
        _row(
            "aj-v6-003",
            "refused_action",
            ["gap::blocked_action_rows"],
            "Refuse blocked action identifiers from the user gap analysis packet: " + ", ".join(refused_actions) + ".",
            "The row records refusal categories only and makes no official-action completion claim.",
        ),
        _row(
            "aj-v6-004",
            "manual_handoff",
            ["gap::manual_handoff_notes", "handoff::manual_handoff_notes"],
            "Record manual handoff as note counts only: user gap notes " + str(len(user_gap_analysis_packet_v6.get("manual_handoff_notes", []))) + ", guarded handoff notes " + str(len(guarded_draft_preview_handoff_packet_v6.get("manual_handoff_notes", []))) + ".",
            "The row avoids copying private values and sends consequential work to attended review.",
        ),
        _row(
            "aj-v6-005",
            "exact_confirmation_checkpoint",
            ["handoff::required_facts", "gap::blocked_action_rows"],
            "Require action-specific attended confirmation before upload, submission, payment, certification, scheduling, cancellation, or official change checkpoints.",
            "The row is a checkpoint reminder only and does not instruct an automated final action.",
        ),
        _row(
            "aj-v6-006",
            "completion_evidence_placeholder",
            ["gap::citation_payloads"],
            "Create completion-evidence placeholders for citation ids: " + ", ".join(citation_ids) + ".",
            "The row names evidence slots for later review and does not assert official completion.",
        ),
        _row(
            "aj-v6-007",
            "redaction_policy",
            ["policy::commit_safe_action_journal_v6"],
            "Apply redaction policy for credentials, cookies, auth state, screenshots, traces, HAR data, private values, payment details, local private file paths, and official completion claims.",
            "The row stores policy labels only and validates absence attestations.",
        ),
        _row(
            "aj-v6-008",
            "retention_note",
            ["policy::fixture_retention_v6"],
            "Retain committed fixture metadata and discard browser artifacts, raw private material, payment material, and local private file references.",
            "The row records retention intent without retaining prohibited artifacts.",
        ),
        _row(
            "aj-v6-009",
            "offline_validation_commands",
            ["policy::offline_validation_v6"],
            "Record the exact offline validation command list only.",
            "The command list is deterministic and contains no live crawl, browser, upload, payment, or private-file operation.",
        ),
    ]

    packet = {
        "packet_type": PACKET_TYPE,
        "version": VERSION,
        "fixture_first": True,
        "commit_safe": True,
        "consumes_only": list(CONSUMED_PACKET_TYPES),
        "source_packet_refs": source_packet_refs,
        "event_rows": rows,
        "redaction_policy": {
            "policy_id": "redaction::action-journal-dry-run-v6",
            "excluded_material": [
                "credentials",
                "cookies",
                "auth_state",
                "screenshots",
                "traces",
                "har_data",
                "private_values",
                "payment_details",
                "local_private_file_paths",
                "official_action_completion_claims",
            ],
            "allowed_material": [
                "packet_type",
                "version",
                "fact_ids",
                "citation_ids",
                "blocked_action_ids",
                "redacted_summaries",
                "offline_validation_commands",
            ],
        },
        "retention_notes": [
            {
                "note_id": "retention::committed-fixture-metadata-only",
                "note": "Commit fixture-derived metadata and deterministic validation commands only.",
            },
            {
                "note_id": "retention::discard-prohibited-artifacts",
                "note": "Do not retain browser artifacts, raw private material, payment material, local private file references, or official-action completion claims.",
            },
        ],
        "no_effect_flags": {flag: False for flag in sorted(FALSE_SIDE_EFFECT_FLAGS)},
        "attestations": {name: True for name in sorted(REQUIRED_ATTESTATIONS)},
        "offline_validation_commands": list(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }
    errors = validate_action_journal_dry_run_packet_v6(packet)
    if errors:
        raise ValueError("invalid action journal dry-run packet v6: " + "; ".join(errors))
    return packet


def assemble_from_fixture_paths(user_gap_path: str | Path, guarded_handoff_path: str | Path) -> dict[str, Any]:
    return assemble_action_journal_dry_run_packet_v6(load_json(user_gap_path), load_json(guarded_handoff_path))


def validate_action_journal_dry_run_packet_v6(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be an object"]
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("version") != VERSION:
        errors.append("version must be 6")
    for flag in ("fixture_first", "commit_safe"):
        if packet.get(flag) is not True:
            errors.append(f"{flag} must be True")
    if packet.get("consumes_only") != CONSUMED_PACKET_TYPES:
        errors.append("consumes_only must exactly reference user gap analysis packet v6 and guarded draft preview handoff packet v6")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("offline_validation_commands must exactly match the action journal dry-run packet v6 command list")

    _validate_source_refs(packet.get("source_packet_refs"), errors)
    _validate_event_rows(packet.get("event_rows"), errors)
    _validate_redaction_policy(packet.get("redaction_policy"), errors)
    _validate_retention_notes(packet.get("retention_notes"), errors)
    _validate_no_effect_flags(packet.get("no_effect_flags"), errors)
    _validate_attestations(packet.get("attestations"), errors)
    _scan_for_prohibited_material(packet, errors)
    return sorted(set(errors))


def assert_valid_action_journal_dry_run_packet_v6(packet: dict[str, Any]) -> None:
    errors = validate_action_journal_dry_run_packet_v6(packet)
    if errors:
        raise AssertionError("invalid action journal dry-run packet v6:\n" + "\n".join(errors))


def _require_handoff_packet(packet: dict[str, Any]) -> None:
    if packet.get("packet_type") != "guarded_draft_preview_handoff_packet_v6" or packet.get("version") != 6:
        raise ValueError("guarded draft preview handoff fixture must be packet_type guarded_draft_preview_handoff_packet_v6 version 6")


def _row(row_id: str, event_type: str, source_evidence_ids: list[str], redacted_summary: str, commit_safe_reason: str) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "event_type": event_type,
        "source_packet_types": list(CONSUMED_PACKET_TYPES),
        "source_evidence_ids": source_evidence_ids,
        "redacted_summary": redacted_summary,
        "redaction_policy_refs": ["redaction::action-journal-dry-run-v6"],
        "retention_refs": ["retention::committed-fixture-metadata-only"],
        "commit_safe_reason": commit_safe_reason,
        "offline_validation_commands": list(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }


def _validate_source_refs(refs: Any, errors: list[str]) -> None:
    if not isinstance(refs, list) or len(refs) != 2:
        errors.append("source_packet_refs must contain exactly two consumed fixture packet references")
        return
    packet_types = [ref.get("packet_type") for ref in refs if isinstance(ref, dict)]
    if packet_types != CONSUMED_PACKET_TYPES:
        errors.append("source_packet_refs must be user gap analysis packet v6 then guarded draft preview handoff packet v6")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f"source_packet_refs[{index}] must be an object")
            continue
        if ref.get("version") != 6:
            errors.append(f"source_packet_refs[{index}].version must be 6")
        if ref.get("packet_type") == "fixture_first_user_gap_analysis_packet_v6" and "guarded_draft_preview_handoff_packet_v6" not in ref.get("source_packet_types", []):
            errors.append("source_packet_refs[0] must carry guarded draft preview handoff provenance")


def _validate_event_rows(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        errors.append("event_rows must be a list")
        return
    event_types = [row.get("event_type") for row in rows if isinstance(row, dict)]
    if event_types != REQUIRED_EVENT_TYPES:
        errors.append("event_rows must include required v6 event types in deterministic order")
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        path = f"event_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        for field in (
            "row_id",
            "event_type",
            "source_packet_types",
            "source_evidence_ids",
            "redacted_summary",
            "redaction_policy_refs",
            "retention_refs",
            "commit_safe_reason",
            "offline_validation_commands",
        ):
            if field not in row:
                errors.append(f"{path}.{field} is required")
        row_id = row.get("row_id")
        event_type = row.get("event_type")
        if not _text(row_id):
            errors.append(f"{path}.row_id must be non-empty text")
        elif row_id in seen_ids:
            errors.append(f"{path}.row_id is duplicated")
        else:
            seen_ids.add(str(row_id))
        if event_type not in REQUIRED_EVENT_TYPES:
            errors.append(f"{path}.event_type is unsupported")
        if row.get("source_packet_types") != CONSUMED_PACKET_TYPES:
            errors.append(f"{path}.source_packet_types must exactly match consumed packet types")
        for field in ("source_evidence_ids", "redaction_policy_refs", "retention_refs"):
            if not _string_list(row.get(field)):
                errors.append(f"{path}.{field} must be a non-empty string list")
        if isinstance(event_type, str) and event_type in REQUIRED_ROW_EVIDENCE:
            evidence_ids = set(row.get("source_evidence_ids", [])) if isinstance(row.get("source_evidence_ids"), list) else set()
            if not REQUIRED_ROW_EVIDENCE[event_type].issubset(evidence_ids):
                errors.append(f"{path}.source_evidence_ids must include required references for {event_type}")
        for field in ("redacted_summary", "commit_safe_reason"):
            if not _text(row.get(field)):
                errors.append(f"{path}.{field} must be non-empty text")
        if row.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
            errors.append(f"{path}.offline_validation_commands must exactly match packet commands")


def _validate_redaction_policy(policy: Any, errors: list[str]) -> None:
    if not isinstance(policy, dict):
        errors.append("redaction_policy must be an object")
        return
    if not _text(policy.get("policy_id")):
        errors.append("redaction_policy.policy_id is required")
    for field in ("excluded_material", "allowed_material"):
        if not _string_list(policy.get(field)):
            errors.append(f"redaction_policy.{field} must be a non-empty string list")
    required_exclusions = {
        "credentials",
        "cookies",
        "auth_state",
        "screenshots",
        "traces",
        "har_data",
        "private_values",
        "payment_details",
        "local_private_file_paths",
        "official_action_completion_claims",
    }
    if not required_exclusions.issubset(set(policy.get("excluded_material", []))):
        errors.append("redaction_policy.excluded_material must cover all prohibited committed artifacts")


def _validate_retention_notes(notes: Any, errors: list[str]) -> None:
    if not isinstance(notes, list) or not notes:
        errors.append("retention_notes must be a non-empty list")
        return
    for index, note in enumerate(notes):
        if not isinstance(note, dict):
            errors.append(f"retention_notes[{index}] must be an object")
            continue
        if not _text(note.get("note_id")) or not _text(note.get("note")):
            errors.append(f"retention_notes[{index}] must include note_id and note")


def _validate_no_effect_flags(flags: Any, errors: list[str]) -> None:
    if not isinstance(flags, dict):
        errors.append("no_effect_flags must be an object")
        return
    for flag in sorted(FALSE_SIDE_EFFECT_FLAGS):
        if flags.get(flag) is not False:
            errors.append(f"no_effect_flags.{flag} must be False")


def _validate_attestations(attestations: Any, errors: list[str]) -> None:
    if not isinstance(attestations, dict):
        errors.append("attestations must be an object")
        return
    for attestation in sorted(REQUIRED_ATTESTATIONS):
        if attestations.get(attestation) is not True:
            errors.append(f"attestations.{attestation} must be True")


def _scan_for_prohibited_material(value: Any, errors: list[str], path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalize_key(str(key))
            child_path = f"{path}.{key}"
            if normalized in PROHIBITED_KEYS:
                errors.append(f"{child_path} uses a prohibited sensitive key")
            if normalized in FALSE_SIDE_EFFECT_FLAGS and child is not False:
                errors.append(f"{child_path} must be False")
            if normalized in ACTIVE_MUTATION_FLAGS and child is not False:
                errors.append(f"{child_path} must not enable active mutation")
            _scan_for_prohibited_material(child, errors, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_prohibited_material(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        for label, pattern in PROHIBITED_TEXT_PATTERNS.items():
            if pattern.search(value):
                errors.append(f"{path} contains prohibited {label}")


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


__all__ = [
    "CONSUMED_PACKET_TYPES",
    "EXACT_OFFLINE_VALIDATION_COMMANDS",
    "PACKET_TYPE",
    "REQUIRED_EVENT_TYPES",
    "VERSION",
    "assemble_action_journal_dry_run_packet_v6",
    "assemble_from_fixture_paths",
    "assert_valid_action_journal_dry_run_packet_v6",
    "load_json",
    "validate_action_journal_dry_run_packet_v6",
]
