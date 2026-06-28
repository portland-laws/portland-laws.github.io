from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PACKET_VERSION = "devhub-read-only-preflight-packet-v6"
EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/devhub_read_only_preflight_packet_v6.py", "ppd/tests/test_devhub_read_only_preflight_packet_v6.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_devhub_read_only_preflight_packet_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_ALLOWED_SOURCE_TYPES = {"agent_guardrail_api_compat_v6", "synthetic_devhub_surface_fixture"}
_REQUIRED_SOURCE_TYPES = {"agent_guardrail_api_compat_v6", "synthetic_devhub_surface_fixture"}
_ALLOWED_PAGE_CATEGORIES = {
    "devhub_home",
    "my_permits_and_requests",
    "permit_or_request_detail",
    "status_messages",
    "fee_notice_review",
    "correction_request_review",
    "attachment_list_review",
    "inspection_results_review",
}
_REQUIRED_REFUSED_TOPICS = {"captcha", "mfa", "account_creation"}
_REQUIRED_CAPTURE_FIELDS = {
    "synthetic_surface_id",
    "synthetic_page_category",
    "synthetic_heading_text",
    "synthetic_landmark_role",
    "synthetic_region_label",
    "synthetic_control_role",
    "synthetic_accessible_name",
    "synthetic_status_message_category",
    "synthetic_validation_message_category",
    "synthetic_read_only_stop_reason",
}
_REQUIRED_PRIVATE_EXCLUSIONS = {
    "credentials",
    "cookies",
    "auth_state",
    "session_state",
    "screenshots",
    "traces",
    "har_files",
    "private_documents",
    "downloaded_documents",
    "raw_page_values",
    "local_private_paths",
    "payment_details",
}
_PROHIBITED_FALSE_FLAGS = (
    "opens_devhub",
    "stores_auth_state",
    "creates_traces",
    "creates_screenshots",
    "creates_har_files",
    "reads_private_documents",
    "uploads",
    "submits",
    "certifies",
    "pays",
    "schedules",
    "creates_accounts",
    "makes_legal_or_permitting_guarantees",
)
_REQUIRED_LIST_SECTIONS = (
    "source_fixtures",
    "manual_login_handoff_prerequisites",
    "allowed_read_only_page_categories",
    "refused_paths",
    "redaction_requirements",
    "accessible_structure_capture_fields",
    "private_artifact_exclusions",
    "timeout_abort_criteria",
    "post_capture_review_placeholders",
    "validation_commands",
)
_ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "mutation_enabled",
    "write_enabled",
    "writes_enabled",
    "can_mutate",
    "mutates_devhub",
    "mutation_mode",
}
_COMPLETION_KEYS = {"submitted", "uploaded", "paid", "scheduled", "certified", "account_created"}
_PRIVATE_ARTIFACT_KEYS = {
    "credentials",
    "cookies",
    "auth_state",
    "session_state",
    "trace",
    "traces",
    "har",
    "har_file",
    "har_files",
    "screenshot",
    "screenshots",
    "private_document",
    "private_documents",
    "downloaded_document",
    "downloaded_documents",
    "raw_page_value",
    "raw_page_values",
    "payment_detail",
    "payment_details",
}
_ALLOWED_PRIVATE_ARTIFACT_POLICY_PATHS = {
    "$.private_artifact_exclusions",
    "$.no_effect_policy.stores_auth_state",
    "$.no_effect_policy.creates_traces",
    "$.no_effect_policy.creates_screenshots",
    "$.no_effect_policy.creates_har_files",
    "$.no_effect_policy.reads_private_documents",
    "$.no_effect_policy.pays",
    "$.auth_state_stored",
}


