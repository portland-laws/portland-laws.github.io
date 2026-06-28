"""Validate inactive release decision packet v1 safety gates."""

from __future__ import annotations

from typing import Any, Iterable

PACKET_VERSION = "inactive-release-decision-packet-v1"
REQUIRED_FIELDS = (
    "promotion_candidate_references",
    "readiness_replay_references",
    "release_decisions",
    "dependency_ordering",
    "human_reviewer_routing",
    "release_blocker_summaries",
    "smoke_replay_requirements",
    "rollback_notes",
    "validation_commands",
)
REQUIRED_DECISIONS = {"approve", "hold", "reject"}

PRIVATE_FIELD_MARKERS = (
    "auth_state",
    "browser",
    "cookie",
    "credential",
    "download",
    "har",
    "private",
    "raw_",
    "screenshot",
    "session",
    "storage_state",
    "token",
    "trace",
)
PRIVATE_TEXT_MARKERS = (
    "file://",
    "/home/",
    "/users/",
    "/tmp/",
    "auth state",
    "browser state",
    "cookie",
    "credential",
    "downloaded",
    "har",
    "password",
    "private artifact",
    "private file",
    "private path",
    "raw artifact",
    "raw body",
    "raw crawl",
    "raw data",
    "raw download",
    "raw html",
    "raw pdf",
    "screenshot",
    "session artifact",
    "session state",
    "storage state",
    "token",
    "trace.zip",
)
LIVE_OR_DEVHUB_CLAIMS = (
    "live crawl",
    "live browser",
    "live devhub",
    "live execution",
    "live run",
    "crawl completed",
    "ran live",
    "accessed devhub",
    "devhub was accessed",
    "devhub accessed",
    "logged in",
    "authenticated session",
)
PROMOTION_CLAIMS = (
    "release was promoted",
    "promoted release",
    "promoted the release",
    "promotion completed",
    "promotion applied",
    "fixtures were promoted",
    "activated release",
    "activated the release",
    "release state updated",
    "release state changed",
)
OFFICIAL_ACTION_CLAIMS = (
    "official action completed",
    "official action performed",
    "submitted",
    "submission completed",
    "paid the fee",
    "paid fee",
    "payment completed",
    "scheduled inspection",
    "canceled inspection",
    "cancelled inspection",
    "certified application",
    "uploaded plans",
    "uploaded corrections",
)
GUARANTEE_CLAIMS = (
    "legal advice",
    "legal guarantee",
    "permitting guarantee",
    "guaranteed approval",
    "guaranteed issuance",
    "guaranteed permit outcome",
    "approval is guaranteed",
    "issuance is guaranteed",
    "permit will be approved",
    "permit will be issued",
)
COMMAND_FORBIDDEN = ("live", "crawl", "devhub", "playwright", "browser", "network", "auth", "session")
MUTATION_MARKERS = ("mutation", "mutates", "promotes", "release_state_update", "fixture_promotion")


