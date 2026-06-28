"""Fixture-first re-extracted RequirementNode candidate set v6.

Consumes only committed requirement re-extraction work packet v6 fixtures and
produces inactive candidate RequirementNode deltas plus unchanged requirement
rows for reviewer handoff. The builder never crawls, downloads, opens DevHub,
reads private documents, stores raw bodies, uploads, submits, certifies, pays,
schedules, or makes legal/permitting guarantees.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

PACKET_TYPE = "fixture_first_reextracted_requirement_candidate_set_v6"
SOURCE_PACKET_ID = "requirement-reextraction-work-packet-v6"

OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/requirement_candidate_set_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_requirement_candidate_set_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

FORBIDDEN_LIVE_ACCESS = {
    "crawl_live_sites",
    "download_documents",
    "store_raw_bodies",
    "open_devhub",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantees",
}

FORBIDDEN_KEYS = {
    "access_token",
    "auth_artifact",
    "auth_state",
    "body",
    "browser_trace",
    "cookie",
    "credential",
    "devhub_session",
    "document_text",
    "downloaded_artifact",
    "downloaded_artifacts",
    "downloaded_document",
    "downloaded_documents",
    "har",
    "har_file",
    "html_body",
    "local_private_path",
    "page_source",
    "password",
    "private_artifact",
    "private_document",
    "raw_artifact",
    "raw_body",
    "raw_bodies",
    "raw_crawl_artifact",
    "raw_crawl_artifacts",
    "raw_crawl_output",
    "raw_html",
    "raw_pdf",
    "raw_text",
    "session_artifact",
    "session_file",
    "session_state",
    "screenshot",
    "storage_state",
    "trace",
}

FORBIDDEN_TRUE_FLAGS = {
    "active",
    "active_crawl",
    "active_guardrail_mutation",
    "active_mutation",
    "active_mutation_enabled",
    "active_process_model_mutation",
    "active_refresh",
    "active_requirement_mutation",
    "live_crawl_completed",
    "live_crawl_executed",
    "live_mutation",
    "mutation_enabled",
    "official_action_completed",
    "write_mode_enabled",
}

FORBIDDEN_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\blive crawl (?:completed|executed|ran|succeeded)\b",
        r"\blive crawl execution\b",
        r"\b(?:fetched|crawled|recrawled) live\b",
        r"\bdownloaded (?:document|documents|pdf|pdfs|artifact|artifacts)\b",
        r"\braw (?:html|pdf|body|bodies|crawl artifact|crawl artifacts|crawl output)\b",
        r"\b(?:auth state|session file|session artifact|trace|har file|credential|cookie)\b",
        r"\bofficial action (?:complete|completed)\b",
        r"\b(?:submitted|certified|uploaded|paid|scheduled) (?:the )?(?:permit|application|correction|fee|inspection)\b",
        r"\b(?:legal advice|legal(?:ly)? sufficient|permit approval guaranteed|permitting approval guaranteed|guaranteed approval|will be approved)\b",
        r"\b(?:active mutation enabled|mutated live state|mutates live systems)\b",
    )
)


def load_work_packet_fixture(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("work packet fixture must be a JSON object")
    return payload


def build_candidate_set_from_fixture(path: Path | str) -> dict[str, Any]:
    return build_candidate_set(load_work_packet_fixture(path), fixture_ref=str(path))


def build_candidate_set(work_packet: Mapping[str, Any], fixture_ref: str = "inline_work_packet_v6_fixture") -> dict[str, Any]:
    _validate_source_work_packet(work_packet)

    source_evidence_refs: list[dict[str, Any]] = []
    candidate_deltas: list[dict[str, Any]] = []
    unchanged_rows: list[dict[str, Any]] = []
    impact_hints: list[dict[str, Any]] = []

    for process in _required_list(work_packet, "process_packets"):
        process_id = _required_text(process, "process_id")
        permit_type = _required_text(process, "permit_type")
        targets = _required_list(process, "source_span_refresh_targets")
        evidence_by_requirement = {str(target.get("requirement_id")): target for target in targets if isinstance(target, Mapping)}

        for input_row in _required_list(process, "extraction_inputs"):
            source_evidence_refs.append(
                {
                    "process_id": process_id,
                    "fixture_document_id": _required_text(input_row, "fixture_document_id"),
                    "source_id": _required_text(input_row, "source_id"),
                    "source_kind": _required_text(input_row, "source_kind"),
                    "normalized_text_fixture_ref": _required_text(input_row, "normalized_text_fixture_ref"),
                    "raw_body_ref": None,
                    "requires_live_fetch": False,
                }
            )

        for placeholder in _required_list(process, "requirement_placeholders"):
            requirement_id = _required_text(placeholder, "requirement_id")
            review_status = _placeholder_review_status(placeholder)
            target = evidence_by_requirement.get(requirement_id)
            if target is None:
                raise ValueError("every requirement placeholder must have source evidence refresh target")
            evidence_ids = [_required_text(target, "source_evidence_id")]
            common = {
                "requirement_id": requirement_id,
                "process_id": process_id,
                "permit_type": permit_type,
                "source_evidence_ids": evidence_ids,
                "old_requirement_placeholder": _required_text(placeholder, "old_requirement_placeholder"),
                "new_requirement_placeholder": _required_text(placeholder, "new_requirement_placeholder"),
                "confidence": "pending_reviewer_assignment",
                "human_review_status": review_status,
                "formalization_deferred": True,
                "formalization_status": "deferred_until_human_review",
            }
            if review_status == "held_for_human_review":
                candidate_deltas.append(
                    {
                        **common,
                        "candidate_delta_id": f"candidate-delta-v6-{_slug(process_id)}-{_slug(requirement_id)}",
                        "candidate_requirement_node_delta": True,
                        "delta_status": "candidate_reextracted_delta_pending_review",
                        "superseded_citation_note": _superseded_note(target),
                    }
                )
                impact_hints.append(
                    {
                        "process_id": process_id,
                        "requirement_id": requirement_id,
                        "impact_hint_id": f"impact-v6-{_slug(process_id)}-{_slug(requirement_id)}",
                        "downstream_process_model_impact_hint": "review required before changing process model requirements, documents, stages, or guardrails",
                        "activation_allowed": False,
                    }
                )
            else:
                unchanged_rows.append(
                    {
                        **common,
                        "unchanged_row_id": f"unchanged-v6-{_slug(process_id)}-{_slug(requirement_id)}",
                        "unchanged_requirement_row": True,
                        "unchanged_reason": "work packet placeholder remains pending fixture comparison; no RequirementNode delta is promoted",
                        "superseded_citation_note": _superseded_note(target),
                    }
                )

    work_packet_ref = {
        "fixture_role": "requirement_reextraction_work_packet_v6",
        "path": fixture_ref,
        "packet_id": _required_text(work_packet, "packet_id"),
        "packet_version": work_packet.get("packet_version"),
    }
    candidate_set = {
        "packet_type": PACKET_TYPE,
        "version": 6,
        "fixture_only": True,
        "consumes_only": {"requirement_reextraction_work_packet_v6_fixtures": True},
        "work_packet_refs": [dict(work_packet_ref)],
        "source_fixture_refs": [dict(work_packet_ref)],
        "candidate_requirement_node_deltas": candidate_deltas,
        "unchanged_requirement_rows": unchanged_rows,
        "source_evidence_refs": source_evidence_refs,
        "confidence_placeholder": "pending_reviewer_assignment",
        "human_review_status_placeholder": "pending_human_review_or_held_for_human_review",
        "formalization_deferred": True,
        "superseded_citation_notes": [row["superseded_citation_note"] for row in candidate_deltas + unchanged_rows],
        "downstream_process_model_impact_hints": impact_hints,
        "live_access": {name: False for name in sorted(FORBIDDEN_LIVE_ACCESS)},
        "offline_validation_commands": expected_offline_validation_commands(),
    }
    validate_candidate_set(candidate_set)
    return candidate_set


def expected_offline_validation_commands() -> list[list[str]]:
    return [list(command) for command in OFFLINE_VALIDATION_COMMANDS]


def validate_candidate_set(packet: Mapping[str, Any]) -> None:
    _reject_forbidden_content(packet)
    if packet.get("packet_type") != PACKET_TYPE:
        raise ValueError("packet_type must be fixture_first_reextracted_requirement_candidate_set_v6")
    if packet.get("version") != 6:
        raise ValueError("version must be 6")
    if packet.get("fixture_only") is not True:
        raise ValueError("candidate set must remain fixture-only")
    if packet.get("consumes_only") != {"requirement_reextraction_work_packet_v6_fixtures": True}:
        raise ValueError("consumes_only must require requirement re-extraction work packet v6 fixtures")
    if packet.get("offline_validation_commands") != expected_offline_validation_commands():
        raise ValueError("offline validation commands must exactly match v6 command list")
    if packet.get("confidence_placeholder") != "pending_reviewer_assignment":
        raise ValueError("confidence placeholder is required")
    if packet.get("human_review_status_placeholder") != "pending_human_review_or_held_for_human_review":
        raise ValueError("human review status placeholder is required")
    if packet.get("formalization_deferred") is not True:
        raise ValueError("formalization must be deferred")

    live_access = packet.get("live_access")
    if not isinstance(live_access, Mapping):
        raise ValueError("live_access controls are required")
    if set(live_access) != FORBIDDEN_LIVE_ACCESS:
        raise ValueError("live_access must enumerate all prohibited actions")
    if any(value is not False for value in live_access.values()):
        raise ValueError("live_access controls must all be false")

    _validate_work_packet_refs(_required_list(packet, "work_packet_refs"), "work_packet_refs")
    _validate_work_packet_refs(_required_list(packet, "source_fixture_refs"), "source_fixture_refs")

    deltas = _required_list(packet, "candidate_requirement_node_deltas")
    unchanged = _required_list(packet, "unchanged_requirement_rows")
    evidence_refs = _required_list(packet, "source_evidence_refs")
    superseded_notes = _required_list(packet, "superseded_citation_notes")
    _required_list(packet, "downstream_process_model_impact_hints")

    for ref in evidence_refs:
        if not isinstance(ref, Mapping):
            raise ValueError("source_evidence_refs must contain objects")
        _required_text(ref, "process_id")
        _required_text(ref, "fixture_document_id")
        _required_text(ref, "source_id")
        _required_text(ref, "source_kind")
        _required_text(ref, "normalized_text_fixture_ref")
        if ref.get("raw_body_ref") is not None:
            raise ValueError("source evidence references must not include raw body refs")
        if ref.get("requires_live_fetch") is not False:
            raise ValueError("source evidence references must not require live fetch")

    for row in deltas:
        _validate_requirement_row(row, marker="candidate_requirement_node_delta", expected=True)
        _required_text(row, "candidate_delta_id")
        if row.get("delta_status") != "candidate_reextracted_delta_pending_review":
            raise ValueError("candidate deltas must remain pending review")
        if row.get("human_review_status") != "held_for_human_review":
            raise ValueError("candidate deltas must be held for human review")

    for row in unchanged:
        _validate_requirement_row(row, marker="unchanged_requirement_row", expected=True)
        _required_text(row, "unchanged_row_id")
        _required_text(row, "unchanged_reason")
        if row.get("human_review_status") != "pending_human_review":
            raise ValueError("unchanged rows must remain pending human review")

    for note in superseded_notes:
        if not isinstance(note, str) or not note.strip():
            raise ValueError("superseded citation notes must be non-empty text")

    for hint in _required_list(packet, "downstream_process_model_impact_hints"):
        _required_text(hint, "impact_hint_id")
        _required_text(hint, "process_id")
        _required_text(hint, "requirement_id")
        _required_text(hint, "downstream_process_model_impact_hint")
        if hint.get("activation_allowed") is not False:
            raise ValueError("downstream process-model impact hints must not activate changes")


def _validate_work_packet_refs(refs: list[Any], field_name: str) -> None:
    if len(refs) != 1 or not isinstance(refs[0], Mapping):
        raise ValueError(f"{field_name} must reference exactly one requirement re-extraction work packet v6 fixture")
    if refs[0].get("fixture_role") != "requirement_reextraction_work_packet_v6":
        raise ValueError(f"{field_name} must reference only requirement re-extraction work packet v6 fixture")
    if refs[0].get("packet_id") != SOURCE_PACKET_ID or refs[0].get("packet_version") != 6:
        raise ValueError(f"{field_name} must point to requirement re-extraction work packet v6")
    _required_text(refs[0], "path")


def _validate_source_work_packet(packet: Mapping[str, Any]) -> None:
    _reject_forbidden_content(packet)
    if packet.get("packet_id") != SOURCE_PACKET_ID:
        raise ValueError("source fixture must be requirement re-extraction work packet v6")
    if packet.get("packet_version") != 6:
        raise ValueError("source fixture must be work packet version 6")
    if packet.get("fixture_only") is not True:
        raise ValueError("source work packet must be fixture-only")
    live_access = packet.get("live_access")
    if not isinstance(live_access, Mapping):
        raise ValueError("source work packet must declare live_access controls")
    if any(live_access.get(name) is not False for name in FORBIDDEN_LIVE_ACCESS):
        raise ValueError("source work packet may not enable live or consequential access")
    if packet.get("validation_commands") != [
        ["python3", "-m", "py_compile", "ppd/extraction/requirement_reextraction_work_packet_v6.py"],
        ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_work_packet_v6.py"],
        ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ]:
        raise ValueError("source work packet validation commands must remain exact offline commands")
    for process in _required_list(packet, "process_packets"):
        if process.get("inactive_guardrail_status") != "unchanged":
            raise ValueError("source work packet must keep inactive guardrails unchanged")
        for input_row in _required_list(process, "extraction_inputs"):
            if input_row.get("raw_body_ref") is not None:
                raise ValueError("source work packet must not reference raw bodies")
            if input_row.get("requires_live_fetch") is not False:
                raise ValueError("source work packet must not require live fetch")
        targets = _required_list(process, "source_span_refresh_targets")
        target_requirement_ids = set()
        for target in targets:
            if target.get("requires_live_fetch") is not False:
                raise ValueError("source work packet refresh targets must not require live fetch")
            target_requirement_ids.add(_required_text(target, "requirement_id"))
            _required_text(target, "source_evidence_id")
        for placeholder in _required_list(process, "requirement_placeholders"):
            requirement_id = _required_text(placeholder, "requirement_id")
            if requirement_id not in target_requirement_ids:
                raise ValueError("every requirement placeholder must have source evidence refresh target")


def _validate_requirement_row(row: Mapping[str, Any], marker: str, expected: bool) -> None:
    if row.get(marker) is not expected:
        raise ValueError(f"{marker} marker is required")
    _required_text(row, "requirement_id")
    _required_text(row, "process_id")
    _required_text(row, "permit_type")
    _required_text(row, "old_requirement_placeholder")
    _required_text(row, "new_requirement_placeholder")
    evidence_ids = row.get("source_evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        raise ValueError("source_evidence_ids must be listed")
    if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in evidence_ids):
        raise ValueError("source_evidence_ids must be non-empty text")
    if row.get("confidence") != "pending_reviewer_assignment":
        raise ValueError("confidence must remain a reviewer placeholder")
    _required_text(row, "human_review_status")
    if row.get("formalization_deferred") is not True:
        raise ValueError("requirement rows must defer formalization")
    if row.get("formalization_status") != "deferred_until_human_review":
        raise ValueError("formalization status must be deferred until human review")
    _required_text(row, "superseded_citation_note")


def _placeholder_review_status(row: Mapping[str, Any]) -> str:
    status = _required_text(row, "human_review_status")
    if status == "hold":
        return "held_for_human_review"
    if status == "pending":
        return "pending_human_review"
    raise ValueError("placeholder human_review_status must be pending or hold")


def _superseded_note(target: Mapping[str, Any]) -> str:
    evidence_id = _required_text(target, "source_evidence_id")
    goal = _required_text(target, "refresh_goal")
    return f"Potentially supersedes prior citation {evidence_id}; reviewer must compare fixture span before promotion. Refresh goal: {goal}."


def _required_text(source: Mapping[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required {key}")
    return value.strip()


def _required_list(source: Mapping[str, Any], key: str) -> list[Any]:
    value = source.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing required {key}")
    return value


def _reject_forbidden_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in FORBIDDEN_KEYS:
                raise ValueError(f"{path} contains prohibited artifact key: {key}")
            if key_text in FORBIDDEN_TRUE_FLAGS and child is not False:
                raise ValueError(f"{path} contains prohibited live, official-action, or mutation flag: {key}")
            _reject_forbidden_content(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_forbidden_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(value):
                raise ValueError(f"{path} contains prohibited claim text")


def _slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "row"


__all__ = [
    "build_candidate_set",
    "build_candidate_set_from_fixture",
    "expected_offline_validation_commands",
    "load_work_packet_fixture",
    "validate_candidate_set",
]
