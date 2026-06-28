from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ppd.crawler.public_dry_run_promotion_manifest import (
    REQUIRED_ABORT_CONDITIONS,
    _scan_for_forbidden_values,
    _sequence,
    _url_policy_errors,
    validate_public_dry_run_promotion_manifest,
)

INTAKE_PACKET_TYPE = "ppd.public_crawl_metadata_intake_packet.v1"


@dataclass(frozen=True)
class PublicCrawlMetadataIntakeSummary:
    packet_id: str
    promotion_manifest_id: str
    selected_target_count: int
    skipped_target_count: int
    abort_decision_count: int
    expected_archive_manifest_count: int


def build_public_crawl_metadata_intake_packet(
    promotion_manifest: Mapping[str, Any],
    *,
    packet_id: str = "fixture-public-crawl-metadata-intake-001",
    operator_id: str = "synthetic-operator-fixture",
    acknowledged_at: str = "2026-05-28T00:00:00Z",
    selected_source_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    errors = validate_public_dry_run_promotion_manifest(promotion_manifest)
    if errors:
        raise ValueError("invalid promotion manifest: " + "; ".join(errors))

    targets = list(_sequence(promotion_manifest.get("promotion_targets")))
    target_ids = {str(target["source_id"]) for target in targets if isinstance(target, Mapping)}
    selected_ids = set(selected_source_ids or sorted(target_ids))
    unknown_selected = selected_ids - target_ids
    if unknown_selected:
        raise ValueError("selected_source_ids include unknown sources: " + ", ".join(sorted(unknown_selected)))

    handoffs_by_source = {
        str(row["source_id"]): row
        for row in _sequence(promotion_manifest.get("processor_handoff_intent"))
        if isinstance(row, Mapping) and "source_id" in row
    }

    prerequisites = []
    for row in _sequence(promotion_manifest.get("robots_policy_prerequisites")):
        if not isinstance(row, Mapping):
            continue
        source_id = str(row["source_id"])
        evidence_id = str(row.get("evidence_id") or "evidence:" + source_id + ":robots-policy-prerequisite")
        prerequisites.append(
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "robots_status": row.get("robots_status"),
                "policy_status": row.get("policy_status"),
                "required_before_live_run": True,
            }
        )

    selected_targets = []
    skipped_targets = []
    attestations = []
    expected_archive_manifest_ids = []

    for target in targets:
        if not isinstance(target, Mapping):
            continue
        source_id = str(target["source_id"])
        handoff = handoffs_by_source[source_id]
        archive_manifest_id = str(handoff["expected_archive_manifest_id"])
        if source_id in selected_ids:
            attestation_id = "attest:no-raw-body:" + source_id
            selected_targets.append(
                {
                    "source_id": source_id,
                    "canonical_url": target.get("canonical_url") or target.get("url"),
                    "expected_archive_manifest_id": archive_manifest_id,
                    "prerequisite_evidence_ids": [
                        row["evidence_id"] for row in prerequisites if row["source_id"] == source_id
                    ],
                    "no_raw_body_attestation_id": attestation_id,
                    "selected_for_metadata_intake": True,
                }
            )
            attestations.append(
                {
                    "attestation_id": attestation_id,
                    "source_id": source_id,
                    "expected_archive_manifest_id": archive_manifest_id,
                    "no_raw_body_persisted": True,
                    "raw_body_persisted": False,
                    "downloaded_documents": False,
                    "live_network_invoked": False,
                    "processor_invoked": False,
                }
            )
            expected_archive_manifest_ids.append(archive_manifest_id)
        else:
            skipped_targets.append(
                {
                    "source_id": source_id,
                    "canonical_url": target.get("canonical_url") or target.get("url"),
                    "skipped_reason": "operator_not_selected_for_fixture_intake",
                    "real_crawl_performed": False,
                    "real_download_performed": False,
                }
            )

    abort_decisions = []
    for condition in _sequence(promotion_manifest.get("abort_conditions")):
        if not isinstance(condition, Mapping):
            continue
        abort_decisions.append(
            {
                "condition_id": str(condition.get("condition_id")),
                "decision": "abort_if_triggered",
                "abort_before_live_run": True,
                "operator_override_allowed": False,
            }
        )

    return {
        "packet_type": INTAKE_PACKET_TYPE,
        "packet_id": packet_id,
        "fixture_first": True,
        "dry_run_only": True,
        "metadata_only": True,
        "live_network_invoked": False,
        "processor_invoked": False,
        "real_crawl_performed": False,
        "real_download_performed": False,
        "promotion_manifest_id": promotion_manifest["manifest_id"],
        "synthetic_operator_acknowledgement": {
            "operator_id": operator_id,
            "acknowledged_at": acknowledged_at,
            "acknowledged_fixture_only_dry_run": True,
            "acknowledged_no_live_authority": True,
            "acknowledgement_text": "Synthetic fixture acknowledgement for metadata intake validation only.",
        },
        "selected_allowlisted_targets": selected_targets,
        "skipped_targets": skipped_targets,
        "prerequisite_evidence": prerequisites,
        "prerequisite_evidence_ids": [row["evidence_id"] for row in prerequisites],
        "abort_decisions": abort_decisions,
        "expected_archive_manifest_ids": expected_archive_manifest_ids,
        "no_raw_body_attestations": attestations,
    }


