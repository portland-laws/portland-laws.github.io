"""Fixture-first reviewer packets for inactive guardrail recompile impact plans.

This module is intentionally offline-only. It consumes synthetic inactive impact
plan rows and produces reviewer-facing records. It does not recompile guardrails,
promote bundles, crawl sources, open DevHub, store private artifacts, or perform
official actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

PACKET_VERSION = "inactive_guardrail_recompile_reviewer_packet_v1"
SYNTHETIC_ROW_TYPE = "synthetic_inactive_guardrail_recompile_impact_plan"
OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/logic/inactive_guardrail_recompile_reviewer_packet.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_guardrail_recompile_reviewer_packet.py"],
]

REQUIRED_NON_EMPTY_SECTIONS = (
    "impact_plan_references",
    "reviewer_disposition_rows",
    "predicate_change_review_notes",
    "explanation_template_review_notes",
    "blocked_stale_source_dependencies",
    "approval_hold_reject_routing",
    "rollback_notes",
    "validation_commands",
)

FORBIDDEN_KEY_FRAGMENTS = (
    "auth_state",
    "captcha",
    "cookie",
    "credential",
    "downloaded_artifact",
    "har",
    "live_crawl",
    "password",
    "private_artifact",
    "raw_artifact",
    "raw_crawl",
    "session_file",
    "trace",
)

FORBIDDEN_TEXT_CLAIMS = (
    "active mutation",
    "actively mutates",
    "automated devhub",
    "completed official action",
    "devhub verified",
    "downloaded artifact",
    "final submission complete",
    "guaranteed approval",
    "guaranteed permit",
    "legal advice",
    "legal guarantee",
    "live crawl",
    "official action complete",
    "officially submitted",
    "permitting guarantee",
    "private artifact",
    "promote to production",
    "promoted guardrail",
    "raw artifact",
    "raw crawl",
    "scraped devhub",
)

ACTIVE_MUTATION_KEYS = (
    "active",
    "active_mutation",
    "active_mutation_enabled",
    "apply_patch",
    "auto_promote",
    "enabled",
    "execute_actions",
    "mutate_active_guardrails",
    "promotion_enabled",
    "write_to_devhub",
)


class ReviewerPacketError(ValueError):
    """Raised when fixture rows or reviewer packets are invalid."""


@dataclass(frozen=True)
class ReviewerPacketFinding:
    """A deterministic validation finding for reviewer packet v1."""

    path: str
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass(frozen=True)
class ImpactPlanRow:
    """Normalized synthetic inactive guardrail recompile impact plan row."""

    row_id: str
    guardrail_bundle_id: str
    process_id: str
    inactive_guardrail_id: str
    source_type: str
    source_evidence_ids: tuple[str, ...]
    predicate_changes: tuple[str, ...]
    explanation_template_changes: tuple[str, ...]
    stale_source_dependencies: tuple[str, ...]
    reviewer_recommendation: str
    rollback_note: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "ImpactPlanRow":
        row_id = _required_text(row, "row_id")
        source_type = _required_text(row, "source_type")
        if source_type != SYNTHETIC_ROW_TYPE:
            raise ReviewerPacketError(
                f"row {row_id!r} has unsupported source_type {source_type!r}; "
                f"expected {SYNTHETIC_ROW_TYPE!r}"
            )

        recommendation = _required_text(row, "reviewer_recommendation")
        if recommendation not in {"approve", "hold", "reject"}:
            raise ReviewerPacketError(
                f"row {row_id!r} has invalid reviewer_recommendation {recommendation!r}"
            )

        return cls(
            row_id=row_id,
            guardrail_bundle_id=_required_text(row, "guardrail_bundle_id"),
            process_id=_required_text(row, "process_id"),
            inactive_guardrail_id=_required_text(row, "inactive_guardrail_id"),
            source_type=source_type,
            source_evidence_ids=_text_tuple(row, "source_evidence_ids"),
            predicate_changes=_text_tuple(row, "predicate_changes"),
            explanation_template_changes=_text_tuple(row, "explanation_template_changes"),
            stale_source_dependencies=_text_tuple(row, "stale_source_dependencies"),
            reviewer_recommendation=recommendation,
            rollback_note=_required_text(row, "rollback_note"),
        )


def build_reviewer_packet(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a deterministic offline reviewer packet from synthetic rows only."""

    normalized_rows = [ImpactPlanRow.from_mapping(row) for row in rows]
    normalized_rows.sort(key=lambda row: row.row_id)

    if not normalized_rows:
        raise ReviewerPacketError("at least one synthetic impact plan row is required")

    disposition_rows = [_disposition_row(row) for row in normalized_rows]
    blocked_dependencies = [
        _blocked_dependency(row, dependency)
        for row in normalized_rows
        for dependency in row.stale_source_dependencies
    ]

    packet = {
        "packet_version": PACKET_VERSION,
        "input_policy": {
            "accepted_source_type": SYNTHETIC_ROW_TYPE,
            "fixture_first": True,
            "offline_only": True,
            "forbidden_actions": [
                "recompile_active_guardrails",
                "promote_guardrails",
                "crawl_public_sources",
                "open_devhub",
                "store_private_artifacts",
                "perform_official_actions",
            ],
        },
        "impact_plan_references": [_impact_plan_reference(row) for row in normalized_rows],
        "reviewer_disposition_rows": disposition_rows,
        "predicate_change_review_notes": [
            _review_note(row, "predicate_change", change)
            for row in normalized_rows
            for change in row.predicate_changes
        ],
        "explanation_template_review_notes": [
            _review_note(row, "explanation_template_change", change)
            for row in normalized_rows
            for change in row.explanation_template_changes
        ],
        "blocked_stale_source_dependencies": blocked_dependencies,
        "approval_hold_reject_routing": _routing(disposition_rows),
        "rollback_notes": [_rollback_note(row) for row in normalized_rows],
        "validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_reviewer_packet(packet)
    return packet


def validate_reviewer_packet(packet: Mapping[str, Any]) -> list[ReviewerPacketFinding]:
    """Return all validation findings for inactive reviewer packet v1."""

    if not isinstance(packet, Mapping):
        return [ReviewerPacketFinding("$", "packet must be a mapping")]

    findings: list[ReviewerPacketFinding] = []

    if packet.get("packet_version") != PACKET_VERSION:
        findings.append(ReviewerPacketFinding("packet_version", f"must equal {PACKET_VERSION}"))

    policy = packet.get("input_policy")
    if not isinstance(policy, Mapping):
        findings.append(ReviewerPacketFinding("input_policy", "must be present"))
    else:
        if policy.get("accepted_source_type") != SYNTHETIC_ROW_TYPE:
            findings.append(ReviewerPacketFinding("input_policy.accepted_source_type", f"must equal {SYNTHETIC_ROW_TYPE}"))
        if policy.get("fixture_first") is not True:
            findings.append(ReviewerPacketFinding("input_policy.fixture_first", "must be true"))
        if policy.get("offline_only") is not True:
            findings.append(ReviewerPacketFinding("input_policy.offline_only", "must be true"))

    for key in REQUIRED_NON_EMPTY_SECTIONS:
        if _is_empty(packet.get(key)):
            findings.append(ReviewerPacketFinding(key, "must be present and non-empty"))

    if packet.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        findings.append(ReviewerPacketFinding("validation_commands", "must exactly match offline reviewer packet commands"))

    findings.extend(_validate_cross_references(packet))
    findings.extend(_scan_for_forbidden_content(packet, "$"))
    return findings


def assert_valid_reviewer_packet(packet: Mapping[str, Any]) -> None:
    """Raise a stable error message if reviewer packet v1 is invalid."""

    findings = validate_reviewer_packet(packet)
    if findings:
        rendered = "; ".join(finding.render() for finding in findings)
        raise ReviewerPacketError(rendered)


def _impact_plan_reference(row: ImpactPlanRow) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "source_type": row.source_type,
        "guardrail_bundle_id": row.guardrail_bundle_id,
        "process_id": row.process_id,
        "inactive_guardrail_id": row.inactive_guardrail_id,
        "source_evidence_ids": list(row.source_evidence_ids),
    }


