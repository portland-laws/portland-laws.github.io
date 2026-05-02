"""PP&D archive adapter contract for ipfs_datasets_py processors.

The PP&D crawler owns policy preflight: allowlist, robots, no-persist,
redaction, and private-path checks. Once a public URL passes that policy layer,
this contract records the planned handoff to the read-only website archival
backend under ipfs_datasets_py/ipfs_datasets_py/processors.

The records here are manifests only. They must not contain raw response bodies,
downloaded documents, browser traces, screenshots, credentials, or private
DevHub session state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional
from urllib.parse import urldefrag, urlparse


IPFS_DATASETS_PROCESSOR_BACKEND = "ipfs_datasets_py/ipfs_datasets_py/processors"
SHA256_PREFIX = "sha256:"
SHA256_HEX_LENGTH = 64


class ArchiveProcessorFamily(str, Enum):
    WEB_ARCHIVING = "web_archiving"
    LEGAL_SCRAPER = "legal_scraper"
    WEBSITE_GRAPHRAG = "website_graphrag"
    ADVANCED_GRAPHRAG = "advanced_graphrag"
    SPECIALIZED_SCRAPER = "specialized_scraper"
    PDF_NORMALIZATION = "pdf_normalization"


class ArchivePolicyDecision(str, Enum):
    ALLOW = "allow"
    REFUSE = "refuse"
    DEFER = "defer"


class ArchivePolicyReason(str, Enum):
    PUBLIC_PPD_ALLOWLISTED = "public_ppd_allowlisted"
    ROBOTS_ALLOWED = "robots_allowed"
    NO_PERSIST_APPROVED = "no_persist_approved"
    PRIVATE_DEVHUB_PATH = "private_devhub_path"
    NON_ALLOWLISTED_HOST = "non_allowlisted_host"
    ROBOTS_DISALLOWED = "robots_disallowed"
    RAW_BODY_PERSISTENCE_REQUESTED = "raw_body_persistence_requested"
    CREDENTIAL_OR_TRACE_RISK = "credential_or_trace_risk"
    POLICY_NOT_EVALUATED = "policy_not_evaluated"


@dataclass(frozen=True)
class ArchiveAdapterPolicyDecision:
    decision: ArchivePolicyDecision
    reasons: tuple[ArchivePolicyReason, ...]
    evaluated_at: str
    evaluator: str = "ppd.crawler.policy"
    notes: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.evaluated_at.endswith("Z"):
            errors.append("policy decision evaluated_at must be an ISO UTC timestamp ending in Z")
        if not self.evaluator.strip():
            errors.append("policy decision evaluator is required")
        if not self.reasons:
            errors.append("policy decision requires at least one reason")
        if self.decision == ArchivePolicyDecision.ALLOW:
            refusal_reasons = {
                ArchivePolicyReason.PRIVATE_DEVHUB_PATH,
                ArchivePolicyReason.NON_ALLOWLISTED_HOST,
                ArchivePolicyReason.ROBOTS_DISALLOWED,
                ArchivePolicyReason.RAW_BODY_PERSISTENCE_REQUESTED,
                ArchivePolicyReason.CREDENTIAL_OR_TRACE_RISK,
                ArchivePolicyReason.POLICY_NOT_EVALUATED,
            }
            present_refusal_reasons = refusal_reasons.intersection(self.reasons)
            if present_refusal_reasons:
                errors.append(f"allow decision cannot include refusal reasons: {sorted(reason.value for reason in present_refusal_reasons)}")
        if self.decision == ArchivePolicyDecision.REFUSE:
            blocking_reasons = {
                ArchivePolicyReason.PRIVATE_DEVHUB_PATH,
                ArchivePolicyReason.NON_ALLOWLISTED_HOST,
                ArchivePolicyReason.ROBOTS_DISALLOWED,
                ArchivePolicyReason.RAW_BODY_PERSISTENCE_REQUESTED,
                ArchivePolicyReason.CREDENTIAL_OR_TRACE_RISK,
            }
            if not blocking_reasons.intersection(self.reasons):
                errors.append("refuse decision requires at least one blocking policy reason")
        return errors


@dataclass(frozen=True)
class ArchiveProcessorIdentity:
    name: str
    version: str
    family: ArchiveProcessorFamily
    backend_path: str = IPFS_DATASETS_PROCESSOR_BACKEND

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("processor name is required")
        if not self.version.strip():
            errors.append(f"processor {self.name or ''} version is required")
        if self.backend_path != IPFS_DATASETS_PROCESSOR_BACKEND:
            errors.append(
                "processor backend_path must be "
                f"{IPFS_DATASETS_PROCESSOR_BACKEND}, got {self.backend_path}"
            )
        return errors


@dataclass(frozen=True)
class PpdArchiveAdapterRecord:
    id: str
    source_url: str
    canonical_url: str
    content_hash: str
    processor: ArchiveProcessorIdentity
    policy_decision: ArchiveAdapterPolicyDecision
    created_at: str
    archive_job_id: Optional[str] = None
    manifest_only: bool = True

    def should_invoke_processor(self) -> bool:
        return self.policy_decision.decision == ArchivePolicyDecision.ALLOW and not self.validate()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("archive adapter record id is required")
        errors.extend(_validate_https_url(self.source_url, "source_url"))
        errors.extend(_validate_https_url(self.canonical_url, "canonical_url"))
        errors.extend(_validate_content_hash(self.content_hash))
        if not self.created_at.endswith("Z"):
            errors.append("created_at must be an ISO UTC timestamp ending in Z")
        if not self.manifest_only:
            errors.append("archive adapter records must be manifest_only and must not persist raw bodies")
        if self.archive_job_id is not None and not self.archive_job_id.strip():
            errors.append("archive_job_id must not be blank when present")
        errors.extend(self.processor.validate())
        errors.extend(self.policy_decision.validate())
        return errors


@dataclass(frozen=True)
class PpdArchiveAdapterManifest:
    schema_version: int
    records: tuple[PpdArchiveAdapterRecord, ...]
    generated_at: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.schema_version != 1:
            errors.append("archive adapter manifest schema_version must be 1")
        if not self.generated_at.endswith("Z"):
            errors.append("archive adapter manifest generated_at must end in Z")
        if not self.records:
            errors.append("archive adapter manifest requires at least one record")
        seen_ids: set[str] = set()
        for record in self.records:
            if record.id in seen_ids:
                errors.append(f"duplicate archive adapter record id {record.id}")
            seen_ids.add(record.id)
            errors.extend(f"record {record.id}: {error}" for error in record.validate())
        return errors


def archive_adapter_manifest_from_dict(data: Mapping[str, Any]) -> PpdArchiveAdapterManifest:
    records = tuple(_record_from_dict(item) for item in data.get("records", ()))
    return PpdArchiveAdapterManifest(
        schema_version=int(data.get("schemaVersion", data.get("schema_version", 0))),
        generated_at=str(data.get("generatedAt", data.get("generated_at", ""))),
        records=records,
    )


def archive_adapter_record_from_dict(data: Mapping[str, Any]) -> PpdArchiveAdapterRecord:
    return _record_from_dict(data)


def _record_from_dict(data: Mapping[str, Any]) -> PpdArchiveAdapterRecord:
    processor_data = data.get("processor", {})
    policy_data = data.get("policyDecision", data.get("policy_decision", {}))
    if not isinstance(processor_data, Mapping):
        processor_data = {}
    if not isinstance(policy_data, Mapping):
        policy_data = {}

    return PpdArchiveAdapterRecord(
        id=str(data.get("id", "")),
        source_url=str(data.get("sourceUrl", data.get("source_url", ""))),
        canonical_url=str(data.get("canonicalUrl", data.get("canonical_url", ""))),
        content_hash=str(data.get("contentHash", data.get("content_hash", ""))),
        processor=ArchiveProcessorIdentity(
            name=str(processor_data.get("name", "")),
            version=str(processor_data.get("version", "")),
            family=ArchiveProcessorFamily(str(processor_data.get("family", "web_archiving"))),
            backend_path=str(processor_data.get("backendPath", processor_data.get("backend_path", IPFS_DATASETS_PROCESSOR_BACKEND))),
        ),
        policy_decision=ArchiveAdapterPolicyDecision(
            decision=ArchivePolicyDecision(str(policy_data.get("decision", "defer"))),
            reasons=tuple(ArchivePolicyReason(str(reason)) for reason in policy_data.get("reasons", ())),
            evaluated_at=str(policy_data.get("evaluatedAt", policy_data.get("evaluated_at", ""))),
            evaluator=str(policy_data.get("evaluator", "ppd.crawler.policy")),
            notes=policy_data.get("notes"),
        ),
        created_at=str(data.get("createdAt", data.get("created_at", ""))),
        archive_job_id=data.get("archiveJobId", data.get("archive_job_id")),
        manifest_only=bool(data.get("manifestOnly", data.get("manifest_only", True))),
    )


def _validate_https_url(value: str, field: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{field} must be an HTTPS URL with a hostname")
    if urldefrag(value).fragment:
        errors.append(f"{field} must not include a fragment")
    return errors


def _validate_content_hash(value: str) -> list[str]:
    if not value.startswith(SHA256_PREFIX):
        return ["content_hash must use sha256: format"]
    digest = value[len(SHA256_PREFIX) :]
    if len(digest) != SHA256_HEX_LENGTH:
        return ["content_hash sha256 digest must be 64 lowercase hex characters"]
    if any(character not in "0123456789abcdef" for character in digest):
        return ["content_hash sha256 digest must be lowercase hex"]
    return []
