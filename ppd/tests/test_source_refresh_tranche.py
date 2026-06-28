import json
from pathlib import Path

from ppd.source_refresh_tranche import (
    build_refresh_tranche_proposal,
    validate_refresh_tranche_proposal,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_refresh_tranche" / "proposal_packet.json"


def load_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_builds_expected_metadata_only_refresh_tranche_proposal() -> None:
    fixture = load_fixture()

    proposal = build_refresh_tranche_proposal(fixture)

    assert proposal == fixture["expected_proposal"]


def test_refresh_tranche_proposal_requires_all_safety_attestations() -> None:
    fixture = load_fixture()
    proposal = build_refresh_tranche_proposal(fixture)
    proposal["attestations"]["no_fetch_performed"] = False

    try:
        validate_refresh_tranche_proposal(proposal)
    except ValueError as exc:
        assert "no_fetch_performed" in str(exc)
    else:
        raise AssertionError("missing attestation failure")


def test_refresh_tranche_proposal_requires_reviewer_owner_and_evidence_refs() -> None:
    fixture = load_fixture()
    proposal = build_refresh_tranche_proposal(fixture)
    del proposal["ordered_sources"][0]["reviewer"]

    try:
        validate_refresh_tranche_proposal(proposal)
    except ValueError as exc:
        assert "reviewer" in str(exc)
    else:
        raise AssertionError("missing reviewer failure")