@dataclass(frozen=True)
class DevHubReadOnlyPreflightIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class DevHubReadOnlyPreflightPacketV6Error(ValueError):
    def __init__(self, issues: Sequence[DevHubReadOnlyPreflightIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("invalid DevHub read-only preflight packet v6: " + "; ".join(issue.message for issue in issues))


def validate_devhub_read_only_preflight_packet_v6(packet: Mapping[str, Any]) -> list[DevHubReadOnlyPreflightIssue]:
    issues: list[DevHubReadOnlyPreflightIssue] = []
    if not isinstance(packet, Mapping):
        return [DevHubReadOnlyPreflightIssue("invalid_packet", "$", "packet must be an object")]

    if packet.get("packet_version") != PACKET_VERSION:
        issues.append(DevHubReadOnlyPreflightIssue("invalid_packet_version", "packet_version", f"packet_version must be {PACKET_VERSION}"))
    if packet.get("fixture_first") is not True:
        issues.append(DevHubReadOnlyPreflightIssue("not_fixture_first", "fixture_first", "packet must be fixture_first"))
    if packet.get("devhub_opened") is not False:
        issues.append(DevHubReadOnlyPreflightIssue("live_access_not_allowed", "devhub_opened", "packet must not open DevHub"))
    if packet.get("auth_state_stored") is not False:
        issues.append(DevHubReadOnlyPreflightIssue("auth_state_not_allowed", "auth_state_stored", "packet must not store auth state"))

    for key in _REQUIRED_LIST_SECTIONS:
        if not _non_empty_sequence(packet.get(key)):
            issues.append(DevHubReadOnlyPreflightIssue("missing_section", key, f"{key} must be a non-empty list"))

    _validate_no_effect_policy(packet.get("no_effect_policy"), issues)
    _validate_source_fixtures(packet.get("source_fixtures"), issues)
    _validate_manual_login_handoff(packet.get("manual_login_handoff_prerequisites"), issues)
    _validate_page_categories(packet.get("allowed_read_only_page_categories"), issues)
    _validate_refused_paths(packet.get("refused_paths"), issues)
    _validate_redaction_requirements(packet.get("redaction_requirements"), issues)
    _validate_capture_fields(packet.get("accessible_structure_capture_fields"), issues)
    _validate_private_exclusions(packet.get("private_artifact_exclusions"), issues)
    _validate_timeouts(packet.get("timeout_abort_criteria"), issues)
    _validate_review_placeholders(packet.get("post_capture_review_placeholders"), issues)
    _validate_validation_commands(packet.get("validation_commands"), issues)
    _scan_for_forbidden_claims_and_artifacts(packet, issues)
    return _dedupe(issues)


def assert_valid_devhub_read_only_preflight_packet_v6(packet: Mapping[str, Any]) -> None:
    issues = validate_devhub_read_only_preflight_packet_v6(packet)
    if issues:
        raise DevHubReadOnlyPreflightPacketV6Error(issues)


def validate_packet(packet: Mapping[str, Any]) -> list[DevHubReadOnlyPreflightIssue]:
    return validate_devhub_read_only_preflight_packet_v6(packet)


def _validate_no_effect_policy(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not isinstance(value, Mapping):
        issues.append(DevHubReadOnlyPreflightIssue("missing_no_effect_policy", "no_effect_policy", "no_effect_policy must be an object"))
        return
    for key in _PROHIBITED_FALSE_FLAGS:
        if value.get(key) is not False:
            issues.append(DevHubReadOnlyPreflightIssue("unsafe_effect_policy", f"no_effect_policy.{key}", f"no_effect_policy.{key} must be false"))


def _validate_source_fixtures(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    seen_types: set[str] = set()
    for index, row in enumerate(value):
        path = f"source_fixtures[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_source_fixture", path, "source fixture must be an object"))
            continue
        source_type = row.get("source_type")
        if source_type not in _ALLOWED_SOURCE_TYPES:
            issues.append(DevHubReadOnlyPreflightIssue("invalid_source_type", f"{path}.source_type", "source fixture must be agent_guardrail_api_compat_v6 or synthetic_devhub_surface_fixture"))
        else:
            seen_types.add(str(source_type))
        fixture_path = row.get("fixture_path")
        if not isinstance(fixture_path, str) or not fixture_path.startswith("ppd/tests/fixtures/"):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_fixture_path", f"{path}.fixture_path", "fixture_path must point under ppd/tests/fixtures"))
        if row.get("live_fetch_performed") is not False:
            issues.append(DevHubReadOnlyPreflightIssue("live_fetch_not_allowed", f"{path}.live_fetch_performed", "source fixture must not be live-fetched"))
        if row.get("contains_private_values") is not False:
            issues.append(DevHubReadOnlyPreflightIssue("private_values_not_allowed", f"{path}.contains_private_values", "source fixture must not contain private values"))
    missing = _REQUIRED_SOURCE_TYPES - seen_types
    if missing:
        issues.append(DevHubReadOnlyPreflightIssue("missing_source_fixture_type", "source_fixtures", "source_fixtures must include guardrail compatibility v6 and synthetic DevHub surface fixtures"))


def _validate_manual_login_handoff(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    text = " ".join(str(row.get("requirement", "")) for row in value if isinstance(row, Mapping)).lower()
    required_fragments = ("user-owned account", "manually complete sign-in", "read-only")
    if not all(fragment in text for fragment in required_fragments):
        issues.append(DevHubReadOnlyPreflightIssue("missing_manual_login_handoff", "manual_login_handoff_prerequisites", "manual-login handoff must require a user-owned account, manual sign-in, and read-only confirmation"))
    for index, row in enumerate(value):
        path = f"manual_login_handoff_prerequisites[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_manual_login_handoff", path, "manual-login prerequisite must be an object"))
            continue
        action = row.get("packet_action")
        if action not in {"document_prerequisite_only", "refuse_automation", "require_operator_check"}:
            issues.append(DevHubReadOnlyPreflightIssue("invalid_manual_login_action", f"{path}.packet_action", "manual-login prerequisite action must be documentation, refusal, or operator check only"))


def _validate_page_categories(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    categories = {item for item in value if isinstance(item, str)}
    if categories != _ALLOWED_PAGE_CATEGORIES:
        issues.append(DevHubReadOnlyPreflightIssue("invalid_page_categories", "allowed_read_only_page_categories", "allowed page categories must exactly match the read-only DevHub category set"))


def _validate_refused_paths(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    topics: set[str] = set()
    for index, row in enumerate(value):
        path = f"refused_paths[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_refused_path", path, "refused path must be an object"))
            continue
        topic = row.get("topic")
        if isinstance(topic, str):
            topics.add(topic)
        if row.get("disposition") != "refuse_and_manual_handoff":
            issues.append(DevHubReadOnlyPreflightIssue("invalid_refused_disposition", f"{path}.disposition", "refused paths must use refuse_and_manual_handoff"))
        if row.get("automated") is not False:
            issues.append(DevHubReadOnlyPreflightIssue("refused_path_automation", f"{path}.automated", "refused paths must not be automated"))
    if not _REQUIRED_REFUSED_TOPICS.issubset(topics):
        issues.append(DevHubReadOnlyPreflightIssue("missing_refused_topics", "refused_paths", "refused paths must cover CAPTCHA, MFA, and account creation"))


def _validate_redaction_requirements(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    text = " ".join(str(row.get("requirement", "")) for row in value if isinstance(row, Mapping)).lower()
    required_fragments = ("synthetic placeholders", "do not capture", "synthetic metadata")
    if not all(fragment in text for fragment in required_fragments):
        issues.append(DevHubReadOnlyPreflightIssue("missing_redaction_requirements", "redaction_requirements", "redaction requirements must require synthetic placeholders, non-capture of private artifacts, and synthetic metadata only"))
    for index, row in enumerate(value):
        path = f"redaction_requirements[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_redaction_requirement", path, "redaction requirement must be an object"))
            continue
        if not isinstance(row.get("redaction_id"), str) or not row.get("redaction_id"):
            issues.append(DevHubReadOnlyPreflightIssue("missing_redaction_id", f"{path}.redaction_id", "redaction requirement needs an id"))


