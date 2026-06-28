"""Validation for guarded draft preview handoff packet v6.

The validator is fixture-first and side-effect free. It rejects handoff packets
that omit required provenance, attended preflight references, reversible local
preview rows, selector caveats, stop gates, local PDF boundaries, exact
confirmation reminders, manual handoff notes, validation commands, or no-effect
attestations. It also scans packet text and flags for live DevHub access claims,
private/session/auth artifacts, official-action completion claims, legal or
permitting guarantees, and active mutation flags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PACKET_VERSION = "guarded-draft-preview-handoff-packet-v6"

EXACT_VALIDATION_COMMANDS: list[list[str]] = [
    [
        "python3",
        "-m",
        "py_compile",
        "ppd/agent_readiness/guarded_draft_preview_handoff_packet_v6.py",
        "ppd/tests/test_guarded_draft_preview_handoff_packet_v6.py",
    ],
    ["python3", "-m", "unittest", "ppd.tests.test_guarded_draft_preview_handoff_packet_v6"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_REFERENCE_SECTIONS = (
    "agent_api_compatibility_refs",
    "attended_preflight_refs",
)
_REQUIRED_LIST_SECTIONS = _REQUIRED_REFERENCE_SECTIONS + (
    "reversible_draft_preview_rows",
    "user_fact_provenance_requirements",
    "selector_confidence_caveats",
    "stop_gates",
    "local_pdf_preview_boundaries",
    "exact_confirmation_checkpoint_reminders",
    "manual_handoff_notes",
    "validation_commands",
)
_REQUIRED_STOP_GATE_TOPICS = {"upload", "submission", "payment", "certification"}
_REQUIRED_NO_EFFECT_FALSE_FLAGS = (
    "live_devhub_access",
    "private_session_auth_artifacts",
    "official_action_completion_claims",
    "legal_or_permitting_guarantees",
    "active_mutation_flags",
    "opens_devhub",
    "uses_authenticated_session",
    "stores_auth_state",
    "stores_cookies",
    "creates_traces",
    "creates_screenshots",
    "creates_har_files",
    "uploads",
    "submits",
    "pays",
    "certifies",
    "schedules",
    "cancels",
    "mutates_release_state",
    "mutates_guardrails",
    "mutates_prompts",
    "writes_pdf",
)
_PRIVATE_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "file://",
    "auth_state",
    "browser_state",
    "session_state",
    "cookie",
    "trace.zip",
    ".har",
    "csrf",
    "bearer ",
    "password",
    "PRIVATE_FACT:",
    "AUTHENTICATED_VALUE:",
    "RAW_PDF_BYTES:",
)
_ACTIVE_MUTATION_KEY_TERMS = (
    "active_mutation",
    "mutation_enabled",
    "mutates_",
    "write_enabled",
    "writes_pdf",
    "updates_guardrail",
    "updates_prompt",
    "release_state_mutation",
)

_LIVE_DEVHUB_PATTERNS = (
    re.compile(r"\b(?:opened|accessed|logged\s+into|used)\s+devhub\b", re.IGNORECASE),
    re.compile(r"\blive\s+devhub\s+(?:access|session|run|crawl)\b", re.IGNORECASE),
    re.compile(r"\bauthenticated\s+devhub\s+(?:session|page|value|artifact)\b", re.IGNORECASE),
)
_OFFICIAL_COMPLETION_PATTERNS = (
    re.compile(r"\b(?:i|we|the\s+agent)\s+(?:submitted|uploaded|paid|certified|scheduled|cancelled|canceled)\b", re.IGNORECASE),
    re.compile(r"\b(?:application|permit|payment|upload|certification|inspection|cancellation)\s+(?:submitted|uploaded|paid|certified|scheduled|completed|cancelled|canceled)\b", re.IGNORECASE),
    re.compile(r"\b(?:final|official)\s+(?:submission|upload|payment|certification|scheduling|cancellation)\s+(?:completed|performed|executed)\b", re.IGNORECASE),
)
_GUARANTEE_PATTERNS = (
    re.compile(r"\bpermit\s+(?:will|shall|is\s+guaranteed\s+to)\s+(?:be\s+)?(?:approved|issued|accepted)\b", re.IGNORECASE),
    re.compile(r"\bapproval\s+(?:is\s+)?guaranteed\b", re.IGNORECASE),
    re.compile(r"\bguarantee(?:d|s)?\s+(?:permit|approval|issuance|code\s+compliance|legal\s+sufficiency)\b", re.IGNORECASE),
    re.compile(r"\blegally\s+(?:sufficient|compliant|approved|guaranteed)\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:code\s+)?(?:violation|enforcement\s+risk|permitting\s+risk)\b", re.IGNORECASE),
)
_FINAL_ACTION_LANGUAGE_PATTERNS = (
    re.compile(r"\b(?:click|press|select)\s+(?:submit|upload|pay|certify|schedule|cancel)\b", re.IGNORECASE),
    re.compile(r"\b(?:submit|upload|pay|certify|schedule|cancel)\s+(?:now|in\s+devhub|the\s+official|the\s+final)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class GuardedDraftPreviewHandoffIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


class GuardedDraftPreviewHandoffPacketV6Error(ValueError):
    def __init__(self, issues: Sequence[GuardedDraftPreviewHandoffIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("invalid guarded draft preview handoff packet v6: " + "; ".join(issue.message for issue in issues))


def validate_guarded_draft_preview_handoff_packet_v6(packet: Mapping[str, Any]) -> list[GuardedDraftPreviewHandoffIssue]:
    issues: list[GuardedDraftPreviewHandoffIssue] = []
    if not isinstance(packet, Mapping):
        return [GuardedDraftPreviewHandoffIssue("invalid_packet", "$", "packet must be an object")]

    if packet.get("packet_version") != PACKET_VERSION:
        issues.append(GuardedDraftPreviewHandoffIssue("invalid_packet_version", "packet_version", f"packet_version must be {PACKET_VERSION}"))
    if packet.get("fixture_first") is not True:
        issues.append(GuardedDraftPreviewHandoffIssue("not_fixture_first", "fixture_first", "packet must be fixture_first"))

    for section in _REQUIRED_LIST_SECTIONS:
        if not _non_empty_sequence(packet.get(section)):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_section", section, f"{section} must be a non-empty list"))

    _validate_reference_rows(packet.get("agent_api_compatibility_refs"), "agent_api_compatibility_refs", "agent_api_compatibility", issues)
    _validate_reference_rows(packet.get("attended_preflight_refs"), "attended_preflight_refs", "attended_preflight", issues)
    _validate_reversible_rows(packet.get("reversible_draft_preview_rows"), issues)
    _validate_user_fact_provenance(packet.get("user_fact_provenance_requirements"), issues)
    _validate_selector_caveats(packet.get("selector_confidence_caveats"), issues)
    _validate_stop_gates(packet.get("stop_gates"), issues)
    _validate_local_pdf_boundaries(packet.get("local_pdf_preview_boundaries"), issues)
    _validate_textual_rows(packet.get("exact_confirmation_checkpoint_reminders"), "exact_confirmation_checkpoint_reminders", issues)
    _validate_textual_rows(packet.get("manual_handoff_notes"), "manual_handoff_notes", issues)
    _validate_no_effect_policy(packet.get("no_effect_policy"), issues)
    _validate_validation_commands(packet.get("validation_commands"), issues)
    _scan_for_forbidden_values(packet, issues)
    return _dedupe(issues)


def assert_valid_guarded_draft_preview_handoff_packet_v6(packet: Mapping[str, Any]) -> None:
    issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
    if issues:
        raise GuardedDraftPreviewHandoffPacketV6Error(issues)


def validate_packet(packet: Mapping[str, Any]) -> list[GuardedDraftPreviewHandoffIssue]:
    return validate_guarded_draft_preview_handoff_packet_v6(packet)


def _validate_reference_rows(value: Any, section: str, expected_kind: str, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"{section}[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_reference", path, "reference row must be an object"))
            continue
        if not _text(row.get("ref_id")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_reference_id", f"{path}.ref_id", "reference row must include ref_id"))
        if _text(row.get("reference_kind")) not in {expected_kind, section.removesuffix("_refs")}:
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_reference_kind", f"{path}.reference_kind", f"reference_kind must identify {expected_kind}"))
        if not _non_empty_sequence(row.get("source_evidence_ids")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_reference_evidence", f"{path}.source_evidence_ids", "reference row must cite source_evidence_ids"))


def _validate_reversible_rows(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"reversible_draft_preview_rows[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_preview_row", path, "preview row must be an object"))
            continue
        if not _text(row.get("row_id")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_preview_row_id", f"{path}.row_id", "preview row must include row_id"))
        for flag in ("reversible", "local_only", "requires_user_review"):
            if row.get(flag) is not True:
                issues.append(GuardedDraftPreviewHandoffIssue("unsafe_preview_row", f"{path}.{flag}", f"preview row must set {flag}=true"))
        for flag in ("official_action", "devhub_mutation", "pdf_write", "upload_ready"):
            if row.get(flag) is not False:
                issues.append(GuardedDraftPreviewHandoffIssue("unsafe_preview_row", f"{path}.{flag}", f"preview row must set {flag}=false"))
        if not _non_empty_sequence(row.get("source_evidence_ids")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_preview_evidence", f"{path}.source_evidence_ids", "preview row must cite source_evidence_ids"))
        if not _non_empty_sequence(row.get("user_fact_provenance_requirements")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_user_fact_provenance", f"{path}.user_fact_provenance_requirements", "preview row must include user-fact provenance requirements"))
        if not _non_empty_sequence(row.get("selector_confidence_caveats")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_selector_caveats", f"{path}.selector_confidence_caveats", "preview row must include selector-confidence caveats"))
        if not _non_empty_sequence(row.get("local_pdf_preview_boundaries")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_local_pdf_boundaries", f"{path}.local_pdf_preview_boundaries", "preview row must include local PDF preview boundaries"))


def _validate_user_fact_provenance(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"user_fact_provenance_requirements[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_user_fact_provenance", path, "user-fact provenance requirement must be an object"))
            continue
        if not _text(row.get("fact_id")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_fact_id", f"{path}.fact_id", "user-fact provenance requirement must include fact_id"))
        if row.get("requires_user_supplied_provenance") is not True:
            issues.append(GuardedDraftPreviewHandoffIssue("missing_user_fact_provenance", f"{path}.requires_user_supplied_provenance", "user-fact provenance must require user-supplied provenance"))
        if row.get("allow_inference_without_source") is not False:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_user_fact_inference", f"{path}.allow_inference_without_source", "user facts must not be inferred without source"))


def _validate_selector_caveats(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"selector_confidence_caveats[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_selector_caveat", path, "selector caveat must be an object"))
            continue
        if not _text(row.get("caveat_id")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_selector_caveat_id", f"{path}.caveat_id", "selector caveat must include caveat_id"))
        if row.get("blocks_unattended_execution") is not True:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_selector_caveat", f"{path}.blocks_unattended_execution", "selector caveat must block unattended execution"))
        if row.get("allows_live_selector_claim") is True:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_selector_caveat", f"{path}.allows_live_selector_claim", "selector caveat must not allow live selector claims"))


def _validate_stop_gates(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    topics: set[str] = set()
    for index, row in enumerate(value):
        path = f"stop_gates[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_stop_gate", path, "stop gate must be an object"))
            continue
        topic = _text(row.get("topic")) or _text(row.get("action"))
        if topic:
            topics.add(topic)
        if row.get("automated") is not False:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_stop_gate", f"{path}.automated", "stop gate must set automated=false"))
        if row.get("requires_attended_user") is not True:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_stop_gate", f"{path}.requires_attended_user", "stop gate must require attended user"))
        if row.get("requires_exact_confirmation") is not True:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_stop_gate", f"{path}.requires_exact_confirmation", "stop gate must require exact confirmation"))
        disposition = _text(row.get("disposition"))
        if disposition not in {"stop_and_manual_handoff", "refuse_and_manual_handoff", "blocked_until_exact_confirmation"}:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_stop_gate", f"{path}.disposition", "stop gate disposition must block and hand off"))
    missing = _REQUIRED_STOP_GATE_TOPICS - topics
    if missing:
        issues.append(GuardedDraftPreviewHandoffIssue("missing_stop_gate_topics", "stop_gates", "stop gates must cover upload, submission, payment, and certification"))


def _validate_local_pdf_boundaries(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"local_pdf_preview_boundaries[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_local_pdf_boundary", path, "local PDF boundary must be an object"))
            continue
        if row.get("local_preview_only") is not True:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_local_pdf_boundary", f"{path}.local_preview_only", "local PDF boundary must be preview-only"))
        if row.get("writes_pdf") is not False:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_local_pdf_boundary", f"{path}.writes_pdf", "local PDF boundary must not write PDFs"))
        if row.get("uses_private_file_path") is not False:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_local_pdf_boundary", f"{path}.uses_private_file_path", "local PDF boundary must not include private file paths"))


def _validate_textual_rows(value: Any, section: str, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"{section}[{index}]"
        if not isinstance(row, Mapping):
            issues.append(GuardedDraftPreviewHandoffIssue("invalid_textual_row", path, f"{section} row must be an object"))
            continue
        if not (_text(row.get("body")) or _text(row.get("note")) or _text(row.get("reminder"))):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_textual_body", path, f"{section} row must include body, note, or reminder"))
        if not _non_empty_sequence(row.get("source_evidence_ids")):
            issues.append(GuardedDraftPreviewHandoffIssue("missing_textual_evidence", f"{path}.source_evidence_ids", f"{section} row must cite source_evidence_ids"))


def _validate_no_effect_policy(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if not isinstance(value, Mapping):
        issues.append(GuardedDraftPreviewHandoffIssue("missing_no_effect_policy", "no_effect_policy", "no_effect_policy must be an object"))
        return
    for flag in _REQUIRED_NO_EFFECT_FALSE_FLAGS:
        if value.get(flag) is not False:
            issues.append(GuardedDraftPreviewHandoffIssue("unsafe_no_effect_policy", f"no_effect_policy.{flag}", f"no_effect_policy.{flag} must be false"))


def _validate_validation_commands(value: Any, issues: list[GuardedDraftPreviewHandoffIssue]) -> None:
    if value != EXACT_VALIDATION_COMMANDS:
        issues.append(GuardedDraftPreviewHandoffIssue("invalid_validation_commands", "validation_commands", "validation_commands must exactly match guarded draft preview handoff packet v6 commands"))


def _scan_for_forbidden_values(value: Any, issues: list[GuardedDraftPreviewHandoffIssue], path: str = "$", parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized_key = str(key).lower().replace("-", "_")
            if child is True and _is_forbidden_true_flag(normalized_key):
                issues.append(GuardedDraftPreviewHandoffIssue("forbidden_active_flag", child_path, "packet must not enable live access, private artifacts, official completion, guarantees, or mutation"))
            _scan_for_forbidden_values(child, issues, child_path, normalized_key)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_values(child, issues, f"{path}[{index}]", parent_key)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in _PRIVATE_MARKERS):
            issues.append(GuardedDraftPreviewHandoffIssue("private_artifact_reference", path, "packet must not reference private/session/auth artifacts, raw values, private paths, or downloaded documents"))
        for code, patterns, message in (
            ("live_devhub_access_claim", _LIVE_DEVHUB_PATTERNS, "packet must not claim live DevHub access"),
            ("official_action_completion_claim", _OFFICIAL_COMPLETION_PATTERNS, "packet must not claim official action completion"),
            ("legal_or_permitting_guarantee", _GUARANTEE_PATTERNS, "packet must not make legal or permitting guarantees"),
            ("final_action_language", _FINAL_ACTION_LANGUAGE_PATTERNS, "packet must not include final official-action instructions"),
        ):
            if any(pattern.search(value) for pattern in patterns):
                issues.append(GuardedDraftPreviewHandoffIssue(code, path, message))


def _is_forbidden_true_flag(normalized_key: str) -> bool:
    explicit = {
        "live_devhub_access",
        "private_session_auth_artifacts",
        "official_action_completion_claims",
        "legal_or_permitting_guarantees",
        "active_mutation_flags",
        "devhub_opened",
        "auth_state_stored",
        "submitted",
        "uploaded",
        "paid",
        "certified",
        "scheduled",
        "canceled",
        "cancelled",
    }
    return normalized_key in explicit or any(term in normalized_key for term in _ACTIVE_MUTATION_KEY_TERMS)


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _dedupe(issues: Sequence[GuardedDraftPreviewHandoffIssue]) -> list[GuardedDraftPreviewHandoffIssue]:
    seen: set[tuple[str, str, str]] = set()
    result: list[GuardedDraftPreviewHandoffIssue] = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result