def validate_public_crawl_metadata_intake_packet(
    packet: Mapping[str, Any],
    promotion_manifest: Mapping[str, Any] | None = None,
) -> list[str]:
    if not isinstance(packet, Mapping):
        return ["packet must be an object"]

    errors: list[str] = []
    _scan_for_forbidden_values(packet, "$", errors)

    if packet.get("packet_type") != INTAKE_PACKET_TYPE:
        errors.append("packet_type must be " + INTAKE_PACKET_TYPE)
    if not _text(packet.get("packet_id")):
        errors.append("packet_id is required")
    for key in ("fixture_first", "dry_run_only", "metadata_only"):
        if packet.get(key) is not True:
            errors.append(key + " must be true")
    for key in ("live_network_invoked", "processor_invoked", "real_crawl_performed", "real_download_performed"):
        if packet.get(key) is not False:
            errors.append(key + " must be false")

    acknowledgement = packet.get("synthetic_operator_acknowledgement")
    if not isinstance(acknowledgement, Mapping):
        errors.append("synthetic_operator_acknowledgement is required")
    else:
        if not _text(acknowledgement.get("operator_id")):
            errors.append("synthetic_operator_acknowledgement.operator_id is required")
        if acknowledgement.get("acknowledged_fixture_only_dry_run") is not True:
            errors.append("synthetic_operator_acknowledgement must acknowledge fixture-only dry run")
        if acknowledgement.get("acknowledged_no_live_authority") is not True:
            errors.append("synthetic_operator_acknowledgement must acknowledge no live authority")

    selected = _sequence(packet.get("selected_allowlisted_targets"))
    skipped = _sequence(packet.get("skipped_targets"))
    attestations = _sequence(packet.get("no_raw_body_attestations"))
    abort_decisions = _sequence(packet.get("abort_decisions"))
    prerequisite_ids = [str(value) for value in _sequence(packet.get("prerequisite_evidence_ids"))]
    expected_archive_ids = [str(value) for value in _sequence(packet.get("expected_archive_manifest_ids"))]

    if not selected:
        errors.append("selected_allowlisted_targets must include at least one target")
    if not prerequisite_ids:
        errors.append("prerequisite_evidence_ids must not be empty")
    if not expected_archive_ids:
        errors.append("expected_archive_manifest_ids must not be empty")

    selected_ids: set[str] = set()
    selected_archive_ids: set[str] = set()
    selected_attestation_ids: set[str] = set()
    for index, target in enumerate(selected):
        location = "selected_allowlisted_targets[" + str(index) + "]"
        if not isinstance(target, Mapping):
            errors.append(location + " must be an object")
            continue
        source_id = _text(target.get("source_id"))
        if not source_id:
            errors.append(location + ".source_id is required")
        else:
            selected_ids.add(source_id)
        url = _text(target.get("canonical_url"))
        if not url:
            errors.append(location + ".canonical_url is required")
        else:
            errors.extend(_url_policy_errors(url, location + ".canonical_url"))
        archive_id = _text(target.get("expected_archive_manifest_id"))
        if not archive_id:
            errors.append(location + ".expected_archive_manifest_id is required")
        else:
            selected_archive_ids.add(archive_id)
        attestation_id = _text(target.get("no_raw_body_attestation_id"))
        if not attestation_id:
            errors.append(location + ".no_raw_body_attestation_id is required")
        else:
            selected_attestation_ids.add(attestation_id)
        if target.get("selected_for_metadata_intake") is not True:
            errors.append(location + ".selected_for_metadata_intake must be true")

    for index, target in enumerate(skipped):
        location = "skipped_targets[" + str(index) + "]"
        if not isinstance(target, Mapping):
            errors.append(location + " must be an object")
            continue
        if not _text(target.get("source_id")):
            errors.append(location + ".source_id is required")
        if not _text(target.get("skipped_reason")):
            errors.append(location + ".skipped_reason is required")
        if target.get("real_crawl_performed") is not False:
            errors.append(location + ".real_crawl_performed must be false")
        if target.get("real_download_performed") is not False:
            errors.append(location + ".real_download_performed must be false")

    attestation_ids = set()
    for index, attestation in enumerate(attestations):
        location = "no_raw_body_attestations[" + str(index) + "]"
        if not isinstance(attestation, Mapping):
            errors.append(location + " must be an object")
            continue
        attestation_id = _text(attestation.get("attestation_id"))
        if not attestation_id:
            errors.append(location + ".attestation_id is required")
        else:
            attestation_ids.add(attestation_id)
        if attestation.get("no_raw_body_persisted") is not True:
            errors.append(location + ".no_raw_body_persisted must be true")
        for key in ("raw_body_persisted", "downloaded_documents", "live_network_invoked", "processor_invoked"):
            if attestation.get(key) is not False:
                errors.append(location + "." + key + " must be false")

    missing_attestations = selected_attestation_ids - attestation_ids
    if missing_attestations:
        errors.append("missing no_raw_body_attestations for " + ", ".join(sorted(missing_attestations)))
    if set(expected_archive_ids) != selected_archive_ids:
        errors.append("expected_archive_manifest_ids must match selected targets")

    abort_ids = set()
    for index, decision in enumerate(abort_decisions):
        location = "abort_decisions[" + str(index) + "]"
        if not isinstance(decision, Mapping):
            errors.append(location + " must be an object")
            continue
        condition_id = _text(decision.get("condition_id"))
        if not condition_id:
            errors.append(location + ".condition_id is required")
        else:
            abort_ids.add(condition_id)
        if decision.get("decision") != "abort_if_triggered":
            errors.append(location + ".decision must be abort_if_triggered")
        if decision.get("abort_before_live_run") is not True:
            errors.append(location + ".abort_before_live_run must be true")
        if decision.get("operator_override_allowed") is not False:
            errors.append(location + ".operator_override_allowed must be false")
    missing_required_abort_ids = REQUIRED_ABORT_CONDITIONS - abort_ids
    if missing_required_abort_ids:
        errors.append("abort_decisions missing " + ", ".join(sorted(missing_required_abort_ids)))

    if promotion_manifest is not None:
        manifest_errors = validate_public_dry_run_promotion_manifest(promotion_manifest)
        if manifest_errors:
            errors.append("promotion manifest invalid: " + "; ".join(manifest_errors))
        else:
            _validate_against_promotion_manifest(packet, promotion_manifest, errors)

    return list(dict.fromkeys(errors))


