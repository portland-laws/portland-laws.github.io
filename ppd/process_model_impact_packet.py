"""Fixture-first PP&D process-model impact packet builder.

This module maps reviewed requirement changes into one synthetic permit process
model impact packet. It is deliberately metadata-only: it does not crawl public
pages, use authenticated DevHub state, upload documents, submit applications,
pay fees, schedule inspections, or cancel permits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REVIEWED_STATUSES = frozenset({"reviewed", "approved", "accepted", "human_reviewed"})
FORBIDDEN_OFFICIAL_ACTIONS = frozenset(
    {
        "submission",
        "payment",
        "upload",
        "scheduling",
        "cancellation",
    }
)
STALE_SOURCE_STATUSES = frozenset({"expired", "needs_refresh", "stale", "unknown", "unknown_stale"})
READY_FOR_PRODUCTION_STATUSES = frozenset(
    {"production_ready", "ready_for_production", "approved_for_production"}
)
PRIVATE_OR_RAW_KEYS = frozenset(
    {
        "auth_state",
        "captcha",
        "case_fact_value",
        "case_fact_values",
        "case_facts",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "downloaded_document",
        "entered_value",
        "har",
        "known_case_facts",
        "local_private_file_path",
        "mfa",
        "password",
        "payment_details",
        "private_case_fact",
        "private_case_facts",
        "private_devhub_session",
        "property_address",
        "raw_authenticated_page_values",
        "raw_case_fact",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "screenshot",
        "session_file",
        "session_state",
        "token",
        "trace",
        "upload_file_path",
        "user_case_facts",
    }
)
CONSEQUENTIAL_ENABLEMENT_KEYS = frozenset(
    {
        "consequential_action_enabled",
        "consequential_actions_enabled",
        "official_action_enabled",
        "official_actions_enabled",
        "submission_enabled",
        "payment_enabled",
        "upload_enabled",
        "scheduling_enabled",
        "cancellation_enabled",
    }
)

STANDARD_STAGE_ORDER = (
    "pre-application research",
    "account setup or manual login",
    "property lookup",
    "permit type selection",
    "eligibility screening",
    "document preparation",
    "application data entry",
    "upload staging",
    "acknowledgement/certification review",
    "submission",
    "prescreen/intake",
    "fee payment",
    "plan review",
    "corrections/checksheets",
    "approval/issuance",
    "inspections",
    "closeout, cancellation, expiration, extension, or reactivation",
)
_STAGE_INDEX = {stage: index for index, stage in enumerate(STANDARD_STAGE_ORDER)}


class ProcessModelImpactPacketError(ValueError):
    """Raised when a process-model impact fixture is incomplete or unsafe."""


def load_process_model_impact_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed JSON fixture for process-model impact assembly."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ProcessModelImpactPacketError("process-model impact fixture must be a JSON object")
    return payload


def build_process_model_impact_packet_from_fixture(path: str | Path) -> dict[str, Any]:
    """Load and build a fixture-first process-model impact packet."""

    return build_process_model_impact_packet(load_process_model_impact_fixture(path))


def build_process_model_impact_packet(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Map reviewed requirement changes into one synthetic process model packet."""

    _reject_private_or_raw_fields(payload)
    _reject_consequential_enablement(payload)

    packet_id = _required_text(payload, "packet_id")
    process_id = _required_text(payload, "process_id")
    permit_type = _required_text(payload, "permit_type")
    scope = _required_text(payload, "scope")
    guardrail_bundle_id = _required_text(payload, "guardrail_bundle_id")
    source_evidence = _committed_source_evidence(payload.get("source_evidence"))
    source_evidence_ids = set(source_evidence)

    changes = payload.get("reviewed_requirement_changes")
    if not isinstance(changes, list) or not changes:
        raise ProcessModelImpactPacketError("reviewed_requirement_changes must be a non-empty list")

    reviewed_changes = [_normalize_change(change, source_evidence_ids) for change in changes if _is_reviewed(change)]
    if not reviewed_changes:
        raise ProcessModelImpactPacketError("at least one reviewed requirement change is required")
    reviewed_changes.sort(key=lambda change: change["change_id"])

    model_evidence_ids = _sorted_unique(
        evidence_id for change in reviewed_changes for evidence_id in change["source_evidence_ids"]
    )
    blockers = _guardrail_bundle_blockers(reviewed_changes, guardrail_bundle_id)

    process_model = {
        "process_id": process_id,
        "permit_type": permit_type,
        "scope": scope,
        "affected_stages": _affected_stages(reviewed_changes),
        "stage_mappings": _stage_mappings(reviewed_changes),
        "required_user_facts": _required_user_facts(reviewed_changes),
        "required_documents": _required_documents(reviewed_changes),
        "unsupported_paths": _unsupported_paths(reviewed_changes),
        "devhub_surface_refs": _devhub_surface_refs(reviewed_changes),
        "guardrail_bundle_id": guardrail_bundle_id,
        "guardrail_bundle_blockers": blockers,
        "requirement_change_ids": [change["change_id"] for change in reviewed_changes],
        "source_evidence_ids": model_evidence_ids,
    }

    packet = {
        "packet_type": "fixture_first_process_model_impact_packet",
        "packet_id": packet_id,
        "fixture_first": True,
        "metadata_only": True,
        "live_services_called": False,
        "official_actions_enabled": False,
        "enabled_official_actions": [],
        "disabled_official_actions": sorted(FORBIDDEN_OFFICIAL_ACTIONS),
        "readiness_status": "blocked_until_human_review_and_exact_confirmation",
        "production_status": "not_ready_for_production",
        "unresolved_blockers": sorted(FORBIDDEN_OFFICIAL_ACTIONS),
        "source_references": _source_references(source_evidence, model_evidence_ids),
        "process_model": process_model,
        "reviewed_requirement_changes": reviewed_changes,
        "guardrail_bundle_linkage": {
            "guardrail_bundle_id": guardrail_bundle_id,
            "process_id": process_id,
            "blocked_actions": sorted({blocker["blocked_action"] for blocker in blockers}),
            "linkage_status": "fixture_blocked_until_human_review_and_exact_confirmation",
            "source_evidence_ids": model_evidence_ids,
        },
    }
    validate_process_model_impact_packet(packet)
    return packet


