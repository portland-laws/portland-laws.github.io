"""Validation for public refresh reviewer bundle packet v1.

The reviewer bundle is fixture-first and metadata-only. It records the evidence a
human reviewer must see before a public refresh can advance, but it must not claim
that extraction, crawling, DevHub work, release activation, official actions, or
artifact mutation already happened.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

PACKET_VERSION = "public-refresh-reviewer-bundle-packet-v1"

ALLOWED_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/public_refresh/reviewer_bundle_packet_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_reviewer_bundle_packet_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_TOP_LEVEL_LISTS = (
    "process_model_delta_refs",
    "guardrail_recompile_refs",
    "agent_gap_analysis_replay_refs",
    "reviewer_ready_dispositions",
    "owner_signoff_placeholders",
    "dependency_sequence",
    "release_blocker_notes",
    "rollback_checkpoints",
    "validation_commands",
)
_REQUIRED_DISPOSITION_TYPES = {"requirement", "process", "guardrail", "agent_impact"}
_REQUIRED_REF_FIELDS = {
    "process_model_delta_refs": ("ref_id", "process_id", "delta_id", "fixture_ref"),
    "guardrail_recompile_refs": ("ref_id", "guardrail_bundle_id", "recompile_plan_id", "fixture_ref"),
    "agent_gap_analysis_replay_refs": ("ref_id", "replay_id", "case_id", "fixture_ref"),
}
_FORBIDDEN_KEY_RE = re.compile(
    r"(^|_)(auth[_-]?state|browser[_-]?(artifact|context|state|trace)|downloaded?[_-]?(artifact|document|path|file)|devhub|har|private[_-]?(artifact|fact|path|url|value)|raw[_-]?(artifact|body|content|crawl|download|html|text)|session[_-]?(artifact|cookie|path|state)|screenshot|storage[_-]?state|trace|warc)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_VALUE_RE = re.compile(
    r"(^(file|session|warc|crawl|archive)://|/(tmp|var/folders|private|home)/|\\users\\|\.har$|\.warc(\.gz)?$|trace\.zip$|/raw/|/downloads?/|/sessions?/|raw crawl output|raw response body|downloaded document|private session|browser trace|auth state)",
    re.IGNORECASE,
)
_LIVE_EXTRACTION_OR_CRAWL_RE = re.compile(
    r"\b(live extraction|live crawl|live recrawl|crawler (?:ran|executed|captured|downloaded)|network (?:access|crawl|extraction) (?:ran|executed|performed)|downloaded live|captured live|extracted live)\b",
    re.IGNORECASE,
)
_DEVHUB_RE = re.compile(r"\bdevhub\b", re.IGNORECASE)
_RELEASE_ACTIVATION_RE = re.compile(
    r"\b(release (?:activated|activation complete|enabled|deployed|promoted)|activated release|production release)\b",
    re.IGNORECASE,
)
_ARTIFACT_MUTATION_RE = re.compile(
    r"\b(artifact(?:s)? (?:mutated|updated|written|changed)|mutated artifact|active artifact mutation|wrote artifact)\b",
    re.IGNORECASE,
)
_OFFICIAL_ACTION_RE = re.compile(
    r"\b(submit(?:ted)? (?:a )?permit|submit(?:ted)? application|pay(?:ing|ment)? fees?|schedule(?:d)? inspection|upload(?:ed)? corrections?|certif(?:y|ied) acknowledgement|purchase(?:d)? permit|cancel(?:led)? permit|withdraw(?:n)? permit|official action (?:completed|complete))\b",
    re.IGNORECASE,
)
_LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|will be approved|approval is assured|permit will issue|permit must issue|ensures issuance|ensures approval|legally valid|legal outcome|legal compliance guaranteed|no legal risk|cannot be denied|permitting outcome guaranteed)\b",
    re.IGNORECASE,
)
_MUTATION_DOMAINS = ("artifact", "source", "process", "requirement", "guardrail", "release_state", "release-state")
_MUTATION_TERMS = ("active", "applied", "changed", "enabled", "mutated", "mutation", "updated", "write", "written")
_ACTIVE_VALUES = {"true", "active", "applied", "changed", "enabled", "mutated", "mutation_enabled", "yes"}
_ALLOWED_DEVHUB_PATHS = {
    "packet.devhub_scope",
    "packet.safety_attestations.no_devhub_claims",
}


@dataclass(frozen=True)
class PublicRefreshReviewerBundlePacketV1ValidationResult:
    valid: bool
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.valid

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors)}


def validate_public_refresh_reviewer_bundle_packet_v1(
    packet: Mapping[str, Any],
) -> PublicRefreshReviewerBundlePacketV1ValidationResult:
    """Validate a metadata-only public refresh reviewer bundle packet."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return PublicRefreshReviewerBundlePacketV1ValidationResult(False, ("packet must be an object",))

    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet_version must be {PACKET_VERSION}")
    if _text(packet.get("mode")) != "fixture_first_offline_review":
        errors.append("mode must be fixture_first_offline_review")
    if _text(packet.get("network_access")) != "not_requested":
        errors.append("network_access must be not_requested")
    if _text(packet.get("devhub_scope")) != "not_touched":
        errors.append("devhub_scope must be not_touched")

    for field in _REQUIRED_TOP_LEVEL_LISTS:
        if not _non_empty_list(packet.get(field)):
            errors.append(f"{field} must be a non-empty list")

    _validate_reference_lists(errors, packet)
    _validate_reviewer_dispositions(errors, packet.get("reviewer_ready_dispositions"))
    _validate_owner_signoffs(errors, packet.get("owner_signoff_placeholders"))
    _validate_dependency_sequence(errors, packet.get("dependency_sequence"))
    _validate_release_blocker_notes(errors, packet.get("release_blocker_notes"))
    _validate_rollback_checkpoints(errors, packet.get("rollback_checkpoints"))
    _validate_validation_commands(errors, packet.get("validation_commands"))
    _validate_safety_attestations(errors, packet.get("safety_attestations"))
    _validate_recursive_safety(errors, packet)
    return PublicRefreshReviewerBundlePacketV1ValidationResult(not errors, tuple(errors))


