"""Fixture-first PP&D agent guardrail API compatibility packet v6.

This module intentionally builds and validates inactive API compatibility rows
from committed fixtures and synthetic requests only. It does not activate
guardrails, open DevHub, crawl live sites, read private documents, upload,
submit, certify, pay, schedule, or make legal/permitting guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

PACKET_VERSION = "agent-guardrail-api-compatibility-v6"
SOURCE_FIXTURE_VERSION = "post-activation-monitoring-rehearsal-v5"
INACTIVE_STATUS = "inactive_fixture_only"
OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/logic/agent_guardrail_api_compat_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_agent_guardrail_api_compat_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]
PROHIBITED_EFFECTS: tuple[str, ...] = (
    "activate_guardrails",
    "open_devhub",
    "crawl_live_sites",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantee",
)
REQUIRED_SCENARIOS: tuple[str, ...] = (
    "missing_facts",
    "stale_source_block",
    "conflicting_evidence_block",
    "reversible_draft_only_action",
    "exact_confirmation_checkpoint",
    "refused_consequential_action",
    "refused_financial_action",
    "citation_payload",
    "manual_handoff_routing",
    "rollback_notes",
    "monitoring_references",
    "exact_offline_validation_commands",
)
PRIVATE_ARTIFACT_KEYS: tuple[str, ...] = (
    "credential",
    "credentials",
    "password",
    "cookie",
    "cookies",
    "session_state",
    "storage_state",
    "auth_state",
    "trace",
    "traces",
    "har",
    "screenshot",
    "screenshots",
    "payment_detail",
    "payment_details",
    "private_file_path",
    "local_private_file_path",
)
PRIVATE_ARTIFACT_VALUE_MARKERS: tuple[str, ...] = (
    "cookie=",
    "set-cookie",
    "bearer ",
    "authorization:",
    "storage_state",
    ".har",
    "trace.zip",
    "screenshot.png",
)
OFFICIAL_COMPLETION_KEYS: tuple[str, ...] = (
    "official_action_completed",
    "official_completion_claim",
    "submission_completed",
    "payment_completed",
    "certification_completed",
    "permit_guarantee",
    "legal_guarantee",
)


@dataclass(frozen=True)
class SyntheticAgentRequest:
    """A committed, non-live request used to shape inactive API rows."""

    request_id: str
    scenario: str
    requested_action: str
    supplied_facts: dict[str, Any]
    evidence_ids: list[str]


ROW_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "row_id": "v6-request-missing-facts-property-and-scope",
        "row_kind": "request",
        "scenario": "missing_facts",
        "requested_action": "analyze_readiness",
        "expected_block": "ask_for_missing_facts",
        "inactive_request": {
            "known_facts": {"permit_type": "building permit"},
            "missing_facts": ["site_address", "work_scope", "applicant_role"],
        },
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "needs_more_information",
            "missing_fact_prompts": [
                "What site address should be used for the fixture-only readiness check?",
                "What work scope should be matched before drafting any next action?",
            ],
            "message_key": "missing_facts_required_before_process_matching",
        },
    },
    {
        "row_id": "v6-response-stale-source-block",
        "row_kind": "response",
        "scenario": "stale_source_block",
        "requested_action": "recommend_next_step",
        "expected_block": "source_refresh_required",
        "inactive_request": {
            "known_facts": {"permit_type": "trade permit"},
            "source_freshness": "stale",
        },
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "blocked",
            "stale_source_block": True,
            "reason": "source evidence is older than the monitoring freshness policy",
        },
    },
    {
        "row_id": "v6-response-conflicting-evidence-block",
        "row_kind": "response",
        "scenario": "conflicting_evidence_block",
        "requested_action": "compile_requirement",
        "expected_block": "human_review_required",
        "inactive_request": {
            "conflicting_evidence": ["devhub-guide-submit-permit-application", "submit-plans-online"],
        },
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "blocked",
            "conflicting_evidence_block": True,
            "reason": "fixture evidence conflicts and must be resolved before formalization",
        },
    },
    {
        "row_id": "v6-response-reversible-draft-only-action",
        "row_kind": "response",
        "scenario": "reversible_draft_only_action",
        "requested_action": "draft_form_values",
        "expected_block": "draft_only_no_official_effect",
        "inactive_request": {
            "draft_surface": "local_pdf_preview",
            "facts_are_sufficient_for_draft": True,
        },
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "draft_allowed_if_activated_elsewhere",
            "next_actions": [
                {
                    "label": "prepare local draft preview",
                    "draft_only": True,
                    "reversible": True,
                    "official_effect": False,
                }
            ],
            "limits": ["local preview only", "no upload", "no submit", "no certification"],
        },
    },
    {
        "row_id": "v6-request-exact-confirmation-checkpoint",
        "row_kind": "request",
        "scenario": "exact_confirmation_checkpoint",
        "requested_action": "prepare_checkpoint",
        "expected_block": "await_exact_user_confirmation",
        "inactive_request": {
            "checkpoint_text": "I confirm I want to submit this permit application.",
            "official_action": "submit permit application",
        },
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "checkpoint_required",
            "exact_confirmation_checkpoint": True,
            "confirmation_match": "exact_text_only",
        },
    },
    {
        "row_id": "v6-response-refused-consequential-action",
        "row_kind": "response",
        "scenario": "refused_consequential_action",
        "requested_action": "submit_application",
        "expected_block": "refuse_official_action",
        "inactive_request": {"official_action": "submit", "user_attended": False},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "refused",
            "refusal_explanation": "official submissions require attended exact confirmation and are not performed by this packet",
            "reason": "official submissions require attended exact confirmation and are not performed by this packet",
        },
    },
    {
        "row_id": "v6-response-refused-financial-action",
        "row_kind": "response",
        "scenario": "refused_financial_action",
        "requested_action": "pay_fee",
        "expected_block": "refuse_financial_action",
        "inactive_request": {"official_action": "pay", "payment_details_present": False},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "refused",
            "refusal_explanation": "payment entry and final payment execution are outside this inactive fixture packet",
            "reason": "payment entry and final payment execution are outside this inactive fixture packet",
        },
    },
    {
        "row_id": "v6-response-citation-payload",
        "row_kind": "response",
        "scenario": "citation_payload",
        "requested_action": "explain_requirement",
        "expected_block": "cite_public_fixture_evidence",
        "inactive_request": {"requirement_id": "fixture-requirement-upload-staging"},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "explain_with_citations",
            "citation_payload_required": True,
        },
    },
    {
        "row_id": "v6-response-manual-handoff-routing",
        "row_kind": "response",
        "scenario": "manual_handoff_routing",
        "requested_action": "continue_authenticated_workflow",
        "expected_block": "manual_handoff",
        "inactive_request": {"auth_scope": "devhub_authenticated", "requires_attendance": True},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "manual_handoff_required",
            "handoff_route": "attended_devhub_worker",
        },
    },
    {
        "row_id": "v6-response-rollback-notes",
        "row_kind": "response",
        "scenario": "rollback_notes",
        "requested_action": "save_reversible_draft",
        "expected_block": "record_rollback_notes",
        "inactive_request": {"draft_action": "fill local preview field", "reversible": True},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "record_rollback_notes_only",
            "rollback_notes": ["discard local draft preview", "restore fixture request state"],
        },
    },
    {
        "row_id": "v6-response-monitoring-references",
        "row_kind": "response",
        "scenario": "monitoring_references",
        "requested_action": "link_monitoring_rehearsal",
        "expected_block": "reference_v5_monitoring_fixture",
        "inactive_request": {"monitoring_fixture_version": SOURCE_FIXTURE_VERSION},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "monitoring_reference_attached",
            "monitoring_reference_required": True,
        },
    },
    {
        "row_id": "v6-response-exact-offline-validation-commands",
        "row_kind": "response",
        "scenario": "exact_offline_validation_commands",
        "requested_action": "validate_packet",
        "expected_block": "offline_validation_only",
        "inactive_request": {"network_allowed": False, "live_devhub_allowed": False},
        "inactive_response": {
            "status": INACTIVE_STATUS,
            "decision": "offline_validation_commands_only",
            "validation_commands": OFFLINE_VALIDATION_COMMANDS,
        },
    },
)


class AgentGuardrailApiCompatV6ValidationError(ValueError):
    """Raised when a v6 compatibility packet omits a required safety control."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("invalid agent guardrail API compatibility packet v6: " + "; ".join(problems))


