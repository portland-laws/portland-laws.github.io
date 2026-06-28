from __future__ import annotations

from ppd.logic.traceability_audit import (
    assert_valid_traceability_audit_packet,
    validate_traceability_audit_packet,
)


def _valid_packet() -> dict[str, object]:
    return {
        "packet_id": "traceability-audit-fixture",
        "sources": [
            {
                "source_id": "src-ppd-tools",
                "canonical_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
                "source_type": "public_html",
                "freshness_status": "current",
            }
        ],
        "requirements": [
            {
                "requirement_id": "req-apply-guide",
                "source_evidence_ids": ["src-ppd-tools"],
                "prerequisites": [
                    {
                        "requirement_id": "req-account-needed",
                        "source_evidence_ids": ["src-ppd-tools"],
                    }
                ],
            },
            {
                "requirement_id": "req-account-needed",
                "source_evidence_ids": ["src-ppd-tools"],
            },
        ],
        "guardrail_bundle": {
            "guardrail_bundle_id": "bundle-public-ppd",
            "requirement_ids": ["req-apply-guide", "req-account-needed"],
            "source_evidence_ids": ["src-ppd-tools"],
            "active_bundle_mutation": False,
        },
    }


def test_valid_traceability_packet_has_no_findings() -> None:
    assert validate_traceability_audit_packet(_valid_packet()) == []
    assert_valid_traceability_audit_packet(_valid_packet())


def test_rejects_missing_prerequisite_links_and_uncited_gaps() -> None:
    packet = _valid_packet()
    requirements = packet["requirements"]
    assert isinstance(requirements, list)
    requirements.append(
        {
            "requirement_id": "req-bad-prereq",
            "source_evidence_ids": ["src-ppd-tools"],
            "prerequisites": [{"source_evidence_ids": ["src-ppd-tools"]}],
            "traceability_gaps": [{"gap_id": "gap-missing-citation", "summary": "no source citation"}],
        }
    )

    codes = {finding.code for finding in validate_traceability_audit_packet(packet)}

    assert "missing_prerequisite_link" in codes
    assert "uncited_traceability_gap" in codes


def test_rejects_unknown_source_and_requirement_ids() -> None:
    packet = _valid_packet()
    bundle = packet["guardrail_bundle"]
    assert isinstance(bundle, dict)
    bundle["source_evidence_ids"] = ["src-does-not-exist"]
    bundle["requirement_ids"] = ["req-does-not-exist"]

    codes = {finding.code for finding in validate_traceability_audit_packet(packet)}

    assert "unknown_source_id" in codes
    assert "unknown_requirement_id" in codes


def test_rejects_stale_sources_marked_current_without_acknowledgement() -> None:
    packet = _valid_packet()
    sources = packet["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    source["is_stale"] = True
    source["freshness_status"] = "current"

    codes = {finding.code for finding in validate_traceability_audit_packet(packet)}

    assert "stale_source_marked_current" in codes


def test_allows_acknowledged_stale_source_marker_for_review_packet() -> None:
    packet = _valid_packet()
    packet["acknowledged_stale_source_ids"] = ["src-ppd-tools"]
    sources = packet["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    source["is_stale"] = True
    source["freshness_status"] = "current"

    codes = {finding.code for finding in validate_traceability_audit_packet(packet)}

    assert "stale_source_marked_current" not in codes


def test_rejects_private_urls_raw_references_live_fetch_claims_and_mutation_flags() -> None:
    packet = _valid_packet()
    packet["live_fetch_performed"] = True
    packet["notes"] = "This packet was fetched live from the portal."
    packet["sources"] = [
        {
            "source_id": "src-private",
            "canonical_url": "https://devhub.portlandoregon.gov/Account/Login?token=secret",
            "source_type": "devhub_authenticated",
            "privacy_classification": "authenticated",
            "freshness_status": "current",
            "raw_body_ref": "local-private-body.html",
        }
    ]
    packet["requirements"] = [
        {
            "requirement_id": "req-private",
            "source_evidence_ids": ["src-private"],
            "download_url": "https://www.portland.gov/ppd/documents/how-pay-fees/download",
        }
    ]
    packet["guardrail_bundle"] = {
        "guardrail_bundle_id": "bundle-private",
        "requirement_ids": ["req-private"],
        "source_evidence_ids": ["src-private"],
        "active_mutation": True,
    }

    codes = {finding.code for finding in validate_traceability_audit_packet(packet)}

    assert "private_or_authenticated_url" in codes
    assert "private_or_authenticated_source" in codes
    assert "raw_reference" in codes
    assert "live_fetch_claim" in codes
    assert "active_bundle_mutation" in codes
