"""Fixture-first public refresh reviewer disposition packet v1.

Consumes only synthetic public refresh reviewer handoff rows and emits an
offline reviewer disposition packet. The packet records seed decisions,
citation refresh priority dispositions, stale-source hold outcomes, owner
signoff placeholders, dependency sequencing, rollback checkpoints, and exact
offline validation commands. It does not crawl, fetch, open DevHub, promote
rows, activate releases, store raw output, or perform official actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PACKET_VERSION = "public-refresh-reviewer-disposition-packet-v1"
INPUT_CONTRACT = "synthetic_public_refresh_reviewer_handoff_rows_only"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_reviewer_disposition_packet_v1.py"),
    ("python3", "-m", "py_compile", "ppd/tests/test_public_refresh_reviewer_disposition_packet_v1.py"),
    ("python3", "-m", "unittest", "ppd.tests.test_public_refresh_reviewer_disposition_packet_v1"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_SEED_DECISIONS = frozenset(
    {
        "approved",
        "held",
        "skipped",
        "needs_human_review",
    }
)

ALLOWED_PRIORITY_DISPOSITIONS = frozenset(
    {
        "approve_priority",
        "hold_priority",
        "skip_priority",
        "needs_human_review",
    }
)

ALLOWED_STALE_SOURCE_OUTCOMES = frozenset(
    {
        "hold_active",
        "hold_released_by_reviewer_placeholder",
        "not_stale",
        "needs_human_review",
    }
)

REQUIRED_FALSE_FLAGS = (
    "live_crawl",
    "live_extraction",
    "document_download",
    "raw_output_stored",
    "devhub_opened",
    "release_activation",
    "source_row_promoted",
    "archive_row_promoted",
    "official_action_completed",
    "active_mutation",
)

SENSITIVE_OR_RUNTIME_KEYS = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "downloaded_artifact",
        "downloaded_document",
        "downloaded_pdf",
        "har",
        "html_body",
        "local_path",
        "password",
        "private_artifact",
        "raw_artifact",
        "raw_body",
        "raw_crawl_output",
        "raw_download",
        "raw_html",
        "raw_output",
        "raw_pdf",
        "screenshot",
        "session_state",
        "trace",
        "warc_path",
    }
)

PROHIBITED_CLAIM_PHRASES = frozenset(
    {
        "archive row promoted",
        "devhub opened",
        "document downloaded",
        "live crawl completed",
        "official action completed",
        "raw output stored",
        "release activated",
        "source row promoted",
    }
)


@dataclass(frozen=True)
class PublicRefreshReviewerHandoffRow:
    row_id: str
    source_id: str
    canonical_url: str
    seed_decision: str
    seed_decision_reason: str
    citation_refresh_priority: str
    citation_refresh_priority_disposition: str
    stale_source_hold_outcome: str
    owner: str
    owner_signoff_placeholder: str
    dependency_after: tuple[str, ...]
    rollback_checkpoint: str
    reviewer_notes_placeholder: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "PublicRefreshReviewerHandoffRow":
        _reject_runtime_or_private_content(row)
        if row.get("synthetic_public_refresh_reviewer_handoff_row") is not True:
            raise ValueError("handoff row must declare synthetic_public_refresh_reviewer_handoff_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"handoff row must declare {flag} false")

        seed_decision = _required_text(row, "seed_decision")
        if seed_decision not in ALLOWED_SEED_DECISIONS:
            raise ValueError(f"unsupported seed_decision: {seed_decision}")
        priority_disposition = _required_text(row, "citation_refresh_priority_disposition")
        if priority_disposition not in ALLOWED_PRIORITY_DISPOSITIONS:
            raise ValueError(f"unsupported citation_refresh_priority_disposition: {priority_disposition}")
        stale_outcome = _required_text(row, "stale_source_hold_outcome")
        if stale_outcome not in ALLOWED_STALE_SOURCE_OUTCOMES:
            raise ValueError(f"unsupported stale_source_hold_outcome: {stale_outcome}")

        return cls(
            row_id=_required_text(row, "row_id"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            seed_decision=seed_decision,
            seed_decision_reason=_required_text(row, "seed_decision_reason"),
            citation_refresh_priority=_required_text(row, "citation_refresh_priority"),
            citation_refresh_priority_disposition=priority_disposition,
            stale_source_hold_outcome=stale_outcome,
            owner=_required_text(row, "owner"),
            owner_signoff_placeholder=_required_text(row, "owner_signoff_placeholder"),
            dependency_after=_optional_text_tuple(row, "dependency_after"),
            rollback_checkpoint=_required_text(row, "rollback_checkpoint"),
            reviewer_notes_placeholder=_required_text(row, "reviewer_notes_placeholder"),
        )


def build_public_refresh_reviewer_disposition_packet_v1(
    handoff_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = tuple(PublicRefreshReviewerHandoffRow.from_mapping(row) for row in handoff_rows)
    if not rows:
        raise ValueError("at least one synthetic public refresh reviewer handoff row is required")

    packet = {
        "packet_version": PACKET_VERSION,
        "input_contract": INPUT_CONTRACT,
        "mode": "fixture_first_offline_reviewer_disposition_only",
        "handoff_row_count": len(rows),
        "seed_decisions": _seed_decisions(rows),
        "citation_refresh_priority_dispositions": _priority_dispositions(rows),
        "stale_source_hold_outcomes": _stale_source_outcomes(rows),
        "owner_signoff_placeholders": _owner_signoffs(rows),
        "dependency_sequencing": _dependency_sequencing(rows),
        "rollback_checkpoints": _rollback_checkpoints(rows),
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        "prohibited_actions": [
            "live_crawling",
            "document_retrieval",
            "raw_output_storage",
            "devhub_access",
            "release_activation",
            "source_or_archive_promotion",
            "official_action",
        ],
        "attestations": {
            "fixture_first": True,
            "synthetic_rows_only": True,
            "no_live_crawling": True,
            "no_document_retrieval": True,
            "no_raw_output_storage": True,
            "no_devhub_access": True,
            "no_release_activation": True,
            "no_source_or_archive_promotion": True,
            "no_official_actions": True,
        },
    }
    validate_public_refresh_reviewer_disposition_packet_v1(packet)
    return packet


def load_public_refresh_reviewer_disposition_fixture(path: Path) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("fixture must be a JSON object")
    _reject_runtime_or_private_content(payload)
    rows = payload.get("public_refresh_reviewer_handoff_rows")
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError("fixture must contain public_refresh_reviewer_handoff_rows objects")
    return tuple(rows)


def build_public_refresh_reviewer_disposition_packet_from_fixture(path: Path) -> dict[str, Any]:
    return build_public_refresh_reviewer_disposition_packet_v1(
        load_public_refresh_reviewer_disposition_fixture(path)
    )


def validate_public_refresh_reviewer_disposition_packet_v1(packet: Mapping[str, Any]) -> None:
    _reject_runtime_or_private_content(packet)
    if packet.get("packet_version") != PACKET_VERSION:
        raise ValueError(f"packet_version must be {PACKET_VERSION}")
    if packet.get("input_contract") != INPUT_CONTRACT:
        raise ValueError(f"input_contract must be {INPUT_CONTRACT}")
    if packet.get("mode") != "fixture_first_offline_reviewer_disposition_only":
        raise ValueError("packet must remain fixture_first_offline_reviewer_disposition_only")
    if packet.get("exact_offline_validation_commands") != [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]:
        raise ValueError("packet must include exact offline validation commands")

    for key in (
        "seed_decisions",
        "citation_refresh_priority_dispositions",
        "stale_source_hold_outcomes",
        "owner_signoff_placeholders",
        "dependency_sequencing",
        "rollback_checkpoints",
    ):
        if not _non_empty_list_of_mappings(packet.get(key)):
            raise ValueError(f"{key} must contain at least one row")

    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("packet must include attestations")
    for key in (
        "fixture_first",
        "synthetic_rows_only",
        "no_live_crawling",
        "no_document_retrieval",
        "no_raw_output_storage",
        "no_devhub_access",
        "no_release_activation",
        "no_source_or_archive_promotion",
        "no_official_actions",
    ):
        if attestations.get(key) is not True:
            raise ValueError(f"packet attestation {key} must be true")

    decisions = packet["seed_decisions"]
    observed_decisions = {str(row.get("seed_decision")) for row in decisions}
    missing = ALLOWED_SEED_DECISIONS - observed_decisions
    if missing:
        raise ValueError(f"packet must include all seed decision categories: {sorted(missing)}")

    for section in (
        "seed_decisions",
        "citation_refresh_priority_dispositions",
        "stale_source_hold_outcomes",
        "rollback_checkpoints",
    ):
        for row in packet[section]:
            for flag in REQUIRED_FALSE_FLAGS:
                if row.get(flag) is not False:
                    raise ValueError(f"{section} row must declare {flag} false")


def _seed_decisions(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            _with_false_flags(
                {
                    "decision_id": f"seed::{row.row_id}",
                    "row_id": row.row_id,
                    "source_id": row.source_id,
                    "canonical_url": row.canonical_url,
                    "seed_decision": row.seed_decision,
                    "seed_decision_reason": row.seed_decision_reason,
                    "reviewer_notes_placeholder": row.reviewer_notes_placeholder,
                }
            )
            for row in rows
        ),
        key=lambda item: item["decision_id"],
    )


def _priority_dispositions(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            _with_false_flags(
                {
                    "priority_disposition_id": f"priority::{row.row_id}",
                    "row_id": row.row_id,
                    "source_id": row.source_id,
                    "citation_refresh_priority": row.citation_refresh_priority,
                    "citation_refresh_priority_disposition": row.citation_refresh_priority_disposition,
                }
            )
            for row in rows
        ),
        key=lambda item: item["priority_disposition_id"],
    )


def _stale_source_outcomes(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            _with_false_flags(
                {
                    "stale_source_outcome_id": f"stale::{row.row_id}",
                    "row_id": row.row_id,
                    "source_id": row.source_id,
                    "stale_source_hold_outcome": row.stale_source_hold_outcome,
                    "agent_may_treat_source_as_current": row.stale_source_hold_outcome == "hold_released_by_reviewer_placeholder",
                }
            )
            for row in rows
        ),
        key=lambda item: item["stale_source_outcome_id"],
    )


def _owner_signoffs(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "owner_signoff_id": f"owner-signoff::{row.row_id}",
                "row_id": row.row_id,
                "source_id": row.source_id,
                "owner": row.owner,
                "owner_signoff_placeholder": row.owner_signoff_placeholder,
                "signed_off": False,
            }
            for row in rows
        ),
        key=lambda item: item["owner_signoff_id"],
    )


def _dependency_sequencing(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "dependency_id": f"dependency::{row.row_id}",
                "row_id": row.row_id,
                "source_id": row.source_id,
                "ordered_steps": list(row.dependency_after)
                + [
                    "record seed decision",
                    "record citation refresh priority disposition",
                    "record stale-source hold outcome",
                    "record owner signoff placeholder",
                    "confirm rollback checkpoint",
                ],
            }
            for row in rows
        ),
        key=lambda item: item["dependency_id"],
    )


def _rollback_checkpoints(rows: Sequence[PublicRefreshReviewerHandoffRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            _with_false_flags(
                {
                    "rollback_id": f"rollback::{row.row_id}",
                    "row_id": row.row_id,
                    "source_id": row.source_id,
                    "rollback_checkpoint": row.rollback_checkpoint,
                    "active_state_changed": False,
                }
            )
            for row in rows
        ),
        key=lambda item: item["rollback_id"],
    )


def _with_false_flags(row: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for flag in REQUIRED_FALSE_FLAGS:
        output[flag] = False
    return output


def _reject_runtime_or_private_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key_text in SENSITIVE_OR_RUNTIME_KEYS:
                raise ValueError(f"{path} contains runtime, raw, downloaded, or private key: {key}")
            _reject_runtime_or_private_content(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_runtime_or_private_content(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
        for phrase in PROHIBITED_CLAIM_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key, ())
    if value in (None, ()):
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{key} must be a list of strings")
    output = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return output


def _non_empty_list_of_mappings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)
