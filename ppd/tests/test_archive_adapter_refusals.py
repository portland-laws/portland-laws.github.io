from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ppd.contracts.archive_adapter import PpdArchiveAdapterRecord
from ppd.crawler.archive_adapter_preflight import invoke_archive_processor_from_dict


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "archive-adapter" / "refusal_cases.json"


class RecordingArchiveBackend:
    def __init__(self) -> None:
        self.records: list[PpdArchiveAdapterRecord] = []

    def archive(self, record: PpdArchiveAdapterRecord) -> Mapping[str, Any]:
        self.records.append(record)
        return {"archivedRecordId": record.id, "backend": record.processor.backend_path}


def test_archive_adapter_refuses_unsafe_fixtures_before_processor_invocation() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert fixture["fixtureKind"] == "archive_adapter_refusal_cases"

    refusal_cases = [case for case in fixture["cases"] if not case["expectedInvoke"]]
    assert refusal_cases, "fixture must include unsafe refusal cases"

    for case in refusal_cases:
        backend = RecordingArchiveBackend()
        result = invoke_archive_processor_from_dict(case["record"], backend)

        assert result.status == "refused", case["id"]
        assert result.invoked_processor is False, case["id"]
        assert backend.records == [], case["id"]
        assert result.errors, case["id"]
        assert case["expectedErrorContains"] in "\n".join(result.errors), case["id"]


def test_archive_adapter_invokes_processor_for_public_allowlisted_control() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    control_cases = [case for case in fixture["cases"] if case["expectedInvoke"]]
    assert len(control_cases) == 1

    backend = RecordingArchiveBackend()
    result = invoke_archive_processor_from_dict(control_cases[0]["record"], backend)

    assert result.status == "invoked"
    assert result.invoked_processor is True
    assert result.errors == ()
    assert [record.id for record in backend.records] == ["allow-public-ppd-control"]
    assert result.processor_response == {
        "archivedRecordId": "allow-public-ppd-control",
        "backend": "ipfs_datasets_py/ipfs_datasets_py/processors",
    }
