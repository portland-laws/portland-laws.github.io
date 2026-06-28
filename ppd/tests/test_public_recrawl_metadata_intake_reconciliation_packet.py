from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.crawler.public_recrawl_metadata_intake_reconciliation_packet import (
    build_public_recrawl_metadata_intake_reconciliation_packet,
    validate_public_recrawl_metadata_intake_reconciliation_packet,
)

_FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'public_recrawl_metadata_intake_reconciliation'


class PublicRecrawlMetadataIntakeReconciliationPacketTest(unittest.TestCase):
    def test_builds_metadata_only_reconciliation_packet_from_fixture_inputs(self) -> None:
        packet = _valid_packet()
        result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
        self.assertTrue(result.valid, result.errors)
        self.assertFalse(packet['liveNetworkUsed'])
        self.assertFalse(packet['processorInvoked'])
        self.assertFalse(packet['archiveArtifactWritten'])
        self.assertEqual(2, packet['reconciliationSummary']['syntheticIntakeRowCount'])
        self.assertEqual(2, packet['reconciliationSummary']['expectedManifestReferenceCount'])
        self.assertEqual(2, packet['reconciliationSummary']['changedSourceReviewQueueCount'])
        self.assertEqual(1, packet['reconciliationSummary']['freshnessBadgeUpdateCandidateCount'])
        self.assertGreaterEqual(packet['reconciliationSummary']['abortNoteCount'], 3)
        intake_source_ids = {row['source_id'] for row in packet['syntheticMetadataOnlyIntakeRows']}
        self.assertEqual({'source-portland-ppd', 'source-devhub-faqs'}, intake_source_ids)
        for row in packet['syntheticMetadataOnlyIntakeRows']:
            self.assertTrue(row['metadataOnly'])
            self.assertTrue(row['fixtureSynthetic'])
            self.assertFalse(row['liveFetchUsed'])
            self.assertFalse(row['processorInvoked'])
            self.assertFalse(row['archiveArtifactWritten'])

    def test_rejects_live_fetch_claim_in_reconciliation_packet(self) -> None:
        packet = _valid_packet()
        packet['syntheticMetadataOnlyIntakeRows'][0]['liveFetchUsed'] = True
        result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any('liveFetchUsed' in error for error in result.errors))

    def test_rejects_raw_download_archive_and_private_url_references(self) -> None:
        packet = _valid_packet()
        packet['syntheticMetadataOnlyIntakeRows'][0]['raw_body_ref'] = 'raw_body://source-portland-ppd'
        packet['syntheticMetadataOnlyIntakeRows'][0]['download_url'] = 'file:///tmp/downloaded_documents/source.pdf'
        packet['expectedManifestReferences'][0]['archive_ref'] = 's3://ppd-private-archive/object'
        packet['expectedManifestReferences'][0]['canonical_url'] = 'https://devhub.portlandoregon.gov/account/permits'
        result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
        self.assertFalse(result.valid)
        joined = '\n'.join(result.errors)
        self.assertIn('raw_body', joined)
        self.assertIn('file://', joined)
        self.assertIn('s3://', joined)
        self.assertIn('private or authenticated', joined)

    def test_rejects_non_allowlisted_urls_execution_claims_and_mutation_flags(self) -> None:
        packet = _valid_packet()
        packet['syntheticMetadataOnlyIntakeRows'][0]['requested_url'] = 'https://example.com/ppd'
        packet['processorExecuted'] = True
        packet['archiveArtifactWritesAllowed'] = True
        packet['sourceRegistryMutation'] = {'activeSourceRegistryMutated': True}
        result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
        self.assertFalse(result.valid)
        joined = '\n'.join(result.errors)
        self.assertIn('requested_url must be an HTTPS allowlisted public URL', joined)
        self.assertIn('processorExecuted', joined)
        self.assertIn('archiveArtifactWritesAllowed', joined)
        self.assertIn('activeSourceRegistryMutated', joined)

    def test_rejects_uncited_freshness_updates_missing_abort_notes_and_missing_queue_owner(self) -> None:
        packet = _valid_packet()
        packet['freshnessBadgeUpdateCandidates'][0]['source_evidence_ids'] = []
        packet['changedSourceReviewQueues'][0]['reviewer_owner'] = ''
        packet['abortNotes'] = [{'abort_id': 'metadata-only-policy', 'note': 'Metadata-only reconciliation policy note.', 'abortBeforeLiveFetch': True, 'processorInvocationAllowed': False, 'archiveArtifactWriteAllowed': False}]
        result = validate_public_recrawl_metadata_intake_reconciliation_packet(packet)
        self.assertFalse(result.valid)
        joined = '\n'.join(result.errors)
        self.assertIn('freshnessBadgeUpdateCandidates[0].source_evidence_ids', joined)
        self.assertIn('changedSourceReviewQueues[0].reviewer_owner', joined)
        self.assertIn('live-fetch abort note', joined)
        self.assertIn('processor execution abort note', joined)
        self.assertIn('archive mutation abort note', joined)


def _valid_packet() -> dict[str, object]:
    return build_public_recrawl_metadata_intake_reconciliation_packet(
        _load_fixture('processor_handoff_rehearsal_packet.json'),
        _load_fixture('public_source_registry_coverage_gap_packet.json'),
        generated_at='2026-05-29T00:00:00Z',
    )


def _load_fixture(name: str) -> dict[str, object]:
    with (_FIXTURE_DIR / name).open(encoding='utf-8') as handle:
        return json.load(handle)


if __name__ == '__main__':
    unittest.main()