def validate_inactive_release_decision_packet_v1(packet: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if packet.get("packet_version") != PACKET_VERSION:
        _issue(issues, "invalid_packet_version", "packet_version", f"packet_version must be {PACKET_VERSION}")
    if packet.get("mode") != "fixture-first-offline-only":
        _issue(issues, "invalid_mode", "mode", "mode must remain fixture-first-offline-only")

    for field in REQUIRED_FIELDS:
        if not _non_empty_list(packet.get(field)):
            _issue(issues, f"missing_{field}", field, f"{field} must be a non-empty list")

    _validate_reference_rows(packet.get("promotion_candidate_references"), "promotion_candidate_references", issues)
    _validate_reference_rows(packet.get("readiness_replay_references"), "readiness_replay_references", issues)
    _validate_release_decisions(packet.get("release_decisions"), issues)
    _validate_dependency_ordering(packet.get("dependency_ordering"), issues)
    _validate_human_reviewer_routing(packet.get("human_reviewer_routing"), issues)
    _validate_blockers(packet.get("release_blocker_summaries"), issues)
    _validate_smoke_replay(packet.get("smoke_replay_requirements"), issues)
    _validate_rollback_notes(packet.get("rollback_notes"), issues)
    _validate_commands(packet.get("validation_commands"), issues)
    _scan_for_unsafe_content(packet, "", issues)
    return issues


def assert_valid_inactive_release_decision_packet_v1(packet: dict[str, Any]) -> None:
    issues = validate_inactive_release_decision_packet_v1(packet)
    if issues:
        formatted = "; ".join(f"{issue['code']} at {issue['path']}" for issue in issues)
        raise ValueError(f"inactive release decision packet v1 validation failed: {formatted}")


def _validate_reference_rows(value: Any, field: str, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"{field}[{index}]"
        for key in ("ref_id", "packet_type", "fixture_path"):
            if not _text(row.get(key)):
                _issue(issues, f"invalid_{field}", f"{path}.{key}", f"{field} requires {key}")


def _validate_release_decisions(value: Any, issues: list[dict[str, str]]) -> None:
    decisions: set[str] = set()
    for index, row in enumerate(_dict_rows(value)):
        path = f"release_decisions[{index}]"
        decision = _text(row.get("decision"))
        if decision in REQUIRED_DECISIONS:
            decisions.add(decision)
        else:
            _issue(issues, "invalid_release_decision", f"{path}.decision", "decision must be approve, hold, or reject")
        if not _text(row.get("decision_id")):
            _issue(issues, "missing_release_decision_id", f"{path}.decision_id", "release decision requires decision_id")
        if not _text(row.get("rationale")):
            _issue(issues, "missing_release_decision_rationale", f"{path}.rationale", "release decision requires rationale")
        if not _non_empty_list(row.get("evidence_refs")):
            _issue(issues, "missing_release_decision_evidence", f"{path}.evidence_refs", "release decision requires evidence_refs")
    for decision in sorted(REQUIRED_DECISIONS - decisions):
        _issue(issues, f"missing_{decision}_decision", "release_decisions", f"release_decisions must include {decision}")


def _validate_dependency_ordering(value: Any, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"dependency_ordering[{index}]"
        if not _text(row.get("item_id")):
            _issue(issues, "missing_dependency_item", f"{path}.item_id", "dependency ordering requires item_id")
        if not isinstance(row.get("depends_on"), list):
            _issue(issues, "invalid_dependency_depends_on", f"{path}.depends_on", "depends_on must be a list")
        if not _text(row.get("ordering_reason")):
            _issue(issues, "missing_dependency_ordering_reason", f"{path}.ordering_reason", "dependency ordering requires ordering_reason")


def _validate_human_reviewer_routing(value: Any, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"human_reviewer_routing[{index}]"
        if not _text(row.get("reviewer_role")):
            _issue(issues, "missing_reviewer_role", f"{path}.reviewer_role", "routing requires reviewer_role")
        if not _text(row.get("review_queue")):
            _issue(issues, "missing_review_queue", f"{path}.review_queue", "routing requires review_queue")
        if row.get("required_before") != "any_release_promotion_or_official_action":
            _issue(issues, "invalid_reviewer_gate", f"{path}.required_before", "routing must gate promotion and official action")


def _validate_blockers(value: Any, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"release_blocker_summaries[{index}]"
        if not _text(row.get("blocker_id")):
            _issue(issues, "missing_blocker_id", f"{path}.blocker_id", "blocker summary requires blocker_id")
        if not _text(row.get("summary")):
            _issue(issues, "missing_blocker_summary", f"{path}.summary", "blocker summary requires summary")
        if _text(row.get("status")) not in {"open", "deferred", "cleared_by_fixture_review"}:
            _issue(issues, "invalid_blocker_status", f"{path}.status", "invalid blocker status")


def _validate_smoke_replay(value: Any, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"smoke_replay_requirements[{index}]"
        if not _text(row.get("requirement_id")):
            _issue(issues, "missing_smoke_replay_requirement_id", f"{path}.requirement_id", "smoke replay requires requirement_id")
        if not _text(row.get("fixture_ref")):
            _issue(issues, "missing_smoke_replay_fixture_ref", f"{path}.fixture_ref", "smoke replay requires fixture_ref")
        if not _non_empty_list(row.get("expected_checks")):
            _issue(issues, "missing_smoke_replay_expected_checks", f"{path}.expected_checks", "smoke replay requires expected_checks")


def _validate_rollback_notes(value: Any, issues: list[dict[str, str]]) -> None:
    for index, row in enumerate(_dict_rows(value)):
        path = f"rollback_notes[{index}]"
        if not _text(row.get("note_id")):
            _issue(issues, "missing_rollback_note_id", f"{path}.note_id", "rollback note requires note_id")
        if not _text(row.get("rollback_scope")):
            _issue(issues, "missing_rollback_scope", f"{path}.rollback_scope", "rollback note requires rollback_scope")
        if not _text(row.get("operator_note")):
            _issue(issues, "missing_rollback_operator_note", f"{path}.operator_note", "rollback note requires operator_note")


def _validate_commands(value: Any, issues: list[dict[str, str]]) -> None:
    if not isinstance(value, list):
        return
    for index, command in enumerate(value):
        path = f"validation_commands[{index}]"
        if not isinstance(command, list) or not command or not all(isinstance(part, str) and part.strip() for part in command):
            _issue(issues, "invalid_validation_command", path, "validation command must be a non-empty argv string list")
            continue
        command_text = " ".join(command).lower()
        if any(marker in command_text for marker in COMMAND_FORBIDDEN):
            _issue(issues, "unsafe_validation_command", path, "validation command must remain offline and fixture-only")


def _scan_for_unsafe_content(value: Any, path: str, issues: list[dict[str, str]]) -> None:
    for child_path, child in _walk(value, path):
        name = _path_name(child_path).lower().replace("-", "_")
        if name == "active_mutation_flags" and _present_value(child):
            _issue(issues, "active_mutation_flag", child_path, "active mutation flags are not allowed")
        if name.startswith("active_") and any(marker in name for marker in MUTATION_MARKERS) and _active_flag(child):
            _issue(issues, "active_mutation_flag", child_path, "active mutation flags are not allowed")
        if name and not name.startswith("no_") and any(marker in name for marker in PRIVATE_FIELD_MARKERS) and _present_value(child):
            _issue(issues, "private_or_raw_artifact", child_path, "private, raw, downloaded, browser, session, or trace artifacts are not allowed")
        if isinstance(child, str):
            text = child.lower()
            if any(marker in text for marker in PRIVATE_TEXT_MARKERS):
                _issue(issues, "private_or_raw_artifact", child_path, "private, raw, downloaded, browser, session, or trace text is not allowed")
            if any(marker in text for marker in LIVE_OR_DEVHUB_CLAIMS):
                _issue(issues, "live_crawl_or_devhub_claim", child_path, "live crawl or DevHub claims are not allowed")
            if any(marker in text for marker in PROMOTION_CLAIMS):
                _issue(issues, "release_promotion_claim", child_path, "release promotion claims are not allowed")
            if any(marker in text for marker in OFFICIAL_ACTION_CLAIMS):
                _issue(issues, "official_action_completion_claim", child_path, "official action completion claims are not allowed")
            if any(marker in text for marker in GUARANTEE_CLAIMS):
                _issue(issues, "legal_or_permitting_guarantee", child_path, "legal or permitting guarantees are not allowed")


def _walk(value: Any, path: str) -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = str(key) if not path else f"{path}.{key}"
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _path_name(path: str) -> str:
    if not path:
        return ""
    return path.rsplit(".", 1)[-1].split("[", 1)[0]


def _active_flag(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "active", "enabled", "true", "yes"}
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return False


def _present_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return bool(value)
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})


validate_inactive_release_decision_packet = validate_inactive_release_decision_packet_v1
assert_valid_inactive_release_decision_packet = assert_valid_inactive_release_decision_packet_v1
