from copy import deepcopy
from pathlib import Path

import pytest

from ppd.crawler.public_source_delta_summary import (
    PublicSourceDeltaSummaryError,
    build_public_source_delta_summary,
    build_public_source_delta_summary_from_file,
    load_public_data_release_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_source_delta_summary"
BASE_PACKET = FIXTURE_DIR / "public_data_dry_run_release_packet.json"


def _packet():
    return deepcopy(load_public_data_release_packet(BASE_PACKET))


def test_public_source_delta_summary_is_operator_facing_and_metadata_only():
    summary = build_public_source_delta_summary_from_file(BASE_PACKET)

    assert summary["packet_type"] == "public_source_delta_summary"
    assert summary["generated_from"] == "fixture_public_data_dry_run_release_packet"
    assert summary["side_effect_policy"] == {
        "metadata_only": True,
        "crawl_performed": False,
        "download_performed": False,
        "production_bundle_changed": False,
    }
    assert summary["operator_attention_counts"] == {
        "changed_sources": 2,
        "impacted_requirements": 2,
        "blocked_guardrails": 2,
        "unresolved_review_items": 1,
        "allowed_next_steps": 2,
    }


def test_public_source_delta_summary_lists_changed_sources_and_impacted_requirements():
    summary = build_public_source_delta_summary_from_file(BASE_PACKET)

    changed_source_ids = {source["source_id"] for source in summary["changed_sources"]}
    assert changed_source_ids == {"ppd-submit-plans-online", "ppd-fee-payment-guide"}
    assert summary["impacted_requirement_ids"] == [
        "req-payment-final-submit-gate",
        "req-single-pdf-plans",
    ]
    for source in summary["changed_sources"]:
        assert source["evidence_ref"].startswith("fixture-manifest:")
        assert source["citation_refs"]


def test_public_source_delta_summary_blocks_impacted_guardrails_and_keeps_metadata_only_steps():
    summary = build_public_source_delta_summary_from_file(BASE_PACKET)

    blocked_ids = {guardrail["guardrail_id"] for guardrail in summary["blocked_guardrails"]}
    assert blocked_ids == {"guardrail-upload-staging-review", "guardrail-payment-final-submit"}

    next_step_ids = {step["step_id"] for step in summary["allowed_metadata_only_next_steps"]}
    assert next_step_ids == {"next-update-metadata-fixture", "next-operator-guardrail-review"}


def test_public_source_delta_summary_rejects_non_metadata_only_packets():
    packet = _packet()
    packet["side_effect_policy"]["crawl_performed"] = True

    with pytest.raises(PublicSourceDeltaSummaryError):
        build_public_source_delta_summary(packet)


def test_public_source_delta_summary_rejects_missing_prerequisite_packet_ids():
    packet = _packet()
    packet["prerequisite_packet_ids"] = []

    with pytest.raises(PublicSourceDeltaSummaryError, match="prerequisite_packet_ids"):
        build_public_source_delta_summary(packet)


def test_public_source_delta_summary_rejects_uncited_changed_source_claims():
    packet = _packet()
    packet["sources"][0]["citation_refs"] = []

    with pytest.raises(PublicSourceDeltaSummaryError, match="citation_refs"):
        build_public_source_delta_summary(packet)


def test_public_source_delta_summary_rejects_private_or_authenticated_urls():
    packet = _packet()
    packet["sources"][0]["canonical_url"] = "https://devhub.portlandoregon.gov/dashboard?token=abc"

    with pytest.raises(PublicSourceDeltaSummaryError, match="private or authenticated URL"):
        build_public_source_delta_summary(packet)


@pytest.mark.parametrize(
    "key,value,match",
    [
        ("raw_body_excerpt", "Official page body excerpt copied from a crawl.", "raw body excerpt"),
        ("downloaded_document_path", "/tmp/ppd/downloads/form.pdf", "downloaded document path"),
    ],
)
def test_public_source_delta_summary_rejects_raw_body_excerpts_and_downloaded_paths(key, value, match):
    packet = _packet()
    packet["sources"][0][key] = value

    with pytest.raises(PublicSourceDeltaSummaryError, match=match):
        build_public_source_delta_summary(packet)


@pytest.mark.parametrize(
    "key,value",
    [
        ("release_label", "production-ready"),
        ("production_ready", True),
    ],
)
def test_public_source_delta_summary_rejects_unsupported_production_ready_labels(key, value):
    packet = _packet()
    packet[key] = value

    with pytest.raises(PublicSourceDeltaSummaryError, match="production-ready"):
        build_public_source_delta_summary(packet)


def test_public_source_delta_summary_rejects_live_crawl_recommendations():
    packet = _packet()
    packet["next_steps"].append(
        {
            "step_id": "next-live-crawl",
            "kind": "live_crawl",
            "description": "Run a live crawl from this delta packet.",
            "metadata_only": False,
        }
    )

    with pytest.raises(PublicSourceDeltaSummaryError, match="unsupported next step kind"):
        build_public_source_delta_summary(packet)


def test_public_source_delta_summary_rejects_consequential_devhub_recommendations():
    packet = _packet()
    packet["next_steps"].append(
        {
            "step_id": "next-devhub-submit",
            "kind": "operator_note",
            "description": "Recommend DevHub submit for the affected permit application.",
            "metadata_only": True,
        }
    )

    with pytest.raises(PublicSourceDeltaSummaryError, match="unsafe next step recommendation"):
        build_public_source_delta_summary(packet)