def _disposition_row(row: ImpactPlanRow) -> dict[str, Any]:
    blocked = bool(row.stale_source_dependencies)
    route = "hold" if blocked and row.reviewer_recommendation == "approve" else row.reviewer_recommendation
    return {
        "row_id": row.row_id,
        "guardrail_bundle_id": row.guardrail_bundle_id,
        "process_id": row.process_id,
        "inactive_guardrail_id": row.inactive_guardrail_id,
        "reviewer_recommendation": row.reviewer_recommendation,
        "route": route,
        "blocked_by_stale_source_dependency": blocked,
        "source_evidence_ids": list(row.source_evidence_ids),
    }


def _review_note(row: ImpactPlanRow, note_type: str, note: str) -> dict[str, str]:
    return {
        "row_id": row.row_id,
        "guardrail_bundle_id": row.guardrail_bundle_id,
        "inactive_guardrail_id": row.inactive_guardrail_id,
        "note_type": note_type,
        "note": note,
        "review_scope": "inactive_guardrail_recompile_impact_only",
    }


def _blocked_dependency(row: ImpactPlanRow, dependency: str) -> dict[str, str]:
    return {
        "row_id": row.row_id,
        "guardrail_bundle_id": row.guardrail_bundle_id,
        "inactive_guardrail_id": row.inactive_guardrail_id,
        "stale_source_dependency": dependency,
        "block_reason": "source freshness must be reviewed before inactive recompile disposition can be approved",
        "route": "hold",
    }


