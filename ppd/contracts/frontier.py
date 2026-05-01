"""Fixture-only PP&D crawler frontier expansion contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FrontierContentType(str, Enum):
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    DOWNLOADABLE_DOCUMENT = "downloadable_document"
    EXTERNAL_SITE = "external_site"
    MAILTO = "mailto"
    PHONE = "phone"
    PORTAL_ACTION = "portal_action"
    OTHER = "other"


class FrontierLinkRelation(str, Enum):
    SAME_SITE = "same_site"
    DOWNLOAD = "download"
    EXTERNAL_REFERENCE = "external_reference"
    CONTACT = "contact"
    PORTAL_ACTION = "portal_action"
    UNKNOWN = "unknown"


class SkippedUrlReason(str, Enum):
    DUPLICATE_URL = "duplicate_url"
    DISALLOWED_DOMAIN = "disallowed_domain"
    UNSUPPORTED_SCHEME = "unsupported_scheme"
    FRAGMENT_ONLY = "fragment_only"
    PRIVATE_OR_AUTHENTICATED = "private_or_authenticated"
    NON_PUBLIC_ACTION = "non_public_action"
    CONTENT_TYPE_UNSUPPORTED = "content_type_unsupported"
    ROBOTS_NOT_PRECHECKED = "robots_not_prechecked"
    MALFORMED_URL = "malformed_url"


@dataclass(frozen=True)
class DiscoveredFrontierLink:
    id: str
    source_url: str
    raw_href: str
    normalized_url: str
    label: str
    content_type: FrontierContentType
    relation: FrontierLinkRelation
    allowed_domain: bool
    crawl_candidate: bool
    evidence_selector: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("discovered link id is required")
        if not self.source_url.startswith("https://"):
            errors.append(f"discovered link {self.id} source_url must be HTTPS")
        if not self.raw_href.strip():
            errors.append(f"discovered link {self.id} raw_href is required")
        if not self.normalized_url.strip():
            errors.append(f"discovered link {self.id} normalized_url is required")
        if not self.label.strip():
            errors.append(f"discovered link {self.id} label is required")
        if self.crawl_candidate and not self.allowed_domain:
            errors.append(f"discovered link {self.id} cannot be a crawl candidate outside allowed domains")
        if self.content_type in {FrontierContentType.MAILTO, FrontierContentType.PHONE, FrontierContentType.EXTERNAL_SITE} and self.crawl_candidate:
            errors.append(f"discovered link {self.id} contact/external links are not crawl candidates")
        return errors


@dataclass(frozen=True)
class SkippedFrontierUrl:
    id: str
    source_url: str
    raw_href: str
    normalized_url: str
    reason: SkippedUrlReason
    content_type: FrontierContentType = FrontierContentType.OTHER
    label: str = ""
    evidence_selector: Optional[str] = None
    note: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("skipped URL id is required")
        if not self.source_url.startswith("https://"):
            errors.append(f"skipped URL {self.id} source_url must be HTTPS")
        if not self.raw_href.strip():
            errors.append(f"skipped URL {self.id} raw_href is required")
        if not self.normalized_url.strip():
            errors.append(f"skipped URL {self.id} normalized_url is required")
        if self.reason == SkippedUrlReason.DISALLOWED_DOMAIN and self.content_type != FrontierContentType.EXTERNAL_SITE:
            errors.append(f"skipped URL {self.id} disallowed-domain skips should be classified as external_site")
        if self.reason == SkippedUrlReason.PRIVATE_OR_AUTHENTICATED and self.content_type != FrontierContentType.PORTAL_ACTION:
            errors.append(f"skipped URL {self.id} private/authenticated skips should be classified as portal_action")
        return errors


@dataclass(frozen=True)
class FrontierExpansionSummary:
    total_links_seen: int
    discovered_count: int
    skipped_count: int
    crawl_candidate_count: int
    content_type_counts: dict[str, int] = field(default_factory=dict)
    skipped_reason_counts: dict[str, int] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.total_links_seen != self.discovered_count + self.skipped_count:
            errors.append("total_links_seen must equal discovered_count plus skipped_count")
        if self.total_links_seen < 0 or self.discovered_count < 0 or self.skipped_count < 0:
            errors.append("frontier counts must be non-negative")
        if self.crawl_candidate_count < 0:
            errors.append("crawl_candidate_count must be non-negative")
        return errors


@dataclass(frozen=True)
class FrontierExpansion:
    fixture_id: str
    source_document_id: str
    source_url: str
    expanded_at: str
    allowed_domains: tuple[str, ...]
    discovered_links: tuple[DiscoveredFrontierLink, ...] = field(default_factory=tuple)
    skipped_urls: tuple[SkippedFrontierUrl, ...] = field(default_factory=tuple)
    summary: Optional[FrontierExpansionSummary] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.fixture_id.strip():
            errors.append("fixture_id is required")
        if not self.source_document_id.strip():
            errors.append("source_document_id is required")
        if not self.source_url.startswith("https://"):
            errors.append("source_url must be HTTPS")
        if not self.expanded_at.endswith("Z"):
            errors.append("expanded_at must end in Z")
        if not self.allowed_domains:
            errors.append("at least one allowed domain is required")

        discovered_ids: set[str] = set()
        skipped_ids: set[str] = set()
        for link in self.discovered_links:
            if link.id in discovered_ids:
                errors.append(f"duplicate discovered link id {link.id}")
            discovered_ids.add(link.id)
            errors.extend(link.validate())
        for skipped in self.skipped_urls:
            if skipped.id in skipped_ids:
                errors.append(f"duplicate skipped URL id {skipped.id}")
            skipped_ids.add(skipped.id)
            errors.extend(skipped.validate())

        if self.summary is None:
            errors.append("summary is required")
        else:
            errors.extend(self.summary.validate())
            if self.summary.discovered_count != len(self.discovered_links):
                errors.append("summary discovered_count does not match discovered_links")
            if self.summary.skipped_count != len(self.skipped_urls):
                errors.append("summary skipped_count does not match skipped_urls")
            crawl_candidates = sum(1 for link in self.discovered_links if link.crawl_candidate)
            if self.summary.crawl_candidate_count != crawl_candidates:
                errors.append("summary crawl_candidate_count does not match discovered_links")
        return errors
