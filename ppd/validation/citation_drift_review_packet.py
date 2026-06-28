"""Fixture-first citation drift review packets for PP&D RequirementNodes.

The packet builder compares existing RequirementNode citation references against a
changed normalized-document snapshot. It is intentionally local and deterministic:
it reads no live sources, refreshes no requirement text, and emits review prompts
for every stale, missing, or moved citation span before downstream text refresh.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlparse

DRIFT_STATUSES = ("stale", "missing", "moved", "unchanged")
REVIEW_REQUIRED_STATUSES = frozenset({"stale", "missing", "moved"})
HUMAN_REVIEWED_STATUSES = frozenset({"approved", "reviewed", "human_reviewed"})
FORMALIZATION_READY_STATUSES = frozenset({"ready", "formalized", "ready_for_formalization"})
RAW_DOCUMENT_BODY_FIELDS = frozenset(
    {
        "body",
        "bytes",
        "content",
        "document_body",
        "document_text",
        "html",
        "normalized_text",
        "page_html",
        "raw_body",
        "raw_html",
        "raw_text",
        "response_body",
    }
)
PRIVATE_VALUE_KEYS = frozenset(
    {
        "account_number",
        "applicant_email",
        "auth_state",
        "cookie",
        "known_value",
        "password",
        "payment_detail",
        "private_value",
        "raw_value",
        "session",
        "storage_state",
        "token",
    }
)
DOWNLOADED_DOCUMENT_PATH_FIELDS = frozenset(
    {
        "download_path",
        "downloaded_document_path",
        "downloaded_pdf_path",
        "file_path",
        "local_document_path",
        "local_file_path",
        "local_pdf_path",
        "pdf_path",
    }
)
OFFSET_FIELDS = frozenset({"start_offset", "end_offset", "char_start", "char_end", "byte_start", "byte_end"})
PRIVATE_PATH_MARKERS = (
    "/.daemon/",
    "/auth/",
    "/private/",
    "/raw/",
    "/sessions/",
    "/traces/",
    "har",
    "storage_state",
)
LOCAL_PATH_PREFIXES = ("/tmp/", "/var/tmp/", "/private/", "/home/", "/Users/", "~", "./", "../")
PRIVATE_URL_PATH_PREFIXES = ("/private/", "/admin/", "/auth/", "/login", "/oauth", "/sso", "/session")


@dataclass(frozen=True)
class CitationSpanRecord:
    evidence_id: str
    document_id: str
    source_id: str
    archive_artifact_ref: str
    span_id: str
    locator: str
    text_hash: str
    document_hash: str
    quote: str
    section_id: str

    def as_public_dict(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "archive_artifact_ref": self.archive_artifact_ref,
            "span_id": self.span_id,
            "locator": self.locator,
            "text_hash": self.text_hash,
            "document_hash": self.document_hash,
            "quote": self.quote,
            "section_id": self.section_id,
        }


def build_citation_drift_review_packet(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic human-review packet from a local fixture mapping."""

    validate_citation_drift_review_packet_input(fixture)
    previous_spans = _span_index(_sequence(fixture.get("previous_normalized_documents")))
    current_spans = _span_index(_sequence(fixture.get("changed_normalized_documents")))
    requirements = _sequence(fixture.get("requirement_nodes"))

    observations: list[dict[str, Any]] = []
    prompts: list[dict[str, Any]] = []
    counts = {status: 0 for status in DRIFT_STATUSES}

    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            continue
        requirement_id = _required_text(requirement, "requirement_id")
        requirement_label = _requirement_label(requirement)
        refs = _requirement_citation_refs(requirement)
        if not refs:
            observation = {
                "requirement_id": requirement_id,
                "evidence_id": "",
                "status": "missing",
                "reason": "requirement has no citation span reference",
                "previous_span": None,
                "current_span": None,
            }
            observations.append(observation)
            counts["missing"] += 1
            prompts.append(_review_prompt(requirement_id, requirement_label, observation))
            continue

        for evidence_id in refs:
            previous = previous_spans.get(evidence_id)
            current = current_spans.get(evidence_id)
            observation = _compare_span(requirement_id, evidence_id, previous, current)
            observations.append(observation)
            counts[observation["status"]] += 1
            if observation["status"] in REVIEW_REQUIRED_STATUSES:
                prompts.append(_review_prompt(requirement_id, requirement_label, observation))

    packet_status = "blocked_pending_human_review" if prompts else "ready_no_citation_drift"
    return {
        "schema_version": 1,
        "packet_type": "citation_drift_review_packet",
        "fixture_id": _required_text(fixture, "fixture_id"),
        "source_change_id": _required_text(fixture, "source_change_id"),
        "requirement_text_refresh_status": packet_status,
        "requirement_text_refresh_allowed": not prompts,
        "summary": {
            "requirement_count": len(requirements),
            "citation_observation_count": len(observations),
            "stale_count": counts["stale"],
            "missing_count": counts["missing"],
            "moved_count": counts["moved"],
            "unchanged_count": counts["unchanged"],
            "human_review_prompt_count": len(prompts),
        },
        "citation_drift_observations": observations,
        "human_review_prompts": prompts,
    }


