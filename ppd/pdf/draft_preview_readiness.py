"""Validation for reversible PDF draft preview readiness packets.

Readiness packets are commit-safe manifests for local preview planning only. They
must not contain private artifacts, raw documents, legal/permitting guarantees, or
claims that a live PDF fill/upload/submission/payment action has already run.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_REVIEWER_CHECKPOINTS = (
    "source_citation_review",
    "privacy_artifact_review",
    "preview_only_review",
    "control_state_review",
)

_CONSEQUENTIAL_CONTROL_WORDS = (
    "upload",
    "submit",
    "submission",
    "certify",
    "certification",
    "payment",
    "pay",
)

_PRIVATE_PATH_RE = re.compile(
    r"(?i)(?:\bfile://|\b/[Uu]sers/|\b/home/|\b/private/|\b/var/folders/|\b/tmp/|\b[A-Z]:\\|\b~[/\\])"
)
_RAW_PDF_TEXT_RE = re.compile(r"(?is)(?:^|[\s:=])%PDF-\d\.\d|JVBERi0")
_GUARANTEE_RE = re.compile(
    r"(?i)\b(guarantee[sd]?|ensure[sd]?|will be approved|approval is certain|permit will issue|"
    r"legally sufficient|legal advice|code compliant|complies with all codes|no risk of denial)\b"
)
_LIVE_EXECUTION_RE = re.compile(
    r"(?i)\b(filled|wrote|modified|executed|ran|uploaded|submitted|certified|paid|downloaded)\b"
    r".{0,80}\b(pdf|form|document|permit|application|payment)\b"
)
_PROMPT_KEY_RE = re.compile(r"(?i)(?:^|_)(prompt|instruction|agent_message|llm_request)(?:_|$)")
_CITATION_KEY_RE = re.compile(r"(?i)(citation|source_evidence|evidence_id|source_id)")
_DOWNLOADED_KEY_RE = re.compile(r"(?i)(downloaded|download_path|download_url|raw_download|downloaded_document)")
_RAW_DOCUMENT_KEY_RE = re.compile(r"(?i)(raw_pdf|pdf_bytes|document_bytes|raw_content|file_bytes)")


@dataclass(frozen=True)
class ReadinessViolation:
    """A deterministic readiness rejection with a stable code."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReadinessValidationResult:
    """Validation result for a reversible PDF draft preview readiness packet."""

    ready: bool
    violations: tuple[ReadinessViolation, ...]

    def require_ready(self) -> None:
        if not self.ready:
            details = "; ".join(f"{v.code} at {v.path}" for v in self.violations)
            raise ValueError(f"PDF draft preview readiness packet rejected: {details}")


def validate_pdf_draft_preview_readiness_packet(packet: Mapping[str, Any]) -> ReadinessValidationResult:
    """Return readiness violations for a reversible PDF draft preview packet.

    The validator is intentionally schema-tolerant so it can be used before the
    packet contract stabilizes. It recursively inspects mappings and sequences for
    unsafe artifacts and claims, then enforces a small set of required reviewer
    checkpoints.
    """

    violations: list[ReadinessViolation] = []

    if not isinstance(packet, Mapping):
        violations.append(
            ReadinessViolation(
                code="packet_not_mapping",
                path="$",
                message="Readiness packet must be a mapping.",
            )
        )
        return ReadinessValidationResult(False, tuple(violations))

    _scan_value(packet, "$", violations)
    _validate_prompt_citations(packet, violations)
    _validate_reviewer_checkpoints(packet, violations)
    _validate_consequential_controls(packet, violations)

    return ReadinessValidationResult(not violations, tuple(violations))


