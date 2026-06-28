"""Deterministic public crawl batch planning for PP&D source registries.

This module is intentionally fixture-first and network-free. It converts committed
SourceRegistry-style records into a processor handoff plan while enforcing PP&D
crawl policy at the boundary before any archival processor is invoked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

DEFAULT_ALLOWED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PUBLIC_SOURCE_TYPES = frozenset(
    {
        "public_html",
        "public_pdf",
        "public_form",
        "devhub_public",
        "external_reference",
    }
)

PRIVATE_SOURCE_TYPES = frozenset({"devhub_authenticated"})
SUPPORTED_SCHEMES = frozenset({"https"})


@dataclass(frozen=True)
class BatchPlanDecision:
    """Policy decision for a single SourceRegistry entry."""

    source_id: str
    requested_url: str
    canonical_url: str
    source_type: str
    owning_surface: str
    crawl_frequency: str
    allowlist_decision: str
    robots_decision: str
    handoff_decision: str
    skip_reasons: tuple[str, ...]
    processor_policy: str
    privacy_classification: str
    citation_source_id: str
    no_raw_body_persisted: bool = True
    persist_raw_body: bool = False

    def to_handoff_item(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "citation_source_id": self.citation_source_id,
            "requested_url": self.requested_url,
            "canonical_url": self.canonical_url,
            "source_type": self.source_type,
            "owning_surface": self.owning_surface,
            "crawl_frequency": self.crawl_frequency,
            "allowlist_decision": self.allowlist_decision,
            "robots_decision": self.robots_decision,
            "handoff_decision": self.handoff_decision,
            "skip_reasons": list(self.skip_reasons),
            "processor_policy": self.processor_policy,
            "privacy_classification": self.privacy_classification,
            "no_raw_body_persisted": self.no_raw_body_persisted,
            "persist_raw_body": self.persist_raw_body,
        }


def canonicalize_public_url(url: str) -> str:
    """Return a stable crawl URL without fragments or tracking query params."""

    raw = url.strip()
    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = parsed.port

    netloc = hostname
    if port is not None and not (scheme == "https" and port == 443):
        netloc = f"{hostname}:{port}"

    path = parsed.path or "/"
    encoded_path = quote(path, safe="/%-._~")

    kept_query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {"fbclid", "gclid", "mc_cid", "mc_eid"}:
            continue
        kept_query_pairs.append((key, value))
    kept_query_pairs.sort()

    return urlunsplit((scheme, netloc, encoded_path, urlencode(kept_query_pairs), ""))


def build_public_crawl_batch_plan(
    registry: dict[str, Any],
    *,
    allowed_hosts: frozenset[str] = DEFAULT_ALLOWED_HOSTS,
) -> dict[str, Any]:
    """Convert SourceRegistry fixture data into a deterministic handoff plan."""

    entries = registry.get("sources", registry.get("source_registry", []))
    if not isinstance(entries, list):
        raise ValueError("source registry must contain a sources list")

    decisions = [_decide_source(entry, allowed_hosts=allowed_hosts) for entry in entries]
    decisions.sort(key=lambda decision: (decision.canonical_url, decision.source_id))

    handoff_queue = [decision.to_handoff_item() for decision in decisions]
    eligible_count = sum(1 for item in handoff_queue if item["handoff_decision"] == "enqueue")

    return {
        "plan_id": registry.get("plan_id", "fixture-public-crawl-batch-plan"),
        "network_access": "disabled",
        "processor_handoff_queue": handoff_queue,
        "summary": {
            "total_sources": len(handoff_queue),
            "eligible_for_handoff": eligible_count,
            "skipped": len(handoff_queue) - eligible_count,
            "no_raw_body_persisted": all(item["no_raw_body_persisted"] is True for item in handoff_queue),
        },
    }


def _decide_source(entry: dict[str, Any], *, allowed_hosts: frozenset[str]) -> BatchPlanDecision:
    source_id = _required_text(entry, "source_id")
    requested_url = _required_text(entry, "canonical_url")
    canonical_url = canonicalize_public_url(requested_url)
    parsed = urlsplit(canonical_url)

    source_type = str(entry.get("source_type", "public_html"))
    owning_surface = str(entry.get("owning_surface", "ppd_public"))
    crawl_frequency = str(entry.get("crawl_frequency", "manual"))
    processor_policy = str(entry.get("processor_policy", "metadata_and_normalized_text_only"))
    privacy_classification = str(entry.get("privacy_classification", "public"))
    robots_policy = str(entry.get("robots_policy", "unknown"))
    explicit_allowlist_policy = str(entry.get("allowlist_policy", "allow"))

    skip_reasons: list[str] = []

    if parsed.scheme not in SUPPORTED_SCHEMES:
        skip_reasons.append("unsupported_scheme")

    if parsed.hostname not in allowed_hosts or explicit_allowlist_policy in {"deny", "skip"}:
        skip_reasons.append("outside_allowlist")
        allowlist_decision = "deny"
    else:
        allowlist_decision = "allow"

    if robots_policy in {"disallow", "deny"}:
        skip_reasons.append("disallowed_by_robots")
        robots_decision = "deny"
    elif robots_policy in {"allow", "allowed"}:
        robots_decision = "allow"
    else:
        robots_decision = "unknown_requires_live_preflight"

    if source_type in PRIVATE_SOURCE_TYPES or privacy_classification != "public":
        skip_reasons.append("private_or_authenticated")

    if source_type not in PUBLIC_SOURCE_TYPES:
        skip_reasons.append("unsupported_source_type")

    if entry.get("persist_raw_body") is True:
        skip_reasons.append("raw_body_persistence_not_permitted")

    deduped_skip_reasons = tuple(dict.fromkeys(skip_reasons))
    handoff_decision = "skip" if deduped_skip_reasons else "enqueue"

    return BatchPlanDecision(
        source_id=source_id,
        requested_url=requested_url,
        canonical_url=canonical_url,
        source_type=source_type,
        owning_surface=owning_surface,
        crawl_frequency=crawl_frequency,
        allowlist_decision=allowlist_decision,
        robots_decision=robots_decision,
        handoff_decision=handoff_decision,
        skip_reasons=deduped_skip_reasons,
        processor_policy=processor_policy,
        privacy_classification=privacy_classification,
        citation_source_id=source_id,
    )


def _required_text(entry: dict[str, Any], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SourceRegistry entry is missing required text field: {key}")
    return value.strip()
