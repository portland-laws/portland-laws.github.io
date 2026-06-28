"""Validation for PP&D public recrawl execution rehearsal plans.

The validator is intentionally deterministic and side-effect free. It does not
fetch URLs, inspect robots.txt over the network, or authenticate to any service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlparse


DEFAULT_ALLOWLISTED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "efiles.portlandoregon.gov",
    }
)

_PRIVATE_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
    }
)

_AUTH_HINTS = (
    "login",
    "logout",
    "signin",
    "sign-in",
    "auth",
    "oauth",
    "saml",
    "session",
    "account",
    "admin",
    "dashboard",
    "devhub",
)

_RAW_BODY_DOWNLOAD_ARCHIVE_HINTS = (
    "/raw",
    "/body",
    "/download",
    "/downloads",
    "/archive",
    "/archives",
    "format=raw",
    "download=1",
    "download=true",
)

_REAL_RECRAWL_CLAIMS = (
    "real recrawl was performed",
    "recrawl was performed",
    "completed live recrawl",
    "executed live recrawl",
    "performed live recrawl",
    "ran the recrawl",
    "live crawl completed",
    "production recrawl completed",
)


@dataclass(frozen=True)
class PublicRecrawlRehearsalPlan:
    """Side-effect-free description of a proposed public recrawl rehearsal."""

    urls: Sequence[str]
    allowlisted_hosts: Iterable[str] = field(default_factory=lambda: DEFAULT_ALLOWLISTED_HOSTS)
    robots_prerequisites_confirmed: bool = False
    policy_prerequisites_confirmed: bool = False
    live_network_execution: bool = False
    authenticated_automation: bool = False
    processor_handoff_intent: str = ""
    abort_conditions: Sequence[str] = field(default_factory=tuple)
    notes: str = ""


def _as_bool(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _as_str_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def plan_from_mapping(data: Mapping[str, object]) -> PublicRecrawlRehearsalPlan:
    """Build a rehearsal plan from plain data without accepting unknown behavior."""

    allowlisted_hosts = data.get("allowlisted_hosts", DEFAULT_ALLOWLISTED_HOSTS)
    if isinstance(allowlisted_hosts, str):
        allowlisted = (allowlisted_hosts,)
    elif isinstance(allowlisted_hosts, Iterable):
        allowlisted = tuple(str(host) for host in allowlisted_hosts)
    else:
        allowlisted = tuple(DEFAULT_ALLOWLISTED_HOSTS)

    return PublicRecrawlRehearsalPlan(
        urls=_as_str_sequence(data.get("urls", ())),
        allowlisted_hosts=allowlisted,
        robots_prerequisites_confirmed=_as_bool(data.get("robots_prerequisites_confirmed")),
        policy_prerequisites_confirmed=_as_bool(data.get("policy_prerequisites_confirmed")),
        live_network_execution=_as_bool(data.get("live_network_execution")),
        authenticated_automation=_as_bool(data.get("authenticated_automation")),
        processor_handoff_intent=str(data.get("processor_handoff_intent", "") or ""),
        abort_conditions=_as_str_sequence(data.get("abort_conditions", ())),
        notes=str(data.get("notes", "") or ""),
    )


def validate_public_recrawl_rehearsal_plan(plan: PublicRecrawlRehearsalPlan | Mapping[str, object]) -> list[str]:
    """Return validation errors for an unsafe public recrawl rehearsal plan."""

    if isinstance(plan, Mapping):
        plan = plan_from_mapping(plan)

    errors: list[str] = []
    allowlisted_hosts = {host.lower().strip() for host in plan.allowlisted_hosts if host}

    if not plan.urls:
        errors.append("at least one public URL is required")

    for url in plan.urls:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path_and_query = f"{parsed.path}?{parsed.query}".lower()

        if parsed.scheme != "https":
            errors.append(f"URL must use https: {url}")
        if not host:
            errors.append(f"URL is missing a host: {url}")
            continue
        if host in _PRIVATE_HOSTS or host.startswith("10.") or host.startswith("192.168.") or host.startswith("172.16."):
            errors.append(f"private or local URL is not allowed: {url}")
        if host not in allowlisted_hosts:
            errors.append(f"host is not allowlisted: {host}")
        if parsed.username or parsed.password:
            errors.append(f"embedded credentials are not allowed: {url}")
        if any(hint in path_and_query for hint in _AUTH_HINTS):
            errors.append(f"private or authenticated path is not allowed: {url}")
        if any(hint in path_and_query for hint in _RAW_BODY_DOWNLOAD_ARCHIVE_HINTS):
            errors.append(f"raw body, download, or archive path is not allowed: {url}")

    if not plan.robots_prerequisites_confirmed:
        errors.append("robots prerequisites must be confirmed before rehearsal")
    if not plan.policy_prerequisites_confirmed:
        errors.append("policy prerequisites must be confirmed before rehearsal")
    if plan.live_network_execution:
        errors.append("live network execution flags are not allowed in rehearsal plans")
    if plan.authenticated_automation:
        errors.append("authenticated automation is not allowed in public rehearsal plans")
    if not plan.processor_handoff_intent.strip():
        errors.append("processor handoff intent is required")
    if not [condition for condition in plan.abort_conditions if condition.strip()]:
        errors.append("at least one abort condition is required")

    notes = plan.notes.lower()
    if any(claim in notes for claim in _REAL_RECRAWL_CLAIMS):
        errors.append("rehearsal notes must not claim that a real recrawl was performed")

    return errors


def assert_valid_public_recrawl_rehearsal_plan(plan: PublicRecrawlRehearsalPlan | Mapping[str, object]) -> None:
    """Raise ValueError when a public recrawl rehearsal plan is unsafe."""

    errors = validate_public_recrawl_rehearsal_plan(plan)
    if errors:
        raise ValueError("invalid public recrawl rehearsal plan: " + "; ".join(errors))
