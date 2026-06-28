"""Fixture-first public refresh result intake schema v6.

This module intentionally consumes only synthetic dry-run manifest rows. It normalizes
public refresh metadata for downstream processor handoff tests without crawling,
downloading, opening DevHub, storing raw bodies, or making legal/permitting claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = "ppd.public_refresh_result_intake.v6"

ALLOWED_SOURCE_GROUPS = {
    "ppd_public_html",
    "ppd_public_pdf",
    "ppd_public_form",
    "devhub_public_help",
    "portland_maps_public_reference",
}

ALLOWED_SKIPPED_REASONS = {
    "synthetic_dry_run_no_fetch",
    "outside_allowlist",
    "unsupported_scheme",
    "private_or_authenticated",
    "robots_or_policy_disallowed",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
}

HTTP_METADATA_PLACEHOLDER_KEYS = (
    "status_code",
    "content_type",
    "etag",
    "last_modified",
    "redirect_chain",
)

FORBIDDEN_ARTIFACT_KEYS = {
    "raw_body",
    "body",
    "html",
    "document_bytes",
    "downloaded_document",
    "download_path",
    "raw_download_path",
    "raw_crawl_artifact",
    "crawl_artifact_path",
    "local_private_path",
    "private_file_path",
    "session_file",
    "session_path",
    "devhub_session_path",
    "auth_state",
    "auth_state_path",
    "storage_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "token",
    "trace_path",
    "har_path",
    "screenshot_path",
}

LIVE_CRAWL_CLAIM_KEYS = {
    "live_crawl_performed",
    "live_crawl_executed",
    "crawl_executed",
    "crawl_performed",
    "fetch_performed",
    "fetched",
    "downloaded",
    "download_performed",
    "processor_executed_live",
}

ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "active_mutations",
    "mutation_enabled",
    "mutations_enabled",
    "execute_mutations",
    "write_enabled",
    "writes_enabled",
    "official_action_enabled",
}

OFFICIAL_COMPLETION_KEYS = {
    "official_action_completed",
    "official_action_completion_claim",
    "permit_submitted",
    "permit_approved",
    "payment_completed",
    "inspection_scheduled",
    "upload_completed",
    "certification_completed",
}

FORBIDDEN_TEXT_FRAGMENTS = (
    "live crawl executed",
    "live crawl performed",
    "downloaded raw",
    "raw crawl artifact",
    "official action completed",
    "permit submitted",
    "permit approved",
    "payment completed",
    "inspection scheduled",
    "legal guarantee",
    "permitting guarantee",
    "guaranteed approval",
)

PRIVATE_QUERY_KEYS = {
    "access_token",
    "auth",
    "code",
    "password",
    "session",
    "state",
    "token",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_public_url(url: str) -> str:
    """Return a stable public URL form without fetching the URL."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("source_url must be a non-empty string")

    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"https", "http"}:
        raise ValueError(f"unsupported URL scheme for synthetic intake: {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise ValueError("public refresh intake URLs must not include credentials")

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    for key, _value in query_pairs:
        if key.lower() in PRIVATE_QUERY_KEYS:
            raise ValueError("public refresh intake URLs must not include private/session/auth query fields")

    host = parsed.netloc.lower()
    path = parsed.path or "/"
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, host, path, query, ""))


