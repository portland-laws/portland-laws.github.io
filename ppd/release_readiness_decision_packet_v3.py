"""Fixture-first release readiness decision packets for PP&D.

This module intentionally produces synthetic, offline-only decision packets. It does
not read DevHub, crawl public sources, promote artifacts, or mutate release state.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence

SCENARIOS = {"release-ready", "release-held", "release-rejected"}

OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/release_readiness_decision_packet_v3.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_release_readiness_decision_packet_v3.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

REQUIRED_PACKET_SECTIONS: tuple[tuple[str, str], ...] = (
    ("agent_impact_replay_references", "missing agent impact replay references"),
    ("inactive_promotion_recommendation", "missing inactive promotion recommendation"),
    ("reviewer_signoff_placeholders", "missing reviewer signoff placeholders"),
    ("stale_evidence_holds", "missing stale-evidence holds"),
    ("activation_prerequisites", "missing activation prerequisites"),
    ("rollback_plan", "missing rollback plan"),
    ("post_decision_smoke_checks", "missing post-decision smoke checks"),
    ("validation_commands", "missing validation commands"),
    ("inactive_process_model_gate_recommendations", "missing inactive process-model gate recommendations"),
    ("inactive_guardrail_gate_recommendations", "missing inactive guardrail gate recommendations"),
    ("agent_readiness_replay", "missing agent readiness replay"),
    ("devhub_observation_delta_holds", "missing DevHub observation delta holds"),
    ("public_refresh_impact_summary", "missing public refresh impact summary"),
    ("reviewer_dispositions", "missing reviewer dispositions"),
    ("rollback_notes", "missing rollback notes"),
    ("offline_validation_commands", "missing offline validation commands"),
)

PRIVATE_OR_SESSION_ARTIFACT_KEYS = {
    "auth_state",
    "authenticated_artifact",
    "authenticated_artifacts",
    "browser_artifact",
    "browser_artifacts",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "downloaded_document",
    "downloaded_document_path",
    "har",
    "har_path",
    "har_paths",
    "local_private_path",
    "private_artifact",
    "private_artifacts",
    "private_file",
    "private_files",
    "private_value",
    "private_values",
    "raw_authenticated_capture",
    "screenshot",
    "screenshot_path",
    "screenshot_paths",
    "screenshots",
    "session_artifact",
    "session_artifacts",
    "session_state",
    "session_state_path",
    "storage_state",
    "trace",
    "trace_path",
    "trace_paths",
    "traces",
}

PROHIBITED_CLAIM_KEYS = {
    "active_surface_map_mutation_claims",
    "devhub_interaction_claims",
    "form_fill_claims",
    "form_filled",
    "legal_guarantees",
    "live_devhub_claims",
    "live_devhub_interaction_claims",
    "official_action_completion_claims",
    "permitting_guarantees",
    "surface_map_mutation_claims",
    "upload_claims",
    "uploaded_documents",
}

ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "active_mutation_flags",
    "active_prompt_mutation",
    "active_surface_map_mutation",
    "artifact_promotion_enabled",
    "certifies_actions",
    "devhub_surface_mutation",
    "form_fill_enabled",
    "guardrail_mutation_active",
    "mutates_active_surface_map",
    "mutates_remote_state",
    "promotes_release",
    "release_state_mutation",
    "submits_forms",
    "uploads_documents",
}

_PRIVATE_OR_ARTIFACT_TEXT_RE = re.compile(
    r"\b(?:auth state|authenticated artifact|browser artifact|cookies?|credentials?|downloaded document|HAR|private artifact|private value|raw authenticated|screenshots?|session state|storage state|traces?)\b",
    re.IGNORECASE,
)
_PROHIBITED_CLAIM_TEXT_RE = re.compile(
    r"\b(?:actively mutated the surface map|completed the official action|filled the form|guarantee(?:d|s)? permit|guarantee(?:d|s)? legal|live DevHub interaction|submitted the permit|uploaded the document)\b",
    re.IGNORECASE,
)
_NEGATED_TEXT_RE = re.compile(r"\b(?:no|not|never|without|does not|did not|must not|forbidden|disallowed)\b", re.IGNORECASE)


@dataclass(frozen=True)
class DecisionPacketValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class DecisionPacket:
    packet_version: str
    scenario: str
    release_state_changed: bool
    artifact_promotion_allowed: bool
    live_source_access_allowed: bool
    devhub_access_allowed: bool
    private_file_access_allowed: bool
    agent_impact_replay_references: tuple[Mapping[str, Any], ...]
    inactive_promotion_recommendation: Mapping[str, Any]
    reviewer_signoff_placeholders: tuple[Mapping[str, Any], ...]
    stale_evidence_holds: tuple[Mapping[str, Any], ...]
    activation_prerequisites: tuple[Mapping[str, Any], ...]
    rollback_plan: tuple[Mapping[str, Any], ...]
    post_decision_smoke_checks: tuple[Mapping[str, Any], ...]
    validation_commands: tuple[tuple[str, ...], ...]
    inactive_process_model_gate_recommendations: tuple[Mapping[str, Any], ...]
    inactive_guardrail_gate_recommendations: tuple[Mapping[str, Any], ...]
    agent_readiness_replay: Mapping[str, Any]
    devhub_observation_delta_holds: tuple[Mapping[str, Any], ...]
    public_refresh_impact_summary: Mapping[str, Any]
    reviewer_dispositions: tuple[Mapping[str, Any], ...]
    rollback_notes: tuple[str, ...]
    offline_validation_commands: tuple[tuple[str, ...], ...]
    decision: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_version": self.packet_version,
            "scenario": self.scenario,
            "release_state_changed": self.release_state_changed,
            "artifact_promotion_allowed": self.artifact_promotion_allowed,
            "live_source_access_allowed": self.live_source_access_allowed,
            "devhub_access_allowed": self.devhub_access_allowed,
            "private_file_access_allowed": self.private_file_access_allowed,
            "agent_impact_replay_references": [dict(item) for item in self.agent_impact_replay_references],
            "inactive_promotion_recommendation": deepcopy(dict(self.inactive_promotion_recommendation)),
            "reviewer_signoff_placeholders": [dict(item) for item in self.reviewer_signoff_placeholders],
            "stale_evidence_holds": [dict(item) for item in self.stale_evidence_holds],
            "activation_prerequisites": [dict(item) for item in self.activation_prerequisites],
            "rollback_plan": [dict(item) for item in self.rollback_plan],
            "post_decision_smoke_checks": [dict(item) for item in self.post_decision_smoke_checks],
            "validation_commands": [list(command) for command in self.validation_commands],
            "inactive_process_model_gate_recommendations": [dict(item) for item in self.inactive_process_model_gate_recommendations],
            "inactive_guardrail_gate_recommendations": [dict(item) for item in self.inactive_guardrail_gate_recommendations],
            "agent_readiness_replay": deepcopy(dict(self.agent_readiness_replay)),
            "devhub_observation_delta_holds": [dict(item) for item in self.devhub_observation_delta_holds],
            "public_refresh_impact_summary": deepcopy(dict(self.public_refresh_impact_summary)),
            "reviewer_dispositions": [dict(item) for item in self.reviewer_dispositions],
            "rollback_notes": list(self.rollback_notes),
            "offline_validation_commands": [list(command) for command in self.offline_validation_commands],
            "decision": deepcopy(dict(self.decision)),
        }


def _is_empty(value: Any) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, (str, bytes, Sequence, Mapping, set, frozenset)):
        return len(value) == 0
    return False


def _path_join(path: str, segment: str) -> str:
    return f"{path}.{segment}" if path else segment


def _iter_nodes(value: Any, path: str = "$", parent_key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield path, parent_key, value
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            yield from _iter_nodes(nested, _path_join(path, key_text), key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            yield from _iter_nodes(nested, f"{path}[{index}]", parent_key)


def _is_negated_text(value: str) -> bool:
    prefix = value[:80]
    return _NEGATED_TEXT_RE.search(prefix) is not None


def validate_release_readiness_decision_packet_v3(packet: Mapping[str, Any]) -> list[DecisionPacketValidationIssue]:
    """Return validation issues for a DevHub read-only release decision packet v3."""
    issues: list[DecisionPacketValidationIssue] = []

    if packet.get("packet_version") != "release-readiness-decision-packet-v3":
        issues.append(
            DecisionPacketValidationIssue(
                "packet_version",
                "$.packet_version",
                "packet_version must be release-readiness-decision-packet-v3",
            )
        )

    for key, message in REQUIRED_PACKET_SECTIONS:
        if _is_empty(packet.get(key)):
            issues.append(DecisionPacketValidationIssue(key, _path_join("$", key), message))

    for key in (
        "release_state_changed",
        "artifact_promotion_allowed",
        "live_source_access_allowed",
        "devhub_access_allowed",
        "private_file_access_allowed",
    ):
        if packet.get(key) is not False:
            issues.append(
                DecisionPacketValidationIssue(
                    "forbidden_effect",
                    _path_join("$", key),
                    f"{key} must be false for an offline read-only decision packet",
                )
            )

    for path, key, value in _iter_nodes(packet):
        normalized_key = key.lower().replace("-", "_")
        if normalized_key in PRIVATE_OR_SESSION_ARTIFACT_KEYS and not _is_empty(value):
            issues.append(
                DecisionPacketValidationIssue(
                    "private_or_session_artifact",
                    path,
                    "private/session/auth artifacts, screenshots, traces, HAR, raw captures, and downloaded documents are not allowed",
                )
            )
        if normalized_key in PROHIBITED_CLAIM_KEYS and not _is_empty(value):
            issues.append(
                DecisionPacketValidationIssue(
                    "prohibited_claim",
                    path,
                    "live DevHub, active surface-map mutation, form-fill/upload, official-action completion, legal, or permitting guarantee claims are not allowed",
                )
            )
        if normalized_key in ACTIVE_MUTATION_KEYS and not _is_empty(value):
            issues.append(
                DecisionPacketValidationIssue(
                    "active_mutation_flag",
                    path,
                    "active mutation flags are not allowed",
                )
            )
        if isinstance(value, str):
            if _PRIVATE_OR_ARTIFACT_TEXT_RE.search(value) and not _is_negated_text(value):
                issues.append(
                    DecisionPacketValidationIssue(
                        "private_or_session_artifact_text",
                        path,
                        "packet text must not claim private/session/auth artifacts, screenshots, traces, HAR, raw captures, or downloaded documents",
                    )
                )
            if _PROHIBITED_CLAIM_TEXT_RE.search(value) and not _is_negated_text(value):
                issues.append(
                    DecisionPacketValidationIssue(
                        "prohibited_claim_text",
                        path,
                        "packet text must not claim live DevHub interaction, active mutation, form-fill/upload completion, official-action completion, or guarantees",
                    )
                )

    return issues


def assert_valid_release_readiness_decision_packet_v3(packet: Mapping[str, Any]) -> None:
    issues = validate_release_readiness_decision_packet_v3(packet)
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def build_release_readiness_decision_packet_v3(scenario: str) -> dict[str, Any]:
    """Build a deterministic synthetic release readiness decision packet."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unsupported synthetic scenario: {scenario}")

    held = scenario == "release-held"
    rejected = scenario == "release-rejected"
    ready = scenario == "release-ready"

    packet = DecisionPacket(
        packet_version="release-readiness-decision-packet-v3",
        scenario=scenario,
        release_state_changed=False,
        artifact_promotion_allowed=False,
        live_source_access_allowed=False,
        devhub_access_allowed=False,
        private_file_access_allowed=False,
        agent_impact_replay_references=(
            {
                "replay_id": "agent-readiness-regression-replay-v4",
                "scope": "agent impact replay reference only",
                "result": "passed" if ready else "held" if held else "failed",
                "active_mutation_performed": False,
            },
            {
                "replay_id": "agent-api-smoke-rehearsal-v1",
                "scope": "offline consumer smoke replay reference only",
                "result": "passed" if ready else "needs-review" if held else "failed",
                "active_mutation_performed": False,
            },
        ),
        inactive_promotion_recommendation={
            "mode": "inactive-recommendation-only",
            "recommendation": "promote-after-operator-review" if ready else "hold" if held else "reject",
            "promotion_applied": False,
            "reason": "decision packet records an offline recommendation without changing release state or active artifacts",
        },
        reviewer_signoff_placeholders=(
            {
                "role": "release-captain",
                "status": "placeholder-required-before-activation",
                "signed_off": False,
            },
            {
                "role": "automation-guardrail-reviewer",
                "status": "placeholder-required-before-activation",
                "signed_off": False,
            },
        ),
        stale_evidence_holds=(
            {
                "hold_id": "source-freshness-hold",
                "applies_when": "source evidence is stale, missing, conflicting, or uncited",
                "hold_required": not ready,
                "release_state_changed": False,
            },
        ),
        activation_prerequisites=(
            {
                "prerequisite_id": "operator-signoff",
                "description": "operator signoff placeholders must be resolved outside this packet before activation",
                "satisfied_by_packet": False,
            },
            {
                "prerequisite_id": "validation-clean",
                "description": "offline validation commands must pass before any later activation decision",
                "satisfied_by_packet": ready,
            },
        ),
        rollback_plan=(
            {
                "step_id": "discard-packet",
                "action": "discard this synthetic packet if review fails",
                "requires_devhub": False,
                "mutates_release_state": False,
            },
            {
                "step_id": "retain-current-active-state",
                "action": "keep existing active release, guardrail, process, and surface-map state unchanged",
                "requires_devhub": False,
                "mutates_release_state": False,
            },
        ),
        post_decision_smoke_checks=(
            {
                "check_id": "packet-import-smoke",
                "command_ref": "py-compile-release-readiness-decision-packet-v3",
                "requires_network": False,
            },
            {
                "check_id": "daemon-self-test-smoke",
                "command_ref": "ppd-daemon-self-test",
                "requires_network": False,
            },
        ),
        validation_commands=OFFLINE_VALIDATION_COMMANDS,
        inactive_process_model_gate_recommendations=(
            {
                "gate": "process-model-coverage",
                "mode": "inactive-recommendation-only",
                "recommendation": "pass" if ready else "hold" if held else "reject",
                "reason": "synthetic replay evidence only; no active process-model mutation",
            },
            {
                "gate": "process-model-drift",
                "mode": "inactive-recommendation-only",
                "recommendation": "pass" if ready else "hold" if held else "reject",
                "reason": "fixture delta reviewed without changing requirements or contracts",
            },
        ),
        inactive_guardrail_gate_recommendations=(
            {
                "gate": "automation-safety",
                "mode": "inactive-recommendation-only",
                "recommendation": "pass" if ready else "hold" if held else "reject",
                "reason": "no CAPTCHA, MFA, upload, payment, scheduling, submission, or certification automation",
            },
            {
                "gate": "source-access",
                "mode": "inactive-recommendation-only",
                "recommendation": "pass",
                "reason": "packet is fixture-first and does not crawl live sources or open DevHub",
            },
        ),
        agent_readiness_replay={
            "source": "synthetic-fixture",
            "replayed_at": "2026-05-31T00:00:00Z",
            "result": "passed" if ready else "needs-review" if held else "failed",
            "release_state_mutation": False,
            "active_prompt_mutation": False,
        },
        devhub_observation_delta_holds=(
            {
                "surface": "DevHub permit observation",
                "delta": "none" if ready else "unverified fixture delta" if held else "conflicting fixture delta",
                "hold_required": not ready,
                "reason": "DevHub was not opened; disposition is synthetic and offline",
            },
        ),
        public_refresh_impact_summary={
            "source": "synthetic public refresh fixture",
            "crawl_performed": False,
            "impact": "no public refresh blocker" if ready else "public refresh requires reviewer hold" if held else "public refresh indicates release rejection",
            "artifact_promotion": False,
        },
        reviewer_dispositions=(
            {
                "reviewer": "release-captain",
                "disposition": "approve" if ready else "hold" if held else "reject",
                "notes": "synthetic disposition only; no forms, uploads, submissions, or certifications drafted",
            },
            {
                "reviewer": "automation-guardrail",
                "disposition": "approve" if ready else "hold" if held else "reject",
                "notes": "offline evidence packet preserves active guardrail and daemon state",
            },
        ),
        rollback_notes=(
            "No release state was changed by this packet.",
            "No artifacts were promoted; rollback is limited to discarding this synthetic packet.",
            "No DevHub session, private file, trace, crawl output, or downloaded document was created.",
        ),
        offline_validation_commands=OFFLINE_VALIDATION_COMMANDS,
        decision={
            "status": "ready" if ready else "held" if held else "rejected",
            "release_allowed": ready,
            "hold_required": held,
            "rejection_required": rejected,
            "basis": "synthetic offline fixture decision packet v3",
        },
    )
    result = packet.to_dict()
    assert_valid_release_readiness_decision_packet_v3(result)
    return result


def build_all_release_readiness_decision_packets_v3() -> dict[str, dict[str, Any]]:
    return {scenario: build_release_readiness_decision_packet_v3(scenario) for scenario in sorted(SCENARIOS)}