def require_public_refresh_reviewer_bundle_packet_v1(packet: Mapping[str, Any]) -> None:
    result = validate_public_refresh_reviewer_bundle_packet_v1(packet)
    if not result.valid:
        raise ValueError("invalid public refresh reviewer bundle packet v1: " + "; ".join(result.errors))


def _validate_reference_lists(errors: list[str], packet: Mapping[str, Any]) -> None:
    for list_name, required_fields in _REQUIRED_REF_FIELDS.items():
        for index, item in enumerate(_mapping_sequence(packet.get(list_name))):
            prefix = f"{list_name}[{index}]"
            for field in required_fields:
                if not _text(item.get(field)):
                    errors.append(f"{prefix}.{field} must be present")
            if not _text(item.get("review_status")):
                errors.append(f"{prefix}.review_status must be present")
            if item.get("required_before_release") is not True:
                errors.append(f"{prefix}.required_before_release must be true")


def _validate_reviewer_dispositions(errors: list[str], value: Any) -> None:
    dispositions = _mapping_sequence(value)
    present_types: set[str] = set()
    for index, item in enumerate(dispositions):
        prefix = f"reviewer_ready_dispositions[{index}]"
        disposition_type = _text(item.get("disposition_type")).lower()
        if disposition_type:
            present_types.add(disposition_type)
        if disposition_type not in _REQUIRED_DISPOSITION_TYPES:
            errors.append(f"{prefix}.disposition_type must be one of: {', '.join(sorted(_REQUIRED_DISPOSITION_TYPES))}")
        if _text(item.get("status")) != "reviewer_ready":
            errors.append(f"{prefix}.status must be reviewer_ready")
        for field in ("subject_id", "reviewer_role", "evidence_ref"):
            if not _text(item.get(field)):
                errors.append(f"{prefix}.{field} must be present")
        if item.get("required_before_release") is not True:
            errors.append(f"{prefix}.required_before_release must be true")
    missing = sorted(_REQUIRED_DISPOSITION_TYPES.difference(present_types))
    if missing:
        errors.append("reviewer_ready_dispositions missing disposition types: " + ", ".join(missing))


def _validate_owner_signoffs(errors: list[str], value: Any) -> None:
    for index, item in enumerate(_mapping_sequence(value)):
        prefix = f"owner_signoff_placeholders[{index}]"
        for field in ("placeholder_id", "owner_role", "signoff_scope", "status"):
            if not _text(item.get(field)):
                errors.append(f"{prefix}.{field} must be present")
        if _text(item.get("status")) != "pending_owner_signoff":
            errors.append(f"{prefix}.status must be pending_owner_signoff")
        if item.get("required_before_release") is not True:
            errors.append(f"{prefix}.required_before_release must be true")


def _validate_dependency_sequence(errors: list[str], value: Any) -> None:
    expected_order = 1
    seen_ids: set[str] = set()
    for index, item in enumerate(_mapping_sequence(value)):
        prefix = f"dependency_sequence[{index}]"
        dependency_id = _text(item.get("dependency_id"))
        if not dependency_id:
            errors.append(f"{prefix}.dependency_id must be present")
        if item.get("order") != expected_order:
            errors.append(f"{prefix}.order must be {expected_order}")
        expected_order += 1
        depends_on = _string_sequence(item.get("depends_on"))
        missing_dependencies = [dependency for dependency in depends_on if dependency not in seen_ids]
        if missing_dependencies:
            errors.append(f"{prefix}.depends_on references later or missing dependencies: {', '.join(missing_dependencies)}")
        if dependency_id:
            seen_ids.add(dependency_id)
        if not _text(item.get("completion_state")):
            errors.append(f"{prefix}.completion_state must be present")