def _validate_capture_fields(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    fields = {item for item in value if isinstance(item, str)}
    if not _REQUIRED_CAPTURE_FIELDS.issubset(fields):
        issues.append(DevHubReadOnlyPreflightIssue("missing_capture_fields", "accessible_structure_capture_fields", "accessible capture fields must include the required synthetic structure fields"))
    for field in fields:
        if not field.startswith("synthetic_"):
            issues.append(DevHubReadOnlyPreflightIssue("unsafe_capture_field", "accessible_structure_capture_fields", "capture fields must be synthetic metadata fields"))


def _validate_private_exclusions(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    exclusions = {item for item in value if isinstance(item, str)}
    missing = _REQUIRED_PRIVATE_EXCLUSIONS - exclusions
    if missing:
        issues.append(DevHubReadOnlyPreflightIssue("missing_private_exclusions", "private_artifact_exclusions", "private artifact exclusions must cover auth, browser artifacts, private documents, raw values, paths, and payment details"))


def _validate_timeouts(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"timeout_abort_criteria[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_timeout", path, "timeout criterion must be an object"))
            continue
        if not isinstance(row.get("criterion_id"), str) or not row.get("criterion_id"):
            issues.append(DevHubReadOnlyPreflightIssue("missing_timeout_id", f"{path}.criterion_id", "timeout criterion needs an id"))
        if row.get("action") != "abort_without_artifact_capture":
            issues.append(DevHubReadOnlyPreflightIssue("invalid_timeout_action", f"{path}.action", "timeout action must abort without artifact capture"))


def _validate_review_placeholders(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"post_capture_review_placeholders[{index}]"
        if not isinstance(row, Mapping):
            issues.append(DevHubReadOnlyPreflightIssue("invalid_review_placeholder", path, "review placeholder must be an object"))
            continue
        if row.get("status") != "placeholder_only":
            issues.append(DevHubReadOnlyPreflightIssue("invalid_review_status", f"{path}.status", "review placeholders must remain placeholder_only"))
        if row.get("contains_captured_devhub_data") is not False:
            issues.append(DevHubReadOnlyPreflightIssue("captured_data_not_allowed", f"{path}.contains_captured_devhub_data", "review placeholders must not contain captured DevHub data"))


def _validate_validation_commands(value: Any, issues: list[DevHubReadOnlyPreflightIssue]) -> None:
    if value != EXACT_OFFLINE_VALIDATION_COMMANDS:
        issues.append(DevHubReadOnlyPreflightIssue("invalid_validation_commands", "validation_commands", "validation_commands must exactly match the offline packet commands"))


def _scan_for_forbidden_claims_and_artifacts(value: Any, issues: list[DevHubReadOnlyPreflightIssue], path: str = "$", parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key)
            normalized_key = key_text.lower()
            if normalized_key in _COMPLETION_KEYS and child is True:
                issues.append(DevHubReadOnlyPreflightIssue("forbidden_completion_claim", child_path, "packet must not claim official DevHub completion"))
            if normalized_key in _ACTIVE_MUTATION_KEYS and child not in (False, "disabled", "none", None):
                issues.append(DevHubReadOnlyPreflightIssue("active_mutation_not_allowed", child_path, "packet must not enable active mutation flags"))
            if normalized_key in _PRIVATE_ARTIFACT_KEYS and child_path not in _ALLOWED_PRIVATE_ARTIFACT_POLICY_PATHS:
                if child not in (False, None, [], {}, ""):
                    issues.append(DevHubReadOnlyPreflightIssue("private_artifact_not_allowed", child_path, "packet must not include private session, auth, browser, document, or payment artifacts"))
            _scan_for_forbidden_claims_and_artifacts(child, issues, child_path, normalized_key)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            if path == "$.private_artifact_exclusions":
                continue
            _scan_for_forbidden_claims_and_artifacts(child, issues, child_path, parent_key)
    elif isinstance(value, str):
        _scan_string_claim(value, issues, path, parent_key)


def _scan_string_claim(value: str, issues: list[DevHubReadOnlyPreflightIssue], path: str, parent_key: str) -> None:
    text = value.lower()
    allowed_policy_keys = {"requirement", "reason", "exclusion", "abort_when", "placeholder", "description", "purpose"}
    if "live devhub access" in text and not any(word in text for word in ("no ", "not ", "without", "before any")):
        issues.append(DevHubReadOnlyPreflightIssue("live_access_claim_not_allowed", path, "packet must not claim live DevHub access"))
    if parent_key not in allowed_policy_keys:
        if "legal guarantee" in text or "permitting guarantee" in text or "permit approved" in text:
            issues.append(DevHubReadOnlyPreflightIssue("forbidden_guarantee_claim", path, "packet must not make legal or permitting guarantees"))
        if "official action completed" in text or "submission completed" in text or "payment completed" in text:
            issues.append(DevHubReadOnlyPreflightIssue("forbidden_completion_claim", path, "packet must not claim official DevHub completion"))


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _dedupe(issues: list[DevHubReadOnlyPreflightIssue]) -> list[DevHubReadOnlyPreflightIssue]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[DevHubReadOnlyPreflightIssue] = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
