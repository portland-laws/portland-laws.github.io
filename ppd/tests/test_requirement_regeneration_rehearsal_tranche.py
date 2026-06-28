import json
import unittest
from pathlib import Path

from ppd.requirement_regeneration_rehearsal_tranche import (
    build_requirement_regeneration_rehearsal_tranche_packet,
    validate_requirement_regeneration_rehearsal_tranche_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_regeneration_rehearsal_tranche" / "packet.json"


def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class RequirementRegenerationRehearsalTrancheTest(unittest.TestCase):
    def test_builds_expected_ordered_synthetic_rerun_cases(self) -> None:
        fixture = load_fixture()

        packet = build_requirement_regeneration_rehearsal_tranche_packet(fixture)

        self.assertEqual(packet, fixture["expected_packet"])

    def test_rehearsal_tranche_requires_no_live_extraction_attestation(self) -> None:
        fixture = load_fixture()
        packet = build_requirement_regeneration_rehearsal_tranche_packet(fixture)
        packet["attestations"]["no_live_extraction_performed"] = False

        with self.assertRaisesRegex(ValueError, "no_live_extraction_performed"):
            validate_requirement_regeneration_rehearsal_tranche_packet(packet)

    def test_rehearsal_tranche_requires_metadata_only_outputs(self) -> None:
        fixture = load_fixture()
        packet = build_requirement_regeneration_rehearsal_tranche_packet(fixture)
        packet["expected_metadata_only_outputs"][0]["metadata_only"] = False

        with self.assertRaisesRegex(ValueError, "metadata_only"):
            validate_requirement_regeneration_rehearsal_tranche_packet(packet)

    def test_rehearsal_tranche_requires_reviewer_owner(self) -> None:
        fixture = load_fixture()
        packet = build_requirement_regeneration_rehearsal_tranche_packet(fixture)
        del packet["ordered_synthetic_rerun_cases"][0]["reviewer_owner"]

        with self.assertRaisesRegex(ValueError, "reviewer_owner"):
            validate_requirement_regeneration_rehearsal_tranche_packet(packet)


if __name__ == "__main__":
    unittest.main()
