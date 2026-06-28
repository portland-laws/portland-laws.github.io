from pathlib import Path

import pytest

from ppd.extraction.change_monitor import build_change_report_from_fixture, reject_raw_body_fields


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "change_monitoring" / "source_hash_changes.json"


def test_change_monitor_fixture_reports_changed_source_hashes_and_affected_ids() -> None:
    report = build_change_report_from_fixture(FIXTURE_PATH)

    assert report["monitoring_mode"] == "deterministic_fixture"
    assert report["live_crawl_performed"] is False
    assert report["raw_page_bodies_stored"] is False

    assert report["changed_sources"] == [
        {
            "source_id": "src_devhub_faq",
            "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
            "previous_content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "current_content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "affected_requirement_ids": [
                "req_devhub_account_services",
                "req_devhub_status_tracking",
                "req_upload_corrections_gate",
            ],
            "affected_process_ids": [
                "process_corrections_upload",
                "process_devhub_account_setup",
                "process_status_review",
            ],
            "affected_guardrail_bundle_ids": ["guardrail_devhub_authenticated_actions"],
        }
    ]

    assert report["added_sources"][0]["source_id"] == "src_file_naming_standards"
    assert report["removed_sources"][0]["source_id"] == "src_retired_fee_notice"
    assert report["affected_requirement_ids"] == [
        "req_devhub_account_services",
        "req_devhub_status_tracking",
        "req_file_naming_rule",
        "req_pdf_preparation_rule",
        "req_retired_fee_notice",
        "req_upload_corrections_gate",
    ]
    assert report["affected_process_ids"] == [
        "process_corrections_upload",
        "process_devhub_account_setup",
        "process_fee_payment",
        "process_status_review",
        "process_document_preparation",
        "process_upload_staging",
    ]
    assert report["affected_guardrail_bundle_ids"] == [
        "guardrail_devhub_authenticated_actions",
        "guardrail_document_upload_staging",
        "guardrail_fee_payment",
    ]


def test_change_monitor_fixture_rejects_raw_page_body_fields() -> None:
    with pytest.raises(ValueError, match="raw page body field"):
        reject_raw_body_fields(
            {
                "previous_sources": [],
                "current_sources": [
                    {
                        "source_id": "src_bad_fixture",
                        "canonical_url": "https://www.portland.gov/ppd",
                        "content_hash": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                        "raw_body": "committed page body is not allowed",
                    }
                ],
            }
        )
