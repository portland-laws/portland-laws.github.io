from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_readiness.devhub_fixture_first_read_only_observation_seed_packet_v1 import (
    PACKET_VERSION,
    validate_devhub_fixture_first_read_only_observation_seed_packet_v1,
)

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'devhub_fixture_first_read_only_observation_seed_packet_v1' / 'seed_packet.json'


def load_packet() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))


def issue_messages(packet: dict) -> list[str]:
    return [issue.message for issue in validate_devhub_fixture_first_read_only_observation_seed_packet_v1(packet)]


class DevHubFixtureFirstReadOnlyObservationSeedPacketV1Test(unittest.TestCase):
    def assert_rejects(self, packet: dict, expected_fragment: str) -> None:
        messages = issue_messages(packet)
        self.assertTrue(messages, 'packet unexpectedly validated')
        self.assertTrue(any(expected_fragment in message for message in messages), messages)

    def test_fixture_packet_passes(self) -> None:
        packet = load_packet()
        self.assertEqual(PACKET_VERSION, packet['packet_version'])
        self.assertEqual([], validate_devhub_fixture_first_read_only_observation_seed_packet_v1(packet))

    def test_requires_synthetic_post_decision_rows_only(self) -> None:
        packet = load_packet()
        packet['input_rows'][0]['source_type'] = 'live_devhub_observation'
        self.assert_rejects(packet, 'input row must come from synthetic post-decision smoke replay data')

        packet = load_packet()
        packet['input_rows'][0]['contains_private_values'] = True
        self.assert_rejects(packet, 'input row must declare no private values')

    def test_requires_official_guidance_placeholders_without_live_fetch(self) -> None:
        packet = load_packet()
        packet['official_guidance_placeholders'][0]['source_type'] = 'downloaded_devhub_page'
        self.assert_rejects(packet, 'guidance source must be an official DevHub guidance placeholder')

        packet = load_packet()
        packet['official_guidance_placeholders'][0]['live_fetch_performed'] = True
        self.assert_rejects(packet, 'guidance placeholder must not perform live fetches')

    def test_requires_read_only_targets_with_declared_references(self) -> None:
        packet = load_packet()
        packet['observation_targets'][0]['classification'] = 'reversible_draft'
        self.assert_rejects(packet, 'observation target must be read-only')

        packet = load_packet()
        packet['observation_targets'][0]['basis_row_ids'] = ['missing-row']
        self.assert_rejects(packet, 'does not reference a declared row')

    def test_requires_fixture_only_capture_schema_updates(self) -> None:
        packet = load_packet()
        packet['fixture_only_capture_schema_updates'][0]['fixture_only'] = False
        self.assert_rejects(packet, 'capture schema update must be fixture_only')

        packet = load_packet()
        packet['fixture_only_capture_schema_updates'][0]['allowed_fixture_fields'] = ['permit_number']
        self.assert_rejects(packet, 'fixture capture fields must use synthetic_ prefixes')

    def test_rejects_artifact_or_live_action_policy_enabled(self) -> None:
        for key in packet_artifact_policy_keys():
            packet = load_packet()
            packet['artifact_policy'][key] = True
            self.assert_rejects(packet, f'artifact_policy.{key} must be false')

    def test_rejects_live_devhub_claims_outside_policy_context(self) -> None:
        packet = load_packet()
        packet['observation_targets'][0]['objective'] = 'Opened DevHub and logged in for an authenticated run.'
        self.assert_rejects(packet, 'live access or official-action claim is not allowed')

    def test_validation_commands_are_exact_offline_commands(self) -> None:
        packet = load_packet()
        packet['validation_commands'] = [['python3', '-m', 'unittest', 'discover']]
        self.assert_rejects(packet, 'validation command must be one of the exact offline commands for this packet')


def packet_artifact_policy_keys() -> tuple[str, ...]:
    return (
        'opens_devhub',
        'logs_in',
        'performs_form_fills',
        'performs_official_actions',
        'stores_auth_artifacts',
        'stores_session_artifacts',
        'stores_screenshots',
        'stores_traces',
        'stores_har_files',
        'stores_private_values',
        'stores_raw_crawl_output',
        'downloads_documents',
    )


if __name__ == '__main__':
    unittest.main()