def _rollback_note(row: ImpactPlanRow) -> dict[str, str]:
    return {
        "row_id": row.row_id,
        "guardrail_bundle_id": row.guardrail_bundle_id,
        "inactive_guardrail_id": row.inactive_guardrail_id,
        "rollback_note": row.rollback_note,
        "rollback_scope": "review_packet_only_no_guardrail_state_changed",
    }


def _routing(disposition_rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    routes: dict[str, list[str]] = {"approve": [], "hold": [], "reject": []}
    for row in disposition_rows:
        routes[str(row["route"])].append(str(row["row_id"]))
    return routes


def _validate_cross_references(packet: Mapping[str, Any]) -> list[ReviewerPacketFinding]:
    findings: list[ReviewerPacketFinding] = []
    reference_ids = _row_ids(packet.get("impact_plan_references"))
    disposition_ids = _row_ids(packet.get("reviewer_disposition_rows"))

    for section in (
        "reviewer_disposition_rows",
        "predicate_change_review_notes",
        "explanation_template_review_notes",
        "blocked_stale_source_dependencies",
        "rollback_notes",
    ):
        value = packet.get(section)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for index, item in enumerate(value):
                if not isinstance(item, Mapping):
                    findings.append(ReviewerPacketFinding(f"{section}[{index}]", "must be a mapping"))
                    continue
                row_id = item.get("row_id")
                if not isinstance(row_id, str) or not row_id.strip():
                    findings.append(ReviewerPacketFinding(f"{section}[{index}].row_id", "must be present"))
                elif row_id not in reference_ids:
                    findings.append(ReviewerPacketFinding(f"{section}[{index}].row_id", "must reference impact_plan_references"))

    routing = packet.get("approval_hold_reject_routing")
    if isinstance(routing, Mapping):
        for route in ("approve", "hold", "reject"):
            route_rows = routing.get(route)
            if not isinstance(route_rows, list):
                findings.append(ReviewerPacketFinding(f"approval_hold_reject_routing.{route}", "must be a list"))
                continue
            for index, row_id in enumerate(route_rows):
                if row_id not in disposition_ids:
                    findings.append(ReviewerPacketFinding(f"approval_hold_reject_routing.{route}[{index}]", "must reference reviewer_disposition_rows"))

    dispositions = packet.get("reviewer_disposition_rows")
    if isinstance(dispositions, Sequence) and not isinstance(dispositions, (str, bytes, bytearray)):
        for index, row in enumerate(dispositions):
            if not isinstance(row, Mapping):
                continue
            route = row.get("route")
            if route not in {"approve", "hold", "reject"}:
                findings.append(ReviewerPacketFinding(f"reviewer_disposition_rows[{index}].route", "must be approve, hold, or reject"))
            elif isinstance(routing, Mapping) and row.get("row_id") not in routing.get(route, []):
                findings.append(ReviewerPacketFinding(f"reviewer_disposition_rows[{index}].route", "must be represented in approval_hold_reject_routing"))
            if _is_empty(row.get("source_evidence_ids")):
                findings.append(ReviewerPacketFinding(f"reviewer_disposition_rows[{index}].source_evidence_ids", "must be present and non-empty"))

    return findings


def _row_ids(value: Any) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return set()
    row_ids: set[str] = set()
    for item in value:
        if isinstance(item, Mapping):
            row_id = item.get("row_id")
            if isinstance(row_id, str) and row_id.strip():
                row_ids.add(row_id)
    return row_ids


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReviewerPacketError(f"field {key!r} must be a non-empty string")
    return value


def _text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key, [])
    if not isinstance(value, list):
        raise ReviewerPacketError(f"field {key!r} must be a list of strings")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ReviewerPacketError(f"field {key!r} must contain only non-empty strings")
    return tuple(value)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _scan_for_forbidden_content(value: Any, path: str) -> list[ReviewerPacketFinding]:
    findings: list[ReviewerPacketFinding] = []

    if isinstance(value, Mapping):
        for raw_key, raw_child in value.items():
            key = str(raw_key)
            normalized_key = _normalize(key)
            child_path = f"{path}.{key}" if path != "$" else key

            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in normalized_key:
                    findings.append(ReviewerPacketFinding(child_path, f"forbidden artifact or live-operation key: {fragment}"))

            if normalized_key in ACTIVE_MUTATION_KEYS and _truthy(raw_child):
                findings.append(ReviewerPacketFinding(child_path, "active mutation or promotion flag must not be true"))

            findings.extend(_scan_for_forbidden_content(raw_child, child_path))
        return findings

    if isinstance(value, str):
        normalized_value = _normalize(value)
        for claim in FORBIDDEN_TEXT_CLAIMS:
            if claim in normalized_value:
                findings.append(ReviewerPacketFinding(path, f"forbidden claim: {claim}"))
        return findings

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            findings.extend(_scan_for_forbidden_content(item, f"{path}[{index}]"))

    return findings


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def _normalize(value: str) -> str:
    return " ".join(value.replace("-", "_").replace(".", "_").lower().split())
