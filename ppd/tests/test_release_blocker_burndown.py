from __future__ import annotations

import pytest

from ppd.daemon.release_blocker_burndown import (
    assert_release_blocker_burndown_queue_safe,
    validate_release_blocker_burndown_queue,
)


def test_accepts_cited_reconciled_release_blocker_queue() -> None:
    queue = {
        "items": [
            {
                "id": "rb-1",
                "type": "release-blocker",
                "status": "reconciled",
                "priority": "critical",
                "priority_citations": ["source:ppd-devhub-faq:fee-payment-boundary"],
                "reconciliation_link": "ppd/reconciliation/rb-1.md",
                "labels": ["guardrail"],
                "summary": "Read-only fee notice review remains allowed; payment execution remains blocked.",
            }
        ]
    }

    report = validate_release_blocker_burndown_queue(queue)

    assert report.ok
    assert report.violations == ()
    assert_release_blocker_burndown_queue_safe(queue)


def test_rejects_missing_reconciliation_link_for_release_blocker() -> None:
    report = validate_release_blocker_burndown_queue(
        [
            {
                "id": "rb-missing-link",
                "type": "release-blocker",
                "status": "open",
                "priority": "high",
                "priority_citations": ["source:ppd-plan:non-negotiable-boundaries"],
            }
        ]
    )

    assert not report.ok
    assert _codes(report) == {"missing_reconciliation_link"}


def test_rejects_uncited_blocker_priority() -> None:
    report = validate_release_blocker_burndown_queue(
        {
            "items": [
                {
                    "id": "rb-uncited-priority",
                    "type": "release-blocker",
                    "status": "open",
                    "priority": "critical",
                    "reconciliation_link": "ppd/reconciliation/rb-uncited-priority.md",
                }
            ]
        }
    )

    assert not report.ok
    assert _codes(report) == {"uncited_blocker_priority"}


def test_rejects_private_session_artifacts_and_raw_crawl_references() -> None:
    report = validate_release_blocker_burndown_queue(
        {
            "items": [
                {
                    "id": "rb-artifacts",
                    "type": "release-blocker",
                    "status": "open",
                    "priority": "high",
                    "priority_citations": ["source:ppd-plan:privacy-limits"],
                    "reconciliation_link": "ppd/reconciliation/rb-artifacts.md",
                    "artifact_refs": [
                        "tmp/devhub-session/storage-state.json",
                        "runs/crawler/raw-response.html",
                    ],
                }
            ]
        }
    )

    assert not report.ok
    assert _codes(report) == {
        "private_or_session_artifact_reference",
        "raw_crawl_output_reference",
    }


def test_rejects_production_ready_labels_with_open_blockers() -> None:
    report = validate_release_blocker_burndown_queue(
        {
            "items": [
                {
                    "id": "rb-prod-ready-open",
                    "type": "release-blocker",
                    "status": "blocked",
                    "priority": "p0",
                    "priority_citations": ["source:ppd-plan:release-gates"],
                    "reconciliation_link": "ppd/reconciliation/rb-prod-ready-open.md",
                    "labels": ["production-ready"],
                }
            ]
        }
    )

    assert not report.ok
    assert _codes(report) == {"production_ready_with_open_blockers"}


def test_rejects_consequential_action_enablement() -> None:
    queue = {
        "items": [
            {
                "id": "rb-enablements",
                "type": "release-blocker",
                "status": "open",
                "priority": "high",
                "priority_citations": ["source:ppd-plan:consequential-actions"],
                "reconciliation_link": "ppd/reconciliation/rb-enablements.md",
                "next_action": "Enable upload correction, submit permit, schedule inspection, cancel permit, certify acknowledgement, and submit payment.",
            }
        ]
    }

    report = validate_release_blocker_burndown_queue(queue)

    assert not report.ok
    assert _codes(report) == {"consequential_action_enablement"}
    with pytest.raises(ValueError, match="consequential_action_enablement"):
        assert_release_blocker_burndown_queue_safe(queue)


def _codes(report: object) -> set[str]:
    return {violation.code for violation in report.violations}
