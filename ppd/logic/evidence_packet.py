"""Assemble sanitized PP&D evidence packets for agent use.

The assembler is intentionally whitelist-based. It accepts fixture-shaped records
for sources, archive manifests, documents, requirements, process models,
guardrails, and gap-analysis next-safe-actions, then emits only citation and id
metadata that an agent can use for grounded reasoning.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

FORBIDDEN_FIELD_NAMES = {
    "raw_body",
    "raw_html",
    "raw_text",
    "body",
    "html",
    "devhub_private_values",
    "private_values",
    "auth_state",
    "storage_state",
    "cookies",
    "cookie",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "password",
    "secret",
    "screenshot",
    "screenshots",
    "trace",
    "traces",
    "har",
    "local_path",
    "private_file_path",
    "download_path",
}

FORBIDDEN_TEXT_MARKERS = (
    "BEGIN PRIVATE DEVHUB VALUE",
    "devhub_private_value",
    "storageState",
    "Set-Cookie",
    "Authorization:",
    ".har",
    "trace.zip",
    "screenshot.png",
    "/home/",
    "/Users/",
    "C:\\Users\\",
)


def assemble_evidence_packet(records: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic, sanitized evidence packet.

    The output deliberately excludes document bodies and crawl/browser artifacts.
    Citations are represented by source/document/span ids and locator metadata,
    with short labels only.
    """

    sources = _index_by(records.get("sources", []), "source_id")
    manifests = _index_by(records.get("archive_manifests", []), "manifest_id")
    documents = _index_by(records.get("documents", []), "document_id")
    requirements = _index_by(records.get("requirements", []), "requirement_id")
    process_models = _index_by(records.get("process_models", []), "process_id")
    guardrails = _index_by(records.get("guardrail_bundles", []), "guardrail_bundle_id")

    citations_by_evidence_id = _citation_index(documents)

    packet = {
        "packet_id": str(records.get("packet_id", "ppd-fixture-evidence-pack")),
        "schema_version": "ppd.agent_evidence_packet.v1",
        "source_registry": [
            _public_source_summary(source) for source in sorted(sources.values(), key=lambda item: item["source_id"])
        ],
        "archive_manifests": [
            _archive_summary(manifest) for manifest in sorted(manifests.values(), key=lambda item: item["manifest_id"])
        ],
        "requirements": [
            _requirement_summary(requirement, citations_by_evidence_id)
            for requirement in sorted(requirements.values(), key=lambda item: item["requirement_id"])
        ],
        "process_models": [
            _process_summary(process) for process in sorted(process_models.values(), key=lambda item: item["process_id"])
        ],
        "guardrail_bundles": [
            _guardrail_summary(bundle) for bundle in sorted(guardrails.values(), key=lambda item: item["guardrail_bundle_id"])
        ],
        "next_safe_actions": [
            _next_safe_action_summary(action) for action in records.get("next_safe_actions", [])
        ],
        "omitted_materials": [
            "raw public or authenticated page bodies",
            "private DevHub values",
            "credentials, cookies, tokens, and auth state",
            "screenshots, traces, HAR files, and browser artifacts",
            "local private file paths and downloaded document paths",
        ],
    }
    assert_agent_packet_is_sanitized(packet)
    return packet


def assert_agent_packet_is_sanitized(packet: Mapping[str, Any]) -> None:
    """Raise ValueError if an assembled packet contains forbidden material."""

    problems: list[str] = []
    _scan_for_forbidden_material(packet, path="packet", problems=problems)
    if problems:
        raise ValueError("Evidence packet contains forbidden material: " + "; ".join(problems))


def _index_by(items: Iterable[Mapping[str, Any]], field_name: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        value = item.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing required id field {field_name!r}")
        indexed[value] = deepcopy(dict(item))
    return indexed


def _citation_index(documents: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    citations: dict[str, dict[str, Any]] = {}
    for document in documents.values():
        document_id = _required_str(document, "document_id")
        source_id = _required_str(document, "source_id")
        for span in document.get("citation_spans", []):
            evidence_id = _required_str(span, "evidence_id")
            citations[evidence_id] = {
                "evidence_id": evidence_id,
                "document_id": document_id,
                "source_id": source_id,
                "citation_span_id": _required_str(span, "citation_span_id"),
                "section_id": str(span.get("section_id", "")),
                "page": span.get("page"),
                "start_char": span.get("start_char"),
                "end_char": span.get("end_char"),
                "label": str(span.get("label", "source citation")),
            }
    return citations


def _public_source_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": _required_str(source, "source_id"),
        "canonical_url": _required_str(source, "canonical_url"),
        "source_type": _required_str(source, "source_type"),
        "owning_surface": str(source.get("owning_surface", "")),
        "allowlist_policy": str(source.get("allowlist_policy", "")),
        "robots_policy": str(source.get("robots_policy", "")),
        "privacy_classification": str(source.get("privacy_classification", "")),
        "freshness_status": str(source.get("freshness_status", "")),
    }


def _archive_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "manifest_id": _required_str(manifest, "manifest_id"),
        "source_id": _required_str(manifest, "source_id"),
        "canonical_url": _required_str(manifest, "canonical_url"),
        "http_status": manifest.get("http_status"),
        "content_type": str(manifest.get("content_type", "")),
        "content_hash": str(manifest.get("content_hash", "")),
        "processor_name": str(manifest.get("processor_name", "")),
        "processor_version": str(manifest.get("processor_version", "")),
        "normalized_document_id": str(manifest.get("normalized_document_id", "")),
        "no_raw_body_persisted": bool(manifest.get("no_raw_body_persisted", False)),
    }


