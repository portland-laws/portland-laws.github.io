"""Validation for release rollback drill outcome review packets.

Outcome review packets are fixture-only governance artifacts. They may summarize
simulated rollback observations and follow-up work, but they must remain cited,
review-owned, artifact-scoped, and free of private runtime material or active
release controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RollbackDrillOutcomeReviewValidationResult:
    """Structured validation outcome for an outcome review packet."""

    ok: bool
    errors: tuple[str, ...]


class RollbackDrillOutcomeReviewValidationError(ValueError):
    """Raised when a rollback drill outcome review packet fails validation."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("release rollback drill outcome review packet failed validation: " + "; ".join(self.errors))


_PACKET_TYPE = "fixture_first_release_rollback_drill_outcome_review"
_OBSERVATION_KEYS = ("simulated_rollback_observations", "rollback_observations", "observations")
_THRESHOLD_KEYS = ("decision_thresholds", "rollback_decision_thresholds", "thresholds")
_ARTIFACT_KEYS = ("affected_artifact_references", "affected_artifact_refs", "affected_artifacts", "artifact_refs")
_REVIEWER_KEYS = ("reviewer_owner_fields", "reviewer_owners", "reviewers", "owners")
_FOLLOW_UP_KEYS = ("follow_up_work_items", "follow_ups", "work_items")
_CITATION_KEYS = ("citation", "citations", "source_evidence_ids", "source_refs", "evidence_refs")
_PRIVATE_KEY_TOKENS = ("auth", "browser", "cookie", "credential", "har", "mfa", "password", "private", "secret", "session", "screenshot", "storage", "token", "trace")
_PRIVATE_VALUE_TOKENS = ("auth_state", "browser_state", "cookie", "credential", "password", "private artifact", "secret", "session_state", "storage_state", "token", "trace.zip")
_LOCAL_PATH_TOKENS = ("file://", "~/", "~\\", "/home/", "/Users/", "/private/", "/root/", "/tmp/", "/var/folders/", "c:\\users\\")
_RAW_KEY_TOKENS = ("archive_artifact_ref", "archive_path", "archive_url", "download_path", "download_url", "raw_archive_ref", "raw_body", "raw_crawl", "raw_download_ref")
_RAW_VALUE_TOKENS = ("raw crawl", "raw_crawl", "raw download", "raw_download", "raw archive", "raw_archive", "/raw/", "/download/", "/downloads/", "/archive/", "/archives/", ".warc", ".har", "crawl_output", "downloaded_documents")
_MUTATION_FLAG_KEYS = {"active_artifact_mutation", "allow_artifact_mutation", "artifact_mutation_enabled", "can_mutate_artifacts", "commit_enabled", "delete_enabled", "mutation_allowed", "mutation_enabled", "publish_enabled", "write_enabled"}
_LIVE_FLAG_KEYS = {"active_rollback", "active_rollback_started", "live_publication", "live_rollback", "publication_performed", "published", "release_published", "rollback_executed"}


def validate_release_rollback_drill_outcome_review_packet(packet: Mapping[str, Any]) -> RollbackDrillOutcomeReviewValidationResult:
    """Validate a fixture-only release rollback drill outcome review packet."""

    if not isinstance(packet, Mapping):
        return RollbackDrillOutcomeReviewValidationResult(False, ("packet must be a mapping",))

    errors: list[str] = []
    if packet.get("packet_type") != _PACKET_TYPE:
        errors.append("packet_type must be fixture_first_release_rollback_drill_outcome_review")
    if packet.get("mode") != "simulated_fixture_only":
        errors.append("mode must be simulated_fixture_only")

    observations = _first_mapping_sequence(packet, _OBSERVATION_KEYS)
    if not observations:
        errors.append("missing simulated rollback observations")
    for index, observation in enumerate(observations):
        if not _has_citation(observation):
            errors.append(f"simulated rollback observation {index + 1} is uncited")
        if not _non_empty(observation.get("finding") or observation.get("summary") or observation.get("observation")):
            errors.append(f"simulated rollback observation {index + 1} is missing a finding")

    thresholds = _first_mapping_sequence(packet, _THRESHOLD_KEYS)
    if not thresholds:
        errors.append("missing decision thresholds")
    for index, threshold in enumerate(thresholds):
        if not _non_empty(threshold.get("condition")):
            errors.append(f"decision threshold {index + 1} is missing condition")
        if not _non_empty(threshold.get("decision")):
            errors.append(f"decision threshold {index + 1} is missing decision")
        if not _has_citation(threshold):
            errors.append(f"decision threshold {index + 1} is uncited")

    artifacts = _first_mapping_sequence(packet, _ARTIFACT_KEYS)
    if not artifacts:
        errors.append("missing affected-artifact references")
    for index, artifact in enumerate(artifacts):
        artifact_ref = artifact.get("artifact_id") or artifact.get("artifact_ref") or artifact.get("artifact_reference") or artifact.get("ref")
        if not _non_empty(artifact_ref):
            errors.append(f"affected artifact reference {index + 1} is missing artifact reference")
        if not _has_citation(artifact):
            errors.append(f"affected artifact reference {index + 1} is uncited")
        if artifact.get("mutation_allowed") is not False:
            errors.append(f"affected artifact reference {index + 1} must set mutation_allowed false")
        if artifact.get("active_artifact_mutation") is True:
            errors.append(f"affected artifact reference {index + 1} has active artifact mutation enabled")

    if not _has_reviewer_owner_fields(packet):
        errors.append("missing reviewer owners")

    follow_ups = _first_mapping_sequence(packet, _FOLLOW_UP_KEYS)
    if not follow_ups:
        errors.append("missing follow-up work items")
    for index, item in enumerate(follow_ups):
        if not _non_empty(item.get("owner") or item.get("reviewer_owner")):
            errors.append(f"follow-up work item {index + 1} is missing owner")
        if not _non_empty(item.get("description") or item.get("summary")):
            errors.append(f"follow-up work item {index + 1} is missing description")
        if not _non_empty(item.get("source_observation") or item.get("source_observation_id") or item.get("citation")):
            errors.append(f"follow-up work item {index + 1} is missing source observation or citation")

    for path, key, value in _walk(packet):
        key_text = str(key or "")
        if _contains_token(key_text, _PRIVATE_KEY_TOKENS):
            errors.append(f"private/session artifact key is not allowed at {path}")
        if _contains_token(key_text, _RAW_KEY_TOKENS):
            errors.append(f"raw crawl/download/archive reference key is not allowed at {path}")
        if isinstance(value, str):
            _validate_text_value(path, value, errors)
        if key_text in _MUTATION_FLAG_KEYS and value is True:
            errors.append(f"active artifact mutation flag is not allowed at {path}")
        if key_text in _LIVE_FLAG_KEYS and value is True:
            errors.append(f"live rollback or publication flag is not allowed at {path}")

    for path, control in _iter_controls(packet):
        if _control_is_enabled(control) and _control_is_consequential(control):
            errors.append(f"enabled consequential control is not allowed at {path}")

    return RollbackDrillOutcomeReviewValidationResult(not errors, tuple(dict.fromkeys(errors)))


