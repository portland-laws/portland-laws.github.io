"""Fixture-first process model refresh impact queue v8.

Consumes only re-extracted RequirementNode candidate set v8 fixtures and
existing process model fixtures. The queue assembles offline impact rows and
placeholders only; it never activates guardrails, opens DevHub, crawls live
sites, reads private documents, uploads, submits, certifies, pays, schedules, or
makes legal/permitting guarantees.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

QUEUE_TYPE = "ppd.process_model_refresh_impact_queue.v8"
QUEUE_VERSION = "v8"
QUEUE_MODE = "fixture_first_offline_process_model_refresh_impact_queue_v8"
CANDIDATE_SET_TYPE = "ppd.reextracted_requirement_node_candidate_set.v8"
CANDIDATE_SET_VERSION = "v8"
CANDIDATE_SET_MODE = "fixture_first_reextracted_requirement_node_candidates_v8_only"
PROCESS_MODEL_FIXTURE_TYPE = "ppd.existing_process_model_fixture.v8"

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/process_model_refresh_impact_queue_v8.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_process_model_refresh_impact_queue_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_process_model_refresh_impact_queue_v8.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

ALLOWED_REQUIREMENT_TYPES = frozenset(
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

REQUIRED_FALSE_FLAGS = (
    "live_crawl_executed",
    "live_extraction_executed",
    "document_downloaded",
    "raw_body_stored",
    "devhub_opened",
    "private_document_read",
    "upload_attempted",
    "submission_attempted",
    "certification_attempted",
    "payment_attempted",
    "inspection_scheduling_attempted",
    "official_action_completed",
    "legal_or_permitting_guarantee",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "active_requirement_mutation",
    "guardrail_activation_attempted",
)

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "har",
        "html_body",
        "local_private_path",
        "password",
        "payment_detail",
        "private_document",
        "raw_body",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "screenshot",
        "session_state",
        "storage_state",
        "trace",
    }
)

PROHIBITED_PHRASES = (
    "application submitted",
    "approval guaranteed",
    "certification completed",
    "crawled live",
    "devhub opened",
    "guaranteed permit",
    "inspection scheduled",
    "legal advice",
    "official action completed",
    "payment completed",
    "permit guaranteed",
    "private document read",
    "submission completed",
    "upload completed",
)

CANDIDATE_REF_FIELDS = (
    "eligibility_impact_placeholder_refs",
    "required_fact_impact_placeholder_refs",
    "required_document_impact_placeholder_refs",
    "file_rule_impact_placeholder_refs",
    "fee_impact_placeholder_refs",
    "deadline_impact_placeholder_refs",
    "action_gate_impact_placeholder_refs",
    "unsupported_path_carry_forward_refs",
    "guardrail_recompile_candidate_refs",
    "reviewer_hold_note_refs",
)


def load_json_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    return payload


def build_process_model_refresh_impact_queue_v8_from_fixture(path: str | Path) -> dict[str, Any]:
    candidate_path = Path(path)
    candidate_set = load_json_fixture(candidate_path)
    validate_reextracted_requirement_node_candidate_set_v8(candidate_set)
    process_models = _load_process_model_fixtures(candidate_path, candidate_set)
    return build_process_model_refresh_impact_queue_v8(candidate_set, process_models)


def build_process_model_refresh_impact_queue_v8(
    candidate_set: Mapping[str, Any], process_models: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    validate_reextracted_requirement_node_candidate_set_v8(candidate_set)
    if not process_models:
        raise ValueError("existing process model fixtures are required")
    for model in process_models.values():
        validate_existing_process_model_fixture_v8(model)

    candidates = _candidate_rows(candidate_set)
    affected_process_ids = sorted({process_id for row in candidates for process_id in _text_list(row, "affected_process_ids")})
    missing = [process_id for process_id in affected_process_ids if process_id not in process_models]
    if missing:
        raise ValueError("candidate set references process ids without fixtures: " + ", ".join(missing))

    rows = [_impact_row(process_id, process_models[process_id], candidates) for process_id in affected_process_ids]
    queue = {
        "queue_type": QUEUE_TYPE,
        "queue_version": QUEUE_VERSION,
        "mode": QUEUE_MODE,
        "fixture_first": True,
        "consumes_only": {
            "reextracted_requirement_node_candidate_set_v8_fixtures": True,
            "existing_process_model_fixtures": True,
        },
        "source_candidate_set_ref": _required_text(candidate_set, "candidate_set_id"),
        "existing_process_model_fixture_refs": sorted(
            _required_text(model, "fixture_id") for model in process_models.values()
        ),
        "affected_process_ids": affected_process_ids,
        "row_count": len(rows),
        "affected_process_impact_rows": rows,
        "permit_type_impact_rows": [_permit_type_impact_row(row) for row in rows],
        "eligibility_and_required_fact_impact_placeholders": _section_rows(
            rows,
            ("eligibility_impact_placeholders", "required_fact_impact_placeholders"),
            "eligibility_or_required_fact_impact_ref",
        ),
        "required_document_and_file_rule_impact_placeholders": _section_rows(
            rows,
            ("required_document_impact_placeholders", "file_rule_impact_placeholders"),
            "required_document_or_file_rule_impact_ref",
        ),
        "fee_deadline_action_gate_impact_placeholders": _section_rows(
            rows,
            ("fee_impact_placeholders", "deadline_impact_placeholders", "action_gate_impact_placeholders"),
            "fee_deadline_or_action_gate_impact_ref",
        ),
        "unsupported_path_carry_forward_rows": _section_rows(
            rows, ("unsupported_path_carry_forward_refs",), "unsupported_path_carry_forward_ref"
        ),
        "guardrail_recompile_candidate_references": _section_rows(
            rows, ("guardrail_recompile_candidate_refs",), "guardrail_recompile_candidate_ref"
        ),
        "reviewer_hold_notes": _section_rows(rows, ("reviewer_hold_note_refs",), "reviewer_hold_note_ref"),
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "attestations": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    validate_process_model_refresh_impact_queue_v8(queue)
    return queue


def validate_reextracted_requirement_node_candidate_set_v8(candidate_set: Mapping[str, Any]) -> None:
    _reject_prohibited_content(candidate_set)
    if candidate_set.get("candidate_set_type") != CANDIDATE_SET_TYPE:
        raise ValueError(f"candidate_set_type must be {CANDIDATE_SET_TYPE}")
    if candidate_set.get("candidate_set_version") != CANDIDATE_SET_VERSION:
        raise ValueError("candidate_set_version must be v8")
    if candidate_set.get("mode") != CANDIDATE_SET_MODE:
        raise ValueError(f"mode must be {CANDIDATE_SET_MODE}")
    if candidate_set.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    if candidate_set.get("consumes_only_reextracted_requirement_node_candidate_set_v8_fixtures") is not True:
        raise ValueError("candidate set must declare v8 RequirementNode fixture-only consumption")
    if not isinstance(candidate_set.get("existing_process_model_fixture_refs"), Mapping):
        raise ValueError("candidate set must declare existing_process_model_fixture_refs")
    _require_exact_validation_commands(candidate_set.get("exact_offline_validation_commands"), "candidate set")
    for flag in REQUIRED_FALSE_FLAGS:
        if candidate_set.get(flag) is not False:
            raise ValueError(f"candidate set must declare {flag} false")
    for row in _candidate_rows(candidate_set):
        _validate_candidate_row(row)


def validate_existing_process_model_fixture_v8(process_model: Mapping[str, Any]) -> None:
    _reject_prohibited_content(process_model)
    if process_model.get("fixture_type") != PROCESS_MODEL_FIXTURE_TYPE:
        raise ValueError(f"process model fixture_type must be {PROCESS_MODEL_FIXTURE_TYPE}")
    if process_model.get("fixture_first") is not True:
        raise ValueError("process model fixture_first must be true")
    _required_text(process_model, "fixture_id")
    _required_text(process_model, "process_id")
    _required_text(process_model, "permit_type")
    _required_text(process_model, "guardrail_bundle_id")
    for key in ("eligibility_rules", "required_user_facts", "required_documents", "file_rules", "fees", "deadlines", "action_gates", "unsupported_paths"):
        _text_list(process_model, key)
    for flag in REQUIRED_FALSE_FLAGS:
        if process_model.get(flag) is not False:
            raise ValueError(f"process model fixture must declare {flag} false")


def validate_process_model_refresh_impact_queue_v8(queue: Mapping[str, Any]) -> None:
    _reject_prohibited_content(queue)
    if queue.get("queue_type") != QUEUE_TYPE:
        raise ValueError(f"queue_type must be {QUEUE_TYPE}")
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError("queue_version must be v8")
    if queue.get("mode") != QUEUE_MODE:
        raise ValueError(f"mode must be {QUEUE_MODE}")
    if queue.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    if queue.get("consumes_only") != {
        "reextracted_requirement_node_candidate_set_v8_fixtures": True,
        "existing_process_model_fixtures": True,
    }:
        raise ValueError("queue must consume only candidate set v8 and existing process model fixtures")
    _require_exact_validation_commands(queue.get("exact_offline_validation_commands"), "queue")
    attestations = queue.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("queue must include attestations")
    for flag in REQUIRED_FALSE_FLAGS:
        if attestations.get(flag) is not False:
            raise ValueError(f"queue attestation {flag} must be false")
    rows = queue.get("affected_process_impact_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("affected_process_impact_rows must be a non-empty list")
    process_ids = [_validate_impact_row(row) for row in rows]
    if queue.get("affected_process_ids") != sorted(process_ids):
        raise ValueError("affected_process_ids must match impact rows")
    if queue.get("row_count") != len(rows):
        raise ValueError("row_count must match impact row count")
    for section in (
        "permit_type_impact_rows",
        "eligibility_and_required_fact_impact_placeholders",
        "required_document_and_file_rule_impact_placeholders",
        "fee_deadline_action_gate_impact_placeholders",
        "unsupported_path_carry_forward_rows",
        "guardrail_recompile_candidate_references",
        "reviewer_hold_notes",
    ):
        if not isinstance(queue.get(section), list) or not queue[section]:
            raise ValueError(f"{section} must be non-empty")


def _load_process_model_fixtures(candidate_path: Path, candidate_set: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    refs = candidate_set.get("existing_process_model_fixture_refs")
    if not isinstance(refs, Mapping):
        raise ValueError("existing_process_model_fixture_refs must be an object")
    loaded: dict[str, Mapping[str, Any]] = {}
    for process_id, ref in refs.items():
        if not isinstance(process_id, str) or not process_id.strip() or not isinstance(ref, str) or not ref.strip():
            raise ValueError("existing process model fixture refs must map process ids to paths")
        fixture_path = (candidate_path.parent / ref).resolve()
        payload = load_json_fixture(fixture_path)
        validate_existing_process_model_fixture_v8(payload)
        if payload["process_id"] != process_id:
            raise ValueError("process model fixture ref key must match process_id")
        loaded[process_id] = payload
    return loaded


def _impact_row(process_id: str, process_model: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scoped = [row for row in candidates if process_id in _text_list(row, "affected_process_ids")]
    return {
        "process_id": process_id,
        "process_model_fixture_ref": _required_text(process_model, "fixture_id"),
        "permit_type": _required_text(process_model, "permit_type"),
        "current_guardrail_bundle_id": _required_text(process_model, "guardrail_bundle_id"),
        "candidate_refs": _sorted_unique(_required_text(row, "candidate_id") for row in scoped),
        "requirement_node_candidate_refs": _sorted_unique(_required_text(row, "requirement_node_id") for row in scoped),
        "permit_type_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "permit_type_placeholders")),
        "eligibility_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "eligibility_impact_placeholder_refs")),
        "required_fact_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "required_fact_impact_placeholder_refs")),
        "required_document_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "required_document_impact_placeholder_refs")),
        "file_rule_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "file_rule_impact_placeholder_refs")),
        "fee_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "fee_impact_placeholder_refs")),
        "deadline_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "deadline_impact_placeholder_refs")),
        "action_gate_impact_placeholders": _sorted_unique(value for row in scoped for value in _text_list(row, "action_gate_impact_placeholder_refs")),
        "unsupported_path_carry_forward_refs": _sorted_unique(value for row in scoped for value in _text_list(row, "unsupported_path_carry_forward_refs")),
        "guardrail_recompile_candidate_refs": _sorted_unique(value for row in scoped for value in _text_list(row, "guardrail_recompile_candidate_refs")),
        "reviewer_hold_note_refs": _sorted_unique(value for row in scoped for value in _text_list(row, "reviewer_hold_note_refs")),
        "process_model_mutation_allowed": False,
        "guardrail_activation_allowed": False,
        "official_action_completed": False,
        "legal_or_permitting_guarantee": False,
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }


def _validate_candidate_row(row: Mapping[str, Any]) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if row.get(flag) is not False:
            raise ValueError(f"requirement node candidate must declare {flag} false")
    if _required_text(row, "requirement_type") not in ALLOWED_REQUIREMENT_TYPES:
        raise ValueError("unsupported requirement_type")
    _required_text(row, "candidate_id")
    _required_text(row, "requirement_node_id")
    _text_list(row, "affected_process_ids")
    _text_list(row, "permit_type_placeholders")
    for field in CANDIDATE_REF_FIELDS:
        _text_list(row, field)
    _require_exact_validation_commands(row.get("exact_offline_validation_commands"), "requirement node candidate")


def _validate_impact_row(row: Any) -> str:
    if not isinstance(row, Mapping):
        raise ValueError("impact row must be an object")
    process_id = _required_text(row, "process_id")
    for field in (
        "candidate_refs",
        "requirement_node_candidate_refs",
        "permit_type_placeholders",
        "eligibility_impact_placeholders",
        "required_fact_impact_placeholders",
        "required_document_impact_placeholders",
        "file_rule_impact_placeholders",
        "fee_impact_placeholders",
        "deadline_impact_placeholders",
        "action_gate_impact_placeholders",
        "unsupported_path_carry_forward_refs",
        "guardrail_recompile_candidate_refs",
        "reviewer_hold_note_refs",
    ):
        _text_list(row, field)
    for flag in ("process_model_mutation_allowed", "guardrail_activation_allowed", "official_action_completed", "legal_or_permitting_guarantee"):
        if row.get(flag) is not False:
            raise ValueError(f"{flag} must be false")
    _require_exact_validation_commands(row.get("exact_offline_validation_commands"), "impact row")
    return process_id


def _permit_type_impact_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "process_id": _required_text(row, "process_id"),
        "permit_type": _required_text(row, "permit_type"),
        "permit_type_placeholders": list(row["permit_type_placeholders"]),
        "status": "placeholder_pending_reviewer_disposition",
        "activation_allowed": False,
    }


def _section_rows(rows: Sequence[Mapping[str, Any]], source_fields: Sequence[str], ref_field: str) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        for source_field in source_fields:
            for ref in row[source_field]:
                output.append(
                    {
                        "process_id": row["process_id"],
                        ref_field: ref,
                        "source_impact_field": source_field,
                        "status": "placeholder_pending_reviewer_disposition",
                        "activation_allowed": False,
                        "official_action_completed": False,
                    }
                )
    return sorted(output, key=lambda item: (item["process_id"], item[ref_field], item["source_impact_field"]))


def _candidate_rows(candidate_set: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = candidate_set.get("requirement_node_candidates")
    if not isinstance(rows, list) or not rows:
        raise ValueError("candidate set must include non-empty requirement_node_candidates")
    if not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("requirement_node_candidates must contain objects")
    return rows


def _reject_prohibited_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in PROHIBITED_KEYS:
                raise ValueError(f"{path} contains prohibited key: {key}")
            if key_text in REQUIRED_FALSE_FLAGS and child is not False:
                raise ValueError(f"{path}.{key} must be false")
            _reject_prohibited_content(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = " ".join(value.lower().split())
        for phrase in PROHIBITED_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _require_exact_validation_commands(value: Any, label: str) -> None:
    if value != EXACT_OFFLINE_VALIDATION_COMMANDS:
        raise ValueError(f"{label} must contain only exact offline validation commands")


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _text_list(row: Mapping[str, Any], key: str) -> list[str]:
    value = row.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return list(value)


def _sorted_unique(values: Sequence[str] | Any) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})
