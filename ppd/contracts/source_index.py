"""PP&D source-index record contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CrawlStatus(str, Enum):
    FETCHED = "fetched"
    NOT_MODIFIED = "not_modified"
    SKIPPED = "skipped"
    FAILED = "failed"


class SourcePageType(str, Enum):
    GUIDANCE = "guidance"
    FORM_INDEX = "form_index"
    FAQ = "faq"
    PORTAL_REFERENCE = "portal_reference"
    PUBLIC_SEARCH_REFERENCE = "public_search_reference"
    PDF = "pdf"
    OTHER = "other"


@dataclass(frozen=True)
class RedirectHop:
    from_url: str
    to_url: str
    status_code: int
    observed_at: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.from_url.startswith("https://"):
            errors.append("redirect from_url must be HTTPS")
        if not self.to_url.startswith("https://"):
            errors.append("redirect to_url must be HTTPS")
        if self.status_code not in {301, 302, 303, 307, 308}:
            errors.append("redirect status_code must be an HTTP redirect code")
        if not self.observed_at.endswith("Z"):
            errors.append("redirect observed_at must end in Z")
        return errors


@dataclass(frozen=True)
class SourceIndexRecord:
    id: str
    source_url: str
    canonical_url: str
    title: str
    bureau: str
    page_type: SourcePageType
    content_type: str
    first_seen_at: str
    last_seen_at: str
    crawl_status: CrawlStatus
    redirects: tuple[RedirectHop, ...] = field(default_factory=tuple)
    fetched_at: Optional[str] = None
    http_status: Optional[int] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: Optional[str] = None
    skip_reason: Optional[str] = None
    failure_reason: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("id is required")
        if not self.source_url.startswith("https://"):
            errors.append("source_url must be HTTPS")
        if not self.canonical_url.startswith("https://"):
            errors.append("canonical_url must be HTTPS")
        if not self.title.strip():
            errors.append("title is required")
        if not self.bureau.strip():
            errors.append("bureau is required")
        if "/" not in self.content_type:
            errors.append("content_type must be MIME-like")
        if not self.first_seen_at.endswith("Z"):
            errors.append("first_seen_at must end in Z")
        if not self.last_seen_at.endswith("Z"):
            errors.append("last_seen_at must end in Z")
        if self.fetched_at is not None and not self.fetched_at.endswith("Z"):
            errors.append("fetched_at must end in Z")

        for redirect in self.redirects:
            errors.extend(redirect.validate())
        if self.redirects:
            if self.redirects[0].from_url != self.source_url:
                errors.append("first redirect must start at source_url")
            if self.redirects[-1].to_url != self.canonical_url:
                errors.append("last redirect must end at canonical_url")
        elif self.source_url != self.canonical_url:
            errors.append("redirects are required when source_url differs from canonical_url")

        if self.crawl_status in {CrawlStatus.FETCHED, CrawlStatus.NOT_MODIFIED}:
            if not self.fetched_at:
                errors.append(f"{self.crawl_status.value} records require fetched_at")
            if self.http_status not in {200, 304}:
                errors.append(f"{self.crawl_status.value} records require http_status 200 or 304")
            if not (self.content_hash or "").startswith("sha256:"):
                errors.append(f"{self.crawl_status.value} records require sha256 content_hash")
        if self.crawl_status == CrawlStatus.NOT_MODIFIED and self.http_status != 304:
            errors.append("not_modified records require http_status 304")
        if self.crawl_status == CrawlStatus.SKIPPED and not (self.skip_reason or "").strip():
            errors.append("skipped records require skip_reason")
        if self.crawl_status == CrawlStatus.FAILED and not (self.failure_reason or "").strip():
            errors.append("failed records require failure_reason")
        return errors
