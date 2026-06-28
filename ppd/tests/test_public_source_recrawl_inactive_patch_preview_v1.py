from __future__ import annotations

import ast
import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.public_source_recrawl_inactive_patch_preview_v1 import (
    build_public_source_recrawl_inactive_patch_preview_v1,
    validate_public_source_recrawl_inactive_patch_preview_v1,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'public_source_recrawl_inactive_patch_preview'


class PublicSourceRecrawlInactivePatchPreviewV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_text = (FIXTURE_DIR / 'reviewer_disposition_packet_v1.pydata').read_text(encoding='utf-8')
        self.disposition_packet = ast.literal_eval(fixture_text)
        self.preview = build_public_source_recrawl_inactive_patch_preview_v1(self.disposition_packet)

    def issue_codes(self, packet: dict[str, object]) -> set[str]:
        return {issue.code for issue in validate_public_source_recrawl_inactive_patch_preview_v1(packet)}

    def test_builder_emits_valid_inactive_preview_from_approved_rows_only(self) -> None:
        self.assertEqual([], validate_public_source_recrawl_inactive_patch_preview_v1(self.preview))
        self.assertEqual({'ppd-devhub-faq'}, {row['source_id'] for row in self.preview['source_registry_delta_placeholders']})
        self.assertEqual('excluded_from_inactive_delta_placeholders', self.preview['held_or_skipped_reviewer_disposition_notes'][0]['preview_effect'])
        self.assertEqual('not_promoted', self.preview['source_registry_delta_placeholders'][0]['active_source_promotion_state'])
        self.assertEqual('not_promoted', self.preview['archive_manifest_delta_placeholders'][0]['active_archive_promotion_state'])
        self.assertFalse(self.preview['active_source_artifacts_mutated'])
        self.assertFalse(self.preview['active_archive_artifacts_mutated'])
        self.assertFalse(self.preview['active_requirement_artifacts_mutated'])

    def test_preview_contains_required_placeholder_families(self) -> None:
        for key in ('source_registry_delta_placeholders', 'archive_manifest_delta_placeholders', 'normalized_document_reference_placeholders', 'freshness_monitor_replay_notes'):
            self.assertEqual(1, len(self.preview[key]))
            self.assertEqual('inactive_preview_only', self.preview[key][0]['inactive_patch_state'])

    def test_rejects_missing_reviewer_and_metadata_dry_run_references(self) -> None:
        packet = copy.deepcopy(self.preview)
        packet['reviewer_disposition_packet_ref'] = {'packet_version': 'wrong'}
        packet['metadata_dry_run_plan_ref'] = {'manifest_id': '', 'manifest_version': '', 'metadata_only': False}
        codes = self.issue_codes(packet)
        self.assertIn('missing_reviewer_disposition_ref', codes)
        self.assertIn('missing_metadata_dry_run_plan_ref', codes)

    def test_rejects_missing_placeholders_and_source_mismatch(self) -> None:
        packet = copy.deepcopy(self.preview)
        packet['source_registry_delta_placeholders'] = []
        packet['archive_manifest_delta_placeholders'] = []
        packet['freshness_monitor_replay_notes'][0]['source_id'] = 'wrong-source'
        codes = self.issue_codes(packet)
        self.assertIn('missing_placeholder_rows', codes)
        self.assertIn('placeholder_source_mismatch', codes)

    def test_rejects_missing_canonical_redirect_http_and_content_type_expectations(self) -> None:
        packet = copy.deepcopy(self.preview)
        packet['source_registry_delta_placeholders'][0]['canonical_url'] = ''
        archive = packet['archive_manifest_delta_placeholders'][0]
        archive['canonical_url'] = ''
        archive['requested_url_placeholder'] = ''
        archive['redirect_chain_placeholder'] = []
        archive['expected_http_status'] = ''
        archive['expected_content_type'] = ''
        codes = self.issue_codes(packet)
        self.assertIn('missing_canonical_url', codes)
        self.assertIn('missing_redirect_placeholder', codes)
        self.assertIn('missing_http_status_expectation', codes)
        self.assertIn('missing_content_type_expectation', codes)

    def test_rejects_missing_archive_metadata_rows_skipped_reason_holds_and_rollback(self) -> None:
        packet = copy.deepcopy(self.preview)
        archive = packet['archive_manifest_delta_placeholders'][0]
        archive['content_hash_placeholder'] = ''
        archive['processor_name_placeholder'] = ''
        archive['normalized_document_id_placeholder'] = ''
        archive['skipped_reason_handling'] = ''
        archive['no_raw_body_persisted'] = False
        packet['held_or_skipped_reviewer_disposition_notes'][0]['skipped_reason_code'] = ''
        packet['held_or_skipped_reviewer_disposition_notes'][0]['reviewer_hold_placeholder'] = ''
        packet['held_or_skipped_reviewer_disposition_notes'][0]['rollback_note'] = ''
        packet['rollback_notes'] = []
        codes = self.issue_codes(packet)
        self.assertIn('missing_archive_manifest_patch_preview_row', codes)
        self.assertIn('missing_skipped_reason_handling', codes)
        self.assertIn('missing_payload_exclusion', codes)
        self.assertIn('missing_reviewer_holds', codes)
        self.assertIn('missing_rollback_notes', codes)

    def test_rejects_missing_validation_commands_unsafe_text_and_mutation_flags(self) -> None:
        packet = copy.deepcopy(self.preview)
        packet['validation_commands'] = []
        packet['active_guardrail_artifacts_mutated'] = True
        packet['active_archive_artifacts_mutated'] = True
        packet['authenticated_session_ref'] = 'session.json'
        packet['operator_note'] = 'Live network request executed and raw response body retained. Submit permit after review.'
        codes = self.issue_codes(packet)
        self.assertIn('missing_validation_commands', codes)
        self.assertIn('unsafe_execution_or_mutation_flag', codes)
        self.assertIn('unsafe_artifact_reference', codes)
        self.assertIn('live_execution_claim', codes)
        self.assertIn('payload_or_download_claim', codes)
        self.assertIn('consequential_devhub_action_language', codes)

    def test_rejects_active_promotion_official_action_and_guarantee_claims(self) -> None:
        packet = copy.deepcopy(self.preview)
        packet['source_registry_delta_placeholders'][0]['active_source_promotion_state'] = 'promoted_to_active'
        packet['archive_manifest_delta_placeholders'][0]['active_archive_promotion_state'] = 'promoted_to_active'
        packet['promotion_note'] = 'Promoted source registry and active archive promotion completed.'
        packet['official_note'] = 'Permit submitted and payment completed.'
        packet['legal_note'] = 'Permit will be approved.'
        codes = self.issue_codes(packet)
        self.assertIn('active_source_promotion_claim', codes)
        self.assertIn('active_archive_promotion_claim', codes)
        self.assertIn('active_promotion_claim', codes)
        self.assertIn('official_action_completion_claim', codes)
        self.assertIn('legal_or_permitting_outcome_guarantee', codes)


if __name__ == '__main__':
    unittest.main()
