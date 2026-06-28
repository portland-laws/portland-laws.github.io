from pathlib import Path

import pytest

from ppd.devhub.surface_drift import (
    SurfaceDriftStatus,
    classify_surface_drift,
    controls_from_manifest,
    load_surface_manifest,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_surface_drift"


def test_known_consequential_controls_require_attended_review() -> None:
    baseline = load_surface_manifest(FIXTURES / "baseline.json")

    report = classify_surface_drift(baseline, baseline)

    assert report.status == SurfaceDriftStatus.ATTENDED_REVIEW
    assert not report.blocked
    assert report.requires_attended_review
    assert {finding.control_key for finding in report.findings} == {
        "upload_plans",
        "submit_application",
    }
    assert {finding.reason for finding in report.findings} == {
        "known_control_requires_attended_review"
    }


def test_new_or_uncertain_controls_are_not_treated_as_safe() -> None:
    baseline = load_surface_manifest(FIXTURES / "baseline.json")
    observed = load_surface_manifest(FIXTURES / "observed_with_drift.json")

    report = classify_surface_drift(baseline, observed)

    assert report.status == SurfaceDriftStatus.BLOCKED
    assert report.blocked
    assert report.requires_attended_review
    reasons_by_key = {finding.control_key: finding.reason for finding in report.findings}
    assert reasons_by_key["dynamic_owner_certification"] == "uncertain_new_control"
    assert reasons_by_key["new_status_help"] == "new_control"


def test_private_page_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="private page values"):
        controls_from_manifest(
            {
                "controls": [
                    {
                        "key": "applicant_name",
                        "label": "Applicant name",
                        "control_type": "input",
                        "action": "draft",
                        "value": "Jane Example",
                    }
                ]
            }
        )
