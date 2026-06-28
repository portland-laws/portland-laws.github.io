from __future__ import annotations

from copy import deepcopy

import pytest

from ppd.agent_readiness.public_refresh_normalized_document_extraction_readiness_packet_v1 import (
    VALIDATION_COMMANDS,
    require_valid_public_refresh_normalized_document_extraction_readiness_packet_v1,
    validate_public_refresh_normalized_document_extraction_readiness_packet_v1,
)


def _valid_packet() -> dict[str, object]:
    return {
        'packet_version': 'public-refresh-normalized-document-extraction-readiness-packet-v1',
        'mode': 'fixture_first_offline_validation_only',
        'fixture_first': True,
        'inactive_archive_patch_preview_refs': ['inactive-archive-preview::ppd-devhub-faq'],
        'citation_impact_queue_refs': ['citation-impact-queue::ppd-devhub-faq'],
        'normalized_document_extraction_candidates': [
            {
                'candidate_id': 'normalized-extraction-readiness::ppd-devhub-faq',
                'source_id': 'ppd-devhub-faq',
                'canonical_url': 'https://www.portland.gov/ppd/devhub-faqs',
                'inactive_archive_patch_preview_ref': 'inactive-archive-preview::ppd-devhub-faq',
                'citation_impact_queue_ref': 'citation-impact-queue::ppd-devhub-faq',
                'normalized_document_id_placeholder': 'pending-normalized-document-ppd-devhub-faq',
                'extraction_route_decision': 'extract_public_html_fixture_only',
                'citation_span_acceptance_checks': ['public citation span anchors required'],
                'table_extraction_expectations': ['capture public guidance tables when present'],
                'file_rule_extraction_expectations': ['record file-rule guidance placeholders only'],
                'confidence_placeholder': 'placeholder:confidence-pending-human-review',
                'human_review_route': 'public-refresh-normalized-document-review-queue',
                'stale_source_hold': 'hold source freshness until archive preview and citation queue are reviewed',
                'rollback_note': 'Discard fixture extraction readiness if source freshness changes before review.',
                'allowed_next_action': 'human_review_of_fixture_extraction_plan_only',
                'agent_may_treat_source_as_current': False,
                'live_extraction': False,
                'live_crawl': False,
                'document_download': False,
                'raw_output_stored': False,
                'devhub_accessed': False,
                'active_document_record_mutation': False,
                'official_action_completed': False,
                'legal_or_permitting_guarantee': False,
                'active_mutation': False,
            }
        ],
        'validation_commands': [list(command) for command in VALIDATION_COMMANDS],
        'live_extraction': False,
        'live_crawl': False,
        'document_download': False,
        'raw_output_stored': False,
        'devhub_accessed': False,
        'active_document_record_mutation': False,
        'official_action_completed': False,
        'legal_or_permitting_guarantee': False,
        'active_mutation': False,
    }


def _codes(packet: dict[str, object]) -> set[str]:
    return {issue.code for issue in validate_public_refresh_normalized_document_extraction_readiness_packet_v1(packet)}


def test_accepts_fixture_first_normalized_document_extraction_readiness_packet() -> None:
    packet = _valid_packet()

    require_valid_public_refresh_normalized_document_extraction_readiness_packet_v1(packet)

    candidate = packet['normalized_document_extraction_candidates'][0]
    assert candidate['normalized_document_id_placeholder'] == 'pending-normalized-document-ppd-devhub-faq'
    assert candidate['agent_may_treat_source_as_current'] is False
    assert candidate['active_document_record_mutation'] is False


@pytest.mark.parametrize(
    ('packet_key', 'expected_code'),
    [
        ('inactive_archive_patch_preview_refs', 'missing_inactive_archive_patch_preview_refs'),
        ('citation_impact_queue_refs', 'missing_citation_impact_queue_refs'),
        ('normalized_document_extraction_candidates', 'missing_normalized_document_extraction_candidates'),
        ('validation_commands', 'missing_validation_commands'),
    ],
)
def test_rejects_missing_top_level_references_and_validation_commands(packet_key: str, expected_code: str) -> None:
    packet = _valid_packet()
    packet[packet_key] = []

    assert expected_code in _codes(packet)