def validate_citation_drift_review_packet_input(fixture: Mapping[str, Any]) -> None:
    """Reject unsafe packet fields before citation drift classification."""

    if not isinstance(fixture, Mapping):
        raise ValueError("citation drift review packet fixture must be a mapping")
    _required_text(fixture, "fixture_id")
    _required_text(fixture, "source_change_id")
    _reject_private_or_raw_values(fixture, "$", parent_key="")
    _validate_documents(_sequence(fixture.get("previous_normalized_documents")), "previous_normalized_documents")
    _validate_documents(_sequence(fixture.get("changed_normalized_documents")), "changed_normalized_documents")
    _validate_requirements(_sequence(fixture.get("requirement_nodes")))
    _validate_declared_unchanged_statuses(fixture)


def _compare_span(
    requirement_id: str,
    evidence_id: str,
    previous: CitationSpanRecord | None,
    current: CitationSpanRecord | None,
) -> dict[str, Any]:
    if previous is None and current is None:
        return {
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "status": "missing",
            "reason": "citation evidence id is absent from previous and changed normalized documents",
            "previous_span": None,
            "current_span": None,
        }
    if current is None:
        return {
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "status": "missing",
            "reason": "citation evidence id is absent from changed normalized documents",
            "previous_span": previous.as_public_dict() if previous else None,
            "current_span": None,
        }
    if previous is None:
        return {
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "status": "moved",
            "reason": "citation evidence id is new in the changed normalized document snapshot",
            "previous_span": None,
            "current_span": current.as_public_dict(),
        }
    if previous.text_hash != current.text_hash:
        return {
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "status": "stale",
            "reason": "citation text hash changed and requirement text must not be refreshed without review",
            "previous_span": previous.as_public_dict(),
            "current_span": current.as_public_dict(),
        }
    if previous.locator != current.locator or previous.section_id != current.section_id:
        return {
            "requirement_id": requirement_id,
            "evidence_id": evidence_id,
            "status": "moved",
            "reason": "citation text is unchanged but span locator or section moved",
            "previous_span": previous.as_public_dict(),
            "current_span": current.as_public_dict(),
        }
    return {
        "requirement_id": requirement_id,
        "evidence_id": evidence_id,
        "status": "unchanged",
        "reason": "citation text hash and locator are unchanged",
        "previous_span": previous.as_public_dict(),
        "current_span": current.as_public_dict(),
    }


def _span_index(documents: Iterable[Any]) -> dict[str, CitationSpanRecord]:
    spans: dict[str, CitationSpanRecord] = {}
    for document in documents:
        if not isinstance(document, Mapping):
            continue
        document_id = _required_text(document, "document_id")
        source_id = _required_text(document, "source_id")
        document_hash = _required_text(document, "content_hash")
        archive_artifact_ref = _required_text(document, "archive_artifact_ref")
        for span in _sequence(document.get("citation_spans")):
            if not isinstance(span, Mapping):
                continue
            evidence_id = _first_text(span, ("evidence_id", "source_evidence_id", "citation_id"))
            span_id = _first_text(span, ("span_id", "citation_span_id", "id"))
            if not evidence_id or not span_id:
                continue
            spans[evidence_id] = CitationSpanRecord(
                evidence_id=evidence_id,
                document_id=document_id,
                source_id=_text(span.get("source_id")) or source_id,
                archive_artifact_ref=_text(span.get("archive_artifact_ref")) or archive_artifact_ref,
                span_id=span_id,
                locator=_first_text(span, ("locator", "selector", "anchor_id")) or span_id,
                text_hash=_required_text(span, "text_hash"),
                document_hash=_text(span.get("document_hash")) or document_hash,
                quote=_text(span.get("quote")),
                section_id=_first_text(span, ("section_id", "anchor_id", "heading_id")) or "",
            )
    return spans


