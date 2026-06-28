"""Local dry-run public crawl plan generation for Portland PP&D seeds.

This module is intentionally offline-only. It converts official seed metadata into
fetch intentions and never performs network requests or writes crawl output.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import argparse
import json

_ALLOWED_SCHEMES = {"https"}
_DEFAULT_FREQUENCY = "weekly"
_DEFAULT_RATE_LIMIT_BUCKET = "official-public"
_PROCESSOR_BY_KIND = {
    "html": "html_public_page",
    "pdf": "pdf_document",
    "json": "json_api",
    "csv": "tabular_csv",
}


@dataclass(frozen=True)
class FetchIntention:
    order: int
    seed_id: str
    url: str
    allowlist_decision: str
    allowlist_reason: str
    robots_preflight_status: str
    crawl_frequency: str
    processor_capability: str
    rate_limit_bucket: str
    no_raw_body_persisted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "seed_id": self.seed_id,
            "url": self.url,
            "allowlist_decision": self.allowlist_decision,
            "allowlist_reason": self.allowlist_reason,
            "robots_preflight_status": self.robots_preflight_status,
            "crawl_frequency": self.crawl_frequency,
            "processor_capability": self.processor_capability,
            "rate_limit_bucket": self.rate_limit_bucket,
            "no_raw_body_persisted": self.no_raw_body_persisted,
        }


def load_seed_metadata(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("seed metadata must be a JSON object")
    return data


def generate_public_crawl_plan(seed_metadata: dict[str, Any]) -> dict[str, Any]:
    seeds = seed_metadata.get("seeds")
    if not isinstance(seeds, list):
        raise ValueError("seed metadata must include a seeds array")

    allowed_hosts = _normalize_hosts(seed_metadata.get("allowed_hosts", []))
    intentions = [_build_intention(index, seed, allowed_hosts) for index, seed in enumerate(seeds, start=1)]
    intentions.sort(key=lambda item: (item.allowlist_decision != "allow", item.order, item.seed_id))

    return {
        "mode": "dry_run_public_crawl_plan",
        "source": seed_metadata.get("source", "official_seed_metadata"),
        "network_requests_made": False,
        "crawl_output_created": False,
        "intentions": [intention.to_dict() for intention in intentions],
    }


def _build_intention(order: int, seed: Any, allowed_hosts: set[str]) -> FetchIntention:
    if not isinstance(seed, dict):
        raise ValueError("each seed must be a JSON object")

    url = _required_text(seed, "url")
    seed_id = str(seed.get("id") or seed.get("seed_id") or f"seed-{order}")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    scheme_allowed = parsed.scheme.lower() in _ALLOWED_SCHEMES
    host_allowed = host in allowed_hosts or any(host.endswith(f".{allowed}") for allowed in allowed_hosts)

    if scheme_allowed and host_allowed:
        allowlist_decision = "allow"
        allowlist_reason = f"{host} matches official seed allowlist"
    elif not scheme_allowed:
        allowlist_decision = "deny"
        allowlist_reason = f"scheme {parsed.scheme or ''} is not allowed for public crawl seeds"
    else:
        allowlist_decision = "deny"
        allowlist_reason = f"{host or ''} is outside official seed allowlist"

    return FetchIntention(
        order=order,
        seed_id=seed_id,
        url=url,
        allowlist_decision=allowlist_decision,
        allowlist_reason=allowlist_reason,
        robots_preflight_status=_preflight_status(seed, allowlist_decision),
        crawl_frequency=str(seed.get("crawl_frequency") or seed.get("frequency") or _DEFAULT_FREQUENCY),
        processor_capability=_processor_capability(seed),
        rate_limit_bucket=str(seed.get("rate_limit_bucket") or _DEFAULT_RATE_LIMIT_BUCKET),
        no_raw_body_persisted=True,
    )


def _normalize_hosts(hosts: Any) -> set[str]:
    if not isinstance(hosts, list):
        raise ValueError("allowed_hosts must be an array")
    normalized = set()
    for host in hosts:
        if not isinstance(host, str) or not host.strip():
            raise ValueError("allowed_hosts entries must be non-empty strings")
        normalized.add(host.strip().lower())
    return normalized


def _preflight_status(seed: dict[str, Any], allowlist_decision: str) -> str:
    if allowlist_decision != "allow":
        return "skipped_not_allowlisted"
    robots = str(seed.get("robots") or seed.get("robots_status") or "requires_live_check")
    if robots in {"allowed", "disallowed", "requires_live_check", "manual_review"}:
        return robots
    return "manual_review"


def _processor_capability(seed: dict[str, Any]) -> str:
    explicit = seed.get("processor_capability")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    kind = str(seed.get("kind") or seed.get("content_type") or "html").lower()
    return _PROCESSOR_BY_KIND.get(kind, "generic_public_document")


def _required_text(seed: dict[str, Any], key: str) -> str:
    value = seed.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"seed missing required text field: {key}")
    return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an offline dry-run public crawl plan from seed metadata.")
    parser.add_argument("seed_metadata", help="Path to official seed metadata JSON")
    args = parser.parse_args()
    plan = generate_public_crawl_plan(load_seed_metadata(args.seed_metadata))
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