def _requirement_summary(requirement: Mapping[str, Any], citations_by_evidence_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    evidence_ids = [str(value) for value in requirement.get("source_evidence_ids", [])]
    return {
        "requirement_id": _required_str(requirement, "requirement_id"),
        "requirement_type": _required_str(requirement, "requirement_type"),
        "subject": str(requirement.get("subject", "")),
        "action": str(requirement.get("action", "")),
        "object": str(requirement.get("object", "")),
        "process_stage": str(requirement.get("process_stage", "")),
        "source_evidence_ids": evidence_ids,
        "citations": [citations_by_evidence_id[evidence_id] for evidence_id in evidence_ids if evidence_id in citations_by_evidence_id],
        "human_review_status": str(requirement.get("human_review_status", "")),
        "formalization_status": str(requirement.get("formalization_status", "")),
    }


def _process_summary(process: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "process_id": _required_str(process, "process_id"),
        "permit_type": str(process.get("permit_type", "")),
        "scope": str(process.get("scope", "")),
        "required_user_facts": list(process.get("required_user_facts", [])),
        "required_documents": list(process.get("required_documents", [])),
        "stages": list(process.get("stages", [])),
        "unsupported_paths": list(process.get("unsupported_paths", [])),
        "guardrail_bundle_id": str(process.get("guardrail_bundle_id", "")),
    }


def _guardrail_summary(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "guardrail_bundle_id": _required_str(bundle, "guardrail_bundle_id"),
        "process_id": _required_str(bundle, "process_id"),
        "source_evidence_ids": [str(value) for value in bundle.get("source_evidence_ids", [])],
        "deterministic_predicate_ids": _ids_only(bundle.get("deterministic_predicates", [])),
        "reversible_action_predicate_ids": _ids_only(bundle.get("reversible_action_predicates", [])),
        "exact_confirmation_predicate_ids": _ids_only(bundle.get("exact_confirmation_predicates", [])),
        "refused_action_predicate_ids": _ids_only(bundle.get("refused_action_predicates", [])),
        "validation_status": str(bundle.get("validation_status", "")),
    }


def _next_safe_action_summary(action: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action_id": _required_str(action, "action_id"),
        "process_id": _required_str(action, "process_id"),
        "guardrail_bundle_id": _required_str(action, "guardrail_bundle_id"),
        "label": str(action.get("label", "")),
        "action_class": str(action.get("action_class", "")),
        "allowed": bool(action.get("allowed", False)),
        "requires_attendance": bool(action.get("requires_attendance", False)),
        "requires_exact_confirmation": bool(action.get("requires_exact_confirmation", False)),
        "blocked_reason": str(action.get("blocked_reason", "")),
        "supporting_requirement_ids": [str(value) for value in action.get("supporting_requirement_ids", [])],
    }


def _ids_only(items: Iterable[Any]) -> list[str]:
    ids: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            value = item.get("id") or item.get("predicate_id") or item.get("requirement_id")
            if value:
                ids.append(str(value))
        elif item:
            ids.append(str(item))
    return ids


def _required_str(item: Mapping[str, Any], field_name: str) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing required string field {field_name!r}")
    return value


def _scan_for_forbidden_material(value: Any, *, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_lower in FORBIDDEN_FIELD_NAMES:
                problems.append(f"forbidden field {path}.{key_text}")
            _scan_for_forbidden_material(child, path=f"{path}.{key_text}", problems=problems)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_material(child, path=f"{path}[{index}]", problems=problems)
        return
    if isinstance(value, str):
        if any(marker in value for marker in FORBIDDEN_TEXT_MARKERS):
            problems.append(f"forbidden marker at {path}")
        if _looks_like_private_local_path(value):
            problems.append(f"local private path at {path}")


def _looks_like_private_local_path(value: str) -> bool:
    if value.startswith(("/home/", "/Users/")):
        return True
    if len(value) >= 3 and value[1:3] == ":\\":
        return bool(PureWindowsPath(value).parts)
    if value.startswith("/"):
        parts = PurePosixPath(value).parts
        return len(parts) > 2 and parts[1] in {"home", "Users", "private", "tmp"}
    return False
