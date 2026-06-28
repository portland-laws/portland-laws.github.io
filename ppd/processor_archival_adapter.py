"""PP&D archival adapter boundary for processor-suite delegation.

The adapter keeps PP&D policy decisions outside the processor suite.  It only
calls the downstream processor after the local preflight contract has accepted
URL allowlisting, robots policy, content type, timeout budget, and the rule that
raw response bodies are not passed through this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


class PolicyPreflightError(RuntimeError):
    """Raised when a PP&D archival request fails local policy preflight."""


@dataclass(frozen=True)
class ProcessorArchiveRequest:
    """Normalized request passed to the archival adapter."""

    url: str
    content_type: str
    timeout_seconds: float
    metadata: Mapping[str, Any] = field(default_factory=dict)
    raw_body: bytes | None = None


@dataclass(frozen=True)
class ProcessorArchiveResult:
    """Small stable result shape returned by processor-suite adapters."""

    url: str
    processor: str
    status: str
    artifact_ref: str | None = None


class PpdPolicyPreflight(Protocol):
    """Policy checks required before processor-suite delegation."""

    def require_allowed_url(self, request: ProcessorArchiveRequest) -> None:
        """Reject URLs outside the PP&D archival allowlist."""

    def require_robots_allowed(self, request: ProcessorArchiveRequest) -> None:
        """Reject URLs disallowed by robots policy."""

    def require_supported_content_type(self, request: ProcessorArchiveRequest) -> None:
        """Reject content types outside the archival contract."""

    def require_timeout_budget(self, request: ProcessorArchiveRequest) -> None:
        """Reject missing or non-positive timeout budgets."""

    def require_no_raw_body(self, request: ProcessorArchiveRequest) -> None:
        """Reject attempts to pass raw crawl bodies into processors."""


class ProcessorSuite(Protocol):
    """Minimal ipfs_datasets_py processor-suite shape used by PP&D."""

    def process(self, request: ProcessorArchiveRequest) -> ProcessorArchiveResult:
        """Archive a preflight-approved request."""


class ProcessorArchivalAdapter:
    """Apply PP&D preflight before calling an ipfs_datasets_py processor suite."""

    def __init__(self, preflight: PpdPolicyPreflight, processors: ProcessorSuite) -> None:
        self._preflight = preflight
        self._processors = processors

    def archive(self, request: ProcessorArchiveRequest) -> ProcessorArchiveResult:
        self._preflight.require_allowed_url(request)
        self._preflight.require_robots_allowed(request)
        self._preflight.require_supported_content_type(request)
        self._preflight.require_timeout_budget(request)
        self._preflight.require_no_raw_body(request)
        return self._processors.process(request)
