"""Deterministic archive artifact retention validation for PP&D.

This module intentionally performs no filesystem, network, or processor access. It
validates caller-provided artifact descriptors so crawl and archive planning code
can decide whether proposed outputs are safe to retain in committed/local PP&D
artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


_ALLOWED_ARTIFACT_TYPES = frozenset(
    {
        "archive_manifest",
        "citation_index",
        "checksum_manifest",
        "extraction_report",
        "metadata_manifest",
        "normalized_document",
        "processor_handoff_manifest",
        "source_registry",
    }
)

_FORBIDDEN_ARTIFACT_TYPES = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookie_jar",
        "credentials",
        "devhub_private_capture",
        "downloaded_document",
        "har",
        "payment_detail",
        "private_upload",
        "raw_body",
        "raw_html",
        "raw_pdf",
        "screenshot",
        "session_state",
        "warc",
    }
)

_FORBIDDEN_PATH_FRAGMENTS = (
    "/.daemon/",
    "/auth/",
    "/auth_state/",
    "/cookies/",
    "/credentials/",
    "/downloads/",
    "/har/",
    "/raw/",
    "/screenshots/",
    "/session/",
    "/traces/",
)

_PRIVATE_CLASSIFICATIONS = frozenset(
    {
        "authenticated",
        "credential",
        "financial",
        "payment",
        "private",
        "private_devhub",
        "session_secret",
        "user_private",
    }
)


@dataclass(frozen=True)
class RetentionFinding:
    """A deterministic validation finding for one proposed archive artifact."""

    artifact_id: str
    code: str
    message: str


@dataclass(frozen=True)
class RetentionValidationResult:
    """Result returned by :func:`validate_archive_artifact_retention`."""

    ok: bool
    findings: tuple[RetentionFinding, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "ok": self.ok,
            "findings": [
                {
                    "artifact_id": finding.artifact_id,
                    "code": finding.code,
                    "message": finding.message,
                }
                for finding in self.findings
            ],
        }


def validate_archive_artifact_retention(
    artifacts: Iterable[Mapping[str, Any]],
    *,
    allowed_artifact_types: Sequence[str] | None = None,
) -> RetentionValidationResult:
    """Validate whether proposed archive artifacts are safe to retain.

    The validator is deliberately conservative. It permits metadata-oriented PP&D
    archive outputs and rejects raw bodies, authenticated/session material,
    payment/private data, and path locations that commonly hold non-committable
    browser or crawl artifacts. The function is pure: it only inspects the
    supplied descriptors and never checks whether referenced paths exist.
    """

    allowed_types = frozenset(allowed_artifact_types or _ALLOWED_ARTIFACT_TYPES)
    findings: list[RetentionFinding] = []

    for index, artifact in enumerate(artifacts):
        artifact_id = _artifact_id(artifact, index)
        artifact_type = _normalized_text(
            artifact.get("artifact_type")
            or artifact.get("type")
            or artifact.get("kind")
            or artifact.get("role")
        )
        path = _normalized_path(artifact.get("path") or artifact.get("artifact_ref") or "")
        privacy_classification = _normalized_text(artifact.get("privacy_classification"))
        auth_scope = _normalized_text(artifact.get("auth_scope") or artifact.get("source_scope"))

        if not artifact_type:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="missing_artifact_type",
                    message="artifact descriptor must include an artifact_type/type/kind/role",
                )
            )
        elif artifact_type in _FORBIDDEN_ARTIFACT_TYPES:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="forbidden_artifact_type",
                    message=f"{artifact_type} artifacts must not be retained by PP&D archive helpers",
                )
            )
        elif artifact_type not in allowed_types:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="unsupported_artifact_type",
                    message=f"{artifact_type} is not in the allowed retention artifact set",
                )
            )

        if _truthy(artifact.get("contains_raw_body")):
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="raw_body_retained",
                    message="artifact descriptor says a raw response body would be retained",
                )
            )

        if artifact.get("no_raw_body_persisted") is False:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="raw_body_not_excluded",
                    message="no_raw_body_persisted must not be false for retained archive artifacts",
                )
            )

        if privacy_classification in _PRIVATE_CLASSIFICATIONS:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="private_privacy_classification",
                    message=f"{privacy_classification} artifacts are not commit-safe archive retention outputs",
                )
            )

        if auth_scope in {"authenticated", "account", "private", "user"}:
            findings.append(
                RetentionFinding(
                    artifact_id=artifact_id,
                    code="authenticated_scope_retained",
                    message=f"{auth_scope} scoped artifacts must not be retained by the public archive helper",
                )
            )

        for fragment in _FORBIDDEN_PATH_FRAGMENTS:
            if fragment in path:
                findings.append(
                    RetentionFinding(
                        artifact_id=artifact_id,
                        code="forbidden_path_fragment",
                        message=f"artifact path contains non-retained location fragment {fragment}",
                    )
                )
                break

    ordered_findings = tuple(
        sorted(findings, key=lambda finding: (finding.artifact_id, finding.code, finding.message))
    )
    return RetentionValidationResult(ok=not ordered_findings, findings=ordered_findings)


def _artifact_id(artifact: Mapping[str, Any], index: int) -> str:
    value = artifact.get("artifact_id") or artifact.get("id") or artifact.get("manifest_id")
    if value is None or str(value).strip() == "":
        return f"artifact[{index}]"
    return str(value).strip()


def _normalized_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _normalized_path(value: Any) -> str:
    if value is None:
        return ""
    path = str(value).strip().replace("\\", "/")
    if path and not path.startswith("/"):
        path = f"/{path}"
    if path and not path.endswith("/"):
        path = f"{path}/" if path.rsplit("/", 1)[-1] == "" else path
    return path.lower()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
