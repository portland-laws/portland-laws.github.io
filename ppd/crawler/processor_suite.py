"""Deterministic PP&D crawl processor-suite integration helpers.

This module intentionally avoids live network access. It models the handoff between
public crawl inputs and downstream archive, document, PDF, requirement, and formal
logic evidence records so daemon validation can prove the contracts are reusable by
agents before any authenticated automation is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, Iterable


REQUIREMENT_KEYWORDS = ("shall", "must", "required", "requirement")


@dataclass(frozen=True)
class CrawlInput:
    url: str
    title: str
    media_type: str
    body: str
    captured_at: str


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _document_kind(item: CrawlInput) -> str:
    lowered_url = item.url.lower()
    lowered_media = item.media_type.lower()
    if lowered_url.endswith(".pdf") or "pdf" in lowered_media:
        return "pdf"
    return "html"


def _archive_path(item: CrawlInput, content_sha256: str) -> str:
    suffix = ".pdf" if _document_kind(item) == "pdf" else ".html"
    name = PurePosixPath(item.url).name or "index"
    stem = name.rsplit(".", 1)[0] or "index"
    return f"ppd/archive/{content_sha256[:2]}/{stem}-{content_sha256[:12]}{suffix}"


def _document_id(item: CrawlInput, content_sha256: str) -> str:
    return f"ppd-doc-{_digest(item.url + ':' + content_sha256)[:16]}"


def _extract_requirement_lines(body: str) -> list[str]:
    requirements: list[str] = []
    for raw_line in body.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        lowered = line.lower()
        if any(keyword in lowered for keyword in REQUIREMENT_KEYWORDS):
            requirements.append(line)
    return requirements


def build_processor_suite(inputs: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build deterministic downstream records for public PP&D crawl inputs."""

    manifests: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    pdf_metadata: list[dict[str, Any]] = []
    requirement_batches: list[dict[str, Any]] = []
    evidence_sources: list[dict[str, Any]] = []

    for raw in inputs:
        item = CrawlInput(
            url=str(raw["url"]),
            title=str(raw.get("title", "")),
            media_type=str(raw.get("media_type", "text/html")),
            body=str(raw.get("body", "")),
            captured_at=str(raw.get("captured_at", "1970-01-01T00:00:00Z")),
        )
        content_sha256 = _digest(item.body)
        archive_path = _archive_path(item, content_sha256)
        document_id = _document_id(item, content_sha256)
        kind = _document_kind(item)

        manifests.append(
            {
                "url": item.url,
                "captured_at": item.captured_at,
                "media_type": item.media_type,
                "sha256": content_sha256,
                "archive_path": archive_path,
            }
        )

        documents.append(
            {
                "document_id": document_id,
                "source_url": item.url,
                "title": item.title,
                "kind": kind,
                "archive_sha256": content_sha256,
                "archive_path": archive_path,
                "jurisdiction": "portland-or",
                "department": "ppd",
                "public_source": True,
            }
        )

        if kind == "pdf":
            pdf_metadata.append(
                {
                    "document_id": document_id,
                    "source_url": item.url,
                    "sha256": content_sha256,
                    "page_count": int(raw.get("page_count", 1)),
                    "title": item.title,
                }
            )

        requirements = _extract_requirement_lines(item.body)
        if requirements:
            batch_id = f"ppd-req-batch-{_digest(document_id)[:12]}"
            requirement_records: list[dict[str, Any]] = []
            for index, text in enumerate(requirements, start=1):
                evidence_id = f"{document_id}#evidence-{index}"
                requirement_id = f"{batch_id}-r{index}"
                requirement_records.append(
                    {
                        "requirement_id": requirement_id,
                        "text": text,
                        "source_evidence_id": evidence_id,
                    }
                )
                evidence_sources.append(
                    {
                        "evidence_id": evidence_id,
                        "document_id": document_id,
                        "source_url": item.url,
                        "archive_sha256": content_sha256,
                        "quote": text,
                    }
                )

            requirement_batches.append(
                {
                    "batch_id": batch_id,
                    "document_id": document_id,
                    "requirements": requirement_records,
                }
            )

    return {
        "archive_manifests": manifests,
        "normalized_documents": documents,
        "pdf_metadata": pdf_metadata,
        "requirement_batches": requirement_batches,
        "formal_logic_source_evidence": evidence_sources,
    }
