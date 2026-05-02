"""Guardrails for blocked-domain syntax recovery proposals.

Syntax-recovery work against a blocked domain task must stay narrow. This module
validates the worker proposal shape before broad validation so the daemon can
reject oversized parser-recovery attempts deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


SOURCE_SUFFIXES = (".py", ".ts", ".tsx")
TEST_FIXTURE_PREFIX = "ppd/tests/fixtures/"


@dataclass(frozen=True)
class BlockedSyntaxRecoveryFinding:
    """A deterministic rejection reason for blocked syntax-recovery proposals."""

    reason: str
    path: str = ""


def changed_source_files(changed_files: Iterable[str]) -> tuple[str, ...]:
    """Return changed Python/TypeScript files that need syntax evidence."""

    paths: list[str] = []
    for changed_file in changed_files:
        normalized = Path(changed_file).as_posix()
        if normalized.startswith(TEST_FIXTURE_PREFIX):
            continue
        if "/node_modules/" in normalized or normalized.startswith("node_modules/"):
            continue
        if normalized.endswith(SOURCE_SUFFIXES):
            paths.append(normalized)
    return tuple(sorted(dict.fromkeys(paths)))


def syntax_preflight_evidence_paths(validation_commands: Sequence[Sequence[str]]) -> tuple[str, ...]:
    """Extract source paths covered by proposal-provided syntax preflight commands."""

    covered: set[str] = set()
    for command in validation_commands:
        command_text = " ".join(str(part) for part in command)
        for part in command:
            token = str(part).strip("'\"")
            normalized = Path(token).as_posix()
            if not normalized.startswith("ppd/") or not normalized.endswith(SOURCE_SUFFIXES):
                continue
            if normalized.endswith(".py") and "py_compile" in command_text:
                covered.add(normalized)
            if normalized.endswith((".ts", ".tsx")) and "tsc" in command_text:
                covered.add(normalized)
    return tuple(sorted(covered))


def validate_blocked_domain_syntax_recovery_proposal(
    *,
    changed_files: Iterable[str],
    validation_commands: Sequence[Sequence[str]],
) -> list[BlockedSyntaxRecoveryFinding]:
    """Reject unsafe syntax-recovery proposals for blocked domain tasks.

    A valid blocked-domain syntax recovery proposal may change at most one
    Python/TypeScript source file, and every changed Python/TypeScript file must
    be named in proposal syntax-preflight evidence: ``py_compile`` for Python or
    ``tsc`` for TypeScript.
    """

    source_files = changed_source_files(changed_files)
    findings: list[BlockedSyntaxRecoveryFinding] = []
    if len(source_files) > 1:
        findings.append(
            BlockedSyntaxRecoveryFinding(
                reason="blocked syntax-recovery proposals may change at most one Python or TypeScript source file",
                path=", ".join(source_files),
            )
        )
    covered = set(syntax_preflight_evidence_paths(validation_commands))
    for source_file in source_files:
        if source_file not in covered:
            findings.append(
                BlockedSyntaxRecoveryFinding(
                    reason="changed Python or TypeScript file lacks proposal syntax-preflight evidence",
                    path=source_file,
                )
            )
    return findings


def assert_blocked_domain_syntax_recovery_proposal(
    *,
    changed_files: Iterable[str],
    validation_commands: Sequence[Sequence[str]],
) -> None:
    """Raise ValueError when a blocked syntax-recovery proposal is unsafe."""

    findings = validate_blocked_domain_syntax_recovery_proposal(
        changed_files=changed_files,
        validation_commands=validation_commands,
    )
    if findings:
        details = "; ".join(
            f"{finding.reason}: {finding.path}" if finding.path else finding.reason
            for finding in findings
        )
        raise ValueError(details)
