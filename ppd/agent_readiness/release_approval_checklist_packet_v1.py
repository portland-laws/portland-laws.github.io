from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.release_approval_checklist_packet.v1"
MODE = "fixture-first-offline-only"
VALIDATION_COMMAND = ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]

_REQUIRED_ROW_SECTIONS = {
    "rehearsal_references": "missing_rehearsal_references",
    "reviewer_disposition_evidence": "missing_reviewer_disposition_evidence",
    "rollback_note_rows": "missing_rollback_note_rows",
    "dependency_order_checks": "missing_dependency_order_checks",
    "hold_reject_reasons": "missing_hold_reject_reasons",
}
_ALLOWED_DECISIONS = {"hold", "reject"}
_ALLOWED_DISPOSITIONS = {"hold", "reject", "needs_review", "approved_for_offline_hold"}
_ALLOWED_DEPENDENCY_STATUSES = {"checked", "hold", "reject"}
_PRIVATE_FIELD_RE = re.compile(r"(auth[_-]?state|browser|cookie|credential|download(ed)?|har|private|raw[_-]?(artifact|body|capture|crawl|data|download|html|pdf)?|screenshot|session|storage[_-]?state|token|trace)", re.IGNORECASE)
_PRIVATE_TEXT_RE = re.compile(r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/tmp/)|(auth[_ -]?state|browser[_ -]?(artifact|profile|state)|cookie|credential|downloaded[_ -]?(artifact|document|file|pdf)|har\b|password|private[_ -]?(artifact|file|path|value)|raw[_ -]?(artifact|body|capture|crawl|data|download|html|pdf)|screenshot|session[_ -]?(artifact|state|storage)|storage[_ -]?state|token|trace[_ -]?(file|zip)?)", re.IGNORECASE)
_LIVE_CLAIM_RE = re.compile(r"\b(live crawl|live devhub|live browser|live run|live execution|ran live|performed live|accessed devhub|logged in to devhub|used authenticated session|devhub claim verified live)\b", re.IGNORECASE)
_GUARANTEE_RE = re.compile(r"\b(guaranteed approval|guaranteed issuance|permit will be approved|permit will be issued|approval is guaranteed|issuance is guaranteed|legal advice|legal guarantee|permitting guarantee|legally sufficient|legally compliant)\b", re.IGNORECASE)
_OFFICIAL_ACTION_RE = re.compile(r"\b(official action (completed|performed)|submitted|submission completed|paid (the )?fee|payment completed|scheduled (an? )?inspection|cancelled (an? )?inspection|canceled (an? )?inspection|certified (the )?application|uploaded (corrections|plans|documents))\b", re.IGNORECASE)
_PROMOTION_RE = re.compile(r"\b(release promoted|release promotion completed|promotion completed|promoted to active|promoted to production|promoted fixtures|production release complete|active release enabled|ready to promote now)\b", re.IGNORECASE)
_MUTATION_FIELD_RE = re.compile(r"(^|_)(active_)?(artifact|browser|crawl|devhub|fixture|guardrail|prompt|release|release_state|agent_state|source|document|requirement)_(mutation|mutating|update|write|promotion|refresh)(_|$)|(^|_)(mutates|updates|promotes|refreshes|writes)_(artifacts|browser|crawl|devhub|fixtures|guardrails|prompts|release|release_state|agent_state)(_|$)", re.IGNORECASE)
_COMMAND_FORBIDDEN_RE = re.compile(r"\b(live|crawl|devhub|playwright|browser|network|auth|session|promote|release)\b", re.IGNORECASE)


class ReleaseApprovalChecklistPacketV1Error(ValueError):
    def __init__(self, issues: Iterable[Mapping[str, str]]) -> None:
        self.issues = tuple(dict(issue) for issue in issues)
        formatted = "; ".join(f"{issue['code']} at {issue['path']}" for issue in self.issues)
        super().__init__(f"invalid release approval checklist packet v1: {formatted}")


