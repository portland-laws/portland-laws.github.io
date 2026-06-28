from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.extraction.change_impact import (
    SourceSnapshot,
    compute_change_impacts,
    impacted_guardrail_bundle_ids,
    impacted_requirement_ids,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "change_impact"


def _load_fixture(name: str) -> list[dict[str, object]]:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, list)
    return value


def test_compute_change_impacts_is_deterministic_and_metadata_only() -> None:
    previous = _load_fixture("previous_sources.json")
    current = _load_fixture("current_sources.json")

    impacts = compute_change_impacts(previous, current)

    assert [impact.as_dict() for impact in impacts] == [
        {
            "source_id": "ppd-devhub-faq",
            "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
            "change_type": "changed",
            "previous_content_hash": "sha256:111111",
            "current_content_hash": "sha256:222222",
            "affected_requirement_ids": ["req-corrections-upload", "req-fee-payment"],
            "affected_guardrail_bundle_ids": ["guard-devhub-actions", "guard-fee-payment"],
            "changed_semantic_signatures": ["action:pay-fees", "action:upload-corrections"],
        },
        {
            "source_id": "ppd-file-standards",
            "canonical_url": "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
            "change_type": "added",
            "previous_content_hash": None,
            "current_content_hash": "sha256:444444",
            "affected_requirement_ids": ["req-file-naming"],
            "affected_guardrail_bundle_ids": ["guard-document-prep"],
            "changed_semantic_signatures": ["document:file-name-rule"],
        },
    ]
    assert impacted_requirement_ids(impacts) == (
        "req-corrections-upload",
        "req-fee-payment",
        "req-file-naming",
    )
    assert impacted_guardrail_bundle_ids(impacts) == (
        "guard-devhub-actions",
        "guard-document-prep",
        "guard-fee-payment",
    )


def test_raw_body_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="raw source body fields"):
        SourceSnapshot.from_mapping(
            {
                "source_id": "unsafe",
                "canonical_url": "https://www.portland.gov/ppd",
                "content_hash": "sha256:unsafe",
                "raw_html": "do not commit this",
            }
        )


def test_duplicate_source_ids_are_rejected() -> None:
    duplicate = {
        "source_id": "same",
        "canonical_url": "https://www.portland.gov/ppd",
        "content_hash": "sha256:aaaaaa",
    }

    with pytest.raises(ValueError, match="duplicate source_id"):
        compute_change_impacts([duplicate, duplicate], [])
