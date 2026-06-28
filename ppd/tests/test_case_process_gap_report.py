from __future__ import annotations

import json
from pathlib import Path

from ppd.reports.case_process_gap_report import build_case_process_gap_report

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "case_process_gap" / "combined_gap_inputs.json"


def test_case_process_gap_report_returns_only_actionable_prompts() -> None:
    inputs = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    report = build_case_process_gap_report(inputs)

    assert report == {
        "case_id": "fixture-case-001",
        "gap_count": 5,
        "gaps": [
            {
                "prompt_id": "citation.tree-plan-code",
                "status": "conflicting",
                "source": "citation integrity",
                "prompt": "Repair citation integrity for tree-plan-code.",
                "evidence": ["Two fixture citations point to different PP&D pages for the same tree plan requirement."],
                "safe_next_action": "Do not choose a winner automatically; preserve both fixture values and escalate for manual review.",
            },
            {
                "prompt_id": "document.site-plan",
                "status": "missing",
                "source": "document compliance",
                "prompt": "Resolve Site plan document compliance status: missing.",
                "evidence": ["Required by process bundle but absent from fixture document set."],
                "safe_next_action": "Collect the missing fixture field or source-backed document before advancing the process.",
            },
            {
                "prompt_id": "process_bundle.required_documents",
                "status": "missing",
                "source": "process bundle",
                "prompt": "Provide required documents for the process bundle.",
                "evidence": ["process_bundle.required_documents is missing or blank"],
                "safe_next_action": "Collect the missing fixture field or source-backed document before advancing the process.",
            },
            {
                "prompt_id": "source.residential-permit-fees",
                "status": "stale",
                "source": "source freshness",
                "prompt": "Refresh or verify source freshness for Residential permit fees.",
                "evidence": ["Fixture source is older than the allowed freshness window."],
                "safe_next_action": "Refresh the cited public source fixture and re-run validation before relying on it.",
            },
            {
                "prompt_id": "case_store.owner_authorization",
                "status": "ambiguous",
                "source": "user case store",
                "prompt": "Confirm whether owner authorization is required for this fixture case.",
                "evidence": ["Applicant role and owner role differ in fixture case store."],
                "safe_next_action": "Compare the fixture evidence and record the PP&D-safe interpretation before proceeding.",
            },
        ],
    }


def test_case_process_gap_report_suppresses_clean_outputs() -> None:
    inputs = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    inputs["case_store"]["prompts"] = []
    inputs["process_bundle"]["required_documents"] = ["site_plan"]
    inputs["document_compliance"]["documents"] = [{"id": "site-plan", "name": "Site plan", "status": "ok"}]
    inputs["source_freshness"]["sources"] = [{"id": "residential-permit-fees", "label": "Residential permit fees", "status": "fresh"}]
    inputs["citation_integrity"]["citations"] = [{"claim_id": "tree-plan-code", "status": "ok"}]

    report = build_case_process_gap_report(inputs)

    assert report == {"case_id": "fixture-case-001", "gap_count": 0, "gaps": []}