def _validate_release_blocker_notes(errors: list[str], value: Any) -> None:
    for index, item in enumerate(_mapping_sequence(value)):
        prefix = f"release_blocker_notes[{index}]"
        for field in ("blocker_id", "severity", "note", "resolution_owner"):
            if not _text(item.get(field)):
                errors.append(f"{prefix}.{field} must be present")
        if item.get("blocks_release") is not True:
            errors.append(f"{prefix}.blocks_release must be true")


def _validate_rollback_checkpoints(errors: list[str], value: Any) -> None:
    for index, item in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_checkpoints[{index}]"
        for field in ("checkpoint_id", "trigger", "rollback_action", "owner_role"):
            if not _text(item.get(field)):
                errors.append(f"{prefix}.{field} must be present")
        if item.get("required_before_release") is not True:
            errors.append(f"{prefix}.required_before_release must be true")


def _validate_validation_commands(errors: list[str], value: Any) -> None:
    commands = _command_sequence(value)
    if not commands:
        errors.append("validation_commands must contain exact offline validation commands")
        return
    if commands != ALLOWED_VALIDATION_COMMANDS:
        errors.append("validation_commands must match the allowed offline validation command list")


def _validate_safety_attestations(errors: list[str], value: Any) -> None:
    if not isinstance(value, Mapping):
        errors.append("safety_attestations must be present")
        return
    required_true = (
        "metadata_only",
        "no_private_raw_or_downloaded_artifacts",
        "no_live_extraction_or_crawl_claims",
        "no_devhub_claims",
        "no_release_activation_claims",
        "no_active_artifact_mutation_claims",
        "no_official_action_completion_claims",
        "no_legal_or_permitting_guarantees",
        "no_active_mutation_flags",
    )
    for key in required_true:
        if value.get(key) is not True:
            errors.append(f"safety_attestations.{key} must be true")


def _validate_recursive_safety(errors: list[str], packet: Mapping[str, Any]) -> None:
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1]
        normalized_key = key.lower().replace("-", "_")
        if _FORBIDDEN_KEY_RE.search(normalized_key) and _truthy_or_text(value):
            errors.append(f"{path} must not include private, raw, downloaded, browser, session, or DevHub artifacts")
        if _is_active_mutation_flag(normalized_key, value):
            errors.append(f"{path} must not set active mutation flags")
        if isinstance(value, str):
            stripped = value.strip()
            if _FORBIDDEN_VALUE_RE.search(stripped):
                errors.append(f"{path} must not reference private, raw, downloaded, browser, or session artifacts")
            if _LIVE_EXTRACTION_OR_CRAWL_RE.search(stripped):
                errors.append(f"{path} must not claim live extraction or crawl execution")
            if path not in _ALLOWED_DEVHUB_PATHS and _DEVHUB_RE.search(stripped):
                errors.append(f"{path} must not claim DevHub scope or activity")
            if _RELEASE_ACTIVATION_RE.search(stripped):
                errors.append(f"{path} must not claim release activation")
            if _ARTIFACT_MUTATION_RE.search(stripped):
                errors.append(f"{path} must not claim active artifact mutation")
            if _OFFICIAL_ACTION_RE.search(stripped):
                errors.append(f"{path} must not claim official-action completion")
            if _LEGAL_OR_PERMITTING_GUARANTEE_RE.search(stripped):
                errors.append(f"{path} must not guarantee legal or permitting outcomes")


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_sequence(value: Any) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _command_sequence(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    commands: list[list[str]] = []
    for command in value:
        if not isinstance(command, list) or not command:
            return []
        parts: list[str] = []
        for part in command:
            if not isinstance(part, str) or not part:
                return []
            parts.append(part)
        commands.append(parts)
    return commands


def _walk(value: Any, path: str = "packet") -> list[tuple[str, Any]]:
    rows = [(path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            rows.extend(_walk(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]"))
    return rows


def _is_active_mutation_flag(normalized_key: str, value: Any) -> bool:
    if normalized_key.startswith("no_active_") or normalized_key.startswith("no_"):
        return False
    has_domain = any(domain.replace("-", "_") in normalized_key for domain in _MUTATION_DOMAINS)
    has_term = any(term in normalized_key for term in _MUTATION_TERMS)
    if not has_domain or not has_term:
        return False
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() in _ACTIVE_VALUES:
        return True
    return False


def _truthy_or_text(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
