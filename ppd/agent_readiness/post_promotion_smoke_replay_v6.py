"""Fixture-first post-promotion smoke replay v6.

This packet consumes only inactive guardrail promotion rehearsal v6 fixtures and
inactive guardrail placeholder fixtures. It verifies post-promotion agent-facing
smoke expectations while remaining offline, inactive, and non-mutating.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.inactive_guardrail_promotion_rehearsal_v6 import (
    PACKET_TYPE as PROMOTION_REHEARSAL_PACKET_TYPE,
    PACKET_VERSION as PROMOTION_REHEARSAL_PACKET_VERSION,
    assert_valid_inactive_guardrail_promotion_rehearsal_v6,
)

PACKET_TYPE = "ppd.post_promotion_smoke_replay.v6"
PACKET_VERSION = "v6"
MODE = "fixture_first_post_promotion_smoke_replay_v6"
PLACEHOLDER_FIXTURE_KIND = "inactive_guardrail_placeholder_fixture"
PLACEHOLDER_STATUS = "inactive_placeholder_only"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/post_promotion_smoke_replay_v6.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_post_promotion_smoke_replay_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_post_promotion_smoke_replay_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "inactive_guardrail_promotion_rehearsal_v6_fixtures_only": True,
    "inactive_guardrail_placeholder_fixtures_only": True,
    "post_promotion_smoke_replay_only": True,
    "active_guardrail_mutation": False,
    "active_guardrail_bundle_mutation": False,
    "active_prompt_mutation": False,
    "active_process_model_mutation": False,
    "active_requirement_mutation": False,
    "active_source_mutation": False,
    "active_devhub_surface_mutation": False,
    "active_release_state_mutation": False,
    "active_mutation": False,
    "guardrails_activated": False,
    "guardrails_changed": False,
    "promotion_executed": False,
    "activation_executed": False,
    "devhub_opened": False,
    "live_crawling_enabled": False,
    "private_documents_read": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "legal_or_permitting_guarantees_made": False,
}

REQUIRED_ATTESTATIONS = {
    "active_activation_claimed": False,
    "guardrails_activated": False,
    "guardrail_mutation_performed": False,
    "devhub_opened": False,
    "live_sites_crawled": False,
    "private_documents_read": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "legal_or_permitting_guarantees_made": False,
}

REQUIRED_LIST_FIELDS = (
    "source_fixture_refs",
    "inactive_guardrail_placeholder_checks",
    "lookup_health_checks",
    "unresolved_hold_display_checks",
    "stale_source_stop_gates",
    "exact_confirmation_checkpoint_checks",
    "refused_action_checks",
    "reversible_draft_only_routing_checks",
    "local_pdf_preview_routing_checks",
    "rollback_trigger_visibility_checks",
    "manual_handoff_reminders",
    "smoke_expectations",
    "exact_offline_validation_commands",
    "validation_commands",
)

REQUIRED_EXPECTATION_IDS = frozenset(
    {
        "lookup-health-check",
        "unresolved-hold-display-check",
        "stale-source-stop-gate-check",
        "exact-confirmation-checkpoint-check",
        "refused-consequential-action-check",
        "refused-financial-action-check",
        "reversible-draft-only-routing-check",
        "local-pdf-preview-routing-check",
        "rollback-trigger-visibility-check",
        "manual-handoff-reminder-check",
        "exact-offline-validation-command-check",
    }
)

FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_activation",
        "active_activation_claimed",
        "active_guardrail_mutation",
        "active_guardrail_bundle_mutation",
        "active_prompt_mutation",
        "active_process_model_mutation",
        "active_requirement_mutation",
        "active_source_mutation",
        "active_devhub_surface_mutation",
        "active_release_state_mutation",
        "active_mutation",
        "guardrail_mutation_performed",
        "guardrails_activated",
        "guardrails_changed",
        "promotion_executed",
        "activation_executed",
        "devhub_opened",
        "live_crawling_enabled",
        "live_sites_crawled",
        "private_documents_read",
        "uploads_performed",
        "submissions_performed",
        "certifications_performed",
        "payments_performed",
        "scheduling_performed",
        "legal_or_permitting_guarantees_made",
    }
)

PRIVATE_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|devhub[_-]?session|download|downloaded|har|password|payment|private|raw|screenshot|secret|session|storage[_-]?state|token|trace)(_|$)",
    re.IGNORECASE,
)
FORBIDDEN_TEXT_RE = re.compile(
    r"(guardrails activated|active activation|active guardrail|active mutation|opened devhub|live crawl|submitted permit|uploaded correction|certified acknowledgement|paid fee|scheduled inspection|official action completed|approval guaranteed|permit guaranteed|permit will be approved|permit will be issued|legal advice|session cookie|auth state|storage state|trace file|raw crawl|raw pdf|private document)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PostPromotionSmokeReplayV6Result:
    valid: bool
    problems: tuple[str, ...]


class PostPromotionSmokeReplayV6Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid post-promotion smoke replay v6: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("post-promotion smoke replay v6 fixture must be a JSON object")
    return loaded


def build_post_promotion_smoke_replay_v6_from_fixture(path: str | Path) -> dict[str, Any]:
    return build_post_promotion_smoke_replay_v6(load_json(path))


def build_post_promotion_smoke_replay_v6(source_fixture: Mapping[str, Any]) -> dict[str, Any]:
    promotion = _mapping(source_fixture.get("inactive_guardrail_promotion_rehearsal_v6"), "inactive_guardrail_promotion_rehearsal_v6")
    placeholders = _mapping_sequence(source_fixture.get("inactive_guardrail_placeholder_fixtures"))
    _validate_promotion_input(promotion)
    _validate_placeholder_inputs(placeholders)

    candidates = _mapping_sequence(promotion.get("inactive_promotion_candidate_rows"))
    holds = _mapping_sequence(promotion.get("unresolved_hold_propagation_rows"))
    freshness = _mapping_sequence(promotion.get("source_freshness_clearance_prerequisites"))
    rollback = _mapping_sequence(promotion.get("rollback_checkpoint_rows"))
    api_rows = _mapping_sequence(promotion.get("agent_api_compatibility_reminders"))
    monitoring_rows = _mapping_sequence(promotion.get("monitoring_handoff_rows"))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "post-promotion-smoke-replay-v6-fixture",
        "mode": MODE,
        "consumes_only": {
            "inactive_guardrail_promotion_rehearsal_v6_fixtures": True,
            "inactive_guardrail_placeholder_fixtures": True,
            "promotion_packet_type": PROMOTION_REHEARSAL_PACKET_TYPE,
            "promotion_packet_version": PROMOTION_REHEARSAL_PACKET_VERSION,
        },
        "source_fixture_refs": _source_refs(source_fixture, placeholders),
        "boundaries": copy.deepcopy(REQUIRED_BOUNDARIES),
        "inactive_guardrail_placeholder_checks": [_placeholder_check(row) for row in placeholders],
        "lookup_health_checks": [_lookup_check(row) for row in candidates],
        "unresolved_hold_display_checks": [_hold_display_check(row) for row in holds],
        "stale_source_stop_gates": _stale_source_stop_gates(freshness, holds),
        "exact_confirmation_checkpoint_checks": [_confirmation_checkpoint(row) for row in candidates],
        "refused_action_checks": _refused_action_checks(candidates),
        "reversible_draft_only_routing_checks": [_draft_route(row) for row in candidates],
        "local_pdf_preview_routing_checks": [_pdf_route(row) for row in candidates],
        "rollback_trigger_visibility_checks": [_rollback_visibility(row) for row in rollback],
        "manual_handoff_reminders": _manual_handoff_reminders(api_rows, monitoring_rows),
        "smoke_expectations": _smoke_expectations(),
        "attestations": copy.deepcopy(REQUIRED_ATTESTATIONS),
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "validation_commands": copy.deepcopy(VALIDATION_COMMANDS),
    }
    assert_valid_post_promotion_smoke_replay_v6(packet)
    return packet


def load_post_promotion_smoke_replay_v6(path: str | Path) -> dict[str, Any]:
    packet = load_json(path)
    assert_valid_post_promotion_smoke_replay_v6(packet)
    return packet


def assert_valid_post_promotion_smoke_replay_v6(packet: Mapping[str, Any]) -> None:
    result = validate_post_promotion_smoke_replay_v6(packet)
    if not result.valid:
        raise PostPromotionSmokeReplayV6Error(result.problems)


def validate_post_promotion_smoke_replay_v6(packet: Mapping[str, Any]) -> PostPromotionSmokeReplayV6Result:
    if not isinstance(packet, Mapping):
        return PostPromotionSmokeReplayV6Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v6")
    if packet.get("mode") != MODE:
        problems.append(f"mode must be {MODE}")
    if packet.get("consumes_only") != {
        "inactive_guardrail_promotion_rehearsal_v6_fixtures": True,
        "inactive_guardrail_placeholder_fixtures": True,
        "promotion_packet_type": PROMOTION_REHEARSAL_PACKET_TYPE,
        "promotion_packet_version": PROMOTION_REHEARSAL_PACKET_VERSION,
    }:
        problems.append("consumes_only must allow only inactive guardrail promotion rehearsal v6 fixtures and inactive guardrail placeholder fixtures")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        problems.append("boundaries must exactly preserve fixture-only inactive non-activation limits")
    if packet.get("attestations") != REQUIRED_ATTESTATIONS:
        problems.append("attestations must deny activation, live access, official actions, guarantees, and mutation")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match post-promotion smoke replay v6 commands")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    for key in REQUIRED_LIST_FIELDS:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    _validate_source_refs(packet.get("source_fixture_refs"), problems)
    _validate_placeholder_checks(packet.get("inactive_guardrail_placeholder_checks"), problems)
    _validate_lookup_checks(packet.get("lookup_health_checks"), problems)
    _validate_hold_display(packet.get("unresolved_hold_display_checks"), problems)
    _validate_stale_stop_gates(packet.get("stale_source_stop_gates"), problems)
    _validate_confirmation(packet.get("exact_confirmation_checkpoint_checks"), problems)
    _validate_refused_actions(packet.get("refused_action_checks"), problems)
    _validate_draft_routes(packet.get("reversible_draft_only_routing_checks"), problems)
    _validate_pdf_routes(packet.get("local_pdf_preview_routing_checks"), problems)
    _validate_rollback(packet.get("rollback_trigger_visibility_checks"), problems)
    _validate_handoffs(packet.get("manual_handoff_reminders"), problems)
    _validate_smoke_expectations(packet.get("smoke_expectations"), problems)
    _scan_for_forbidden_payload(packet, "packet", problems)
    return PostPromotionSmokeReplayV6Result(not problems, tuple(dict.fromkeys(problems)))


def _validate_promotion_input(promotion: Mapping[str, Any]) -> None:
    assert_valid_inactive_guardrail_promotion_rehearsal_v6(promotion)
    if promotion.get("packet_type") != PROMOTION_REHEARSAL_PACKET_TYPE:
        raise ValueError("inactive_guardrail_promotion_rehearsal_v6.packet_type must be inactive guardrail promotion rehearsal v6")
    if promotion.get("packet_version") != PROMOTION_REHEARSAL_PACKET_VERSION:
        raise ValueError("inactive_guardrail_promotion_rehearsal_v6.packet_version must be v6")


def _validate_placeholder_inputs(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError("inactive_guardrail_placeholder_fixtures must be non-empty")
    for index, row in enumerate(rows):
        if row.get("fixture_kind") != PLACEHOLDER_FIXTURE_KIND:
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].fixture_kind must be {PLACEHOLDER_FIXTURE_KIND}")
        if row.get("placeholder_status") != PLACEHOLDER_STATUS:
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].placeholder_status must be {PLACEHOLDER_STATUS}")
        if row.get("activation_allowed") is not False:
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}].activation_allowed must be false")
        if not _text(row.get("placeholder_id")) or not _text(row.get("guardrail_bundle_id")):
            raise ValueError(f"inactive_guardrail_placeholder_fixtures[{index}] must include placeholder_id and guardrail_bundle_id")


def _source_refs(source_fixture: Mapping[str, Any], placeholders: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs = []
    for ref in _string_list(source_fixture.get("inactive_guardrail_promotion_rehearsal_v6_refs")):
        refs.append({"fixture_role": "inactive_guardrail_promotion_rehearsal_v6", "path": ref})
    placeholder_refs = _string_list(source_fixture.get("inactive_guardrail_placeholder_fixture_refs"))
    if not placeholder_refs:
        placeholder_refs = [_text(row.get("placeholder_id")) for row in placeholders if _text(row.get("placeholder_id"))]
    for ref in placeholder_refs:
        refs.append({"fixture_role": "inactive_guardrail_placeholder_fixture", "path": ref})
    return refs


def _placeholder_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "placeholder_id": _text(row.get("placeholder_id")),
        "guardrail_bundle_id": _text(row.get("guardrail_bundle_id")),
        "placeholder_status": PLACEHOLDER_STATUS,
        "activation_allowed": False,
    }


def _lookup_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check_id": f"lookup::{_text(row.get('candidate_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "lookup_status": "healthy_fixture_lookup",
        "fixture_lookup_only": True,
        "activation_allowed": False,
    }


def _hold_display_check(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check_id": f"hold-display::{_text(row.get('propagation_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "source_hold_id": _text(row.get("source_hold_id")),
        "hold_type": _text(row.get("hold_type")),
        "display_status": "display_unresolved_hold",
        "unresolved_hold_visible": True,
        "blocks_agent_ready": True,
    }


def _stale_source_stop_gates(freshness: Sequence[Mapping[str, Any]], holds: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in freshness:
        rows.append(
            {
                "gate_id": f"stale-source::{_text(row.get('prerequisite_id'))}",
                "candidate_id": _text(row.get("candidate_id")),
                "gate_status": "stop_until_source_freshness_review",
                "stop_gate_triggered": True,
                "source_may_be_used_for_final_answer": False,
                "activation_allowed": False,
            }
        )
    for row in holds:
        if _text(row.get("hold_type")) == "stale_evidence":
            rows.append(
                {
                    "gate_id": f"stale-hold::{_text(row.get('source_hold_id'))}",
                    "candidate_id": _text(row.get("candidate_id")),
                    "gate_status": "stop_until_stale_hold_review",
                    "stop_gate_triggered": True,
                    "source_may_be_used_for_final_answer": False,
                    "activation_allowed": False,
                }
            )
    return rows


def _confirmation_checkpoint(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": f"exact-confirmation::{_text(row.get('candidate_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "checkpoint_status": "required_before_consequential_step",
        "exact_confirmation_required": True,
        "checkpoint_executed": False,
        "activation_allowed": False,
    }


def _refused_action_checks(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        candidate_id = _text(candidate.get("candidate_id"))
        for action_category in ("consequential", "financial"):
            rows.append(
                {
                    "check_id": f"refused-{action_category}::{candidate_id}",
                    "candidate_id": candidate_id,
                    "action_category": action_category,
                    "refused": True,
                    "manual_handoff_required": True,
                    "official_action_completed": False,
                }
            )
    return rows


def _draft_route(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "route_id": f"draft-only::{_text(row.get('candidate_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "route": "reversible_draft_only",
        "draft_may_be_prepared": True,
        "official_action_allowed": False,
    }


def _pdf_route(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "route_id": f"local-pdf-preview::{_text(row.get('candidate_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "route": "local_pdf_preview_only",
        "local_preview_allowed": True,
        "upload_allowed": False,
    }


def _rollback_visibility(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "trigger_id": f"rollback-visible::{_text(row.get('checkpoint_id'))}",
        "candidate_id": _text(row.get("candidate_id")),
        "rollback_trigger_visible": True,
        "rollback_target": _text(row.get("rollback_target")),
        "active_state_changed": False,
    }


def _manual_handoff_reminders(api_rows: Sequence[Mapping[str, Any]], monitoring_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in api_rows:
        rows.append(
            {
                "reminder_id": f"manual-handoff::{_text(row.get('reminder_id'))}",
                "candidate_id": _text(row.get("candidate_id")),
                "handoff_status": "pending_manual_handoff",
                "acknowledgement_required": True,
                "display_required": True,
            }
        )
    for row in monitoring_rows:
        rows.append(
            {
                "reminder_id": f"monitoring-handoff::{_text(row.get('handoff_id'))}",
                "candidate_id": _text(row.get("candidate_id")),
                "handoff_status": "pending_manual_handoff",
                "acknowledgement_required": True,
                "display_required": True,
            }
        )
    return rows


def _smoke_expectations() -> list[dict[str, Any]]:
    return [
        {"expectation_id": expectation_id, "expected_result": "required_and_rejected_if_missing", "activation_allowed": False}
        for expectation_id in sorted(REQUIRED_EXPECTATION_IDS)
    ]


def _validate_source_refs(value: Any, problems: list[str]) -> None:
    refs = _mapping_sequence(value)
    roles = {_text(row.get("fixture_role")) for row in refs}
    if "inactive_guardrail_promotion_rehearsal_v6" not in roles:
        problems.append("source_fixture_refs must include an inactive_guardrail_promotion_rehearsal_v6 fixture")
    if "inactive_guardrail_placeholder_fixture" not in roles:
        problems.append("source_fixture_refs must include an inactive_guardrail_placeholder_fixture")
    for index, row in enumerate(refs):
        if not _text(row.get("path")):
            problems.append(f"source_fixture_refs[{index}].path is required")


def _validate_placeholder_checks(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"inactive_guardrail_placeholder_checks[{index}]"
        if not _text(row.get("placeholder_id")) or not _text(row.get("guardrail_bundle_id")):
            problems.append(f"{prefix} must include placeholder_id and guardrail_bundle_id")
        if row.get("placeholder_status") != PLACEHOLDER_STATUS:
            problems.append(f"{prefix}.placeholder_status must be {PLACEHOLDER_STATUS}")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_lookup_checks(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"lookup_health_checks[{index}]"
        if row.get("lookup_status") != "healthy_fixture_lookup":
            problems.append(f"{prefix}.lookup_status must be healthy_fixture_lookup")
        if row.get("fixture_lookup_only") is not True:
            problems.append(f"{prefix}.fixture_lookup_only must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_hold_display(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"unresolved_hold_display_checks[{index}]"
        if row.get("display_status") != "display_unresolved_hold":
            problems.append(f"{prefix}.display_status must be display_unresolved_hold")
        if row.get("unresolved_hold_visible") is not True:
            problems.append(f"{prefix}.unresolved_hold_visible must be true")
        if row.get("blocks_agent_ready") is not True:
            problems.append(f"{prefix}.blocks_agent_ready must be true")


def _validate_stale_stop_gates(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"stale_source_stop_gates[{index}]"
        if row.get("stop_gate_triggered") is not True:
            problems.append(f"{prefix}.stop_gate_triggered must be true")
        if row.get("source_may_be_used_for_final_answer") is not False:
            problems.append(f"{prefix}.source_may_be_used_for_final_answer must be false")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_confirmation(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"exact_confirmation_checkpoint_checks[{index}]"
        if row.get("exact_confirmation_required") is not True:
            problems.append(f"{prefix}.exact_confirmation_required must be true")
        if row.get("checkpoint_executed") is not False:
            problems.append(f"{prefix}.checkpoint_executed must be false")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")


def _validate_refused_actions(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    categories = {_text(row.get("action_category")) for row in rows}
    if "consequential" not in categories:
        problems.append("refused_action_checks must include a consequential action refusal")
    if "financial" not in categories:
        problems.append("refused_action_checks must include a financial action refusal")
    for index, row in enumerate(rows):
        prefix = f"refused_action_checks[{index}]"
        if row.get("refused") is not True:
            problems.append(f"{prefix}.refused must be true")
        if row.get("manual_handoff_required") is not True:
            problems.append(f"{prefix}.manual_handoff_required must be true")
        if row.get("official_action_completed") is not False:
            problems.append(f"{prefix}.official_action_completed must be false")


def _validate_draft_routes(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"reversible_draft_only_routing_checks[{index}]"
        if row.get("route") != "reversible_draft_only":
            problems.append(f"{prefix}.route must be reversible_draft_only")
        if row.get("draft_may_be_prepared") is not True:
            problems.append(f"{prefix}.draft_may_be_prepared must be true")
        if row.get("official_action_allowed") is not False:
            problems.append(f"{prefix}.official_action_allowed must be false")


def _validate_pdf_routes(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"local_pdf_preview_routing_checks[{index}]"
        if row.get("route") != "local_pdf_preview_only":
            problems.append(f"{prefix}.route must be local_pdf_preview_only")
        if row.get("local_preview_allowed") is not True:
            problems.append(f"{prefix}.local_preview_allowed must be true")
        if row.get("upload_allowed") is not False:
            problems.append(f"{prefix}.upload_allowed must be false")


def _validate_rollback(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_trigger_visibility_checks[{index}]"
        if row.get("rollback_trigger_visible") is not True:
            problems.append(f"{prefix}.rollback_trigger_visible must be true")
        if row.get("active_state_changed") is not False:
            problems.append(f"{prefix}.active_state_changed must be false")


def _validate_handoffs(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"manual_handoff_reminders[{index}]"
        if row.get("handoff_status") != "pending_manual_handoff":
            problems.append(f"{prefix}.handoff_status must be pending_manual_handoff")
        if row.get("acknowledgement_required") is not True:
            problems.append(f"{prefix}.acknowledgement_required must be true")
        if row.get("display_required") is not True:
            problems.append(f"{prefix}.display_required must be true")


def _validate_smoke_expectations(value: Any, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    ids = {_text(row.get("expectation_id")) for row in rows}
    missing = sorted(REQUIRED_EXPECTATION_IDS - ids)
    if missing:
        problems.append("smoke_expectations missing required expectation ids: " + ", ".join(missing))
    for index, row in enumerate(rows):
        if row.get("activation_allowed") is not False:
            problems.append(f"smoke_expectations[{index}].activation_allowed must be false")
        if not _text(row.get("expected_result")):
            problems.append(f"smoke_expectations[{index}].expected_result is required")


def _scan_for_forbidden_payload(value: Any, path: str, problems: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized_key = key.lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized_key in FORBIDDEN_TRUE_KEYS and child is True:
                problems.append(f"{child_path} must not be true")
            if PRIVATE_KEY_RE.search(normalized_key) and _truthy(child):
                problems.append(f"{child_path} must not contain private, auth, browser, trace, raw, payment, or downloaded artifacts")
            _scan_for_forbidden_payload(child, child_path, problems)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", problems)
        return
    if isinstance(value, str) and FORBIDDEN_TEXT_RE.search(value):
        problems.append(f"{path} contains a prohibited activation, live-access, official-action, guarantee, private-artifact, or mutation claim")


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


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