def infer_source_group(canonical_url: str, content_type: str | None = None) -> str:
    parsed = urlsplit(canonical_url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    mime = (content_type or "").lower()

    if host == "devhub.portlandoregon.gov":
        return "devhub_public_help"
    if host == "www.portlandmaps.com":
        return "portland_maps_public_reference"
    if path.endswith(".pdf") or mime == "application/pdf":
        return "ppd_public_pdf"
    if "form" in path or "applications" in path:
        return "ppd_public_form"
    return "ppd_public_html"


def processor_handoff_id_for(canonical_url: str, source_group: str) -> str:
    digest = sha256(f"{source_group}\n{canonical_url}".encode("utf-8")).hexdigest()[:16]
    return f"ppd-refresh-v6-{digest}"


def _required_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _required_mapping(row: dict[str, Any], key: str) -> dict[str, Any]:
    value = row.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return dict(value)


def _reject_forbidden_claims(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = key_text.lower()
            child_path = f"{path}.{key_text}"
            if normalized_key in FORBIDDEN_ARTIFACT_KEYS and child not in (None, "", [], {}):
                raise ValueError(f"public refresh intake v6 rejects raw/private artifacts at {child_path}")
            if normalized_key in LIVE_CRAWL_CLAIM_KEYS and child is True:
                raise ValueError(f"public refresh intake v6 rejects live crawl execution claims at {child_path}")
            if normalized_key in ACTIVE_MUTATION_KEYS and child:
                raise ValueError(f"public refresh intake v6 rejects active mutation flags at {child_path}")
            if normalized_key in OFFICIAL_COMPLETION_KEYS and child:
                raise ValueError(f"public refresh intake v6 rejects official-action completion claims at {child_path}")
            _reject_forbidden_claims(child, child_path)
        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_claims(child, f"{path}[{index}]")
        return

    if isinstance(value, str):
        normalized_value = value.lower()
        for fragment in FORBIDDEN_TEXT_FRAGMENTS:
            if fragment in normalized_value:
                raise ValueError(f"public refresh intake v6 rejects prohibited claim text at {path}")


def _require_synthetic_dry_run(row: dict[str, Any]) -> None:
    if row.get("synthetic") is not True or row.get("dry_run") is not True:
        raise ValueError("public refresh intake v6 accepts only rows with synthetic=true and dry_run=true")


def _dry_run_plan_ref(row: dict[str, Any]) -> dict[str, str]:
    ref = _required_mapping(row, "dry_run_plan_ref")
    plan_id = ref.get("plan_id")
    schema_version = ref.get("schema_version")
    if not isinstance(plan_id, str) or not plan_id.strip():
        raise ValueError("dry_run_plan_ref.plan_id must be a non-empty string")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise ValueError("dry_run_plan_ref.schema_version must be a non-empty string")
    return {"plan_id": plan_id.strip(), "schema_version": schema_version.strip()}


def _http_metadata_placeholder(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _required_mapping(row, "http_metadata")
    missing = [key for key in HTTP_METADATA_PLACEHOLDER_KEYS if key not in metadata]
    if missing:
        raise ValueError("http_metadata missing placeholder fields: " + ", ".join(missing))

    result = {key: metadata.get(key) for key in HTTP_METADATA_PLACEHOLDER_KEYS}
    if result["status_code"] is not None:
        raise ValueError("http_metadata.status_code must be a null dry-run placeholder")
    if result["etag"] is not None:
        raise ValueError("http_metadata.etag must be a null dry-run placeholder")
    if result["last_modified"] is not None:
        raise ValueError("http_metadata.last_modified must be a null dry-run placeholder")
    if not isinstance(result["redirect_chain"], list):
        raise ValueError("http_metadata.redirect_chain must be a list placeholder")
    if result["redirect_chain"]:
        raise ValueError("http_metadata.redirect_chain must be empty for fixture dry-run intake")
    if result["content_type"] is not None and not isinstance(result["content_type"], str):
        raise ValueError("http_metadata.content_type must be a string or null placeholder")
    return result


def _content_hash_placeholder(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("content_hash")
    if not isinstance(value, dict):
        raise ValueError("content_hash must be an explicit placeholder object")
    algorithm = value.get("algorithm")
    digest = value.get("value")
    placeholder = value.get("placeholder")
    if algorithm != "sha256":
        raise ValueError("content_hash.algorithm must be sha256")
    if digest not in (None, ""):
        raise ValueError("synthetic dry-run intake must use a content-hash placeholder, not a real digest")
    if placeholder is not True:
        raise ValueError("content_hash.placeholder must be true")
    return {"algorithm": "sha256", "value": None, "placeholder": True}


def _processor_handoff_id(row: dict[str, Any]) -> str:
    value = _required_text(row, "processor_handoff_id")
    if not value.startswith("ppd-refresh-v6-"):
        raise ValueError("processor_handoff_id must use the ppd-refresh-v6 prefix")
    return value


def _skipped_reason(row: dict[str, Any]) -> str:
    value = _required_text(row, "skipped_reason")
    if value not in ALLOWED_SKIPPED_REASONS:
        raise ValueError(f"unsupported skipped_reason for public refresh intake v6: {value}")
    return value


def _no_raw_body_assertions(row: dict[str, Any]) -> tuple[bool, bool]:
    if row.get("no_raw_body_asserted") is not True:
        raise ValueError("no_raw_body_asserted must be true")
    if row.get("no_raw_body_persisted") is not False:
        raise ValueError("no_raw_body_persisted must be false")
    return True, False


def _citation_candidates(row: dict[str, Any], canonical_url: str) -> list[dict[str, str]]:
    candidates = row.get("citation_refresh_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("citation_refresh_candidates must be a non-empty list")

    normalized: list[dict[str, str]] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError("each citation refresh candidate must be an object")
        citation_id = candidate.get("citation_id")
        reason = candidate.get("reason")
        if not isinstance(citation_id, str) or not citation_id.strip():
            raise ValueError(f"citation_refresh_candidates[{index}].citation_id must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"citation_refresh_candidates[{index}].reason must be a non-empty string")
        normalized.append({"citation_id": citation_id.strip(), "canonical_url": canonical_url, "reason": reason.strip()})
    return normalized


def _freshness_delta(row: dict[str, Any]) -> dict[str, Any]:
    delta = row.get("freshness_status_delta")
    if not isinstance(delta, dict):
        raise ValueError("freshness_status_delta must be an object")
    previous_status = delta.get("previous_status")
    current_status = delta.get("current_status")
    changed = delta.get("changed")
    if not isinstance(previous_status, str) or not previous_status.strip():
        raise ValueError("freshness_status_delta.previous_status must be a non-empty string")
    if not isinstance(current_status, str) or not current_status.strip():
        raise ValueError("freshness_status_delta.current_status must be a non-empty string")
    if not isinstance(changed, bool):
        raise ValueError("freshness_status_delta.changed must be a boolean")
    if changed != (previous_status != current_status):
        raise ValueError("freshness_status_delta.changed must match previous/current status comparison")
    return {
        "previous_status": previous_status.strip(),
        "current_status": current_status.strip(),
        "changed": changed,
    }


@dataclass(frozen=True)
class PublicRefreshResultV6:
    schema_version: str
    dry_run_plan_ref: dict[str, str]
    source_url: str
    canonical_url: str
    source_group: str
    http_metadata: dict[str, Any]
    content_hash: dict[str, Any]
    processor_handoff_id: str
    skipped_reason: str
    no_raw_body_asserted: bool
    no_raw_body_persisted: bool
    citation_refresh_candidates: list[dict[str, str]] = field(default_factory=list)
    freshness_status_delta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublicRefreshIntakeV6:
    schema_version: str
    generated_at: str
    source: str
    rows: list[PublicRefreshResultV6]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rows"] = [row.to_dict() for row in self.rows]
        return data


def normalize_manifest_row(row: dict[str, Any]) -> PublicRefreshResultV6:
    if not isinstance(row, dict):
        raise ValueError("manifest row must be an object")
    _reject_forbidden_claims(row)
    _require_synthetic_dry_run(row)

    dry_run_plan_ref = _dry_run_plan_ref(row)
    source_url = normalize_public_url(_required_text(row, "source_url"))
    canonical_url = normalize_public_url(_required_text(row, "canonical_url"))
    source_group = _required_text(row, "source_group")
    if source_group not in ALLOWED_SOURCE_GROUPS:
        raise ValueError(f"unsupported source_group for public refresh intake v6: {source_group}")

    http_metadata = _http_metadata_placeholder(row)
    expected_group = infer_source_group(canonical_url, http_metadata.get("content_type"))
    if source_group != expected_group:
        raise ValueError(f"source_group {source_group!r} does not match canonical URL/content type expectation {expected_group!r}")

    no_raw_body_asserted, no_raw_body_persisted = _no_raw_body_assertions(row)
    return PublicRefreshResultV6(
        schema_version=SCHEMA_VERSION,
        dry_run_plan_ref=dry_run_plan_ref,
        source_url=source_url,
        canonical_url=canonical_url,
        source_group=source_group,
        http_metadata=http_metadata,
        content_hash=_content_hash_placeholder(row),
        processor_handoff_id=_processor_handoff_id(row),
        skipped_reason=_skipped_reason(row),
        no_raw_body_asserted=no_raw_body_asserted,
        no_raw_body_persisted=no_raw_body_persisted,
        citation_refresh_candidates=_citation_candidates(row, canonical_url),
        freshness_status_delta=_freshness_delta(row),
    )


def normalize_manifest_rows(rows: list[dict[str, Any]], source: str = "synthetic_fixture") -> PublicRefreshIntakeV6:
    if not isinstance(rows, list):
        raise ValueError("manifest rows must be supplied as a list")
    return PublicRefreshIntakeV6(
        schema_version=SCHEMA_VERSION,
        generated_at=_utc_now_iso(),
        source=source,
        rows=[normalize_manifest_row(row) for row in rows],
    )
