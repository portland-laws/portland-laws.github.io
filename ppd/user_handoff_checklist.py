"""Fixture-first user handoff checklist packets for PP&D safe-next-action work.

The builder consumes already-sanitized release notes, release gate status, and
DevHub surface registry update candidate packets. It does not call an LLM,
launch DevHub, access the network, or read private files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.surface_registry_update_candidate import assert_valid_surface_registry_update_candidate_packet
from ppd.logic.safe_next_action_release_notes import assert_valid_release_notes_packet
from ppd.release_gate_status import assert_valid_release_gate_status_packet


REQUIRED_PACKET_TYPE = "ppd.safe_next_action.user_handoff_checklist.v1"
REQUIRED_SOURCE_PACKET_KEYS = (
    "agent_safe_next_action_release_notes",
    "release_gate_status",
    "devhub_surface_registry_update_candidate",
)
FORBIDDEN_KEYS = frozenset(
    {
        "archive_artifact_ref",
        "archive_artifact_refs",
        "archive_path",
        "archive_url",
        "auth_state",
        "browser_state",
        "captcha_solution",
        "cookies",
        "credential",
        "credentials",
        "download_path",
        "download_url",
        "downloaded_archive",
        "downloaded_document",
        "downloaded_documents",
        "downloaded_file",
        "downloaded_files",
        "har",
        "mfa_secret",
        "password",
        "payment_details",
        "private_file",
        "private_files",
        "raw_archive_ref",
        "raw_archive_refs",
        "raw_authenticated_text",
        "raw_crawl_output",
        "raw_crawl_reference",
        "raw_crawl_references",
        "raw_download_ref",
        "raw_download_refs",
        "raw_html",
        "screenshot",
        "screenshots",
        "session_cookie",
        "storage_state",
        "token",
        "trace",
        "traces",
        "upload_payload",
        "warc_path",
    }
)
PRIVATE_PATH_PATTERN = re.compile(
    r"(?:/home/|/Users/|C:\\\\Users\\|private[-_ ]?files?|\.har\b|trace\.zip|storage[-_ ]?state|session[-_ ]?cookie)",
    re.IGNORECASE,
)
RAW_ARTIFACT_PATTERN = re.compile(
    r"(?:\.warc(?:\.gz)?\b|raw[-_ ]?(?:crawl|download|archive)|downloaded[-_ ]?(?:document|file|archive)|archive[-_ ]?artifact)",
    re.IGNORECASE,
)
OUTCOME_GUARANTEE_PATTERN = re.compile(
    r"(?:guarantee[sd]?\s+(?:approval|issuance|permit|legal|code)|(?:permit|application|inspection|review)\s+will\s+(?:be\s+)?(?:pass|approve|succeed)|(?:approval|issuance)\s+is\s+guaranteed|legally\s+(?:valid|sufficient)|code[- ]compliant\s+without\s+review)",
    re.IGNORECASE,
)
LIVE_EXECUTION_PATTERN = re.compile(
    r"(?:launched\s+(?:devhub|playwright)|executed\s+(?:devhub|live)|completed\s+(?:a\s+)?live\s+(?:crawl|network|devhub)|network\s+requests?\s+(?:were\s+)?made|authenticated\s+devhub\s+session\s+(?:was\s+)?started)",
    re.IGNORECASE,
)
CONSEQUENTIAL_CAPABILITY_PATTERN = re.compile(
    r"(?:pay|payment|fee_payment|upload|submission|submit|schedule|scheduling|inspection_scheduling|cancel|cancellation|withdraw|certif|acknowledg)",
    re.IGNORECASE,
)
PRODUCTION_READY_PATTERN = re.compile(r"(?:production[-_ ]?ready|ready\s+for\s+production|release[-_ ]?ready)", re.IGNORECASE)
LIVE_BOOLEAN_FIELDS = frozenset(
    {
        "devhub_execution_completed",
        "devhub_launch_allowed",
        "devhub_launched",
        "launches_devhub",
        "launches_playwright",
        "live_capabilities_enabled",
        "live_network_executed",
        "network_allowed",
        "network_requests_made",
        "official_action_allowed",
        "playwright_launched",
    }
)


def load_json_packet(path: str | Path) -> dict[str, Any]:
    """Load a JSON object fixture from a caller-provided public fixture path."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("handoff checklist source fixture must be a JSON object")
    return data


