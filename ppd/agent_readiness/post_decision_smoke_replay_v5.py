"""Fixture-first post-decision smoke replay v5 validation.

This packet is an offline replay artifact for release decision packet v5. It
requires explicit references to the release decision fixture and inactive
placeholder fixtures, requires every post-decision safety check row, and rejects
activation, private runtime artifacts, official-action completion claims,
permitting guarantees, and active mutation flags.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

PACKET_TYPE = "ppd.post_decision_smoke_replay.v5"
PACKET_VERSION = "v5"
MODE = "fixture_first_post_decision_smoke_replay_v5"
RELEASE_DECISION_PACKET_VERSION = "v5"
PLACEHOLDER_FIXTURE_KIND = "inactive_guardrail_placeholder_fixture"
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "release_decision_packet_v5_fixtures_only": True,
    "inactive_guardrail_placeholder_fixtures_only": True,
    "active_activation": False,
    "guardrail_activation_enabled": False,
    "active_mutation": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "upload_enabled": False,
    "submission_enabled": False,
    "certification_enabled": False,
    "payment_enabled": False,
    "scheduling_enabled": False,
    "legal_or_permitting_guarantee_enabled": False,
}

REQUIRED_ATTESTATIONS = {
    "active_activation_claimed": False,
    "guardrails_activated": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "official_action_completion_claimed": False,
    "legal_or_permitting_guarantees_made": False,
    "active_mutation_performed": False,
}

_REQUIRED_LISTS = (
    "go_no_go_outcome_checks",
    "inactive_guardrail_placeholder_checks",
    "unresolved_hold_propagation",
    "source_freshness_caveat_checks",
    "agent_api_compatibility_checks",
    "rollback_owner_placeholders",
    "manual_handoff_reminders",
    "agent_notification_rows",
    "smoke_expectations",
)

_REQUIRED_EXPECTATION_IDS = frozenset(
    {
        "release-decision-reference-check",
        "inactive-guardrail-placeholder-check",
        "go-no-go-outcome-check",
        "unresolved-hold-propagation-check",
        "source-freshness-caveat-check",
        "agent-api-compatibility-check",
        "rollback-owner-placeholder-check",
        "manual-handoff-reminder-check",
        "agent-notification-row-check",
        "validation-command-check",
    }
)

_FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_activation",
        "active_activation_claimed",
        "active_guardrail_activation",
        "active_guardrail_mutation",
        "active_guardrail_bundle_mutation",
        "active_prompt_mutation",
        "active_process_model_mutation",
        "active_requirement_mutation",
        "active_source_mutation",
        "active_devhub_surface_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "active_mutation_performed",
        "guardrail_activation_enabled",
        "guardrails_activated",
        "guardrails_changed",
        "promotion_executed",
        "activation_executed",
        "devhub_opened",
        "private_documents_read",
        "upload_enabled",
        "uploads_performed",
        "submission_enabled",
        "submissions_performed",
        "certification_enabled",
        "certifications_performed",
        "payment_enabled",
        "payments_performed",
        "scheduling_enabled",
        "scheduling_performed",
        "official_action_completion_claimed",
        "legal_or_permitting_guarantee",
        "legal_or_permitting_guarantee_enabled",
        "legal_or_permitting_guarantees_made",
    }
)

_PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser_state|cookie|credential|devhub_session|downloaded|har|password|payment|private|raw|screenshot|secret|session|session_state|storage_state|token|trace)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_TEXT_RE = re.compile(
    r"(activation complete|activated guardrail|active activation|active guardrail|active mutation|approval guaranteed|guaranteed approval|guaranteed issuance|legal advice|legal guarantee|permit will be approved|permit will be issued|will pass plan review|official action completed|submitted permit|uploaded correction|paid fee|scheduled inspection|certified acknowledgement|live devhub|session state|storage state|trace file|raw crawl|raw pdf|auth artifact)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PostDecisionSmokeReplayV5Result:
    valid: bool
    problems: tuple[str, ...]


class PostDecisionSmokeReplayV5Error(ValueError):
    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid post-decision smoke replay v5: " + "; ".join(self.problems))


def load_post_decision_smoke_replay_v5_fixture(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("post-decision smoke replay v5 source fixture must be an object")
    return build_post_decision_smoke_replay_v5(loaded)


def assert_valid_post_decision_smoke_replay_v5(packet: Mapping[str, Any]) -> None:
    result = validate_post_decision_smoke_replay_v5(packet)
    if not result.valid:
        raise PostDecisionSmokeReplayV5Error(result.problems)


def build_post_decision_smoke_replay_v5(source_fixture: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(source_fixture.get("release_decision_packet_v5"), "release_decision_packet_v5")
    placeholders = _mapping_sequence(source_fixture.get("inactive_guardrail_placeholder_fixtures"))
    _validate_release_decision_input(decision)
    _validate_placeholder_inputs(placeholders)

    recommendation_rows = _mapping_sequence(decision.get("reviewer_go_no_go_recommendation"))
    recommendation = _text(recommendation_rows[0].get("recommendation")) if recommendation_rows else "NO_GO"
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "post-decision-smoke-replay-v5-fixture",
        "mode": MODE,
        "consumes_only": {
            "release_decision_packet_v5_fixtures": True,
            "inactive_guardrail_placeholder_fixtures": True,
        },
        "required_source_references": _required_source_references(source_fixture, placeholders),
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "release_outcome_handling": {
            "go_no_go_outcome": recommendation,
            "activation_allowed": False,
            "agent_expected_outcome": "block_activation_and_surface_manual_release_review_requirements",
        },
        "go_no_go_outcome_checks": [_outcome_check(row) for row in recommendation_rows],
        "inactive_guardrail_placeholder_checks": [_placeholder_check(row) for row in placeholders],
        "unresolved_hold_propagation": [_hold_row(row) for row in _mapping_sequence(decision.get("unresolved_hold_inventory"))],
        "source_freshness_caveat_checks": [_freshness_check(row) for row in _mapping_sequence(decision.get("source_freshness_clearance_status"))],
        "agent_api_compatibility_checks": [_api_check(row) for row in _mapping_sequence(decision.get("agent_api_compatibility_caveats"))],
        "rollback_owner_placeholders": [_rollback_row(row) for row in _mapping_sequence(decision.get("rollback_owner_placeholders"))],
        "manual_handoff_reminders": _manual_handoff_reminders(),
        "agent_notification_rows": [_notification_row(row) for row in _mapping_sequence(decision.get("agent_notification_notes"))],
        "smoke_expectations": _smoke_expectations(),
        "attestations": dict(REQUIRED_ATTESTATIONS),
        "validation_commands": [list(command) for command in VALIDATION_COMMANDS],
    }
    assert_valid_post_decision_smoke_replay_v5(packet)
    return packet


def validate_post_decision_smoke_replay_v5(packet: Mapping[str, Any]) -> PostDecisionSmokeReplayV5Result:
    if not isinstance(packet, Mapping):
        return PostDecisionSmokeReplayV5Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v5")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {"release_decision_packet_v5_fixtures": True, "inactive_guardrail_placeholder_fixtures": True}:
        problems.append("consumes_only must allow only release decision packet v5 fixtures and inactive guardrail placeholder fixtures")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        problems.append("boundaries must exactly preserve offline fixture-only non-activation limits")
    if packet.get("attestations") != REQUIRED_ATTESTATIONS:
        problems.append("attestations must deny activation, DevHub access, private artifacts, official action completion, guarantees, and mutation")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    _validate_required_source_references(packet.get("required_source_references"), problems)
    _validate_release_outcome(packet.get("release_outcome_handling"), problems)
    for key in _REQUIRED_LISTS:
        if not _mapping_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    _validate_outcome_checks(packet.get("go_no_go_outcome_checks"), problems)
    _validate_placeholder_checks(packet.get("inactive_guardrail_placeholder_checks"), problems)
    _validate_hold_rows(packet.get("unresolved_hold_propagation"), problems)
    _validate_freshness_rows(packet.get("source_freshness_caveat_checks"), problems)
    _validate_api_rows(packet.get("agent_api_compatibility_checks"), problems)
    _validate_rollback_rows(packet.get("rollback_owner_placeholders"), problems)
    _validate_handoff_rows(packet.get("manual_handoff_reminders"), problems)
    _validate_notification_rows(packet.get("agent_notification_rows"), problems)
    _validate_smoke_expectations(packet.get("smoke_expectations"), problems)
    _scan_for_forbidden_payload(packet, "$", problems)
    return PostDecisionSmokeReplayV5Result(not problems, tuple(dict.fromkeys(problems)))


def _validate_release_decision_input(decision: Mapping[str, Any]) -> None:
    if decision.get("packet_version") != RELEASE_DECISION_PACKET_VERSION:
        raise ValueError("release_decision_packet_v5.packet_version must be v5")
    if decision.get("fixture_first") is not True or decision.get("inactive_candidate_fixture_only") is not True:
        raise ValueError("release decision packet v5 must be fixture-first inactive candidate data")
    for key in ("active_mutation", "active_guardrail_mutation", "active_release_state_mutation", "activation_executed", "opens_devhub", "reads_private_documents", "uploads", "submits", "certifies", "pays", "schedules", "legal_or_permitting_guarantee"):
        if decision.get(key) is not False:
            raise ValueError(f"release decision packet v5 {key} must be false")
    for key in ("reviewer_go_no_go_recommendation", "unresolved_hold_inventory", "source_freshness_clearance_status", "agent_api_compatibility_caveats", "rollback_owner_placeholders", "agent_notification_notes"):
        if not _mapping_sequence(decision.get(key)):
            raise ValueError(f"release decision packet v5 must include {key}")


def _validate_placeholder_inputs(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError("inactive_guardrail_placeholder_fixtures must be non-empty")
    for index, row in enumerate(rows):
        if row.get("fixture_kind") != PLACEHOLDER_FIXTURE_KIND:
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].fixture_kind must be {PLACEHOLDER_FIXTURE_KIND}")
        if row.get("placeholder_status") != "inactive_placeholder_only":
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].placeholder_status must be inactive_placeholder_only")
        if row.get("activation_allowed") is not False:
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].activation_allowed must be false")
        if not _text(row.get("placeholder_id")) or not _text(row.get("guardrail_bundle_id")):
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}] must include placeholder_id and guardrail_bundle_id")


def _validate_required_source_references(value: Any, problems: list[str]) -> None:
    refs = value if isinstance(value, Mapping) else {}
    if not _string_list(refs.get("release_decision_packet_v5_refs")):
        problems.append("required_source_references.release_decision_packet_v5_refs must be non-empty")
    if not _string_list(refs.get("inactive_guardrail_placeholder_fixture_refs")):
        problems.append("required_source_references.inactive_guardrail_placeholder_fixture_refs must be non-empty")


def _validate_release_outcome(value: Any, problems: list[str]) -> None:
    row = value if isinstance(value, Mapping) else {}
    if row.get("go_no_go_outcome") not in {"NO_GO", "GO_WITH_CAVEATS"}:
        problems.append("release_outcome_handling.go_no_go_outcome must be NO_GO or GO_WITH_CAVEATS")
    if row.get("activation_allowed") is not False:
        problems.append("release_outcome_handling.activation_allowed must be false")
    if not _text(row.get("agent_expected_outcome")):
        problems.append("release_outcome_handling.agent_expected_outcome is required")


def _validate_outcome_checks(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"go_no_go_outcome_checks[{index}]"
        if row.get("recommendation") not in {"NO_GO", "GO_WITH_CAVEATS"}:
            problems.append(f"{prefix}.recommendation must be NO_GO or GO_WITH_CAVEATS")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("manual_review_required") is not True:
            problems.append(f"{prefix}.manual_review_required must be true")


def _validate_placeholder_checks(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"inactive_guardrail_placeholder_checks[{index}]"
        for key in ("placeholder_id", "guardrail_bundle_id"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")
        if row.get("placeholder_status") != "inactive_placeholder_only":
            problems.append(f"{prefix}.placeholder_status must be inactive_placeholder_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_hold_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"unresolved_hold_propagation[{index}]"
        if not _text(row.get("hold_id")):
            problems.append(f"{prefix}.hold_id is required")
        if row.get("hold_status") != "unresolved_hold_propagated":
            problems.append(f"{prefix}.hold_status must be unresolved_hold_propagated")
        if row.get("blocks_activation") is not True:
            problems.append(f"{prefix}.blocks_activation must be true")


def _validate_freshness_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"source_freshness_caveat_checks[{index}]"
        if not _text(row.get("clearance_id")):
            problems.append(f"{prefix}.clearance_id is required")
        if row.get("caveat_display_required") is not True:
            problems.append(f"{prefix}.caveat_display_required must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_api_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"agent_api_compatibility_checks[{index}]"
        if not _text(row.get("caveat_id")):
            problems.append(f"{prefix}.caveat_id is required")
        if row.get("requires_manual_review") is not True:
            problems.append(f"{prefix}.requires_manual_review must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_rollback_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_owner_placeholders[{index}]"
        if not _text(row.get("rollback_owner_placeholder_id")):
            problems.append(f"{prefix}.rollback_owner_placeholder_id is required")
        if row.get("owner_assignment_status") != "pending_manual_assignment":
            problems.append(f"{prefix}.owner_assignment_status must be pending_manual_assignment")
        if row.get("active_state_changed") is not False:
            problems.append(f"{prefix}.active_state_changed must be false")


def _validate_handoff_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"manual_handoff_reminders[{index}]"
        if not _text(row.get("reminder_id")):
            problems.append(f"{prefix}.reminder_id is required")
        if row.get("handoff_status") != "pending_manual_handoff":
            problems.append(f"{prefix}.handoff_status must be pending_manual_handoff")
        if row.get("acknowledgement_required") is not True:
            problems.append(f"{prefix}.acknowledgement_required must be true")


def _validate_notification_rows(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"agent_notification_rows[{index}]"
        if not _text(row.get("note_id")):
            problems.append(f"{prefix}.note_id is required")
        if row.get("notification_status") != "draft_note_only":
            problems.append(f"{prefix}.notification_status must be draft_note_only")
        if row.get("requires_manual_review_before_release") is not True:
            problems.append(f"{prefix}.requires_manual_review_before_release must be true")


def _validate_smoke_expectations(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    ids = {_text(row.get("expectation_id")) for row in rows}
    missing = sorted(_REQUIRED_EXPECTATION_IDS - ids)
    if missing:
        problems.append("smoke_expectations missing required expectation ids: " + ", ".join(missing))
    for index, row in enumerate(rows):
        prefix = f"smoke_expectations[{index}]"
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if not _text(row.get("expected_result")):
            problems.append(f"{prefix}.expected_result is required")


def _outcome_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check_id": _stable_id("outcome", _text(row.get("recommendation_id"))),
        "recommendation": _text(row.get("recommendation")),
        "activation_allowed": False,
        "manual_review_required": True,
    }


def _placeholder_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "placeholder_id": _text(row.get("placeholder_id")),
        "guardrail_bundle_id": _text(row.get("guardrail_bundle_id")),
        "placeholder_status": "inactive_placeholder_only",
        "activation_allowed": False,
    }


def _hold_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "hold_id": _text(row.get("hold_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "hold_status": "unresolved_hold_propagated",
        "blocks_activation": True,
        "reviewer_disposition": "hold_until_resolved",
    }


def _freshness_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "clearance_id": _text(row.get("clearance_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "caveat_display_required": True,
        "activation_allowed": False,
    }


def _api_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "caveat_id": _text(row.get("caveat_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "requires_manual_review": True,
        "activation_allowed": False,
    }


def _rollback_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rollback_owner_placeholder_id": _text(row.get("rollback_owner_placeholder_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "owner_assignment_status": "pending_manual_assignment",
        "active_state_changed": False,
    }


def _manual_handoff_reminders() -> list[dict[str, Any]]:
    return [
        {
            "reminder_id": "manual-handoff-release-reviewer-v5",
            "handoff_status": "pending_manual_handoff",
            "acknowledgement_required": True,
            "reminder": "Human release reviewer must reconcile release decision holds before any separate activation review.",
        },
        {
            "reminder_id": "manual-handoff-agent-consumer-v5",
            "handoff_status": "pending_manual_handoff",
            "acknowledgement_required": True,
            "reminder": "Agent consumers must display caveats and keep consequential actions blocked.",
        },
    ]


def _notification_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "note_id": _text(row.get("note_id")),
        "candidate_id": _text(row.get("candidate_id")),
        "notification_status": "draft_note_only",
        "requires_manual_review_before_release": True,
    }


def _smoke_expectations() -> list[dict[str, Any]]:
    return [
        {"expectation_id": expectation_id, "expected_result": "required_and_rejected_if_missing", "activation_allowed": False}
        for expectation_id in sorted(_REQUIRED_EXPECTATION_IDS)
    ]


def _required_source_references(source_fixture: Mapping[str, Any], placeholders: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    release_refs = _string_list(source_fixture.get("release_decision_packet_v5_refs"))
    placeholder_refs = _string_list(source_fixture.get("inactive_guardrail_placeholder_fixture_refs"))
    if not placeholder_refs:
        placeholder_refs = [_text(row.get("placeholder_id")) for row in placeholders if _text(row.get("placeholder_id"))]
    return {
        "release_decision_packet_v5_refs": release_refs,
        "inactive_guardrail_placeholder_fixture_refs": placeholder_refs,
    }


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized_key = key.lower().replace("-", "_")
            child_path = f"{path}.{key}" if path != "$" else key
            if normalized_key in _FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"{child_path} must not be true")
            if _PRIVATE_KEY_RE.search(normalized_key) and _truthy(child):
                problems.append(f"{child_path} must not contain private, session, auth, raw, browser, trace, payment, or downloaded artifacts")
            _scan_for_forbidden_payload(child, child_path, problems)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)
        return
    if isinstance(value, str) and _FORBIDDEN_TEXT_RE.search(value):
        problems.append(f"{path} contains a prohibited activation, private-artifact, official-action, guarantee, live, or mutation claim")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in (_text(item) for item in value) if item]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"
