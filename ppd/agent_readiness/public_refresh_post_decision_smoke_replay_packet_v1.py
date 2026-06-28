"""Validation for public refresh post-decision smoke replay packet v1.

The packet is a fixture-first, offline-only replay artifact. It may summarize
post-decision smoke evidence, but it must not claim live extraction, crawling,
DevHub access, release activation, official action completion, artifact
mutation, or legal/permitting guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


PACKET_TYPE = "public_refresh_post_decision_smoke_replay_packet"
PACKET_VERSION = 1
MODE = "fixture_first_offline_post_decision_smoke_replay"

REQUIRED_SCENARIO_FIELDS: Mapping[str, str] = {
    "release_decision_references": "missing_release_decision_references",
    "offline_agent_api_smoke_expectations": "missing_offline_agent_api_smoke_expectations",
    "source_citation_lookup_checks": "missing_source_citation_lookup_checks",
    "guardrail_predicate_replay_checks": "missing_guardrail_predicate_replay_checks",
    "blocked_action_regression_checks": "missing_blocked_action_regression_checks",
    "stale_source_hold_checks": "missing_stale_source_hold_checks",
    "rollback_notes": "missing_rollback_notes",
    "reviewer_routing": "missing_reviewer_routing",
}

SENSITIVE_KEY_MARKERS: tuple[str, ...] = (
    "auth_state",
    "browser_state",
    "browser_trace",
    "cookie",
    "credential",
    "downloaded_artifact",
    "downloaded_document",
    "downloaded_pdf",
    "har",
    "html_body",
    "local_private_path",
    "password",
    "private_artifact",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "raw_output",
    "raw_pdf",
    "screenshot",
    "session_state",
    "storage_state",
    "token",
    "trace",
)

SENSITIVE_VALUE_MARKERS: tuple[str, ...] = (
    "auth-state",
    "auth_state",
    "browser trace",
    "browser_trace",
    "cookie jar",
    "cookies.json",
    "downloaded artifact",
    "downloaded document",
    "downloaded pdf",
    "har file",
    "private artifact",
    "raw crawl",
    "raw download",
    "raw html",
    "raw output",
    "raw pdf",
    "screenshot",
    "session state",
    "session_state",
    "storage state",
    "storage_state",
    "trace file",
)

LIVE_EXTRACTION_OR_CRAWL_RE = re.compile(
    r"\\b(live|actual|actively)\\s+(crawl|crawling|extraction|extract|fetch|fetched|download|downloaded)\\b|"
    r"\\b(crawl|crawling|extraction|extract|fetched|downloaded)\\s+(completed|performed|ran|executed|succeeded)\\b",
    re.IGNORECASE,
)

DEVHUB_CLAIM_RE = re.compile(
    r"\\b(devhub|portal|authenticated session|browser session)\\b.*\\b(opened|logged in|authenticated|visited|used|observed|executed)\\b|"
    r"\\b(opened|logged in|authenticated|visited|used|observed|executed)\\b.*\\b(devhub|portal|authenticated session|browser session)\\b",
    re.IGNORECASE,
)

RELEASE_ACTIVATION_RE = re.compile(
    r"\\b(release|candidate|packet)\\b.*\\b(activated|activation completed|promoted|promotion completed|enabled live)\\b|"
    r"\\b(activated|promoted)\\b.*\\b(release|candidate|packet)\\b",
    re.IGNORECASE,
)

OFFICIAL_ACTION_RE = re.compile(
    r"\\b(official action|submission|submit|submitted|upload|uploaded|payment|paid|schedule|scheduled|certify|certified|cancel|cancelled|canceled)\\b.*\\b(completed|performed|executed|succeeded|done)\\b|"
    r"\\b(completed|performed|executed|succeeded)\\b.*\\b(official action|submission|submitted|upload|uploaded|payment|paid|scheduled|certified|cancelled|canceled)\\b",
    re.IGNORECASE,
)

LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\\b(legal guarantee|legal advice|legally sufficient|compliant as a matter of law|approval guaranteed|guaranteed approval|guaranteed permit|guaranteed issuance|permit will be approved|permit will be issued|will pass plan review|outcome is guaranteed)\\b",
    re.IGNORECASE,
)

ACTIVE_MUTATION_KEY_RE = re.compile(
    r"(^|_)(active_)?(artifact|archive|document|guardrail|process|prompt|release|release_state|source|surface|surface_registry|agent_state|fixture)_(mutation|mutating|update|write|promotion|activation)(_|$)",
    re.IGNORECASE,
)

ACTIVE_MUTATION_FLAG_NAMES: frozenset[str] = frozenset(
    {
        "active_artifact_mutation",
        "active_archive_mutation",
        "active_document_mutation",
        "active_fixture_mutation",
        "active_guardrail_mutation",
        "active_process_mutation",
        "active_prompt_mutation",
        "active_release_activation",
        "active_release_state_mutation",
        "active_source_mutation",
        "active_surface_registry_mutation",
        "agent_state_write_enabled",
        "artifact_mutation_enabled",
        "artifact_write_enabled",
        "guardrail_mutation_enabled",
        "prompt_mutation_enabled",
        "release_activation_enabled",
        "release_promotion_enabled",
        "release_state_update_enabled",
        "source_mutation_enabled",
        "surface_registry_write_enabled",
    }
)


@dataclass(frozen=True)
class PublicRefreshPostDecisionSmokeReplayIssue:
    """Stable validation issue for deterministic tests and daemon diagnostics."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class PublicRefreshPostDecisionSmokeReplayPacketV1Error(ValueError):
    """Raised when a post-decision smoke replay packet is invalid."""

    def __init__(self, issues: Iterable[PublicRefreshPostDecisionSmokeReplayIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.code}" for issue in self.issues)
        super().__init__(detail)


def validate_public_refresh_post_decision_smoke_replay_packet_v1(
    packet: Mapping[str, Any],
) -> tuple[PublicRefreshPostDecisionSmokeReplayIssue, ...]:
    """Return all validation issues for a v1 post-decision smoke replay packet."""

    issues: list[PublicRefreshPostDecisionSmokeReplayIssue] = []

    if packet.get("packet_type") != PACKET_TYPE:
        issues.append(_issue("invalid_packet_type", "$.packet_type", f"packet_type must be {PACKET_TYPE}"))
    if packet.get("packet_version") != PACKET_VERSION:
        issues.append(_issue("invalid_packet_version", "$.packet_version", "packet_version must be 1"))
    if packet.get("mode") != MODE:
        issues.append(_issue("invalid_mode", "$.mode", f"mode must be {MODE}"))

    validation_commands = packet.get("validation_commands")
    if not _valid_validation_commands(validation_commands):
        issues.append(
            _issue(
                "missing_validation_commands",
                "$.validation_commands",
                "packet must include at least one validation command as a non-empty string array",
            )
        )

    scenarios = packet.get("smoke_scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        issues.append(_issue("missing_smoke_scenarios", "$.smoke_scenarios", "packet must include smoke_scenarios"))
        scenarios = []

    for index, scenario in enumerate(scenarios):
        path = f"$.smoke_scenarios[{index}]"
        if not isinstance(scenario, Mapping):
            issues.append(_issue("invalid_smoke_scenario", path, "smoke scenario must be an object"))
            continue
        _validate_scenario(scenario, path, issues)

    _scan_for_prohibited_content(packet, "$", issues)
    return _dedupe(issues)


def assert_valid_public_refresh_post_decision_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> None:
    """Raise when a v1 post-decision smoke replay packet is invalid."""

    issues = validate_public_refresh_post_decision_smoke_replay_packet_v1(packet)
    if issues:
        raise PublicRefreshPostDecisionSmokeReplayPacketV1Error(issues)


def _validate_scenario(
    scenario: Mapping[str, Any],
    path: str,
    issues: list[PublicRefreshPostDecisionSmokeReplayIssue],
) -> None:
    for field, code in REQUIRED_SCENARIO_FIELDS.items():
        if not _has_substantive_value(scenario.get(field)):
            issues.append(_issue(code, f"{path}.{field}", f"scenario must include {field}"))

    if "validation_commands" in scenario and not _valid_validation_commands(scenario.get("validation_commands")):
        issues.append(
            _issue(
                "invalid_scenario_validation_commands",
                f"{path}.validation_commands",
                "scenario validation_commands must be non-empty string arrays when present",
            )
        )


def _valid_validation_commands(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(command, list)
        and bool(command)
        and all(isinstance(part, str) and bool(part.strip()) for part in command)
        for command in value
    )


def _has_substantive_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value) and all(_has_substantive_value(item) for item in value)
    return True


def _scan_for_prohibited_content(
    value: Any,
    path: str,
    issues: list[PublicRefreshPostDecisionSmokeReplayIssue],
    key: str | None = None,
) -> None:
    normalized_key = _normalize_key(key) if key else ""
    if key is not None:
        if any(marker in normalized_key for marker in SENSITIVE_KEY_MARKERS):
            issues.append(
                _issue(
                    "private_raw_or_downloaded_artifact_reference",
                    path,
                    "packet must not include private, raw, session, browser, or downloaded artifact references",
                )
            )
        if _is_active_mutation_key(normalized_key) and value is True:
            issues.append(_issue("active_mutation_flag", path, "active mutation flags must be false or absent"))
        if "release_activation" in normalized_key and value:
            issues.append(_issue("release_activation_claim", path, "packet must not claim release activation"))
        if "official_action" in normalized_key and "completion" in normalized_key and value:
            issues.append(_issue("official_action_completion_claim", path, "packet must not claim official-action completion"))
        if "devhub" in normalized_key and value not in (None, False, "", [], {}):
            issues.append(_issue("devhub_claim", path, "packet must not include DevHub access claims"))

    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            _scan_for_prohibited_content(child_value, f"{path}.{child_key_text}", issues, child_key_text)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            _scan_for_prohibited_content(child_value, f"{path}[{index}]", issues, None)
        return

    if isinstance(value, str):
        lowered = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
        if any(marker in lowered for marker in SENSITIVE_VALUE_MARKERS):
            issues.append(
                _issue(
                    "private_raw_or_downloaded_artifact_reference",
                    path,
                    "packet must not include private, raw, session, browser, or downloaded artifact references",
                )
            )
        if LIVE_EXTRACTION_OR_CRAWL_RE.search(value):
            issues.append(_issue("live_extraction_or_crawl_claim", path, "packet must not claim live extraction or crawling"))
        if DEVHUB_CLAIM_RE.search(value):
            issues.append(_issue("devhub_claim", path, "packet must not include DevHub access claims"))
        if RELEASE_ACTIVATION_RE.search(value):
            issues.append(_issue("release_activation_claim", path, "packet must not claim release activation"))
        if OFFICIAL_ACTION_RE.search(value):
            issues.append(_issue("official_action_completion_claim", path, "packet must not claim official-action completion"))
        if LEGAL_OR_PERMITTING_GUARANTEE_RE.search(value):
            issues.append(
                _issue(
                    "legal_or_permitting_guarantee",
                    path,
                    "packet must not include legal or permitting guarantees",
                )
            )


def _is_active_mutation_key(normalized_key: str) -> bool:
    return normalized_key in ACTIVE_MUTATION_FLAG_NAMES or bool(ACTIVE_MUTATION_KEY_RE.search(normalized_key))


def _normalize_key(key: str | None) -> str:
    return str(key or "").lower().replace("-", "_").replace(" ", "_")


def _issue(code: str, path: str, message: str) -> PublicRefreshPostDecisionSmokeReplayIssue:
    return PublicRefreshPostDecisionSmokeReplayIssue(code=code, path=path, message=message)


def _dedupe(
    issues: Sequence[PublicRefreshPostDecisionSmokeReplayIssue],
) -> tuple[PublicRefreshPostDecisionSmokeReplayIssue, ...]:
    seen: set[tuple[str, str]] = set()
    output: list[PublicRefreshPostDecisionSmokeReplayIssue] = []
    for issue in issues:
        key = (issue.code, issue.path)
        if key in seen:
            continue
        seen.add(key)
        output.append(issue)
    return tuple(output)
