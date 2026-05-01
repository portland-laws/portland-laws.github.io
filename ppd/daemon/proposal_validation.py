"""Daemon-side validation for proposed PP&D file replacements.

The helpers in this module operate on proposal JSON before broader test
selection or discovery. They only inspect proposed replacement content and do
not write into the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import py_compile
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ProposalValidationFailure:
    """A deterministic proposal validation failure."""

    path: str
    kind: str
    message: str
    retry_same_task: bool
    signature: str


@dataclass(frozen=True)
class ProposalValidationResult:
    """Result of pre-discovery proposal validation."""

    accepted: bool
    failures: tuple[ProposalValidationFailure, ...] = field(default_factory=tuple)

    @property
    def retry_same_task(self) -> bool:
        return self.accepted or all(failure.retry_same_task for failure in self.failures)


def _is_python_replacement(path: str) -> bool:
    return Path(path).suffix == ".py"


def _failure_signature(path: str, message: str) -> str:
    digest = hashlib.sha256(f"{path}\n{message}".encode("utf-8")).hexdigest()
    return f"py_compile:{digest[:24]}"


def _compile_replacement(path: str, content: str) -> ProposalValidationFailure | None:
    with tempfile.TemporaryDirectory(prefix="ppd-proposal-pycompile-") as temp_dir:
        candidate_path = Path(temp_dir) / Path(path).name
        candidate_path.write_text(content, encoding="utf-8")
        try:
            py_compile.compile(str(candidate_path), doraise=True)
        except py_compile.PyCompileError as exc:
            message = exc.msg.strip() or str(exc).strip()
            return ProposalValidationFailure(
                path=path,
                kind="python_syntax_error",
                message=message,
                retry_same_task=False,
                signature=_failure_signature(path, message),
            )
    return None


def validate_python_replacements_before_discovery(proposal: Mapping[str, Any]) -> ProposalValidationResult:
    """Run py_compile on every proposed Python replacement.

    Syntax failures are classified as non-retryable for the same daemon task so
    the supervisor can record the failure and request a smaller repair proposal
    instead of blindly reusing the same task attempt.
    """

    failures: list[ProposalValidationFailure] = []
    files = proposal.get("files", [])
    if not isinstance(files, Sequence) or isinstance(files, (str, bytes)):
        return ProposalValidationResult(
            accepted=False,
            failures=(
                ProposalValidationFailure(
                    path="",
                    kind="invalid_proposal_files",
                    message="proposal files must be a sequence of replacement records",
                    retry_same_task=False,
                    signature="invalid_proposal_files",
                ),
            ),
        )

    for index, replacement in enumerate(files):
        if not isinstance(replacement, Mapping):
            failures.append(
                ProposalValidationFailure(
                    path=f"",
                    kind="invalid_file_replacement",
                    message="file replacement must be an object with path and content",
                    retry_same_task=False,
                    signature=f"invalid_file_replacement:{index}",
                )
            )
            continue

        path = replacement.get("path")
        content = replacement.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            failures.append(
                ProposalValidationFailure(
                    path=f"",
                    kind="invalid_file_replacement",
                    message="file replacement path and content must be strings",
                    retry_same_task=False,
                    signature=f"invalid_file_replacement:{index}:path_content",
                )
            )
            continue

        if _is_python_replacement(path):
            failure = _compile_replacement(path, content)
            if failure is not None:
                failures.append(failure)

    return ProposalValidationResult(accepted=not failures, failures=tuple(failures))


__all__ = [
    "ProposalValidationFailure",
    "ProposalValidationResult",
    "validate_python_replacements_before_discovery",
]
