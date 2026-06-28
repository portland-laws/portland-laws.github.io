"""Whole-site archival planning for public Portland PP&D sources.

The objects in this module describe how the PP&D daemon should plan an archival
run against public sources. They are side-effect free: importing or validating
this module never fetches a URL, launches a browser, stores response bodies, or
touches user-specific DevHub state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from ppd.contracts.archive_adapter import IPFS_DATASETS_PROCESSOR_BACKEND


PUBLIC_PPD_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PRIVATE_PATH_MARKERS = (
    "/account",
    "/accounts",
    "/application",
    "/applications",
    "/cart",
    "/dashboard",
    "/document",
    "/documents/private",
    "/inspection",
    "/inspections",
    "/login",
    "/logout",
    "/my",
    "/payment",
    "/payments",
    "/permit",
    "/permits",
    "/register",
    "/secure",
    "/signin",
    "/sign-in",
    "/upload",
    "/uploads",
)

FORBIDDEN_RUNTIME_ARTIFACT_LABELS = frozenset(
    {
        "response_body",
        "downloaded_document_bytes",
        "browser_trace",
        "visual_capture",
        "authenticated_browser_state",
        "credential_material",
        "financial_material",
    }
)


class ArchivePhase(str, Enum):
    DISCOVER = "discover"
    POLICY_PREFLIGHT = "policy_preflight"
    PROCESSOR_HANDOFF = "processor_handoff"
    NORMALIZE_HTML = "normalize_html"
    NORMALIZE_PDF = "normalize_pdf"
    BUILD_LINK_GRAPH = "build_link_graph"
    EXTRACT_REQUIREMENTS = "extract_requirements"
    FORMAL_LOGIC_HANDOFF = "formal_logic_handoff"
    CHANGE_MONITORING = "change_monitoring"


@dataclass(frozen=True)
class ArchiveSeed:
    id: str
    url: str
    purpose: str
    expected_content_types: tuple[str, ...] = ("text/html",)
    public_only: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("seed id is required")
        if not self.purpose.strip():
            errors.append(f"seed {self.id or '<missing>'} purpose is required")
        parsed = urlparse(self.url)
        if parsed.scheme != "https":
            errors.append(f"seed {self.id or '<missing>'} must use https")
        if parsed.hostname not in PUBLIC_PPD_HOSTS:
            errors.append(f"seed {self.id or '<missing>'} host is not PP&D allowlisted")
        if parsed.hostname == "devhub.portlandoregon.gov" and _looks_private_path(parsed.path):
            errors.append(f"seed {self.id or '<missing>'} must not target private DevHub paths")
        if not self.public_only:
            errors.append(f"seed {self.id or '<missing>'} must be public_only")
        if not self.expected_content_types:
            errors.append(f"seed {self.id or '<missing>'} requires expected content types")
        return errors


@dataclass(frozen=True)
class ProcessorCapability:
    id: str
    module: str
    operation: str
    input_kind: str
    output_kind: str
    backend_path: str = IPFS_DATASETS_PROCESSOR_BACKEND

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("processor capability id is required")
        if self.backend_path != IPFS_DATASETS_PROCESSOR_BACKEND:
            errors.append(f"processor backend_path must be {IPFS_DATASETS_PROCESSOR_BACKEND}")
        if not self.module.startswith("ipfs_datasets_py.processors."):
            errors.append(f"processor capability {self.id or '<missing>'} must use ipfs_datasets_py processors")
        if not self.operation.strip():
            errors.append(f"processor capability {self.id or '<missing>'} operation is required")
        if not self.input_kind.strip() or not self.output_kind.strip():
            errors.append(f"processor capability {self.id or '<missing>'} input and output kinds are required")
        return errors


@dataclass(frozen=True)
class ArchivePolicy:
    allowlisted_hosts: tuple[str, ...]
    robots_preflight_required: bool = True
    public_only: bool = True
    manifest_only: bool = True
    stores_raw_outputs: bool = False
    stores_private_runtime_artifacts: bool = False
    launches_browser: bool = False
    live_network_enabled_by_default: bool = False
    max_pages_per_run: int = 5000
    crawl_delay_floor_seconds: float = 1.0
    skipped_artifact_labels: tuple[str, ...] = tuple(sorted(FORBIDDEN_RUNTIME_ARTIFACT_LABELS))

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not set(self.allowlisted_hosts).issubset(PUBLIC_PPD_HOSTS):
            errors.append("archive policy allowlisted_hosts must stay inside public PP&D hosts")
        if not self.robots_preflight_required:
            errors.append("archive policy requires robots preflight")
        if not self.public_only:
            errors.append("archive policy must be public_only")
        if not self.manifest_only:
            errors.append("archive policy must be manifest_only")
        if self.stores_raw_outputs:
            errors.append("archive policy must not store raw outputs")
        if self.stores_private_runtime_artifacts:
            errors.append("archive policy must not store private runtime artifacts")
        if self.launches_browser:
            errors.append("archive policy must not launch a browser")
        if self.live_network_enabled_by_default:
            errors.append("live network access must be disabled by default")
        if self.max_pages_per_run < 1:
            errors.append("archive policy max_pages_per_run must be positive")
        if self.crawl_delay_floor_seconds <= 0:
            errors.append("archive policy crawl_delay_floor_seconds must be positive")
        missing = FORBIDDEN_RUNTIME_ARTIFACT_LABELS.difference(self.skipped_artifact_labels)
        if missing:
            errors.append(f"archive policy skipped artifact labels missing: {sorted(missing)}")
        return errors


@dataclass(frozen=True)
class ArchiveWorkQueue:
    frontier_store: str
    manifest_store: str
    accepted_content_types: tuple[str, ...]
    phases: tuple[ArchivePhase, ...]
    retry_limit: int = 2
    worker_timeout_seconds: int = 300

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.frontier_store.startswith("ppd/"):
            errors.append("frontier_store must stay under ppd/")
        if not self.manifest_store.startswith("ppd/"):
            errors.append("manifest_store must stay under ppd/")
        if not self.accepted_content_types:
            errors.append("work queue requires accepted content types")
        required = {
            ArchivePhase.DISCOVER,
            ArchivePhase.POLICY_PREFLIGHT,
            ArchivePhase.PROCESSOR_HANDOFF,
            ArchivePhase.EXTRACT_REQUIREMENTS,
            ArchivePhase.FORMAL_LOGIC_HANDOFF,
        }
        missing = required.difference(self.phases)
        if missing:
            errors.append(f"work queue missing required phases: {sorted(phase.value for phase in missing)}")
        if self.retry_limit < 0:
            errors.append("work queue retry_limit must not be negative")
        if self.worker_timeout_seconds < 30:
            errors.append("work queue worker_timeout_seconds must be at least 30")
        return errors


@dataclass(frozen=True)
class WholeSiteArchivePlan:
    plan_id: str
    source_authority: str
    seeds: tuple[ArchiveSeed, ...]
    policy: ArchivePolicy
    processor_capabilities: tuple[ProcessorCapability, ...]
    work_queue: ArchiveWorkQueue
    downstream_outputs: tuple[str, ...]
    citation_urls: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.plan_id.strip():
            errors.append("plan_id is required")
        if self.source_authority != "City of Portland Permitting & Development public sources":
            errors.append("source_authority must name PP&D public sources")
        if len(self.seeds) < 5:
            errors.append("whole-site plan requires at least five public seeds")
        seen_seed_ids: set[str] = set()
        for seed in self.seeds:
            if seed.id in seen_seed_ids:
                errors.append(f"duplicate seed id {seed.id}")
            seen_seed_ids.add(seed.id)
            errors.extend(seed.validate())
        errors.extend(self.policy.validate())
        if len(self.processor_capabilities) < 4:
            errors.append("whole-site plan requires multiple processor capabilities")
        seen_capability_ids: set[str] = set()
        for capability in self.processor_capabilities:
            if capability.id in seen_capability_ids:
                errors.append(f"duplicate processor capability id {capability.id}")
            seen_capability_ids.add(capability.id)
            errors.extend(capability.validate())
        errors.extend(self.work_queue.validate())
        required_outputs = {
            "processor_archive_manifest",
            "normalized_public_document_index",
            "requirement_node_batches",
            "formal_logic_guardrail_bundle",
            "playwright_draft_planning_hints",
        }
        missing_outputs = required_outputs.difference(self.downstream_outputs)
        if missing_outputs:
            errors.append(f"whole-site plan missing downstream outputs: {sorted(missing_outputs)}")
        for url in self.citation_urls:
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in PUBLIC_PPD_HOSTS:
                errors.append(f"citation URL is not a public PP&D URL: {url}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "planId": self.plan_id,
            "sourceAuthority": self.source_authority,
            "seeds": [
                {
                    "id": seed.id,
                    "url": seed.url,
                    "purpose": seed.purpose,
                    "expectedContentTypes": list(seed.expected_content_types),
                    "publicOnly": seed.public_only,
                }
                for seed in self.seeds
            ],
            "policy": {
                "allowlistedHosts": list(self.policy.allowlisted_hosts),
                "robotsPreflightRequired": self.policy.robots_preflight_required,
                "publicOnly": self.policy.public_only,
                "manifestOnly": self.policy.manifest_only,
                "storesRawOutputs": self.policy.stores_raw_outputs,
                "storesPrivateRuntimeArtifacts": self.policy.stores_private_runtime_artifacts,
                "launchesBrowser": self.policy.launches_browser,
                "liveNetworkEnabledByDefault": self.policy.live_network_enabled_by_default,
                "maxPagesPerRun": self.policy.max_pages_per_run,
                "crawlDelayFloorSeconds": self.policy.crawl_delay_floor_seconds,
                "skippedArtifactLabels": list(self.policy.skipped_artifact_labels),
            },
            "processorCapabilities": [
                {
                    "id": capability.id,
                    "module": capability.module,
                    "operation": capability.operation,
                    "inputKind": capability.input_kind,
                    "outputKind": capability.output_kind,
                    "backendPath": capability.backend_path,
                }
                for capability in self.processor_capabilities
            ],
            "workQueue": {
                "frontierStore": self.work_queue.frontier_store,
                "manifestStore": self.work_queue.manifest_store,
                "acceptedContentTypes": list(self.work_queue.accepted_content_types),
                "phases": [phase.value for phase in self.work_queue.phases],
                "retryLimit": self.work_queue.retry_limit,
                "workerTimeoutSeconds": self.work_queue.worker_timeout_seconds,
            },
            "downstreamOutputs": list(self.downstream_outputs),
            "citationUrls": list(self.citation_urls),
        }


def build_default_whole_site_archive_plan() -> WholeSiteArchivePlan:
    """Return the default PP&D public archival plan used by supervisor tranches."""

    seeds = (
        ArchiveSeed(
            id="ppd-home",
            url="https://www.portland.gov/ppd",
            purpose="PP&D public landing page and primary navigation discovery.",
        ),
        ArchiveSeed(
            id="ppd-documents",
            url="https://www.portland.gov/ppd/documents",
            purpose="Public forms, handouts, checklists, and PDF discovery.",
            expected_content_types=("text/html", "application/pdf"),
        ),
        ArchiveSeed(
            id="ppd-building-start-guide",
            url="https://www.portland.gov/ppd/get-permit",
            purpose="Building permit start-guide process discovery.",
        ),
        ArchiveSeed(
            id="ppd-online-tools",
            url="https://www.portland.gov/ppd/how-use-online-permitting-tools",
            purpose="Public DevHub usage guidance and portal handoff discovery.",
        ),
        ArchiveSeed(
            id="ppd-devhub-faqs",
            url="https://www.portland.gov/ppd/devhub-faqs",
            purpose="Public Development Hub PDX FAQ discovery.",
        ),
        ArchiveSeed(
            id="devhub-public-entry",
            url="https://devhub.portlandoregon.gov/",
            purpose="Unauthenticated public portal landing metadata only.",
        ),
        ArchiveSeed(
            id="ppd-zoning-permits",
            url="https://www.portland.gov/ppd/zoning-land-use/zoning-permits",
            purpose="Zoning permit process and public form discovery.",
            expected_content_types=("text/html", "application/pdf"),
        ),
    )
    capabilities = (
        ProcessorCapability(
            id="processor-web-archive",
            module="ipfs_datasets_py.processors.web_archiving",
            operation="capture_public_url_manifest",
            input_kind="allowlisted_public_url",
            output_kind="processor_archive_manifest",
        ),
        ProcessorCapability(
            id="processor-legal-scraper",
            module="ipfs_datasets_py.processors.legal_scrapers.parallel_web_archiver",
            operation="legal_archive_url",
            input_kind="public_guidance_or_rule_url",
            output_kind="source_linked_legal_corpus_record",
        ),
        ProcessorCapability(
            id="processor-pdf-normalizer",
            module="ipfs_datasets_py.processors.pdf",
            operation="normalize_public_pdf_metadata",
            input_kind="public_pdf_reference",
            output_kind="normalized_public_document_metadata",
        ),
        ProcessorCapability(
            id="processor-graphrag",
            module="ipfs_datasets_py.processors.website_graphrag",
            operation="build_public_link_graph",
            input_kind="processor_archive_manifest",
            output_kind="normalized_link_graph",
        ),
    )
    policy = ArchivePolicy(allowlisted_hosts=tuple(sorted(PUBLIC_PPD_HOSTS)))
    queue = ArchiveWorkQueue(
        frontier_store="ppd/data/manifests/public-frontier-checkpoints",
        manifest_store="ppd/data/manifests/processor-archive-manifests",
        accepted_content_types=("text/html", "application/pdf"),
        phases=tuple(ArchivePhase),
        retry_limit=2,
        worker_timeout_seconds=300,
    )
    return WholeSiteArchivePlan(
        plan_id="ppd-whole-site-archive-v2",
        source_authority="City of Portland Permitting & Development public sources",
        seeds=seeds,
        policy=policy,
        processor_capabilities=capabilities,
        work_queue=queue,
        downstream_outputs=(
            "processor_archive_manifest",
            "normalized_public_document_index",
            "requirement_node_batches",
            "formal_logic_guardrail_bundle",
            "playwright_draft_planning_hints",
            "public_change_monitoring_report",
        ),
        citation_urls=(
            "https://www.portland.gov/ppd",
            "https://www.portland.gov/ppd/documents",
            "https://devhub.portlandoregon.gov/",
        ),
    )


def validate_whole_site_archive_plan(plan: WholeSiteArchivePlan) -> list[str]:
    return plan.validate()


def _looks_private_path(path: str) -> bool:
    normalized = "/" + path.strip("/").lower()
    return any(normalized == marker or normalized.startswith(f"{marker}/") for marker in PRIVATE_PATH_MARKERS)
