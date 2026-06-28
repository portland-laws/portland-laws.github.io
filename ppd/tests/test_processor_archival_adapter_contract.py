from __future__ import annotations

from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ppd.processor_archival_adapter import (  # noqa: E402
    PolicyPreflightError,
    ProcessorArchivalAdapter,
    ProcessorArchiveRequest,
    ProcessorArchiveResult,
)


class RecordingPreflight:
    def __init__(self, events: list[str], fail_at: str | None = None) -> None:
        self.events = events
        self.fail_at = fail_at

    def _record(self, stage: str) -> None:
        self.events.append(stage)
        if self.fail_at == stage:
            raise PolicyPreflightError(stage)

    def require_allowed_url(self, request: ProcessorArchiveRequest) -> None:
        assert request.url.startswith("https://www.portland.gov/ppd/")
        self._record("allowlist")

    def require_robots_allowed(self, request: ProcessorArchiveRequest) -> None:
        self._record("robots")

    def require_supported_content_type(self, request: ProcessorArchiveRequest) -> None:
        assert request.content_type == "text/html"
        self._record("content-type")

    def require_timeout_budget(self, request: ProcessorArchiveRequest) -> None:
        assert request.timeout_seconds > 0
        self._record("timeout")

    def require_no_raw_body(self, request: ProcessorArchiveRequest) -> None:
        assert request.raw_body is None
        self._record("no-raw-body")


class RecordingProcessorSuite:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def process(self, request: ProcessorArchiveRequest) -> ProcessorArchiveResult:
        self.events.append("processor-suite")
        assert request.raw_body is None
        return ProcessorArchiveResult(
            url=request.url,
            processor="ipfs_datasets_py",
            status="archived",
            artifact_ref="fixture://processor-archive/ppd-policy-page",
        )


def _request() -> ProcessorArchiveRequest:
    return ProcessorArchiveRequest(
        url="https://www.portland.gov/ppd/permits",
        content_type="text/html",
        timeout_seconds=15.0,
        metadata={"fixture": "processor-archive-contract"},
    )


def test_processor_suite_runs_only_after_all_ppd_policy_preflight_decisions() -> None:
    events: list[str] = []
    adapter = ProcessorArchivalAdapter(
        preflight=RecordingPreflight(events),
        processors=RecordingProcessorSuite(events),
    )

    result = adapter.archive(_request())

    assert result.status == "archived"
    assert result.processor == "ipfs_datasets_py"
    assert events == [
        "allowlist",
        "robots",
        "content-type",
        "timeout",
        "no-raw-body",
        "processor-suite",
    ]


@pytest.mark.parametrize(
    "blocked_stage",
    ["allowlist", "robots", "content-type", "timeout", "no-raw-body"],
)
def test_processor_suite_is_not_called_when_any_preflight_decision_rejects(
    blocked_stage: str,
) -> None:
    events: list[str] = []
    adapter = ProcessorArchivalAdapter(
        preflight=RecordingPreflight(events, fail_at=blocked_stage),
        processors=RecordingProcessorSuite(events),
    )

    with pytest.raises(PolicyPreflightError):
        adapter.archive(_request())

    assert "processor-suite" not in events
    assert events[-1] == blocked_stage
