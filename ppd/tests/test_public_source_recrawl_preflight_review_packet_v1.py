from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from ppd.agent_readiness.public_source_recrawl_preflight_review_packet_v1 import (
    validate_public_source_recrawl_preflight_review_packet_v1,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'public_source_recrawl_preflight_review_packet_v1'
VALID_PACKET_PATH = FIXTURE_DIR / 'valid_packet.json'


def _valid_packet() -> dict[str, object]:
    return json.loads(VALID_PACKET_PATH.read_text(encoding='utf-8'))


def _errors(packet: dict[str, object]) -> tuple[str, ...]:
    return validate_public_source_recrawl_preflight_review_packet_v1(packet).errors


def test_valid_public_source_recrawl_preflight_packet_accepts_metadata_only_fixture() -> None:
    result = validate_public_source_recrawl_preflight_review_packet_v1(_valid_packet())

    assert result.valid is True
    assert result.errors == ()


def test_public_source_recrawl_preflight_packet_rejects_missing_required_checklist_items() -> None:
    packet = _valid_packet()
    for key in (
        'seed_review_references',
        'official_source_anchor_placeholder',
        'request_method_expectations',
        'rate_limit_notes',
        'metadata_only_archive_manifest_expectations',
        'skip_reason_expectations',
        'reviewer_routing',
        'rollback_notes',
        'validation_commands',
    ):
        packet.pop(key)
    row = packet['candidate_preflight_rows'][0]  # type: ignore[index]
    assert isinstance(row, dict)
    for key in (
        'seed_review_references',
        'official_source_anchor_placeholder',
        'robots_decision_placeholder',
        'allowlist_decision_placeholder',
        'canonical_url_expectation',
        'request_method',
        'rate_limit_note',
        'metadata_only_archive_manifest_expectation',
        'skip_reason_expectation',
        'reviewer_routing',
        'rollback_note',
        'allow_reason',
    ):
        row.pop(key)
    synthetic = packet['synthetic_request_rows'][0]  # type: ignore[index]
    assert isinstance(synthetic, dict)
    synthetic.pop('rate_limit_note')

    errors = _errors(packet)

    assert 'seed_review_references must contain at least one reference' in errors
    assert 'official_source_anchor_placeholder is required' in errors
    assert 'request_method_expectations is required' in errors
    assert 'rate_limit_notes is required' in errors
    assert 'metadata_only_archive_manifest_expectations is required' in errors
    assert 'skip_reason_expectations is required' in errors
    assert 'reviewer_routing is required' in errors
    assert 'rollback_notes is required' in errors
    assert 'validation_commands must include at least one command array' in errors
    assert 'candidate_preflight_rows[0].seed_review_references must contain at least one reference' in errors
    assert 'candidate_preflight_rows[0].official_source_anchor_placeholder is required' in errors
    assert 'candidate_preflight_rows[0].robots_decision_placeholder is required' in errors
    assert 'candidate_preflight_rows[0].allowlist_decision_placeholder is required' in errors
    assert 'candidate_preflight_rows[0].canonical_url_expectation is required' in errors
    assert 'candidate_preflight_rows[0].request_method is required' in errors
    assert 'candidate_preflight_rows[0].rate_limit_note is required' in errors
    assert 'candidate_preflight_rows[0].metadata_only_archive_manifest_expectation is required' in errors
    assert 'candidate_preflight_rows[0].skip_reason_expectation is required' in errors
    assert 'candidate_preflight_rows[0].reviewer_routing is required' in errors
    assert 'candidate_preflight_rows[0].rollback_note is required' in errors
    assert 'candidate_preflight_rows[0] must include allow_reason or skip_reason' in errors
    assert 'synthetic_request_rows[0].rate_limit_note is required' in errors


def test_public_source_recrawl_preflight_packet_rejects_prohibited_artifacts_claims_and_mutations() -> None:
    packet = deepcopy(_valid_packet())
    packet['active_guardrail_mutation'] = True
    packet['notes'] = [
        'browser-state trace.zip was captured',
        'raw crawl response body retained',
        'live crawl completed successfully',
        'release activation completed',
        'official action completed after submitted permit',
        'permit will be approved',
        'submit permit through DevHub',
    ]
    row = packet['candidate_preflight_rows'][0]  # type: ignore[index]
    assert isinstance(row, dict)
    row['session_cookie'] = 'cookie=value'

    errors = _errors(packet)

    assert 'active_guardrail_mutation must be false' in errors
    assert any('private/raw/downloaded/session/browser artifact' in error for error in errors)
    assert any('live crawl or DevHub execution' in error for error in errors)
    assert any('release activation' in error for error in errors)
    assert any('official-action completion' in error for error in errors)
    assert any('legal or permitting outcome guarantees' in error for error in errors)
    assert any('consequential DevHub action language' in error for error in errors)


def test_public_source_recrawl_preflight_packet_rejects_non_official_urls_and_unsafe_booleans() -> None:
    packet = _valid_packet()
    row = packet['candidate_preflight_rows'][0]  # type: ignore[index]
    synthetic = packet['synthetic_request_rows'][0]  # type: ignore[index]
    assert isinstance(row, dict)
    assert isinstance(synthetic, dict)
    row['canonical_url'] = 'https://example.com/ppd'
    row['official_anchor_citation'] = 'https://example.com/citation'
    row['request_method'] = 'POST'
    row['metadata_only_capture'] = False
    row['metadata_only_archive_manifest'] = False
    row['no_raw_body_persisted'] = False
    row['live_network_invoked'] = True
    row['raw_download_invoked'] = True
    synthetic['canonical_url'] = 'https://example.com/synthetic'
    synthetic['method'] = 'POST'
    synthetic['synthetic_only'] = False
    synthetic['network_invoked'] = True
    synthetic['body_included'] = True

    errors = _errors(packet)

    assert 'candidate_preflight_rows[0].canonical_url must be an official public PP&D anchor' in errors
    assert 'candidate_preflight_rows[0].official_anchor_citation must cite an official public anchor' in errors
    assert 'candidate_preflight_rows[0].request_method must be GET' in errors
    assert 'candidate_preflight_rows[0].metadata_only_capture must be true' in errors
    assert 'candidate_preflight_rows[0].metadata_only_archive_manifest must be true' in errors
    assert 'candidate_preflight_rows[0].no_raw_body_persisted must be true' in errors
    assert 'candidate_preflight_rows[0].live_network_invoked must be false' in errors
    assert 'candidate_preflight_rows[0].raw_download_invoked must be false' in errors
    assert 'synthetic_request_rows[0].canonical_url must be an official public PP&D anchor' in errors
    assert 'synthetic_request_rows[0].method must be GET' in errors
    assert 'synthetic_request_rows[0].synthetic_only must be true' in errors
    assert 'synthetic_request_rows[0].network_invoked must be false' in errors
    assert 'synthetic_request_rows[0].body_included must be false' in errors
