"""Validation for release rollback drill packets.

The rollback drill packet is a commit-safe planning artifact. It may describe a
simulated rollback drill and the evidence needed to decide whether a rollback
would be safe, but it must not claim that a live rollback or publication already
happened, carry private automation artifacts, or enable consequential controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RollbackDrillValidationResult:
    """Structured validation outcome for a rollback drill packet."""

    ok: bool
    errors: tuple[str, ...]


class RollbackDrillValidationError(ValueError):
    """Raised when a rollback drill packet fails validation."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("release rollback drill packet failed validation: " + "; ".join(self.errors))


_CITATION_KEYS = ("citation", "citations", "source_evidence_ids", "source_refs", "evidence_refs")
_AFFECTED_ARTIFACT_KEYS = ("affected_artifacts", "affected_artifact_refs", "artifact_refs")
_REVIEWER_KEYS = ("reviewer_owners", "reviewers", "owners")
_SMOKE_KEYS = ("smoke_test_rerun_checklist", "smoke_tests", "rerun_checklist")

_CLAIM_KEYS = frozenset(("claims", "rollback_claims", "assertions", "findings"))
_PRIVATE_KEY_RE = re.compile(
    r"(^|[_-])(auth|cookie|credential|har|mfa|password|private|secret|session|screenshot|token|trace)([_-]|$)",
    re.IGNORECASE,
)
_LOCAL_PATH_RE = re.compile(
    r"(file://|~[/\\]|/(?:home|Users|private|tmp|var/folders)/|[A-Za-z]:\\(?:Users|Temp|Windows)\\)",
    re.IGNORECASE,
)
_RAW_REFERENCE_RE = re.compile(
    r"(raw[_ -]?(?:crawl|download|archive)|/raw/|/downloads?/|\.warc(?:\.gz)?\b|\.har\b|crawl[_-]?output|downloaded[_-]?documents)",
    re.IGNORECASE,
)
_LIVE_ROLLBACK_RE = re.compile(
    r"\b(?:performed|executed|completed|applied|ran|triggered)\s+(?:the\s+)?(?:live\s+)?rollback\b|\brollback\s+(?:was\s+)?(?:performed|executed|completed|applied)\b",
    re.IGNORECASE,
)
_PUBLICATION_RE = re.compile(
    r"\b(?:published|released|deployed|promoted)\s+(?:to\s+)?(?:production|live|public)\b|\bpublication\s+(?:completed|succeeded|is\s+live)\b",
    re.IGNORECASE,
)
_LEGAL_GUARANTEE_RE = re.compile(
    r"\b(?:guarantee[sd]?|assure[sd]?|ensure[sd]?|will)\b.{0,48}\b(?:approval|issuance|permit|inspection|legal\s+outcome|compliance)\b|\blegal\s+advice\b",
    re.IGNORECASE,
)
_CONSEQUENTIAL_ACTION_RE = re.compile(
    r"\b(?:cancel|certif(?:y|ication)|pay(?:ment)?|publish|release|schedule|submit|upload|withdraw)\b",
    re.IGNORECASE,
)

_MUTATION_FLAG_KEYS = frozenset(
    (
        "allow_artifact_mutation",
        "artifact_mutation_enabled",
        "can_mutate_artifacts",
        "commit_enabled",
        "delete_enabled",
        "mutation_enabled",
        "publish_enabled",
        "write_enabled",
    )
)
_LIVE_FLAG_KEYS = frozenset(("live_rollback", "live_publication", "published", "release_published", "rollback_executed"))


def validate_release_rollback_drill_packet(packet: Mapping[str, Any]) -> RollbackDrillValidationResult:
    """Validate a commit-safe release rollback drill packet.

    The accepted shape is intentionally dictionary-oriented so packets can be
    loaded from JSON, YAML, or daemon task payloads without a shared contract
    rewrite. Validation is strict about safety-sensitive fields and permissive
    about harmless metadata.
    """

    errors: list[str] = []

    if not isinstance(packet, Mapping):
        return RollbackDrillValidationResult(False, ("packet must be a mapping",))

    claims = _collect_claims(packet)
    if not claims:
        errors.append("missing rollback claims")
    for index, claim in enumerate(claims):
        label = f"rollback claim {index + 1}"
        if not _has_citation(claim):
            errors.append(f"{label} is uncited")
        if not _has_affected_artifact_reference(claim) and not _has_affected_artifact_reference(packet):
            errors.append(f"{label} is missing affected-artifact references")

    if not _has_affected_artifact_reference(packet) and not any(_has_affected_artifact_reference(claim) for claim in claims):
        errors.append("missing affected-artifact references")

    if not _has_reviewer_owner(packet):
        errors.append("missing reviewer owners")

    if not _has_smoke_test_rerun_checklist(packet):
        errors.append("missing smoke-test rerun checklist items")

    for path, key, value in _walk(packet):
        if isinstance(key, str) and _PRIVATE_KEY_RE.search(key):
            errors.append(f"private/session artifact key is not allowed at {path}")
        if isinstance(value, str):
            _validate_text_value(path, value, errors)
        if isinstance(key, str) and key in _MUTATION_FLAG_KEYS and value is True:
            errors.append(f"active artifact mutation flag is not allowed at {path}")
        if isinstance(key, str) and key in _LIVE_FLAG_KEYS and value is True:
            errors.append(f"live rollback or publication flag is not allowed at {path}")

    for path, control in _iter_controls(packet):
        if _control_is_enabled(control) and _control_is_consequential(control):
            errors.append(f"enabled consequential control is not allowed at {path}")

    return RollbackDrillValidationResult(not errors, tuple(dict.fromkeys(errors)))


