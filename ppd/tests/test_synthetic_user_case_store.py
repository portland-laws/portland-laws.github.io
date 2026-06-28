from pathlib import Path

import pytest

from ppd.adapters.synthetic_user_case_store import (
    RedactedSyntheticUserCaseStore,
    SyntheticUserCaseStoreError,
)


FIXTURES = Path(__file__).parent / "fixtures" / "synthetic_user_case"


def test_load_fixture_normalizes_freshness_confidence_and_dates() -> None:
    store = RedactedSyntheticUserCaseStore()

    case = store.load_fixture(FIXTURES / "sample_case.json")

    assert case.case_id == "synthetic-permit-owner-001"
    assert case.facts[0].freshness == "current"
    assert case.facts[0].confidence == 0.9
    assert case.facts[1].freshness == "stale"
    assert case.facts[1].confidence == 1.0
    assert case.documents[0].published_at == "2026-05-01"
    assert store.get_case(case.case_id) == case


@pytest.mark.parametrize(
    "payload",
    [
        {"case_id": "x", "facts": [{"key": "password", "value": "redacted"}], "documents": []},
        {"case_id": "x", "facts": [{"key": "note", "value": "Bearer abc.def"}], "documents": []},
        {"case_id": "x", "facts": [{"key": "note", "value": "4111 1111 1111 1111"}], "documents": []},
        {"case_id": "x", "facts": [{"key": "note", "value": "password: hunter2"}], "documents": []},
        {"case_id": "x", "auth_state": {"cookies": []}, "facts": [], "documents": []},
        {"case_id": "x", "trace_path": "trace.zip", "facts": [], "documents": []},
        {"case_id": "x", "har": {"log": {}}, "facts": [], "documents": []},
        {"case_id": "x", "screenshots": ["screen.png"], "facts": [], "documents": []},
        {"case_id": "x", "facts": [{"key": "note", "value": "/home/alice/private.txt"}], "documents": []},
        {"case_id": "x", "facts": [{"key": "local_private_path", "value": "redacted"}], "documents": []},
    ],
)
def test_rejects_private_artifacts_and_raw_values(payload: dict[str, object]) -> None:
    store = RedactedSyntheticUserCaseStore()

    with pytest.raises(SyntheticUserCaseStoreError):
        store.add_case(payload)


def test_accepts_minimal_redacted_fixture_case() -> None:
    store = RedactedSyntheticUserCaseStore()

    case = store.add_case(
        {
            "case_id": "minimal-redacted-case",
            "facts": [
                {
                    "key": "permit_category",
                    "value": "mechanical",
                    "freshness": "recent",
                    "confidence": "0.75",
                }
            ],
            "documents": [{"document_id": "doc-min", "title": "Synthetic metadata only"}],
        }
    )

    assert case.facts[0].freshness == "recent"
    assert case.facts[0].confidence == 0.75
    assert case.documents[0].url is None