def load_release_approval_checklist_packet_v1(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ReleaseApprovalChecklistPacketV1Error([_issue_obj("invalid_json_root", "$", "JSON root must be an object")])
    packet = copy.deepcopy(dict(data))
    assert_valid_release_approval_checklist_packet_v1(packet)
    return packet


def build_release_approval_checklist_packet_v1(source_packet: Mapping[str, Any]) -> dict[str, Any]:
    packet = copy.deepcopy(dict(source_packet))
    packet.setdefault("packet_type", PACKET_TYPE)
    packet.setdefault("mode", MODE)
    packet.setdefault("approval_decision", "hold")
    packet.setdefault("validation_commands", [VALIDATION_COMMAND])
    assert_valid_release_approval_checklist_packet_v1(packet)
    return packet


def validate_release_approval_checklist_packet_v1(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if packet.get("packet_type") != PACKET_TYPE:
        _add_issue(issues, "invalid_packet_type", "packet_type", f"packet_type must be {PACKET_TYPE}")
    if packet.get("mode") != MODE:
        _add_issue(issues, "invalid_mode", "mode", f"mode must be {MODE}")
    if packet.get("approval_decision") not in _ALLOWED_DECISIONS:
        _add_issue(issues, "invalid_approval_decision", "approval_decision", "approval_decision must be hold or reject for packet v1")

    for section, code in _REQUIRED_ROW_SECTIONS.items():
        rows = packet.get(section)
        if not isinstance(rows, list) or not rows:
            _add_issue(issues, code, section, f"{section} must be a non-empty list")
            continue
        _validate_rows(section, rows, issues)

    commands = packet.get("validation_commands")
    if not isinstance(commands, list) or not commands:
        _add_issue(issues, "missing_validation_commands", "validation_commands", "validation_commands must be a non-empty list of argv lists")
    else:
        for index, command in enumerate(commands):
            _validate_command(command, f"validation_commands[{index}]", issues)

    _scan_for_unsafe_content(packet, "$", issues)
    return issues


def assert_valid_release_approval_checklist_packet_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_release_approval_checklist_packet_v1(packet)
    if issues:
        raise ReleaseApprovalChecklistPacketV1Error(issues)


def _validate_rows(section: str, rows: Sequence[Any], issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows):
        path = f"{section}[{index}]"
        if not isinstance(row, Mapping):
            _add_issue(issues, "invalid_row", path, "section rows must be objects")
            continue
        citations = row.get("source_evidence_ids") or row.get("citations")
        if not _string_list(citations):
            _add_issue(issues, "missing_source_evidence_ids", f"{path}.source_evidence_ids", "row requires cited source evidence")
        if section == "rehearsal_references":
            if not _text(row.get("rehearsal_id")) or not _text(row.get("packet_ref")):
                _add_issue(issues, "invalid_rehearsal_reference", path, "rehearsal reference requires rehearsal_id and packet_ref")
        elif section == "reviewer_disposition_evidence":
            if not _text(row.get("reviewer_id")) or row.get("disposition") not in _ALLOWED_DISPOSITIONS or not _text(row.get("evidence_ref")):
                _add_issue(issues, "invalid_reviewer_disposition_evidence", path, "reviewer disposition evidence requires reviewer_id, hold-style disposition, and evidence_ref")
        elif section == "rollback_note_rows":
            if not _text(row.get("rollback_note_id")) or not _text(row.get("note")):
                _add_issue(issues, "invalid_rollback_note_row", path, "rollback note row requires rollback_note_id and note")
        elif section == "dependency_order_checks":
            if not _text(row.get("check_id")) or not _text(row.get("before")) or not _text(row.get("after")) or row.get("status") not in _ALLOWED_DEPENDENCY_STATUSES:
                _add_issue(issues, "invalid_dependency_order_check", path, "dependency order check requires check_id, before, after, and checked/hold/reject status")
        elif section == "hold_reject_reasons":
            if not _text(row.get("reason_id")) or row.get("decision") not in _ALLOWED_DECISIONS or not _text(row.get("reason")):
                _add_issue(issues, "invalid_hold_reject_reason", path, "hold/reject reason requires reason_id, hold/reject decision, and reason")


def _validate_command(command: Any, path: str, issues: list[dict[str, str]]) -> None:
    if not isinstance(command, list) or not command or not all(isinstance(part, str) and part.strip() for part in command):
        _add_issue(issues, "invalid_validation_command", path, "validation command must be a non-empty argv string list")
        return
    joined = " ".join(command)
    if _COMMAND_FORBIDDEN_RE.search(joined) and command != VALIDATION_COMMAND:
        _add_issue(issues, "unsafe_validation_command", path, "validation command must stay offline and must not invoke live, crawl, DevHub, browser, auth, session, promotion, or release workflows")


def _scan_for_unsafe_content(value: Any, path: str, issues: list[dict[str, str]]) -> None:
    for child_path, child in _walk(value, path):
        name = _path_name(child_path).lower().replace("-", "_")
        if name and _MUTATION_FIELD_RE.search(name) and _active_value(child):
            _add_issue(issues, "active_mutation_flag", child_path, "active mutation flags are not allowed")
        if name and not name.startswith("no_") and _PRIVATE_FIELD_RE.search(name) and _present_value(child):
            _add_issue(issues, "private_or_raw_artifact_field", child_path, "private, session, browser, raw, or downloaded artifact fields are not allowed")
        if isinstance(child, str):
            if _PRIVATE_TEXT_RE.search(child):
                _add_issue(issues, "private_or_raw_artifact_text", child_path, "private, session, browser, raw, or downloaded artifact text is not allowed")
            if _LIVE_CLAIM_RE.search(child):
                _add_issue(issues, "live_crawl_or_devhub_claim", child_path, "live crawl or DevHub claims are not allowed")
            if _GUARANTEE_RE.search(child):
                _add_issue(issues, "legal_or_permitting_guarantee", child_path, "legal or permitting guarantees are not allowed")
            if _OFFICIAL_ACTION_RE.search(child):
                _add_issue(issues, "official_action_completion_claim", child_path, "official-action completion claims are not allowed")
            if _PROMOTION_RE.search(child):
                _add_issue(issues, "release_promotion_claim", child_path, "release promotion claims are not allowed")


def _walk(value: Any, path: str) -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _path_name(path: str) -> str:
    return path.rsplit(".", 1)[-1].split("[", 1)[0]


def _active_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "active", "enabled", "true", "yes"}
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return False


def _present_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return True


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _issue_obj(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _add_issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append(_issue_obj(code, path, message))