def validate_release_rollback_drill_packet_or_raise(packet: Mapping[str, Any]) -> None:
    """Validate a packet and raise ``RollbackDrillValidationError`` on failure."""

    result = validate_release_rollback_drill_packet(packet)
    if not result.ok:
        raise RollbackDrillValidationError(result.errors)


def _collect_claims(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    claims: list[Mapping[str, Any]] = []
    for key in _CLAIM_KEYS:
        value = packet.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                if isinstance(item, Mapping):
                    claims.append(item)
                elif isinstance(item, str):
                    claims.append({"text": item})
        elif isinstance(value, Mapping):
            claims.append(value)
        elif isinstance(value, str):
            claims.append({"text": value})
    return claims


def _has_citation(value: Mapping[str, Any]) -> bool:
    return any(_non_empty(value.get(key)) for key in _CITATION_KEYS)


def _has_affected_artifact_reference(value: Mapping[str, Any]) -> bool:
    for key in _AFFECTED_ARTIFACT_KEYS:
        artifact_value = value.get(key)
        if isinstance(artifact_value, Sequence) and not isinstance(artifact_value, (str, bytes, bytearray)):
            if any(_artifact_ref_present(item) for item in artifact_value):
                return True
        elif _artifact_ref_present(artifact_value):
            return True
    return False


def _artifact_ref_present(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_non_empty(value.get(key)) for key in ("artifact_id", "artifact_ref", "id", "ref", "path"))
    return isinstance(value, str) and bool(value.strip())


def _has_reviewer_owner(packet: Mapping[str, Any]) -> bool:
    for key in _REVIEWER_KEYS:
        value = packet.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                if isinstance(item, Mapping) and any(_non_empty(item.get(owner_key)) for owner_key in ("owner", "name", "role", "reviewer")):
                    return True
                if isinstance(item, str) and item.strip():
                    return True
        elif isinstance(value, Mapping):
            if any(_non_empty(item) for item in value.values()):
                return True
        elif isinstance(value, str) and value.strip():
            return True
    return False


def _has_smoke_test_rerun_checklist(packet: Mapping[str, Any]) -> bool:
    for key in _SMOKE_KEYS:
        value = packet.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return any(_checklist_item_present(item) for item in value)
        if isinstance(value, Mapping):
            items = value.get("items") or value.get("checks") or value.get("checklist")
            if isinstance(items, Sequence) and not isinstance(items, (str, bytes, bytearray)):
                return any(_checklist_item_present(item) for item in items)
    return False


def _checklist_item_present(item: Any) -> bool:
    if isinstance(item, Mapping):
        text = " ".join(str(item.get(key, "")) for key in ("id", "name", "description", "command", "expected_result"))
        return bool(text.strip()) and re.search(r"\b(smoke|rerun|re-run|test|check)\b", text, re.IGNORECASE) is not None
    if isinstance(item, str):
        return bool(item.strip()) and re.search(r"\b(smoke|rerun|re-run|test|check)\b", item, re.IGNORECASE) is not None
    return False


def _walk(value: Any, path: str = "$", key: str | None = None) -> Iterable[tuple[str, str | None, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_name = str(child_key)
            yield from _walk(child_value, f"{path}.{child_name}", child_name)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", None)


def _validate_text_value(path: str, value: str, errors: list[str]) -> None:
    if _LOCAL_PATH_RE.search(value):
        errors.append(f"local private path is not allowed at {path}")
    if _RAW_REFERENCE_RE.search(value):
        errors.append(f"raw crawl/download/archive reference is not allowed at {path}")
    if _LIVE_ROLLBACK_RE.search(value) or _PUBLICATION_RE.search(value):
        errors.append(f"live rollback or publication claim is not allowed at {path}")
    if _LEGAL_GUARANTEE_RE.search(value):
        errors.append(f"legal or permitting outcome guarantee is not allowed at {path}")


def _iter_controls(packet: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for path, key, value in _walk(packet):
        if key in ("controls", "action_controls", "consequential_controls"):
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                for index, item in enumerate(value):
                    if isinstance(item, Mapping):
                        yield f"{path}[{index}]", item
            elif isinstance(value, Mapping):
                yield path, value


def _control_is_enabled(control: Mapping[str, Any]) -> bool:
    return any(control.get(key) is True for key in ("enabled", "active", "default_on", "armed"))


def _control_is_consequential(control: Mapping[str, Any]) -> bool:
    text = " ".join(str(control.get(key, "")) for key in ("action", "action_type", "id", "label", "name", "type"))
    return _CONSEQUENTIAL_ACTION_RE.search(text) is not None


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence):
        return len(value) > 0
    return True