def assert_pdf_draft_preview_readiness_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when the packet is not safe for local preview readiness."""

    validate_pdf_draft_preview_readiness_packet(packet).require_ready()


def _scan_value(value: Any, path: str, violations: list[ReadinessViolation]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            lowered = key.lower()
            if _DOWNLOADED_KEY_RE.search(key) and _truthy_or_present(child):
                violations.append(
                    ReadinessViolation(
                        code="downloaded_document_present",
                        path=child_path,
                        message="Readiness packets must not include downloaded documents or download references.",
                    )
                )
            if _RAW_DOCUMENT_KEY_RE.search(key) and _truthy_or_present(child):
                violations.append(
                    ReadinessViolation(
                        code="raw_document_content_present",
                        path=child_path,
                        message="Readiness packets must not include raw PDF or document bytes/content.",
                    )
                )
            if lowered in {"source_kind", "source_type", "artifact_kind"} and str(child).lower() in {
                "downloaded_document",
                "downloaded_pdf",
                "raw_pdf",
                "private_file",
            }:
                violations.append(
                    ReadinessViolation(
                        code="unsafe_artifact_kind",
                        path=child_path,
                        message="Readiness packet references an unsafe artifact kind.",
                    )
                )
            _scan_value(child, child_path, violations)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_value(child, f"{path}[{index}]", violations)
        return

    if isinstance(value, (bytes, bytearray)):
        if bytes(value).startswith(b"%PDF"):
            violations.append(
                ReadinessViolation(
                    code="raw_pdf_content_present",
                    path=path,
                    message="Readiness packets must not contain raw PDF bytes.",
                )
            )
        return

    if isinstance(value, str):
        if _PRIVATE_PATH_RE.search(value):
            violations.append(
                ReadinessViolation(
                    code="private_file_path_present",
                    path=path,
                    message="Readiness packets must not contain local private file paths.",
                )
            )
        if _RAW_PDF_TEXT_RE.search(value):
            violations.append(
                ReadinessViolation(
                    code="raw_pdf_content_present",
                    path=path,
                    message="Readiness packets must not contain raw or encoded PDF content.",
                )
            )
        if _GUARANTEE_RE.search(value):
            violations.append(
                ReadinessViolation(
                    code="outcome_guarantee_present",
                    path=path,
                    message="Readiness packets must not guarantee legal or permitting outcomes.",
                )
            )
        if _LIVE_EXECUTION_RE.search(value):
            violations.append(
                ReadinessViolation(
                    code="live_pdf_fill_execution_claim_present",
                    path=path,
                    message="Readiness packets may describe preview plans, not live fill/upload/submission/payment execution.",
                )
            )


def _validate_prompt_citations(packet: Mapping[str, Any], violations: list[ReadinessViolation]) -> None:
    for path, key, value, parent in _walk_mapping_items(packet):
        if not _PROMPT_KEY_RE.search(key):
            continue
        if value in (None, "", [], {}):
            continue
        if not _mapping_has_citation(parent) and not _mapping_has_citation(packet):
            violations.append(
                ReadinessViolation(
                    code="uncited_prompt_present",
                    path=path,
                    message="Prompts or agent instructions in readiness packets must carry source citations.",
                )
            )


def _validate_reviewer_checkpoints(packet: Mapping[str, Any], violations: list[ReadinessViolation]) -> None:
    checkpoints = packet.get("reviewer_checkpoints")
    normalized: dict[str, str] = {}

    if isinstance(checkpoints, Mapping):
        for name, status in checkpoints.items():
            normalized[str(name)] = _checkpoint_status(status)
    elif isinstance(checkpoints, Sequence) and not isinstance(checkpoints, (str, bytes, bytearray)):
        for item in checkpoints:
            if isinstance(item, Mapping):
                name = item.get("name") or item.get("checkpoint") or item.get("id")
                if name:
                    normalized[str(name)] = _checkpoint_status(item.get("status", item.get("passed")))
            elif isinstance(item, str):
                normalized[item] = "passed"

    for checkpoint in REQUIRED_REVIEWER_CHECKPOINTS:
        if normalized.get(checkpoint) not in {"passed", "approved", "complete", "completed"}:
            violations.append(
                ReadinessViolation(
                    code="missing_reviewer_checkpoint",
                    path=f"$.reviewer_checkpoints.{checkpoint}",
                    message="Readiness packet is missing a required passed reviewer checkpoint.",
                )
            )


def _validate_consequential_controls(packet: Mapping[str, Any], violations: list[ReadinessViolation]) -> None:
    for path, key, value, parent in _walk_mapping_items(packet):
        if not any(word in key.lower() for word in _CONSEQUENTIAL_CONTROL_WORDS):
            continue
        if _control_enabled(value) or _control_enabled(parent):
            violations.append(
                ReadinessViolation(
                    code="consequential_control_enabled",
                    path=path,
                    message="Upload, submission, certification, and payment controls must be disabled for preview readiness.",
                )
            )


def _walk_mapping_items(value: Any, path: str = "$", parent: Mapping[str, Any] | None = None) -> Iterable[tuple[str, str, Any, Mapping[str, Any]]]:
    if isinstance(value, Mapping):
        current_parent = value if parent is None else parent
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            yield child_path, key, child, value
            yield from _walk_mapping_items(child, child_path, current_parent)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk_mapping_items(child, f"{path}[{index}]", parent)


def _mapping_has_citation(value: Mapping[str, Any]) -> bool:
    for key, child in value.items():
        if _CITATION_KEY_RE.search(str(key)) and _truthy_or_present(child):
            return True
    return False


def _checkpoint_status(value: Any) -> str:
    if value is True:
        return "passed"
    if isinstance(value, Mapping):
        return _checkpoint_status(value.get("status", value.get("passed")))
    return str(value).lower()


def _truthy_or_present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if value == "":
        return False
    if value == [] or value == {}:
        return False
    return True


def _control_enabled(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.lower() in {"enabled", "active", "clickable", "true"}
    if isinstance(value, Mapping):
        for key in ("enabled", "active", "clickable", "available"):
            if _control_enabled(value.get(key)):
                return True
    return False