def _validate_documents(documents: list[Any], label: str) -> None:
    if not documents:
        raise ValueError(f"{label} must include at least one normalized document")
    for index, document in enumerate(documents):
        if not isinstance(document, Mapping):
            raise ValueError(f"{label}[{index}] must be a mapping")
        path = f"{label}[{index}]"
        _required_text(document, "document_id")
        _required_text(document, "source_id")
        _required_text(document, "content_hash")
        _required_text(document, "archive_artifact_ref")
        spans = _sequence(document.get("citation_spans"))
        if not spans:
            raise ValueError(f"{path}.citation_spans must include at least one span")
        for span_index, span in enumerate(spans):
            if not isinstance(span, Mapping):
                raise ValueError(f"{path}.citation_spans[{span_index}] must be a mapping")
            span_path = f"{path}.citation_spans[{span_index}]"
            if not _first_text(span, ("evidence_id", "source_evidence_id", "citation_id")):
                raise ValueError(f"{span_path}.evidence_id is required")
            if not _first_text(span, ("span_id", "citation_span_id", "id")):
                raise ValueError(f"{span_path}.span_id is required")
            _required_text(span, "text_hash")
            _validate_no_invented_offsets(span, span_path)


def _validate_no_invented_offsets(span: Mapping[str, Any], path: str) -> None:
    present = sorted(key for key in span if str(key).lower() in OFFSET_FIELDS)
    if not present:
        return
    evidence = _text(span.get("offset_evidence_id")) or _text(span.get("extractor_run_id"))
    verified = _text(span.get("offset_basis")).lower() in {"extractor_verified", "source_text_index"}
    if not evidence or not verified:
        raise ValueError(f"invented span offsets are not allowed at {path}")


def _validate_requirements(requirements: list[Any]) -> None:
    if not requirements:
        raise ValueError("requirement_nodes must include at least one requirement")
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, Mapping):
            raise ValueError(f"requirement_nodes[{index}] must be a mapping")
        requirement_id = _required_text(requirement, "requirement_id")
        human_review_status = _text(requirement.get("human_review_status") or requirement.get("review_status")).lower()
        formalization_status = _text(requirement.get("formalization_status")).lower()
        if formalization_status in FORMALIZATION_READY_STATUSES and human_review_status not in HUMAN_REVIEWED_STATUSES:
            raise ValueError(f"ready formalization before human review is not allowed for {requirement_id}")


def _validate_declared_unchanged_statuses(fixture: Mapping[str, Any]) -> None:
    declared = _sequence(fixture.get("citation_drift_observations")) + _sequence(fixture.get("review_decisions"))
    if not declared:
        return
    previous_spans = _span_index(_sequence(fixture.get("previous_normalized_documents")))
    current_spans = _span_index(_sequence(fixture.get("changed_normalized_documents")))
    for index, observation in enumerate(declared):
        if not isinstance(observation, Mapping):
            continue
        status = _text(observation.get("status") or observation.get("drift_status")).lower()
        if status != "unchanged":
            continue
        evidence_id = _first_text(observation, ("evidence_id", "source_evidence_id", "citation_id"))
        if not evidence_id:
            continue
        previous = previous_spans.get(evidence_id)
        current = current_spans.get(evidence_id)
        if previous is None or current is None:
            continue
        hashes_changed = previous.text_hash != current.text_hash or previous.document_hash != current.document_hash
        evidence = _text(observation.get("unchanged_hash_evidence_id")) or _text(observation.get("human_review_evidence_id"))
        if hashes_changed and not evidence:
            raise ValueError(f"unchanged status for changed hashes requires evidence at declared observation {index}")