def load_json_fixture(path: Path) -> dict[str, Any]:
    """Load a committed JSON fixture with no network or private-document access."""

    with path.open("r", encoding="utf-8") as fixture_file:
        loaded = json.load(fixture_file)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must contain a JSON object: {path}")
    return loaded


def synthetic_agent_requests() -> list[SyntheticAgentRequest]:
    evidence_by_scenario = {
        "missing_facts": ["ppd-landing", "apply-permits"],
        "stale_source_block": ["devhub-faqs"],
        "conflicting_evidence_block": ["ppd-landing", "apply-permits"],
        "refused_financial_action": ["how-pay-fees"],
    }
    requests: list[SyntheticAgentRequest] = []
    for template in ROW_TEMPLATES:
        scenario = str(template["scenario"])
        requests.append(
            SyntheticAgentRequest(
                request_id=f"synthetic-agent-request-{scenario.replace('_', '-')}",
                scenario=scenario,
                requested_action=str(template["requested_action"]),
                supplied_facts=dict(template["inactive_request"]),
                evidence_ids=evidence_by_scenario.get(scenario, ["ppd-landing"]),
            )
        )
    return requests


def _fixture_evidence_index(monitoring_fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evidence_rows = monitoring_fixture.get("evidence")
    if not isinstance(evidence_rows, list):
        raise ValueError("Monitoring fixture must include an evidence list")
    index: dict[str, dict[str, Any]] = {}
    for row in evidence_rows:
        if not isinstance(row, dict):
            raise ValueError("Monitoring fixture evidence rows must be objects")
        evidence_id = row.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError("Monitoring fixture evidence rows need evidence_id")
        index[evidence_id] = row
    return index


def _monitoring_reference_ids(monitoring_fixture: dict[str, Any]) -> list[str]:
    checks = monitoring_fixture.get("monitoring_checks")
    if not isinstance(checks, list):
        raise ValueError("Monitoring fixture must include monitoring_checks")
    refs: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Monitoring checks must be objects")
        check_id = check.get("check_id")
        if not isinstance(check_id, str) or not check_id:
            raise ValueError("Monitoring checks need check_id")
        refs.append(check_id)
    return refs


def _citation_payload(row: dict[str, Any], evidence_index: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    evidence_ids = row.get("source_evidence_ids") or ["ppd-landing"]
    citations: list[dict[str, str]] = []
    for evidence_id in evidence_ids:
        evidence = evidence_index.get(str(evidence_id))
        if evidence is None:
            continue
        citations.append(
            {
                "evidence_id": str(evidence["evidence_id"]),
                "source_id": str(evidence.get("source_id", "unknown")),
                "title": str(evidence.get("title", "Untitled fixture evidence")),
                "fixture_anchor": str(evidence.get("fixture_anchor", "committed_fixture")),
            }
        )
    return citations


def _materialize_rows(
    monitoring_fixture: dict[str, Any], requests: Iterable[SyntheticAgentRequest]
) -> list[dict[str, Any]]:
    evidence_index = _fixture_evidence_index(monitoring_fixture)
    monitoring_refs = _monitoring_reference_ids(monitoring_fixture)
    request_by_scenario = {request.scenario: request for request in requests}
    rows: list[dict[str, Any]] = []

    for template in ROW_TEMPLATES:
        row = dict(template)
        synthetic_request = request_by_scenario.get(str(row["scenario"]))
        if synthetic_request is None:
            raise ValueError(f"Missing synthetic agent request for scenario {row['scenario']!r}")
        row["synthetic_agent_request"] = {
            "request_id": synthetic_request.request_id,
            "scenario": synthetic_request.scenario,
            "requested_action": synthetic_request.requested_action,
            "supplied_facts": synthetic_request.supplied_facts,
            "evidence_ids": synthetic_request.evidence_ids,
        }
        row["source_evidence_ids"] = synthetic_request.evidence_ids
        row["active"] = False
        row["guardrails_activated"] = False
        row["allowed_effects"] = []
        row["prohibited_effects"] = list(PROHIBITED_EFFECTS)
        row["citation_payload"] = _citation_payload(row, evidence_index)
        row["monitoring_references"] = monitoring_refs
        rows.append(row)

    return rows


def build_compatibility_packet(monitoring_fixture: dict[str, Any]) -> dict[str, Any]:
    source_version = monitoring_fixture.get("fixture_version")
    if source_version != SOURCE_FIXTURE_VERSION:
        raise ValueError(
            f"Expected monitoring fixture version {SOURCE_FIXTURE_VERSION}, got {source_version!r}"
        )

    rows = _materialize_rows(monitoring_fixture, synthetic_agent_requests())
    return {
        "packet_version": PACKET_VERSION,
        "source_fixture_version": SOURCE_FIXTURE_VERSION,
        "status": INACTIVE_STATUS,
        "fixture_first": True,
        "synthetic_requests_only": True,
        "guardrails_activated": False,
        "devhub_opened": False,
        "live_crawl_performed": False,
        "private_documents_read": False,
        "official_actions_performed": [],
        "legal_or_permitting_guarantees": [],
        "rows": rows,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }


def build_compatibility_packet_from_fixture(path: Path) -> dict[str, Any]:
    return build_compatibility_packet(load_json_fixture(path))


def validate_agent_guardrail_api_compatibility_packet_v6(packet: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"]

    _validate_packet_envelope(packet, problems)
    rows = packet.get("rows")
    if not isinstance(rows, list) or not rows:
        problems.append("rows must be a non-empty list")
        rows = []

    row_by_scenario: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            problems.append(f"rows[{index}] must be an object")
            continue
        scenario = row.get("scenario")
        if isinstance(scenario, str):
            row_by_scenario[scenario] = row
        _validate_row_schema(index, row, problems)
        _validate_row_inactive_safety(index, row, problems)

    for scenario in REQUIRED_SCENARIOS:
        if scenario not in row_by_scenario:
            problems.append(f"missing required scenario row: {scenario}")

    _validate_required_scenario_controls(row_by_scenario, problems)
    _scan_for_prohibited_artifacts(packet, problems)
    return problems


def assert_valid_agent_guardrail_api_compatibility_packet_v6(packet: dict[str, Any]) -> None:
    problems = validate_agent_guardrail_api_compatibility_packet_v6(packet)
    if problems:
        raise AgentGuardrailApiCompatV6ValidationError(problems)


def _validate_packet_envelope(packet: dict[str, Any], problems: list[str]) -> None:
    expected_values: tuple[tuple[str, Any], ...] = (
        ("packet_version", PACKET_VERSION),
        ("source_fixture_version", SOURCE_FIXTURE_VERSION),
        ("status", INACTIVE_STATUS),
        ("fixture_first", True),
        ("synthetic_requests_only", True),
        ("guardrails_activated", False),
        ("devhub_opened", False),
        ("live_crawl_performed", False),
        ("private_documents_read", False),
    )
    for key, expected in expected_values:
        if packet.get(key) != expected:
            problems.append(f"{key} must be {expected!r}")

    if packet.get("official_actions_performed") != []:
        problems.append("official_actions_performed must be empty")
    if packet.get("legal_or_permitting_guarantees") != []:
        problems.append("legal_or_permitting_guarantees must be empty")
    if packet.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match fixture-only validation commands")


def _validate_row_schema(index: int, row: dict[str, Any], problems: list[str]) -> None:
    prefix = f"rows[{index}]"
    for key in ("row_id", "row_kind", "scenario", "requested_action", "expected_block"):
        if not isinstance(row.get(key), str) or not row.get(key):
            problems.append(f"{prefix}.{key} is required")
    if row.get("row_kind") not in {"request", "response"}:
        problems.append(f"{prefix}.row_kind must be request or response")
    if not isinstance(row.get("inactive_request"), dict) or not row.get("inactive_request"):
        problems.append(f"{prefix}.inactive_request must be a non-empty object")
    response = row.get("inactive_response")
    if not isinstance(response, dict) or not response:
        problems.append(f"{prefix}.inactive_response must be a non-empty object")
    elif response.get("status") != INACTIVE_STATUS:
        problems.append(f"{prefix}.inactive_response.status must be {INACTIVE_STATUS!r}")

    synthetic_request = row.get("synthetic_agent_request")
    if not isinstance(synthetic_request, dict) or not synthetic_request:
        problems.append(f"{prefix}.synthetic_agent_request must be present")
    else:
        if not isinstance(synthetic_request.get("request_id"), str) or not synthetic_request.get("request_id"):
            problems.append(f"{prefix}.synthetic_agent_request.request_id is required")
        if synthetic_request.get("scenario") != row.get("scenario"):
            problems.append(f"{prefix}.synthetic_agent_request.scenario must match row scenario")
        if synthetic_request.get("requested_action") != row.get("requested_action"):
            problems.append(f"{prefix}.synthetic_agent_request.requested_action must match row requested_action")
        if not isinstance(synthetic_request.get("supplied_facts"), dict):
            problems.append(f"{prefix}.synthetic_agent_request.supplied_facts must be an object")

    if not _non_empty_string_list(row.get("monitoring_references")):
        problems.append(f"{prefix}.monitoring_references must include monitoring rehearsal references")
    if not _valid_citation_payload(row.get("citation_payload")):
        problems.append(f"{prefix}.citation_payload must include evidence_id, source_id, title, and fixture_anchor")
    if not _non_empty_string_list(row.get("source_evidence_ids")):
        problems.append(f"{prefix}.source_evidence_ids must be a non-empty list")


def _validate_row_inactive_safety(index: int, row: dict[str, Any], problems: list[str]) -> None:
    prefix = f"rows[{index}]"
    if row.get("active") is not False:
        problems.append(f"{prefix}.active must be false")
    if row.get("guardrails_activated") is not False:
        problems.append(f"{prefix}.guardrails_activated must be false")
    if row.get("allowed_effects") != []:
        problems.append(f"{prefix}.allowed_effects must be empty")
    if row.get("prohibited_effects") != list(PROHIBITED_EFFECTS):
        problems.append(f"{prefix}.prohibited_effects must exactly match prohibited effects")


def _validate_required_scenario_controls(row_by_scenario: dict[str, dict[str, Any]], problems: list[str]) -> None:
    missing = row_by_scenario.get("missing_facts", {})
    missing_request = missing.get("inactive_request", {})
    missing_response = missing.get("inactive_response", {})
    if not _non_empty_string_list(missing_request.get("missing_facts")):
        problems.append("missing_facts row must include missing fact names")
    if not _non_empty_string_list(missing_response.get("missing_fact_prompts")):
        problems.append("missing_facts row must include missing-fact prompts")

    stale = row_by_scenario.get("stale_source_block", {}).get("inactive_response", {})
    if stale.get("decision") != "blocked" or stale.get("stale_source_block") is not True:
        problems.append("stale_source_block row must include a stale-source block")

    conflict_request = row_by_scenario.get("conflicting_evidence_block", {}).get("inactive_request", {})
    conflict_response = row_by_scenario.get("conflicting_evidence_block", {}).get("inactive_response", {})
    if not _non_empty_string_list(conflict_request.get("conflicting_evidence")):
        problems.append("conflicting_evidence_block row must include conflicting evidence")
    if conflict_response.get("decision") != "blocked" or conflict_response.get("conflicting_evidence_block") is not True:
        problems.append("conflicting_evidence_block row must include a conflicting-evidence block")

    draft_response = row_by_scenario.get("reversible_draft_only_action", {}).get("inactive_response", {})
    next_actions = draft_response.get("next_actions")
    if not isinstance(next_actions, list) or not next_actions:
        problems.append("reversible_draft_only_action row must include next-action rows")
    else:
        for action_index, action in enumerate(next_actions):
            if not isinstance(action, dict):
                problems.append(f"reversible_draft_only_action.next_actions[{action_index}] must be an object")
                continue
            if action.get("draft_only") is not True or action.get("reversible") is not True or action.get("official_effect") is not False:
                problems.append(f"reversible_draft_only_action.next_actions[{action_index}] must be reversible draft-only with no official effect")

    exact_response = row_by_scenario.get("exact_confirmation_checkpoint", {}).get("inactive_response", {})
    if exact_response.get("exact_confirmation_checkpoint") is not True or exact_response.get("confirmation_match") != "exact_text_only":
        problems.append("exact_confirmation_checkpoint row must require exact-confirmation checkpoint")

    for scenario in ("refused_consequential_action", "refused_financial_action"):
        response = row_by_scenario.get(scenario, {}).get("inactive_response", {})
        if response.get("decision") != "refused" or not isinstance(response.get("refusal_explanation"), str) or not response.get("refusal_explanation"):
            problems.append(f"{scenario} row must include refused action explanation")

    citation = row_by_scenario.get("citation_payload", {})
    citation_response = citation.get("inactive_response", {})
    if citation_response.get("citation_payload_required") is not True or not _valid_citation_payload(citation.get("citation_payload")):
        problems.append("citation_payload row must require and include citation payloads")

    handoff_response = row_by_scenario.get("manual_handoff_routing", {}).get("inactive_response", {})
    if handoff_response.get("decision") != "manual_handoff_required" or not isinstance(handoff_response.get("handoff_route"), str) or not handoff_response.get("handoff_route"):
        problems.append("manual_handoff_routing row must include manual handoff routing")

    rollback_response = row_by_scenario.get("rollback_notes", {}).get("inactive_response", {})
    if not _non_empty_string_list(rollback_response.get("rollback_notes")):
        problems.append("rollback_notes row must include rollback notes")

    monitoring_response = row_by_scenario.get("monitoring_references", {}).get("inactive_response", {})
    monitoring_refs = row_by_scenario.get("monitoring_references", {}).get("monitoring_references")
    if monitoring_response.get("monitoring_reference_required") is not True or not _non_empty_string_list(monitoring_refs):
        problems.append("monitoring_references row must include monitoring rehearsal references")

    validation_response = row_by_scenario.get("exact_offline_validation_commands", {}).get("inactive_response", {})
    if validation_response.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands row must include exact validation commands")


def _scan_for_prohibited_artifacts(value: Any, problems: list[str], path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            if lowered_key in PRIVATE_ARTIFACT_KEYS:
                problems.append(f"{path}.{key_text} contains private/session/auth artifact material")
            if lowered_key in OFFICIAL_COMPLETION_KEYS and child:
                problems.append(f"{path}.{key_text} contains official-action completion or guarantee claim")
            _scan_for_prohibited_artifacts(child, problems, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_prohibited_artifacts(child, problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered_value = value.lower()
        if any(marker in lowered_value for marker in PRIVATE_ARTIFACT_VALUE_MARKERS):
            problems.append(f"{path} contains private/session/auth artifact material")


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _valid_citation_payload(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    required = {"evidence_id", "source_id", "title", "fixture_anchor"}
    for row in value:
        if not isinstance(row, dict):
            return False
        if set(row) != required:
            return False
        if not all(isinstance(row[key], str) and row[key] for key in required):
            return False
    return True


def dump_packet_json(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2, sort_keys=True) + "\n"