@pytest.mark.parametrize(
    ('candidate_key', 'expected_code'),
    [
        ('inactive_archive_patch_preview_ref', 'missing_inactive_archive_patch_preview_ref'),
        ('citation_impact_queue_ref', 'missing_citation_impact_queue_ref'),
        ('normalized_document_id_placeholder', 'missing_normalized_document_id_placeholder'),
        ('extraction_route_decision', 'missing_extraction_route_decision'),
        ('citation_span_acceptance_checks', 'missing_citation_span_acceptance_checks'),
        ('confidence_placeholder', 'missing_confidence_placeholder'),
        ('human_review_route', 'missing_human_review_route'),
        ('stale_source_hold', 'missing_stale_source_hold'),
        ('rollback_note', 'missing_rollback_note'),
    ],
)
def test_rejects_missing_candidate_readiness_controls(candidate_key: str, expected_code: str) -> None:
    packet = _valid_packet()
    candidate = packet['normalized_document_extraction_candidates'][0]
    candidate.pop(candidate_key)

    assert expected_code in _codes(packet)


def test_rejects_missing_table_and_file_rule_extraction_expectations() -> None:
    packet = _valid_packet()
    candidate = packet['normalized_document_extraction_candidates'][0]
    candidate['table_extraction_expectations'] = []
    candidate['file_rule_extraction_expectations'] = []

    assert 'missing_table_or_file_rule_extraction_expectations' in _codes(packet)


@pytest.mark.parametrize(
    ('candidate_key', 'value', 'expected_code'),
    [
        ('inactive_archive_patch_preview_ref', 'missing-preview-ref', 'missing_inactive_archive_patch_preview_reference'),
        ('citation_impact_queue_ref', 'missing-citation-ref', 'missing_citation_impact_queue_reference'),
        ('normalized_document_id_placeholder', 'doc-active-001', 'missing_normalized_document_placeholder_id'),
        ('extraction_route_decision', 'run_live_extraction', 'invalid_extraction_route_decision'),
        ('confidence_placeholder', '0.98', 'missing_confidence_placeholder'),
        ('allowed_next_action', 'extract_without_review', 'missing_human_review_routing'),
        ('agent_may_treat_source_as_current', True, 'missing_stale_source_hold'),
    ],
)
def test_rejects_invalid_candidate_readiness_values(candidate_key: str, value: object, expected_code: str) -> None:
    packet = _valid_packet()
    packet['normalized_document_extraction_candidates'][0][candidate_key] = value

    assert expected_code in _codes(packet)


@pytest.mark.parametrize('flag', ['live_extraction', 'live_crawl', 'document_download', 'raw_output_stored', 'devhub_accessed', 'active_document_record_mutation', 'official_action_completed', 'legal_or_permitting_guarantee', 'active_mutation'])
def test_rejects_active_execution_and_mutation_flags(flag: str) -> None:
    packet = _valid_packet()
    packet[flag] = True

    assert 'unsafe_execution_or_mutation_flag' in _codes(packet)

    candidate_packet = _valid_packet()
    candidate_packet['normalized_document_extraction_candidates'][0][flag] = True
    assert 'unsafe_execution_or_mutation_flag' in _codes(candidate_packet)


@pytest.mark.parametrize('key', ['private_artifact', 'raw_output', 'downloaded_document', 'downloaded_pdf', 'raw_crawl_output', 'session_state', 'browser_trace', 'devhub_session'])
def test_rejects_private_raw_downloaded_or_runtime_artifact_keys(key: str) -> None:
    packet = _valid_packet()
    packet['normalized_document_extraction_candidates'][0][key] = 'not allowed'

    assert 'private_raw_downloaded_or_runtime_artifact' in _codes(packet)


@pytest.mark.parametrize('claim', ['live extraction completed', 'live crawl completed', 'DevHub accessed', 'active DocumentRecord mutation', 'official action completed', 'permit guaranteed', 'legal advice', 'raw output stored', 'downloaded document'])
def test_rejects_live_devhub_official_legal_and_artifact_claim_text(claim: str) -> None:
    packet = _valid_packet()
    mutated = deepcopy(packet)
    mutated['normalized_document_extraction_candidates'][0]['rollback_note'] = claim

    assert 'prohibited_claim' in _codes(mutated)