def assert_public_crawl_metadata_intake_packet(
    packet: Mapping[str, Any],
    promotion_manifest: Mapping[str, Any] | None = None,
) -> PublicCrawlMetadataIntakeSummary:
    errors = validate_public_crawl_metadata_intake_packet(packet, promotion_manifest)
    if errors:
        raise ValueError("invalid public crawl metadata intake packet: " + "; ".join(errors))
    return PublicCrawlMetadataIntakeSummary(
        packet_id=str(packet["packet_id"]),
        promotion_manifest_id=str(packet["promotion_manifest_id"]),
        selected_target_count=len(_sequence(packet.get("selected_allowlisted_targets"))),
        skipped_target_count=len(_sequence(packet.get("skipped_targets"))),
        abort_decision_count=len(_sequence(packet.get("abort_decisions"))),
        expected_archive_manifest_count=len(_sequence(packet.get("expected_archive_manifest_ids"))),
    )


def _validate_against_promotion_manifest(
    packet: Mapping[str, Any], promotion_manifest: Mapping[str, Any], errors: list[str]
) -> None:
    if packet.get("promotion_manifest_id") != promotion_manifest.get("manifest_id"):
        errors.append("promotion_manifest_id must match consumed promotion manifest")

    manifest_targets = {
        str(row["source_id"]): row
        for row in _sequence(promotion_manifest.get("promotion_targets"))
        if isinstance(row, Mapping) and "source_id" in row
    }
    manifest_archive_ids = {
        str(row["source_id"]): str(row["expected_archive_manifest_id"])
        for row in _sequence(promotion_manifest.get("processor_handoff_intent"))
        if isinstance(row, Mapping) and "source_id" in row and "expected_archive_manifest_id" in row
    }
    packet_source_ids: set[str] = set()
    for section_name in ("selected_allowlisted_targets", "skipped_targets"):
        for row in _sequence(packet.get(section_name)):
            if isinstance(row, Mapping) and "source_id" in row:
                packet_source_ids.add(str(row["source_id"]))
    if packet_source_ids != set(manifest_targets):
        errors.append("selected and skipped targets must account for every promotion target")

    for row in _sequence(packet.get("selected_allowlisted_targets")):
        if not isinstance(row, Mapping):
            continue
        source_id = str(row.get("source_id"))
        target = manifest_targets.get(source_id)
        if target is None:
            errors.append("selected target references unknown source_id " + source_id)
            continue
        manifest_url = target.get("canonical_url") or target.get("url")
        if row.get("canonical_url") != manifest_url:
            errors.append("selected target " + source_id + " canonical_url must match promotion manifest")
        if row.get("expected_archive_manifest_id") != manifest_archive_ids.get(source_id):
            errors.append("selected target " + source_id + " expected archive manifest must match promotion manifest")

    manifest_abort_ids = {
        str(row.get("condition_id"))
        for row in _sequence(promotion_manifest.get("abort_conditions"))
        if isinstance(row, Mapping)
    }
    packet_abort_ids = {
        str(row.get("condition_id"))
        for row in _sequence(packet.get("abort_decisions"))
        if isinstance(row, Mapping)
    }
    if not manifest_abort_ids.issubset(packet_abort_ids):
        errors.append("abort_decisions must cover promotion manifest abort conditions")


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