def validate_release_rollback_drill_outcome_review_packet_or_raise(packet: Mapping[str, Any]) -> None:
    """Validate a packet and raise on failure."""

    result = validate_release_rollback_drill_outcome_review_packet(packet)
    if not result.ok:
        raise RollbackDrillOutcomeReviewValidationError(result.errors)


def _first_mapping_sequence(packet: Mapping[str, Any], keys: Sequence[str]) -> list[Mapping[str, Any]]:
    for key in keys:
        items = _mapping_sequence(packet.get(key))
        if items:
            return items
    return []


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    if isinstance(value, Mapping):
        return [value]
    return []


def _has_citation(value: Mapping[str, Any]) -> bool:
    return any(_non_empty(value.get(key)) for key in _CITATION_KEYS)


def _has_reviewer_owner_fields(packet: Mapping[str, Any]) -> bool:
    for key in _REVIEWER_KEYS:
        value = packet.get(key)
        if isinstance(value, Mapping):
            required = ("review_owner", "rollback_decision_reviewer", "follow_up_owner")
            if all(_non_empty(value.get(item)) for item in required):
                return True
            if key != "reviewer_owner_fields" and any(_non_empty(item) for item in value.values()):
                return True
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                if isinstance(item, Mapping) and _non_empty(item.get("owner") or item.get("reviewer") or item.get("reviewer_owner")):
                    return True
                if isinstance(item, str) and item.strip():
                    return True
        elif isinstance(value, str) and value.strip():
            return True
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
    text = value.lower()
    if _contains_token(text, _PRIVATE_VALUE_TOKENS):
        errors.append(f"private/session artifact reference is not allowed at {path}")
    if _contains_token(text, _LOCAL_PATH_TOKENS):
        errors.append(f"local private path is not allowed at {path}")
    if _contains_token(text, _RAW_VALUE_TOKENS):
        errors.append(f"raw crawl/download/archive reference is not allowed at {path}")
    if _claims_live_rollback_or_publication(text):
        errors.append(f"live rollback or publication claim is not allowed at {path}")
    if _claims_legal_or_permitting_guarantee(text):
        errors.append(f"legal or permitting outcome guarantee is not allowed at {path}")


def _claims_live_rollback_or_publication(text: str) -> bool:
    rollback_claims = ("active rollback", "live rollback", "rollback was executed", "rollback executed", "rollback was completed", "rollback completed", "rollback was applied", "rollback applied")
    publication_claims = ("published to production", "published to live", "published to public", "released to production", "promoted to production", "publication completed", "publication performed", "publication succeeded", "publication is live")
    return _contains_token(text, rollback_claims) or _contains_token(text, publication_claims)


def _claims_legal_or_permitting_guarantee(text: str) -> bool:
    if "legal advice" in text:
        return True
    guarantee_words = ("guarantee", "guaranteed", "assure", "assured", "ensure", "ensured")
    outcome_words = ("approval", "approved", "issuance", "issued", "permit", "inspection", "legal outcome", "compliance")
    if _contains_token(text, guarantee_words) and _contains_token(text, outcome_words):
        return True
    return "will be approved" in text or "will be issued" in text or "permit will be approved" in text


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
    text = " ".join(str(control.get(key, "")) for key in ("action", "action_type", "id", "label", "name", "type")).lower()
    return _contains_token(text, ("cancel", "certify", "certification", "payment", "publish", "release", "schedule", "submit", "upload", "withdraw"))


def _contains_token(text: str, tokens: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) > 0
    return True