def build_user_handoff_checklist_packet(
    release_notes: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
    devhub_surface_registry_update_candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic offline-only user handoff checklist packet."""

    assert_valid_release_notes_packet(release_notes)
    assert_valid_release_gate_status_packet(release_gate_status)
    assert_valid_surface_registry_update_candidate_packet(devhub_surface_registry_update_candidate)

    release_citations = _text_list(release_notes.get("citations"))
    packet = {
        "packet_id": "safe-next-action-user-handoff-checklist-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": "fixture_first_offline_only_user_handoff",
        "fixture_first": True,
        "offline_only": True,
        "llm_invoked": False,
        "launches_devhub": False,
        "launches_playwright": False,
        "reads_private_files": False,
        "network_requests_made": False,
        "prerequisite_packet_links": _prerequisite_links(release_gate_status),
        "source_packets": {
            "agent_safe_next_action_release_notes": {
                "packet_type": _text(release_notes.get("packet_type")),
                "packet_id": _text(release_notes.get("packet_id")) or _text(release_notes.get("packet_type")),
                "consumed": True,
                "citations": release_citations,
            },
            "release_gate_status": {
                "packet_type": _text(release_gate_status.get("packet_type")),
                "packet_id": _text(release_gate_status.get("packet_id")),
                "consumed": True,
                "citations": _gate_evidence_ids(release_gate_status),
            },
            "devhub_surface_registry_update_candidate": {
                "packet_type": _text(devhub_surface_registry_update_candidate.get("packet_type")),
                "packet_id": _text(devhub_surface_registry_update_candidate.get("packet_id")),
                "consumed": True,
                "citations": _surface_citations(devhub_surface_registry_update_candidate),
            },
        },
        "cited_offline_user_prompts": _user_prompts(release_notes, release_citations),
        "allowed_reversible_local_previews": _local_previews(release_gate_status),
        "blocked_consequential_actions": _blocked_actions(
            release_notes,
            release_gate_status,
            devhub_surface_registry_update_candidate,
        ),
        "reviewer_prompts": _reviewer_prompts(release_gate_status, devhub_surface_registry_update_candidate),
        "rollback_references": _rollback_references(release_notes, release_citations),
    }
    assert_valid_user_handoff_checklist_packet(packet)
    return packet


def assert_valid_user_handoff_checklist_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_user_handoff_checklist_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def validate_user_handoff_checklist_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if packet.get("packet_type") != REQUIRED_PACKET_TYPE:
        errors.append(f"packet_type must be {REQUIRED_PACKET_TYPE}")
    for field in ("fixture_first", "offline_only"):
        if packet.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in ("llm_invoked", "launches_devhub", "launches_playwright", "reads_private_files", "network_requests_made"):
        if packet.get(field) is not False:
            errors.append(f"{field} must be false")

    _validate_prerequisite_links(errors, packet.get("prerequisite_packet_links"))
    _validate_forbidden_content(errors, packet)
    _validate_no_outcome_guarantees(errors, packet)
    _validate_no_live_execution_claims(errors, packet)
    _validate_no_enabled_consequential_capabilities(errors, packet)
    _validate_no_premature_production_label(errors, packet)

    source_packets = _mapping(packet.get("source_packets"))
    for key in REQUIRED_SOURCE_PACKET_KEYS:
        source = _mapping(source_packets.get(key))
        if source.get("consumed") is not True:
            errors.append(f"source_packets.{key}.consumed must be true")
        if not _text(source.get("packet_id")):
            errors.append(f"source_packets.{key}.packet_id is required")
        if not _text_list(source.get("citations")):
            errors.append(f"source_packets.{key}.citations must be non-empty")

    _validate_cited_rows(errors, packet.get("cited_offline_user_prompts"), "cited_offline_user_prompts", "offline_only", True)
    _validate_cited_rows(errors, packet.get("reviewer_prompts"), "reviewer_prompts", "requires_reviewer", True)
    _validate_cited_rows(errors, packet.get("rollback_references"), "rollback_references", "local_rollback_only", True)

    previews = _sequence(packet.get("allowed_reversible_local_previews"))
    if not previews:
        errors.append("allowed_reversible_local_previews must be non-empty")
    for index, raw_preview in enumerate(previews):
        preview = _mapping(raw_preview)
        prefix = f"allowed_reversible_local_previews[{index}]"
        for field in ("local_only", "reversible"):
            if preview.get(field) is not True:
                errors.append(f"{prefix}.{field} must be true")
        for field in ("network_allowed", "devhub_launch_allowed", "official_action_allowed"):
            if preview.get(field) is not False:
                errors.append(f"{prefix}.{field} must be false")
        if not _text_list(preview.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")

    blocked = _sequence(packet.get("blocked_consequential_actions"))
    if not blocked:
        errors.append("blocked_consequential_actions must be non-empty")
    for index, raw_action in enumerate(blocked):
        action = _mapping(raw_action)
        prefix = f"blocked_consequential_actions[{index}]"
        if action.get("enabled") is not False:
            errors.append(f"{prefix}.enabled must be false")
        if action.get("blocked") is not True:
            errors.append(f"{prefix}.blocked must be true")
        if not _text(action.get("action_id")):
            errors.append(f"{prefix}.action_id is required")
        if not _text_list(action.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")
    return tuple(dict.fromkeys(errors))


def _prerequisite_links(release_gate_status: Mapping[str, Any]) -> list[dict[str, Any]]:
    links = []
    for link in _sequence(release_gate_status.get("prerequisite_packet_links")):
        link_map = _mapping(link)
        links.append(
            {
                "area": _text(link_map.get("area")),
                "packet_id": _text(link_map.get("packet_id")),
                "path": _text(link_map.get("path")),
                "kind": _text(link_map.get("kind")),
                "citations": _text_list(link_map.get("evidence_ids")) or _text_list(link_map.get("citations")),
            }
        )
    return links


def _user_prompts(release_notes: Mapping[str, Any], release_citations: list[str]) -> list[dict[str, Any]]:
    prompts = _text_list(release_notes.get("user_facing_escalation_prompts"))
    return [
        {
            "prompt_id": f"user-prompt-{index:02d}",
            "audience": "user",
            "prompt": prompt,
            "offline_only": True,
            "requires_private_file": False,
            "requires_devhub_launch": False,
            "citations": release_citations,
        }
        for index, prompt in enumerate(prompts, start=1)
    ]


def _local_previews(release_gate_status: Mapping[str, Any]) -> list[dict[str, Any]]:
    previews = []
    for step in _sequence(release_gate_status.get("allowed_metadata_only_next_steps")):
        step_map = _mapping(step)
        previews.append(
            {
                "preview_id": _text(step_map.get("step_id")),
                "description": _text(step_map.get("description")),
                "local_only": True,
                "reversible": True,
                "network_allowed": False,
                "devhub_launch_allowed": False,
                "official_action_allowed": False,
                "citations": _text_list(step_map.get("evidence_ids")),
            }
        )
    return previews


def _blocked_actions(
    release_notes: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
    devhub_surface_registry_update_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    release_citations = _text_list(release_notes.get("citations"))
    for action in _text_list(release_notes.get("disabled_live_actions")):
        actions.append(_blocked_action(f"release-notes:{action}", "disabled live action from release notes", release_citations))
    for capability in _sequence(release_gate_status.get("disabled_live_capabilities")):
        capability_map = _mapping(capability)
        actions.append(
            _blocked_action(
                _text(capability_map.get("capability_id")),
                _text(capability_map.get("reason")),
                _text_list(capability_map.get("evidence_ids")),
            )
        )
    surface_packet_id = _text(devhub_surface_registry_update_candidate.get("packet_id"))
    for candidate in _sequence(devhub_surface_registry_update_candidate.get("registry_update_candidates")):
        candidate_map = _mapping(candidate)
        surface_id = _text(candidate_map.get("surface_id"))
        for control in _text_list(candidate_map.get("disabled_consequential_controls")):
            action_id = control.removeprefix("disabled:")
            actions.append(
                _blocked_action(
                    f"{surface_id}:{action_id}",
                    "DevHub surface candidate keeps this consequential control disabled.",
                    [surface_packet_id, surface_id],
                )
            )
    return actions


def _blocked_action(action_id: str, reason: str, citations: list[str]) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "reason": reason,
        "enabled": False,
        "blocked": True,
        "requires_attended_user_confirmation": True,
        "citations": citations,
    }


def _reviewer_prompts(
    release_gate_status: Mapping[str, Any],
    devhub_surface_registry_update_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    prompts = []
    for prompt in _sequence(release_gate_status.get("required_reviewer_prompts")):
        prompt_map = _mapping(prompt)
        prompts.append(
            {
                "prompt_id": _text(prompt_map.get("prompt_id")),
                "reviewer_role": _text(prompt_map.get("reviewer_role")),
                "question": _text(prompt_map.get("question")),
                "requires_reviewer": True,
                "citations": _text_list(prompt_map.get("evidence_ids")),
            }
        )
    surface_packet_id = _text(devhub_surface_registry_update_candidate.get("packet_id"))
    for candidate in _sequence(devhub_surface_registry_update_candidate.get("registry_update_candidates")):
        candidate_map = _mapping(candidate)
        surface_id = _text(candidate_map.get("surface_id"))
        for index, prompt in enumerate(_text_list(candidate_map.get("manual_handoff_prompts")), start=1):
            prompts.append(
                {
                    "prompt_id": f"surface-{surface_id}-manual-handoff-{index:02d}",
                    "reviewer_role": "DevHub surface reviewer",
                    "question": prompt,
                    "requires_reviewer": True,
                    "citations": [surface_packet_id, surface_id],
                }
            )
    return prompts


def _rollback_references(release_notes: Mapping[str, Any], release_citations: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "rollback_id": f"rollback-{index:02d}",
            "instruction": item,
            "local_rollback_only": True,
            "requires_devhub_launch": False,
            "citations": release_citations,
        }
        for index, item in enumerate(_text_list(release_notes.get("rollback_references")), start=1)
    ]


def _gate_evidence_ids(release_gate_status: Mapping[str, Any]) -> list[str]:
    evidence_ids: list[str] = []
    for key in ("open_blockers", "allowed_metadata_only_next_steps", "disabled_live_capabilities", "required_reviewer_prompts"):
        for row in _sequence(release_gate_status.get(key)):
            evidence_ids.extend(_text_list(_mapping(row).get("evidence_ids")))
    return sorted(set(evidence_ids))


def _surface_citations(packet: Mapping[str, Any]) -> list[str]:
    citations = [_text(packet.get("packet_id"))]
    for candidate in _sequence(packet.get("registry_update_candidates")):
        surface_id = _text(_mapping(candidate).get("surface_id"))
        if surface_id:
            citations.append(surface_id)
    return sorted(set(item for item in citations if item))


def _validate_prerequisite_links(errors: list[str], value: Any) -> None:
    links = _sequence(value)
    if not links:
        errors.append("prerequisite_packet_links must be non-empty")
        return
    for index, raw_link in enumerate(links):
        link = _mapping(raw_link)
        prefix = f"prerequisite_packet_links[{index}]"
        if not _text(link.get("packet_id")):
            errors.append(f"{prefix}.packet_id is required")
        path = _text(link.get("path"))
        if not path:
            errors.append(f"{prefix}.path is required")
        elif not path.startswith("ppd/tests/fixtures/"):
            errors.append(f"{prefix}.path must point at a committed ppd/tests/fixtures fixture")
        if not _text(link.get("kind")):
            errors.append(f"{prefix}.kind is required")
        if not _text_list(link.get("citations")):
            errors.append(f"{prefix}.citations must be non-empty")


def _validate_cited_rows(errors: list[str], value: Any, name: str, boolean_field: str, required_value: bool) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append(f"{name} must be non-empty")
    for index, row in enumerate(rows):
        row_map = _mapping(row)
        if row_map.get(boolean_field) is not required_value:
            errors.append(f"{name}[{index}].{boolean_field} must be {str(required_value).lower()}")
        if not _text_list(row_map.get("citations")):
            errors.append(f"{name}[{index}].citations must be non-empty")


def _validate_forbidden_content(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_KEYS:
                errors.append(f"{child_path} is not allowed in user handoff checklist packets")
            _validate_forbidden_content(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_forbidden_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str):
        if PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{path} must not reference private files or browser artifacts")
        if RAW_ARTIFACT_PATTERN.search(value):
            errors.append(f"{path} must not reference raw crawl, download, or archive artifacts")


def _validate_no_outcome_guarantees(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _validate_no_outcome_guarantees(errors, child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_outcome_guarantees(errors, child, f"{path}[{index}]")
    elif isinstance(value, str) and OUTCOME_GUARANTEE_PATTERN.search(value):
        errors.append(f"{path} must not guarantee legal, permitting, inspection, approval, or issuance outcomes")


def _validate_no_live_execution_claims(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in LIVE_BOOLEAN_FIELDS and child is True:
                errors.append(f"{child_path} must not claim live network, DevHub, Playwright, or official action execution")
            _validate_no_live_execution_claims(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_live_execution_claims(errors, child, f"{path}[{index}]")
    elif isinstance(value, str) and LIVE_EXECUTION_PATTERN.search(value):
        errors.append(f"{path} must not claim live network, DevHub, or Playwright execution")


def _validate_no_enabled_consequential_capabilities(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        action_text = " ".join(
            _text(value.get(key)) for key in ("action_id", "capability_id", "control_id", "name", "id") if _text(value.get(key))
        )
        if action_text and CONSEQUENTIAL_CAPABILITY_PATTERN.search(action_text):
            if value.get("enabled") is True:
                errors.append(f"{path}.enabled must be false for payment, upload, submission, scheduling, cancellation, and certification capabilities")
            if value.get("blocked") is False:
                errors.append(f"{path}.blocked must not be false for consequential capabilities")
            status = _text(value.get("status")).lower()
            if status in {"enabled", "active", "allowed", "ready"}:
                errors.append(f"{path}.status must not enable consequential capabilities")
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if child is True and CONSEQUENTIAL_CAPABILITY_PATTERN.search(key_text) and re.search(r"(?:enabled|allowed|ready|completed)$", key_text, re.IGNORECASE):
                errors.append(f"{child_path} must not enable payment, upload, submission, scheduling, cancellation, or certification")
            _validate_no_enabled_consequential_capabilities(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_enabled_consequential_capabilities(errors, child, f"{path}[{index}]")


def _validate_no_premature_production_label(errors: list[str], packet: Mapping[str, Any]) -> None:
    if not _has_open_blocker(packet):
        return
    if _has_production_ready_label(packet):
        errors.append("production-ready labels are not allowed while handoff blockers remain open")


def _has_open_blocker(value: Any) -> bool:
    if isinstance(value, Mapping):
        status = _text(value.get("status")).lower()
        if status == "open" and any("block" in str(key).lower() for key in value.keys()):
            return True
        for key, child in value.items():
            if "blocker" in str(key).lower() and bool(child):
                return True
            if _has_open_blocker(child):
                return True
    elif isinstance(value, list):
        return any(_has_open_blocker(child) for child in value)
    return False


def _has_production_ready_label(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in {"production_ready", "production_readiness", "release_ready"} and child is True:
                return True
            if PRODUCTION_READY_PATTERN.search(key_text) and child is True:
                return True
            if _has_production_ready_label(child):
                return True
    elif isinstance(value, list):
        return any(_has_production_ready_label(child) for child in value)
    elif isinstance(value, str):
        return bool(PRODUCTION_READY_PATTERN.search(value))
    return False


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []
