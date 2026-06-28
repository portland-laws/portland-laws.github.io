"""Fixture-first DevHub read-only observation redaction review packets."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_readiness_decision_packet import (
    assert_valid_read_only_readiness_decision_packet,
)


REQUIRED_PACKET_TYPE = "ppd.devhub.read_only_observation_redaction_review.v1"
REQUIRED_MODE = "fixture_first_devhub_read_only_observation_redaction_review"
REQUIRED_READINESS_PACKET_TYPE = "ppd.devhub.read_only_readiness_decision_packet.v1"
REQUIRED_OPERATOR_CHECKLIST_PACKET_TYPE = "devhub_read_only_pilot_operator_checklist"

FORBIDDEN_PACKET_KEYS = frozenset(
    {
        "auth_state",
        "browser_state",
        "cookies",
        "credentials",
        "downloaded_document",
        "har",
        "har_file",
        "har_files",
        "har_path",
        "local_private_file_path",
        "local_private_file_paths",
        "payment_details",
        "private_value",
        "private_values",
        "raw_authenticated_page_value",
        "raw_authenticated_page_values",
        "raw_authenticated_text",
        "raw_crawl_output",
        "raw_dom",
        "screenshot",
        "screenshots",
        "session_state",
        "storage_state",
        "trace",
        "trace_path",
        "traces",
        "upload_payload",
    }
)

REQUIRED_REVIEW_SECTIONS = (
    "synthetic_observation_fields",
    "allowed_metadata",
    "redaction_rules",
    "abort_prompts",
    "reviewer_owners",
    "private_artifact_prohibitions",
)

REQUIRED_PROHIBITION_TERMS = (
    ("private/session artifacts", ("session", "private")),
    ("screenshots", ("screenshot",)),
    ("traces", ("trace",)),
    ("HAR paths or data", ("har",)),
    ("stored auth state", ("auth state", "auth_state", "storage state", "storage_state")),
    ("local private paths", ("local private", "private file path")),
    ("raw authenticated page values", ("raw authenticated", "private devhub values", "private_field_values")),
)

CONSEQUENTIAL_TERMS = (
    "submit",
    "certify",
    "acknowledge",
    "upload",
    "attach",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "extension",
    "reactivate",
    "account_security_change",
)

TRUE_ENABLEMENT_KEYS = frozenset(
    {
        "enabled",
        "allowed",
        "allow",
        "allowed_in_read_only_pilot",
        "continue_allowed",
        "executes_consequential_action",
        "official_action_completed",
        "performed",
        "completed",
    }
)

AUTOMATION_BOOLEAN_KEY_RE = re.compile(
    r"(captcha|mfa|multi[_ -]?factor|account[_ -]?creation|create[_ -]?account|register[_ -]?account).*(automation|automated|allowed|executed|completed|handled|solved|bypassed)|"
    r"(automation|automated|allowed|executed|completed|handled|solved|bypassed).*(captcha|mfa|multi[_ -]?factor|account[_ -]?creation|create[_ -]?account|register[_ -]?account)",
    re.IGNORECASE,
)
AUTOMATION_CLAIM_RE = re.compile(
    r"\b(automated|completed|handled|solved|bypassed|executed)\b.{0,80}\b(captcha|mfa|multi-factor|multifactor|account creation|create account|register account)\b|"
    r"\b(captcha|mfa|multi-factor|multifactor|account creation|create account|register account)\b.{0,80}\b(automated|completed by automation|handled by automation|solved|bypassed|executed)\b",
    re.IGNORECASE,
)
LIVE_BROWSER_CLAIM_RE = re.compile(
    r"\b(live browser|browser execution|playwright)\b.{0,80}\b(launched|executed|clicked|filled|ran|captured|stored)\b|"
    r"\b(launched|executed|clicked|filled|ran|captured|stored)\b.{0,80}\b(live browser|browser execution|playwright|devhub)\b",
    re.IGNORECASE,
)
LOCAL_PRIVATE_PATH_RE = re.compile(r"(?:^|\s)(?:/home/[^\s]+|/Users/[^\s]+|C:\\\\Users\\[^\s]+|~/(?:\.config|\.cache|Downloads|Desktop|Documents)/[^\s]+)")
PRIVATE_ARTIFACT_VALUE_RE = re.compile(
    r"(trace\.zip|\.har\b|storage[_ -]?state\.json|auth[_ -]?state\.json|cookies\.json|session\.json|devhub-session|playwright/\.auth|screenshot\.(?:png|jpe?g|webp))",
    re.IGNORECASE,
)
PROHIBITIVE_TERMS = (
    "abort",
    "block",
    "disabled",
    "discard",
    "do not",
    "forbid",
    "must not",
    "no ",
    "not ",
    "prohibit",
    "redact",
    "refuse",
    "reject",
    "stop",
    "without",
)


class ReadOnlyObservationRedactionReviewError(ValueError):
    """Raised when a redaction review packet is not commit-safe."""


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ReadOnlyObservationRedactionReviewError("packet fixture must be a JSON object")
    return packet


def build_read_only_observation_redaction_review_packet(
    readiness_decision_packet: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a synthetic observation redaction review from committed fixtures."""

    assert_valid_read_only_readiness_decision_packet(readiness_decision_packet)
    _assert_operator_checklist(operator_checklist)

    readiness_citations = _source_citations(readiness_decision_packet)
    checklist_citations = _checklist_source_ids(operator_checklist)
    citations = _dedupe(readiness_citations + checklist_citations)

    packet = {
        "packet_id": "devhub-read-only-observation-redaction-review-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "offline_only": True,
        "synthetic_only": True,
        "launches_browser": False,
        "launches_devhub": False,
        "launches_playwright": False,
        "network_requests_made": False,
        "stores_browser_artifacts": False,
        "stores_private_artifacts": False,
        "stores_downloads": False,
        "source_packets": {
            "readiness_decision_packet": {
                "packet_id": _text(readiness_decision_packet.get("packet_id")),
                "packet_type": _text(readiness_decision_packet.get("packet_type")),
                "consumed": True,
                "citations": readiness_citations,
            },
            "read_only_pilot_operator_checklist": {
                "packet_id": _text(operator_checklist.get("packet_id")),
                "packet_type": _text(operator_checklist.get("packet_type")),
                "consumed": True,
                "citations": checklist_citations,
            },
        },
        "synthetic_observation_fields": _synthetic_observation_fields(operator_checklist, citations),
        "allowed_metadata": _allowed_metadata(citations),
        "redaction_rules": _redaction_rules(operator_checklist, citations),
        "abort_prompts": _abort_prompts(readiness_decision_packet, operator_checklist, citations),
        "reviewer_owners": _reviewer_owners(readiness_decision_packet, citations),
        "private_artifact_prohibitions": _private_artifact_prohibitions(readiness_decision_packet, operator_checklist, citations),
    }
    assert_valid_read_only_observation_redaction_review_packet(packet)
    return packet


def assert_valid_read_only_observation_redaction_review_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_read_only_observation_redaction_review_packet(packet)
    if errors:
        raise ReadOnlyObservationRedactionReviewError("; ".join(errors))


def validate_read_only_observation_redaction_review_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, isinstance(packet, Mapping), "packet must be a JSON object")
    if not isinstance(packet, Mapping):
        return tuple(errors)

    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    for field in ("fixture_first", "offline_only", "synthetic_only"):
        _require(errors, packet.get(field) is True, f"{field} must be true")
    for field in (
        "launches_browser",
        "launches_devhub",
        "launches_playwright",
        "network_requests_made",
        "stores_browser_artifacts",
        "stores_private_artifacts",
        "stores_downloads",
    ):
        _require(errors, packet.get(field) is False, f"{field} must be false")

    _validate_forbidden_content(errors, packet)
    _validate_sources(errors, _mapping(packet.get("source_packets")))
    for section in REQUIRED_REVIEW_SECTIONS:
        _require(errors, bool(_sequence(packet.get(section))), f"{section} must be non-empty")
        _validate_cited_rows(errors, packet.get(section), section)

    for index, row in enumerate(_sequence(packet.get("synthetic_observation_fields"))):
        item = _mapping(row)
        prefix = f"synthetic_observation_fields[{index}]"
        _require(errors, item.get("raw_value_allowed") is False, f"{prefix}.raw_value_allowed must be false")
        _require(errors, item.get("commit_safe") is True, f"{prefix}.commit_safe must be true")
        _require(errors, bool(_text(item.get("field_name"))), f"{prefix}.field_name is required")

    for index, row in enumerate(_sequence(packet.get("allowed_metadata"))):
        item = _mapping(row)
        prefix = f"allowed_metadata[{index}]"
        _require(errors, item.get("private_value_allowed") is False, f"{prefix}.private_value_allowed must be false")
        _require(errors, item.get("browser_artifact_allowed") is False, f"{prefix}.browser_artifact_allowed must be false")

    for index, row in enumerate(_sequence(packet.get("redaction_rules"))):
        item = _mapping(row)
        prefix = f"redaction_rules[{index}]"
        _require(errors, item.get("required") is True, f"{prefix}.required must be true")
        _require(errors, item.get("raw_storage_allowed") is False, f"{prefix}.raw_storage_allowed must be false")

    for index, row in enumerate(_sequence(packet.get("abort_prompts"))):
        item = _mapping(row)
        prefix = f"abort_prompts[{index}]"
        _require(errors, item.get("must_abort") is True, f"{prefix}.must_abort must be true")
        _require(errors, item.get("continue_allowed") is False, f"{prefix}.continue_allowed must be false")

    for index, row in enumerate(_sequence(packet.get("reviewer_owners"))):
        item = _mapping(row)
        prefix = f"reviewer_owners[{index}]"
        _require(errors, item.get("requires_reviewer") is True, f"{prefix}.requires_reviewer must be true")
        _require(errors, bool(_text(item.get("owner_id"))), f"{prefix}.owner_id is required")

    for index, row in enumerate(_sequence(packet.get("private_artifact_prohibitions"))):
        item = _mapping(row)
        prefix = f"private_artifact_prohibitions[{index}]"
        _require(errors, item.get("allowed") is False, f"{prefix}.allowed must be false")
        _require(errors, item.get("commit_safe") is True, f"{prefix}.commit_safe must be true")

    _validate_required_prohibition_coverage(errors, packet)
    return tuple(_dedupe(errors))


def _assert_operator_checklist(packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_OPERATOR_CHECKLIST_PACKET_TYPE, "operator checklist packet_type is invalid")
    for field in ("manual_session_only", "read_only_only"):
        _require(errors, packet.get(field) is True, f"operator checklist {field} must be true")
    for field in ("launches_playwright", "live_session_authorized", "stores_private_session_state", "stores_browser_artifacts"):
        _require(errors, packet.get(field) is False, f"operator checklist {field} must be false")
    _require(errors, bool(_sequence(packet.get("checklist_steps"))), "operator checklist must include checklist_steps")
    _require(errors, bool(_sequence(packet.get("abort_conditions"))), "operator checklist must include abort_conditions")
    if errors:
        raise ReadOnlyObservationRedactionReviewError("; ".join(errors))


def _synthetic_observation_fields(operator_checklist: Mapping[str, Any], citations: list[str]) -> list[dict[str, Any]]:
    fields = _sequence(_mapping(operator_checklist.get("redaction_policy")).get("allowed_observation_fields"))
    return [
        {
            "field_name": _text(field),
            "source": "operator_checklist.redaction_policy.allowed_observation_fields",
            "synthetic_value_only": True,
            "raw_value_allowed": False,
            "commit_safe": True,
            "citations": citations[:3],
        }
        for field in fields
        if _text(field)
    ]


def _allowed_metadata(citations: list[str]) -> list[dict[str, Any]]:
    metadata = (
        ("stable_surface_id", "Stable synthetic surface identifier"),
        ("page_heading", "Generic heading text after private identifiers are removed"),
        ("accessible_landmark_summary", "Role or landmark category summary"),
        ("redacted_label_category", "Label category with private values removed"),
        ("synthetic_record_status_label", "Generic status label"),
        ("operator_decision_code", "Commit-safe operator decision code"),
        ("redacted_timestamp", "Coarse redacted review timestamp when needed"),
    )
    return [
        {
            "metadata_id": metadata_id,
            "description": description,
            "private_value_allowed": False,
            "browser_artifact_allowed": False,
            "citations": citations[:3],
        }
        for metadata_id, description in metadata
    ]


def _redaction_rules(operator_checklist: Mapping[str, Any], citations: list[str]) -> list[dict[str, Any]]:
    policy = _mapping(operator_checklist.get("redaction_policy"))
    rules: list[dict[str, Any]] = []
    for index, artifact in enumerate(_sequence(policy.get("forbidden_artifacts")), start=1):
        if _text(artifact):
            rules.append(
                {
                    "rule_id": f"redact-forbidden-artifact-{index:02d}",
                    "target": _text(artifact),
                    "required": True,
                    "raw_storage_allowed": False,
                    "replacement": "[REDACTED_PRIVATE]",
                    "citations": citations[:3],
                }
            )
    return rules


def _abort_prompts(
    readiness_decision_packet: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    citations: list[str],
) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    for row in _sequence(readiness_decision_packet.get("abort_conditions")):
        condition = _mapping(row)
        text = _text(condition.get("condition"))
        if text:
            prompts.append(
                {
                    "prompt_id": _text(condition.get("abort_id")) or f"readiness-abort-{len(prompts) + 1:02d}",
                    "prompt": text,
                    "operator_response": _text(condition.get("operator_result")) or "Stop and record only commit-safe metadata.",
                    "must_abort": True,
                    "continue_allowed": False,
                    "citations": _text_list(condition.get("citations")) or citations[:3],
                }
            )
    for row in _sequence(operator_checklist.get("abort_conditions")):
        condition = _mapping(row)
        text = _text(condition.get("trigger"))
        if text:
            prompts.append(
                {
                    "prompt_id": _text(condition.get("condition_id")) or f"operator-abort-{len(prompts) + 1:02d}",
                    "prompt": text,
                    "operator_response": _text(condition.get("operator_action")) or "Stop and record only commit-safe metadata.",
                    "must_abort": True,
                    "continue_allowed": False,
                    "citations": citations[:3],
                }
            )
    return prompts


def _reviewer_owners(readiness_decision_packet: Mapping[str, Any], citations: list[str]) -> list[dict[str, Any]]:
    owners: list[dict[str, Any]] = []
    for row in _sequence(readiness_decision_packet.get("reviewer_owners")):
        owner = _mapping(row)
        owner_id = _text(owner.get("owner_id"))
        if owner_id:
            owners.append(
                {
                    "owner_id": owner_id,
                    "reviewer_role": _text(owner.get("reviewer_role")),
                    "owns": _text(owner.get("owns")),
                    "requires_reviewer": True,
                    "citations": _text_list(owner.get("citations")) or citations[:3],
                }
            )
    return owners


def _private_artifact_prohibitions(
    readiness_decision_packet: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    citations: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sequence(readiness_decision_packet.get("private_artifact_prohibitions")):
        prohibition = _mapping(row)
        text = _text(prohibition.get("prohibition"))
        if text:
            rows.append(
                {
                    "prohibition_id": _text(prohibition.get("prohibition_id")) or f"readiness-prohibition-{len(rows) + 1:02d}",
                    "prohibition": text,
                    "allowed": False,
                    "commit_safe": True,
                    "citations": _text_list(prohibition.get("citations")) or citations[:3],
                }
            )
    for index, artifact in enumerate(_sequence(_mapping(operator_checklist.get("redaction_policy")).get("forbidden_artifacts")), start=1):
        if _text(artifact):
            rows.append(
                {
                    "prohibition_id": f"operator-forbidden-artifact-{index:02d}",
                    "prohibition": f"Do not store or commit {artifact}.",
                    "allowed": False,
                    "commit_safe": True,
                    "citations": citations[:3],
                }
            )
    return rows


def _validate_sources(errors: list[str], source_packets: Mapping[str, Any]) -> None:
    readiness = _mapping(source_packets.get("readiness_decision_packet"))
    checklist = _mapping(source_packets.get("read_only_pilot_operator_checklist"))
    _require(errors, readiness.get("packet_type") == REQUIRED_READINESS_PACKET_TYPE, "source readiness packet_type is invalid")
    _require(errors, readiness.get("consumed") is True, "source readiness packet must be consumed")
    _require(errors, checklist.get("packet_type") == REQUIRED_OPERATOR_CHECKLIST_PACKET_TYPE, "source checklist packet_type is invalid")
    _require(errors, checklist.get("consumed") is True, "source checklist packet must be consumed")
    _require(errors, bool(_text_list(readiness.get("citations"))), "source readiness citations must be non-empty")
    _require(errors, bool(_text_list(checklist.get("citations"))), "source checklist citations must be non-empty")


def _validate_cited_rows(errors: list[str], value: Any, path: str) -> None:
    for index, raw_row in enumerate(_sequence(value)):
        row = _mapping(raw_row)
        _require(errors, bool(_text_list(row.get("citations"))), f"{path}[{index}].citations must be non-empty")


def _validate_forbidden_content(errors: list[str], value: Any, path: str = "$", key_hint: str = "") -> None:
    if isinstance(value, Mapping):
        label = _text(value.get("label") or value.get("control_id") or value.get("action") or value.get("name"))
        if _looks_consequential(label):
            for key, child in value.items():
                if _text(key).casefold() in TRUE_ENABLEMENT_KEYS and child is True:
                    errors.append(f"enabled consequential control at {path}.{key}")
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.casefold().replace("-", "_").replace(" ", "_")
            child_path = f"{path}.{key_text}"
            if normalized_key in FORBIDDEN_PACKET_KEYS and _is_present(child):
                errors.append(f"forbidden private artifact key at {child_path}")
            if child is True and AUTOMATION_BOOLEAN_KEY_RE.search(normalized_key):
                errors.append(f"forbidden CAPTCHA/MFA/account automation claim at {child_path}")
            _validate_forbidden_content(errors, child, child_path, normalized_key)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_forbidden_content(errors, child, f"{path}[{index}]", key_hint)
        return
    if isinstance(value, str):
        lowered = value.casefold()
        if _is_prohibitive_context(lowered):
            return
        if PRIVATE_ARTIFACT_VALUE_RE.search(value) or LOCAL_PRIVATE_PATH_RE.search(value):
            errors.append(f"forbidden private artifact value at {path}")
        if AUTOMATION_CLAIM_RE.search(value):
            errors.append(f"forbidden CAPTCHA/MFA/account automation claim at {path}")
        if LIVE_BROWSER_CLAIM_RE.search(value):
            errors.append(f"forbidden live browser execution claim at {path}")


def _validate_required_prohibition_coverage(errors: list[str], packet: Mapping[str, Any]) -> None:
    text_parts: list[str] = []
    for section in ("redaction_rules", "private_artifact_prohibitions", "abort_prompts"):
        text_parts.extend(_collect_text(packet.get(section)))
    joined = "\n".join(text_parts).casefold().replace("_", " ")
    for label, terms in REQUIRED_PROHIBITION_TERMS:
        if not any(term.casefold().replace("_", " ") in joined for term in terms):
            errors.append(f"private artifact prohibitions must cover {label}")


def _collect_text(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        output: list[str] = []
        for child in value.values():
            output.extend(_collect_text(child))
        return output
    if isinstance(value, list):
        output = []
        for child in value:
            output.extend(_collect_text(child))
        return output
    if isinstance(value, str):
        return [value]
    return []


def _looks_consequential(value: str) -> bool:
    lowered = value.casefold().replace("-", "_")
    return any(term in lowered for term in CONSEQUENTIAL_TERMS)


def _is_prohibitive_context(value: str) -> bool:
    return any(term in value for term in PROHIBITIVE_TERMS)


def _is_present(value: Any) -> bool:
    return value not in (None, "", [], {}, False)


def _source_citations(packet: Mapping[str, Any]) -> list[str]:
    citations = [_text(packet.get("packet_id"))]
    for source in _mapping(packet.get("source_packets")).values():
        citations.extend(_text_list(_mapping(source).get("citations")))
    return _dedupe(citations)


def _checklist_source_ids(packet: Mapping[str, Any]) -> list[str]:
    citations = [_text(packet.get("packet_id"))]
    citations.extend(_text(step.get("step_id")) for step in _sequence(packet.get("checklist_steps")) if isinstance(step, Mapping))
    return _dedupe([citation for citation in citations if citation])


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _text_list(value: Any) -> list[str]:
    return [_text(item) for item in _sequence(value) if _text(item)]


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            output.append(value)
    return output
