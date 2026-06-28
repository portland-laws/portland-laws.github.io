import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.crawler.processor_handoff_operator_checklist import (
    assert_processor_handoff_operator_checklist_is_safe,
    build_processor_handoff_operator_checklist,
    issue_codes,
    validate_processor_handoff_operator_checklist,
)

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'processor_handoff_operator_checklist_packets.json'


def _fixtures():
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


def _checklist():
    fixtures = _fixtures()
    return build_processor_handoff_operator_checklist(
        fixtures['readiness_packet'],
        fixtures['freshness_review_packet'],
        generated_at='2026-05-28T12:00:00Z',
    )


def test_builds_manual_operator_checklist_from_readiness_and_freshness_packets():
    checklist = _checklist()

    assert checklist['schema_version'] == 1
    assert checklist['processor_invocation']['allowed'] is False
    assert checklist['archive_artifact_writes']['allowed'] is False
    assert checklist['no_raw_body_attestations']['checklist_persists_raw_body'] is False
    assert checklist['no_raw_body_attestations']['readiness_packet_attests_no_raw_body'] is True
    assert checklist['prerequisite_links'][0]['url'] == 'https://www.portland.gov/ppd'
    assert checklist['expected_manifest_ids'] == [
        'ppd-processor-manifest-devhub-faqs',
        'ppd-processor-manifest-submit-plans-online',
    ]
    assert checklist['validation_summary']['readiness_ok'] is True
    assert checklist['validation_summary']['target_count'] == 2
    assert checklist['validation_summary']['skipped_target_count'] == 2
    assert any(prompt.startswith('Confirm target devhub-faqs remains public') for prompt in checklist['manual_operator_prompts'])
    assert any(
        skipped['target_id'] == 'devhub-private-permit-dashboard' and 'private authenticated' in skipped['reason']
        for skipped in checklist['skipped_target_reasons']
    )
    assert {caution['bucket'] for caution in checklist['rate_limit_cautions']} == {'public-host:www.portland.gov'}

    assert validate_processor_handoff_operator_checklist(checklist) == []
    assert_processor_handoff_operator_checklist_is_safe(checklist)


def test_checklist_requires_manual_prompts_expected_manifests_prerequisites_skips_and_abort_conditions():
    unsafe = {
        'schema_version': 1,
        'prerequisite_links': [],
        'handoff_targets': [],
        'manual_operator_prompts': [],
        'expected_manifest_ids': [],
        'processor_capability_prerequisites': [],
        'abort_conditions': [],
        'skipped_target_reasons': [],
        'processor_invocation': {'allowed': False},
        'archive_artifact_writes': {'allowed': False},
        'no_raw_body_attestations': {'checklist_persists_raw_body': False},
    }

    codes = issue_codes(validate_processor_handoff_operator_checklist(unsafe))

    assert 'missing_prerequisite_links' in codes
    assert 'missing_handoff_targets' in codes
    assert 'missing_manual_prompts' in codes
    assert 'missing_expected_manifest_ids' in codes
    assert 'missing_processor_capability_prerequisites' in codes
    assert 'missing_abort_conditions' in codes
    assert 'missing_skipped_target_reasons' in codes
    assert 'missing_readiness_no_raw_body_attestation' in codes


def test_checklist_rejects_processor_invocation_archive_writes_and_raw_references():
    unsafe = _checklist()
    unsafe['no_raw_body_attestations']['checklist_persists_raw_body'] = True
    unsafe['processor_invocation'] = {'allowed': True, 'processor_invoked': True, 'status': 'processor_invoked'}
    unsafe['archive_artifact_writes'] = {'allowed': True, 'write_archive_artifacts': True, 'status': 'archive_artifacts_produced'}
    unsafe['operator_notes'] = {'raw_body': 'raw content must not appear'}

    issues = validate_processor_handoff_operator_checklist(unsafe)
    codes = issue_codes(issues)

    assert 'missing_no_raw_body_attestation' in codes
    assert 'processor_invocation_allowed' in codes
    assert 'archive_artifact_writes_allowed' in codes
    assert 'forbidden_execution_or_archive_write_claim' in codes
    assert 'forbidden_raw_or_archive_reference' in codes
    with pytest.raises(ValueError, match='processor_invocation_allowed'):
        assert_processor_handoff_operator_checklist_is_safe(unsafe)


def test_checklist_rejects_private_non_allowlisted_and_raw_download_targets():
    unsafe = _checklist()
    unsafe['handoff_targets'] = [
        {'source_id': 'private-devhub-permit', 'url': 'https://devhub.portlandoregon.gov/permits/private-dashboard', 'host': 'devhub.portlandoregon.gov'},
        {'source_id': 'outside-host', 'url': 'https://example.com/ppd', 'host': 'example.com'},
        {'source_id': 'raw-download', 'url': 'https://www.portland.gov/ppd/documents/how-pay-fees/download', 'host': 'www.portland.gov'},
    ]
    unsafe['prerequisite_links'] = [{'source_id': 'bad-prereq', 'url': 'http://www.portland.gov/ppd', 'host': 'www.portland.gov'}]

    codes = issue_codes(validate_processor_handoff_operator_checklist(unsafe))

    assert 'private_or_authenticated_target' in codes
    assert 'non_allowlisted_target' in codes
    assert 'raw_download_or_archive_target' in codes
    assert 'invalid_public_target_url' in codes


def test_checklist_rejects_missing_skipped_target_reason_and_archive_artifact_claim():
    unsafe = deepcopy(_checklist())
    unsafe['skipped_target_reasons'][0]['reason'] = ''
    unsafe['archive_artifact_produced'] = True
    unsafe['archive_artifact_ref'] = 'ipfs://example-archive-artifact'

    codes = issue_codes(validate_processor_handoff_operator_checklist(unsafe))

    assert 'missing_skipped_target_reason' in codes
    assert 'forbidden_execution_or_archive_write_claim' in codes
    assert 'forbidden_raw_or_archive_reference' in codes