def _requirement_citation_refs(requirement: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("source_evidence_ids", "citation_ids"):
        value = requirement.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
        elif isinstance(value, list):
            refs.extend(item.strip() for item in value if isinstance(item, str) and item.strip())
    citations = requirement.get("citations")
    if isinstance(citations, list):
        for citation in citations:
            if isinstance(citation, Mapping):
                evidence_id = _first_text(citation, ("evidence_id", "source_evidence_id", "citation_id"))
                if evidence_id:
                    refs.append(evidence_id)
            elif isinstance(citation, str) and citation.strip():
                refs.append(citation.strip())
    return sorted(dict.fromkeys(refs))


def _review_prompt(requirement_id: str, requirement_label: str, observation: Mapping[str, Any]) -> dict[str, Any]:
    evidence_id = _text(observation.get("evidence_id")) or "missing-citation-reference"
    status = _required_text(observation, "status")
    return {
        "prompt_id": f"review-{requirement_id}-{evidence_id or status}",
        "requirement_id": requirement_id,
        "evidence_id": evidence_id,
        "drift_status": status,
        "prompt_type": "human_citation_review_before_requirement_text_refresh",
        "question": (
            f"Review requirement {requirement_label} citation {evidence_id}: "
            f"status is {status}. Confirm whether the changed source still supports the requirement before refreshing text."
        ),
        "blocks_requirement_text_refresh": True,
    }


def _requirement_label(requirement: Mapping[str, Any]) -> str:
    subject = _text(requirement.get("subject"))
    action = _text(requirement.get("action"))
    obj = _text(requirement.get("object"))
    label = " ".join(part for part in (subject, action, obj) if part)
    return label or _required_text(requirement, "requirement_id")


def _reject_private_or_raw_values(value: Any, path: str, parent_key: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            child_path = f"{path}.{key_text}" if path else key_text
            if lowered in RAW_DOCUMENT_BODY_FIELDS:
                raise ValueError(f"raw document body field is not allowed: {child_path}")
            if lowered in PRIVATE_VALUE_KEYS:
                raise ValueError(f"private value field is not allowed: {child_path}")
            if lowered in DOWNLOADED_DOCUMENT_PATH_FIELDS:
                raise ValueError(f"downloaded document path is not allowed: {child_path}")
            if lowered.endswith("url") or lowered == "url":
                _validate_public_url(nested, child_path)
            if lowered.endswith("path") or lowered in {"path", "file"}:
                _validate_not_local_private_path(nested, child_path)
            _reject_private_or_raw_values(nested, child_path, lowered)
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_private_or_raw_values(nested, f"{path}[{index}]", parent_key=parent_key)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        if any(marker in lowered_value for marker in PRIVATE_PATH_MARKERS):
            raise ValueError(f"private or raw artifact reference is not allowed: {path}")
        if parent_key.endswith("path") or parent_key in {"path", "file"}:
            _validate_not_local_private_path(value, path)


def _validate_public_url(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"URL field must be a non-empty string: {path}")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"URL must use http or https: {path}")
    if not parsed.hostname:
        raise ValueError(f"URL is missing host: {path}")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise ValueError(f"private host is not allowed: {path}")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ValueError(f"private host is not allowed: {path}")
    decoded_path = unquote(parsed.path).lower()
    if any(decoded_path.startswith(prefix) for prefix in PRIVATE_URL_PATH_PREFIXES):
        raise ValueError(f"authenticated URL path is not allowed: {path}")


def _validate_not_local_private_path(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value:
        return
    normalized = value.replace("\\", "/")
    lowered = normalized.lower()
    if lowered.endswith((".pdf", ".doc", ".docx", ".html")) and (
        normalized.startswith("/") or normalized.startswith(".") or normalized.startswith("~")
    ):
        raise ValueError(f"downloaded document path is not allowed: {path}")
    if normalized.startswith(LOCAL_PATH_PREFIXES):
        raise ValueError(f"local private path is not allowed: {path}")
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ValueError(f"local private path is not allowed: {path}")


def _sequence(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = _text(data.get(key))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _first_text(data: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = _text(data.get(key))
        if value:
            return value
    return ""


__all__ = [
    "DRIFT_STATUSES",
    "REVIEW_REQUIRED_STATUSES",
    "build_citation_drift_review_packet",
    "validate_citation_drift_review_packet_input",
]