def validate_process_model_impact_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a built packet is incomplete or could enable official action."""

    _reject_private_or_raw_fields(packet)
    _reject_consequential_enablement(packet)
    if packet.get("fixture_first") is not True:
        raise ProcessModelImpactPacketError("packet must be fixture_first")
    if packet.get("metadata_only") is not True:
        raise ProcessModelImpactPacketError("packet must be metadata_only")
    if packet.get("live_services_called") is not False:
        raise ProcessModelImpactPacketError("packet must not call live services")
    if packet.get("official_actions_enabled") is not False:
        raise ProcessModelImpactPacketError("official actions must remain disabled")
    if packet.get("enabled_official_actions") != []:
        raise ProcessModelImpactPacketError("enabled_official_actions must be empty")

    unresolved_blockers = _text_list(packet.get("unresolved_blockers"))
    production_status = _text(packet.get("production_status") or packet.get("readiness_status")).lower()
    if unresolved_blockers and production_status in READY_FOR_PRODUCTION_STATUSES:
        raise ProcessModelImpactPacketError("ready-for-production status is forbidden while unresolved blockers remain")

    source_reference_ids = _validate_source_references(packet.get("source_references"))

    model = packet.get("process_model")
    if not isinstance(model, Mapping):
        raise ProcessModelImpactPacketError("process_model is required")

    required_model_lists = (
        "affected_stages",
        "stage_mappings",
        "required_user_facts",
        "required_documents",
        "unsupported_paths",
        "devhub_surface_refs",
        "guardrail_bundle_blockers",
        "requirement_change_ids",
        "source_evidence_ids",
    )
    for key in required_model_lists:
        value = model.get(key)
        if not isinstance(value, list) or not value:
            raise ProcessModelImpactPacketError(f"process_model.{key} must be a non-empty list")

    _validate_stage_mappings(model, packet.get("reviewed_requirement_changes"))
    _validate_requirement_links_are_cited(model, source_reference_ids)
    _validate_requirement_links_are_cited(packet.get("reviewed_requirement_changes"), source_reference_ids)
    _validate_requirement_links_are_cited(packet.get("guardrail_bundle_linkage"), source_reference_ids)

    disabled = set(_text_list(packet.get("disabled_official_actions")))
    blocked = {str(item.get("blocked_action", "")) for item in model["guardrail_bundle_blockers"]}
    missing_blockers = sorted(FORBIDDEN_OFFICIAL_ACTIONS.difference(disabled).union(FORBIDDEN_OFFICIAL_ACTIONS.difference(blocked)))
    if missing_blockers:
        raise ProcessModelImpactPacketError("missing guardrail blockers for: " + ", ".join(missing_blockers))

    linkage = packet.get("guardrail_bundle_linkage")
    if not isinstance(linkage, Mapping):
        raise ProcessModelImpactPacketError("guardrail_bundle_linkage is required")
    if linkage.get("guardrail_bundle_id") != model.get("guardrail_bundle_id"):
        raise ProcessModelImpactPacketError("guardrail bundle linkage must match process model")
    if linkage.get("blocked_actions") != sorted(FORBIDDEN_OFFICIAL_ACTIONS):
        raise ProcessModelImpactPacketError("guardrail linkage must block all forbidden official actions")


def _normalize_change(change: Any, committed_evidence_ids: set[str]) -> dict[str, Any]:
    if not isinstance(change, Mapping):
        raise ProcessModelImpactPacketError("reviewed requirement changes must be objects")

    change_id = _required_text(change, "change_id")
    conditions = change.get("conditions") or {}
    if not isinstance(conditions, Mapping):
        raise ProcessModelImpactPacketError(f"{change_id} conditions must be an object")

    evidence_ids = _text_list(change.get("source_evidence_ids"))
    if not evidence_ids:
        raise ProcessModelImpactPacketError(f"{change_id} must include source_evidence_ids")
    unknown = sorted(set(evidence_ids).difference(committed_evidence_ids))
    if unknown:
        raise ProcessModelImpactPacketError(f"{change_id} references uncommitted evidence ids: {', '.join(unknown)}")

    blocked_actions = _text_list(conditions.get("guardrail_blocked_actions"))
    unexpected_enabled = sorted(set(_text_list(conditions.get("enabled_official_actions"))).intersection(FORBIDDEN_OFFICIAL_ACTIONS))
    if unexpected_enabled:
        raise ProcessModelImpactPacketError(f"{change_id} attempts to enable official actions: {', '.join(unexpected_enabled)}")

    return {
        "change_id": change_id,
        "requirement_id": _required_text(change, "requirement_id"),
        "change_type": _required_text(change, "change_type"),
        "requirement_type": _required_text(change, "requirement_type"),
        "process_stage": _required_text(change, "process_stage"),
        "summary": _required_text(change, "summary"),
        "human_review_status": _required_text(change, "human_review_status"),
        "formalization_status": _text(change.get("formalization_status")) or "impact_candidate",
        "source_evidence_ids": _sorted_unique(evidence_ids),
        "conditions": _stable_jsonable(dict(conditions)),
        "guardrail_blocked_actions": sorted(set(blocked_actions).intersection(FORBIDDEN_OFFICIAL_ACTIONS)),
    }


def _is_reviewed(change: Any) -> bool:
    if not isinstance(change, Mapping):
        return False
    return _text(change.get("human_review_status") or change.get("status")).lower() in REVIEWED_STATUSES


def _committed_source_evidence(source_evidence: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(source_evidence, list) or not source_evidence:
        raise ProcessModelImpactPacketError("source_evidence must be a non-empty list")
    evidence_by_id: dict[str, Mapping[str, Any]] = {}
    for evidence in source_evidence:
        if not isinstance(evidence, Mapping):
            raise ProcessModelImpactPacketError("source_evidence entries must be objects")
        evidence_id = _required_text(evidence, "evidence_id")
        canonical_url = _required_text(evidence, "canonical_url")
        if not canonical_url.startswith(("https://www.portland.gov/", "https://devhub.portlandoregon.gov/")):
            raise ProcessModelImpactPacketError(f"{evidence_id} must cite an official PP&D or DevHub URL")
        status = _text(evidence.get("freshness_status") or "fixture_current").lower()
        if status in STALE_SOURCE_STATUSES:
            raise ProcessModelImpactPacketError(f"{evidence_id} references stale source evidence")
        evidence_by_id[evidence_id] = evidence
    return evidence_by_id


def _source_references(source_evidence: Mapping[str, Mapping[str, Any]], model_evidence_ids: list[str]) -> list[dict[str, Any]]:
    references = []
    for evidence_id in model_evidence_ids:
        evidence = source_evidence[evidence_id]
        references.append(
            {
                "evidence_id": evidence_id,
                "canonical_url": evidence.get("canonical_url"),
                "title": evidence.get("title"),
                "freshness_status": evidence.get("freshness_status", "fixture_current"),
                "source_evidence_ids": [evidence_id],
            }
        )
    return references


def _validate_source_references(source_references: Any) -> set[str]:
    if not isinstance(source_references, list) or not source_references:
        raise ProcessModelImpactPacketError("source_references must be a non-empty list")
    evidence_ids: set[str] = set()
    for reference in source_references:
        if not isinstance(reference, Mapping):
            raise ProcessModelImpactPacketError("source_references entries must be objects")
        evidence_id = _required_text(reference, "evidence_id")
        canonical_url = _required_text(reference, "canonical_url")
        if not canonical_url.startswith(("https://www.portland.gov/", "https://devhub.portlandoregon.gov/")):
            raise ProcessModelImpactPacketError(f"{evidence_id} must cite an official PP&D or DevHub URL")
        status = _text(reference.get("freshness_status") or "fixture_current").lower()
        if status in STALE_SOURCE_STATUSES:
            raise ProcessModelImpactPacketError(f"{evidence_id} references stale source evidence")
        evidence_ids.add(evidence_id)
    return evidence_ids


def _affected_stages(changes: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {change["process_stage"] for change in changes},
        key=lambda stage: (_STAGE_INDEX.get(stage, len(_STAGE_INDEX)), stage),
    )


def _stage_mappings(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "requirement_change_id": change["change_id"],
            "requirement_id": change["requirement_id"],
            "process_stage": change["process_stage"],
            "source_evidence_ids": change["source_evidence_ids"],
        }
        for change in sorted(changes, key=lambda item: (item["process_stage"], item["change_id"]))
    ]


def _required_user_facts(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts = []
    for change in changes:
        conditions = change["conditions"]
        fact_key = _text(conditions.get("required_user_fact"))
        if fact_key:
            facts.append(
                {
                    "fact_key": fact_key,
                    "label": _text(conditions.get("fact_label")) or fact_key.replace("_", " "),
                    "requirement_change_id": change["change_id"],
                    "process_stage": change["process_stage"],
                    "source_evidence_ids": change["source_evidence_ids"],
                }
            )
    return sorted(facts, key=lambda item: (item["fact_key"], item["requirement_change_id"]))


def _required_documents(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents = []
    for change in changes:
        conditions = change["conditions"]
        document_key = _text(conditions.get("required_document"))
        if document_key:
            documents.append(
                {
                    "document_key": document_key,
                    "label": _text(conditions.get("document_label")) or document_key.replace("_", " "),
                    "requirement_change_id": change["change_id"],
                    "process_stage": change["process_stage"],
                    "source_evidence_ids": change["source_evidence_ids"],
                }
            )
    return sorted(documents, key=lambda item: (item["document_key"], item["requirement_change_id"]))


def _unsupported_paths(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = []
    for change in changes:
        path = _text(change["conditions"].get("unsupported_path"))
        if path or change["requirement_type"] in {"prohibition", "exception"}:
            paths.append(
                {
                    "path": path or change["summary"],
                    "requirement_change_id": change["change_id"],
                    "process_stage": change["process_stage"],
                    "source_evidence_ids": change["source_evidence_ids"],
                }
            )
    return sorted(paths, key=lambda item: (item["path"], item["requirement_change_id"]))


def _devhub_surface_refs(changes: list[dict[str, Any]]) -> list[str]:
    refs = []
    for change in changes:
        refs.extend(_text_list(change["conditions"].get("devhub_surface_refs")))
    return _sorted_unique(refs)


def _guardrail_bundle_blockers(changes: list[dict[str, Any]], guardrail_bundle_id: str) -> list[dict[str, Any]]:
    by_action: dict[str, set[str]] = {action: set() for action in FORBIDDEN_OFFICIAL_ACTIONS}
    evidence_by_action: dict[str, set[str]] = {action: set() for action in FORBIDDEN_OFFICIAL_ACTIONS}
    for change in changes:
        for action in change["guardrail_blocked_actions"]:
            by_action.setdefault(action, set()).add(change["change_id"])
            evidence_by_action.setdefault(action, set()).update(change["source_evidence_ids"])

    blockers = []
    for action in sorted(FORBIDDEN_OFFICIAL_ACTIONS):
        blockers.append(
            {
                "guardrail_bundle_id": guardrail_bundle_id,
                "blocked_action": action,
                "predicate": "refuse_official_action_in_fixture_first_impact_packet",
                "reason": "Impact packet is for reviewed-change modeling only and cannot enable official DevHub actions.",
                "requires_attendance": True,
                "requires_exact_confirmation": True,
                "requirement_change_ids": sorted(by_action.get(action) or {"packet-wide-official-action-disablement"}),
                "source_evidence_ids": sorted(evidence_by_action.get(action) or _all_change_evidence(changes)),
            }
        )
    return blockers


def _all_change_evidence(changes: list[dict[str, Any]]) -> set[str]:
    return {evidence_id for change in changes for evidence_id in change["source_evidence_ids"]}


def _validate_stage_mappings(model: Mapping[str, Any], changes: Any) -> None:
    if not isinstance(changes, list) or not changes:
        raise ProcessModelImpactPacketError("reviewed_requirement_changes must be a non-empty list")
    mappings = model.get("stage_mappings")
    if not isinstance(mappings, list) or not mappings:
        raise ProcessModelImpactPacketError("process_model.stage_mappings must be a non-empty list")

    mapping_by_change_id = {
        item.get("requirement_change_id"): item for item in mappings if isinstance(item, Mapping)
    }
    affected_stages = set(_text_list(model.get("affected_stages")))
    for change in changes:
        if not isinstance(change, Mapping):
            raise ProcessModelImpactPacketError("reviewed requirement changes must be objects")
        change_id = _required_text(change, "change_id")
        process_stage = _required_text(change, "process_stage")
        mapping = mapping_by_change_id.get(change_id)
        if not isinstance(mapping, Mapping):
            raise ProcessModelImpactPacketError(f"missing stage mapping for requirement change: {change_id}")
        if mapping.get("process_stage") != process_stage:
            raise ProcessModelImpactPacketError(f"stage mapping mismatch for requirement change: {change_id}")
        if process_stage not in affected_stages:
            raise ProcessModelImpactPacketError(f"stage mapping references missing affected stage: {process_stage}")
        if not _text_list(mapping.get("source_evidence_ids")):
            raise ProcessModelImpactPacketError(f"stage mapping lacks source_evidence_ids: {change_id}")


def _validate_requirement_links_are_cited(value: Any, known_source_ids: set[str], path: str = "packet") -> None:
    if isinstance(value, Mapping):
        has_requirement_link = any(
            key in value
            for key in (
                "requirement_change_id",
                "requirement_change_ids",
                "requirement_id",
                "blocked_action",
                "fact_key",
                "document_key",
                "path",
                "process_stage",
            )
        )
        if has_requirement_link:
            evidence_ids = _text_list(value.get("source_evidence_ids"))
            if not evidence_ids:
                raise ProcessModelImpactPacketError(f"requirement link lacks source_evidence_ids at {path}")
            unknown = sorted(set(evidence_ids).difference(known_source_ids))
            if unknown:
                raise ProcessModelImpactPacketError(f"requirement link references unknown source evidence at {path}: {', '.join(unknown)}")
        for key, child in value.items():
            _validate_requirement_links_are_cited(child, known_source_ids, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_requirement_links_are_cited(child, known_source_ids, f"{path}[{index}]")


def _reject_private_or_raw_fields(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.lower() in PRIVATE_OR_RAW_KEYS:
                raise ProcessModelImpactPacketError(f"private or raw field is not allowed: {path}.{key_text}")
            _reject_private_or_raw_fields(nested, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_private_or_raw_fields(nested, f"{path}[{index}]")


def _reject_consequential_enablement(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            if normalized_key in CONSEQUENTIAL_ENABLEMENT_KEYS and nested is not False:
                raise ProcessModelImpactPacketError(f"consequential action enablement is not allowed: {path}.{key_text}")
            if normalized_key == "enabled_official_actions" and _text_list(nested):
                raise ProcessModelImpactPacketError(f"enabled official actions are not allowed: {path}.{key_text}")
            _reject_consequential_enablement(nested, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_consequential_enablement(nested, f"{path}[{index}]")


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = _text(payload.get(key))
    if not value:
        raise ProcessModelImpactPacketError(f"missing required field: {key}")
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.strip().split())


def _text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_text(value)] if _text(value) else []
    if not isinstance(value, list):
        raise ProcessModelImpactPacketError("list fields must be JSON arrays or strings")
    return [_text(item) for item in value if _text(item)]


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value})


def _stable_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stable_jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable_jsonable(item) for item in value]
    return value
