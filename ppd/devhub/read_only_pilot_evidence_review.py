"""Validation for DevHub read-only pilot evidence review packets.

The validator is intentionally fixture-first and side-effect free. It rejects packet
content that would be unsafe to commit or promote for the read-only DevHub pilot.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


CONSEQUENTIAL_ACTION_TERMS = (
    "submit",
    "submission",
    "upload",
    "certify",
    "certification",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "reactivate",
    "extension",
)

SENSITIVE_KEY_TERMS = (
    "password",
    "credential",
    "cookie",
    "token",
    "session",
    "auth_state",
    "storage_state",
    "local_storage",
    "session_storage",
    "raw_value",
    "raw_authenticated_value",
    "authenticated_value",
    "private_value",
)

ARTIFACT_KEY_TERMS = (
    "screenshot",
    "trace",
    "har",
    "video",
    "auth_state_path",
    "storage_state_path",
    "session_file",
)

ARTIFACT_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".har",
    ".trace",
    "trace.zip",
    "storage_state.json",
    "auth_state.json",
)

PRIVATE_PATH_MARKERS = (
    "/home/",
    "/users/",
    "c:\\users\\",
    "file://",
    "~/",
    "/var/folders/",
    "/private/var/",
)

LIVE_BROWSER_CLAIMS = (
    "live browser",
    "launched browser",
    "ran playwright",
    "executed playwright",
    "clicked in devhub",
    "filled in devhub",
    "real devhub session",
    "authenticated browser session",
)


@dataclass(frozen=True)
class EvidenceReviewFinding:
    code: str
    path: str
    message: str


def validate_read_only_pilot_evidence_packet(packet: Dict[str, Any]) -> List[EvidenceReviewFinding]:
    """Return fail-closed findings for a DevHub read-only pilot packet."""
    findings: List[EvidenceReviewFinding] = []

    if not isinstance(packet, dict):
        return [
            EvidenceReviewFinding(
                "packet_not_object",
                "$",
                "Evidence review packet must be a JSON object.",
            )
        ]

    findings.extend(_validate_required_review_sections(packet))
    findings.extend(_validate_consequential_controls(packet))
    findings.extend(_validate_surface_registry_mutation(packet))
    findings.extend(_scan_tree(packet))
    return _dedupe_findings(findings)


def assert_read_only_pilot_evidence_packet(packet: Dict[str, Any]) -> None:
    findings = validate_read_only_pilot_evidence_packet(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}" for finding in findings)
        raise ValueError(f"Unsafe DevHub read-only pilot evidence packet: {details}")


def _validate_required_review_sections(packet: Dict[str, Any]) -> List[EvidenceReviewFinding]:
    findings: List[EvidenceReviewFinding] = []

    selector_notes = packet.get("selector_confidence_notes")
    if not isinstance(selector_notes, list) or not selector_notes:
        findings.append(
            EvidenceReviewFinding(
                "missing_selector_confidence_notes",
                "$.selector_confidence_notes",
                "Read-only evidence packets must include selector-confidence notes.",
            )
        )
    else:
        for index, note in enumerate(selector_notes):
            if not isinstance(note, dict) or not note.get("selector") or not note.get("rationale"):
                findings.append(
                    EvidenceReviewFinding(
                        "incomplete_selector_confidence_note",
                        f"$.selector_confidence_notes[{index}]",
                        "Each selector-confidence note must include selector and rationale.",
                    )
                )
            confidence = note.get("confidence") if isinstance(note, dict) else None
            if confidence not in {"low", "medium", "high"}:
                findings.append(
                    EvidenceReviewFinding(
                        "invalid_selector_confidence",
                        f"$.selector_confidence_notes[{index}].confidence",
                        "Selector confidence must be low, medium, or high.",
                    )
                )

    attestation = packet.get("redaction_attestation")
    if not isinstance(attestation, dict):
        findings.append(
            EvidenceReviewFinding(
                "missing_redaction_attestation",
                "$.redaction_attestation",
                "Read-only evidence packets must include a redaction attestation.",
            )
        )
    else:
        required_true = (
            "accepted",
            "no_raw_authenticated_values",
            "no_private_session_artifacts",
            "no_local_private_paths",
        )
        for key in required_true:
            if attestation.get(key) is not True:
                findings.append(
                    EvidenceReviewFinding(
                        "failed_redaction_attestation",
                        f"$.redaction_attestation.{key}",
                        "Redaction attestation must explicitly affirm this safety condition.",
                    )
                )

    checkpoints = packet.get("manual_handoff_checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        findings.append(
            EvidenceReviewFinding(
                "missing_manual_handoff_checkpoints",
                "$.manual_handoff_checkpoints",
                "Read-only evidence packets must include manual-handoff checkpoints.",
            )
        )
    else:
        for index, checkpoint in enumerate(checkpoints):
            if not isinstance(checkpoint, dict) or not checkpoint.get("checkpoint_id") or checkpoint.get("status") != "required":
                findings.append(
                    EvidenceReviewFinding(
                        "invalid_manual_handoff_checkpoint",
                        f"$.manual_handoff_checkpoints[{index}]",
                        "Manual-handoff checkpoints must be explicit and required.",
                    )
                )

    return findings


def _validate_consequential_controls(packet: Dict[str, Any]) -> List[EvidenceReviewFinding]:
    findings: List[EvidenceReviewFinding] = []
    controls = packet.get("controls", [])
    if isinstance(controls, dict):
        controls = [dict({"control_id": key}, **value) if isinstance(value, dict) else {"control_id": key, "enabled": value} for key, value in controls.items()]
    if not isinstance(controls, list):
        return findings

    for index, control in enumerate(controls):
        if not isinstance(control, dict):
            continue
        enabled = control.get("enabled") is True or control.get("state") == "enabled"
        text = " ".join(str(control.get(key, "")) for key in ("control_id", "name", "action", "label")).lower()
        if enabled and any(term in text for term in CONSEQUENTIAL_ACTION_TERMS):
            findings.append(
                EvidenceReviewFinding(
                    "enabled_consequential_control",
                    f"$.controls[{index}]",
                    "Read-only pilot packets must not enable consequential controls.",
                )
            )
    return findings


def _validate_surface_registry_mutation(packet: Dict[str, Any]) -> List[EvidenceReviewFinding]:
    findings: List[EvidenceReviewFinding] = []
    mutation = packet.get("surface_registry_mutation")
    if isinstance(mutation, dict):
        for key in ("active", "enabled", "requested"):
            if mutation.get(key) is True:
                findings.append(
                    EvidenceReviewFinding(
                        "active_surface_registry_mutation",
                        f"$.surface_registry_mutation.{key}",
                        "Read-only pilot packets must not request or activate surface-registry mutation.",
                    )
                )
        mode = str(mutation.get("mode", "none")).lower()
        if mode not in {"none", "read_only", "review_only"}:
            findings.append(
                EvidenceReviewFinding(
                    "active_surface_registry_mutation",
                    "$.surface_registry_mutation.mode",
                    "Surface-registry mutation mode must be none, read_only, or review_only.",
                )
            )
    elif packet.get("active_surface_registry_mutation") is True:
        findings.append(
            EvidenceReviewFinding(
                "active_surface_registry_mutation",
                "$.active_surface_registry_mutation",
                "Read-only pilot packets must not activate surface-registry mutation.",
            )
        )
    return findings


def _scan_tree(value: Any, path: str = "$", parent_key: str = "") -> List[EvidenceReviewFinding]:
    findings: List[EvidenceReviewFinding] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if any(term in key_text for term in SENSITIVE_KEY_TERMS):
                findings.append(
                    EvidenceReviewFinding(
                        "raw_authenticated_or_session_value",
                        child_path,
                        "Packet contains a raw authenticated value or session/auth key.",
                    )
                )
            if any(term in key_text for term in ARTIFACT_KEY_TERMS):
                findings.append(
                    EvidenceReviewFinding(
                        "private_session_artifact",
                        child_path,
                        "Packet references screenshots, traces, HAR files, or stored auth state.",
                    )
                )
            if key_text in {"live_browser_execution", "live_browser_claimed"} and child is True:
                findings.append(
                    EvidenceReviewFinding(
                        "live_browser_execution_claim",
                        child_path,
                        "Read-only pilot evidence packets must not claim live browser execution.",
                    )
                )
            findings.extend(_scan_tree(child, child_path, key_text))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_scan_tree(child, f"{path}[{index}]", parent_key))
    elif isinstance(value, str):
        findings.extend(_scan_string(value, path, parent_key))
    return findings


def _scan_string(value: str, path: str, parent_key: str) -> List[EvidenceReviewFinding]:
    lowered = value.lower()
    findings: List[EvidenceReviewFinding] = []

    if any(marker in lowered for marker in PRIVATE_PATH_MARKERS):
        findings.append(
            EvidenceReviewFinding(
                "local_private_path",
                path,
                "Packet contains a local private path.",
            )
        )
    if any(lowered.endswith(suffix) or suffix in lowered for suffix in ARTIFACT_SUFFIXES):
        findings.append(
            EvidenceReviewFinding(
                "private_session_artifact",
                path,
                "Packet references screenshots, traces, HAR files, or stored auth state.",
            )
        )
    if any(claim in lowered for claim in LIVE_BROWSER_CLAIMS):
        findings.append(
            EvidenceReviewFinding(
                "live_browser_execution_claim",
                path,
                "Read-only pilot evidence packets must not claim live browser execution.",
            )
        )
    if parent_key in {"execution_mode", "browser_mode"} and lowered in {"live", "headed", "playwright_live"}:
        findings.append(
            EvidenceReviewFinding(
                "live_browser_execution_claim",
                path,
                "Read-only pilot evidence packets must remain fixture-only or review-only.",
            )
        )
    return findings


def _dedupe_findings(findings: Iterable[EvidenceReviewFinding]) -> List[EvidenceReviewFinding]:
    seen: set[Tuple[str, str]] = set()
    deduped: List[EvidenceReviewFinding] = []
    for finding in findings:
        identity = (finding.code, finding.path)
        if identity not in seen:
            seen.add(identity)
            deduped.append(finding)
    return deduped
