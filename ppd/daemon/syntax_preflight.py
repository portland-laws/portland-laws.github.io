"""Changed-file syntax preflight for the PP&D daemon.

The daemon runs this before full validation so parser failures are caught and
rolled back with compact diagnostics. It intentionally scopes checks to changed
Python and TypeScript files only.
"""

from __future__ import annotations

import py_compile
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SyntaxPreflightResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class ApplyFlowSyntaxPreflight:
    """Daemon apply-flow payload for changed-file syntax checks."""

    ok: bool
    failure_kind: str
    errors: tuple[str, ...]
    validation_results: tuple[SyntaxPreflightResult, ...]


PYTHON_CONTROL_FLOW_RE = re.compile(r"^(if|elif|while|assert|return)\b")
PYTHON_TYPE_EXPR_RE = re.compile(r"\b(list|dict|tuple|set)\s*\[[^\]]+\]")
MISSING_COMPARISON_OPERATOR_RE = re.compile(
    r"\b(or|and)\s+[A-Za-z_][A-Za-z0-9_\.]*\s+(None|True|False|list\s*\[|dict\s*\[|tuple\s*\[|set\s*\[)"
)
RETURN_ANNOTATION_FRAGMENT_RE = re.compile(
    r"\breturn\s+[^#\n]+\s+(list|dict|tuple|set)\s*\[[^\]]+\]"
)


def changed_syntax_paths(changed_files: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return changed Python and TypeScript paths eligible for syntax preflight."""

    python_files: list[str] = []
    typescript_files: list[str] = []
    for changed_file in changed_files:
        normalized = Path(changed_file).as_posix()
        if "/node_modules/" in normalized or normalized.startswith("node_modules/"):
            continue
        if normalized.endswith(".py"):
            python_files.append(normalized)
        elif normalized.endswith((".ts", ".tsx")):
            typescript_files.append(normalized)
    return tuple(sorted(python_files)), tuple(sorted(typescript_files))


def run_changed_syntax_preflight(repo_root: Path, changed_files: Iterable[str], *, timeout: int = 300) -> list[SyntaxPreflightResult]:
    """Run py_compile and strict tsc only for changed syntax-bearing files."""

    python_files, typescript_files = changed_syntax_paths(changed_files)
    results: list[SyntaxPreflightResult] = []
    if python_files:
        results.extend(_run_python_preflight(repo_root, python_files))
    if typescript_files:
        results.append(_run_typescript_preflight(repo_root, typescript_files, timeout=timeout))
    return results


def run_apply_flow_syntax_preflight(repo_root: Path, changed_files: Iterable[str], *, timeout: int = 300) -> ApplyFlowSyntaxPreflight:
    """Return an apply-flow-ready syntax preflight decision.

    The daemon can call this immediately after writing proposed replacements and
    before broad validation. If ``ok`` is false, the caller should roll back the
    changed files, persist failed work with ``failure_kind``, and skip broad
    unittest or TypeScript validation for that cycle.
    """

    results = tuple(run_changed_syntax_preflight(repo_root, changed_files, timeout=timeout))
    if not results or all(result.ok for result in results):
        return ApplyFlowSyntaxPreflight(
            ok=True,
            failure_kind="",
            errors=(),
            validation_results=results,
        )
    diagnostics = compact_syntax_diagnostics(results)
    message = "Syntax preflight failed; file edits were rolled back."
    if diagnostics:
        message = f"{message} {diagnostics}"
    return ApplyFlowSyntaxPreflight(
        ok=False,
        failure_kind="syntax_preflight",
        errors=(message,),
        validation_results=results,
    )


def compact_syntax_diagnostics(results: Iterable[SyntaxPreflightResult], *, limit: int = 900) -> str:
    """Build compact parser diagnostics for failed syntax preflight commands."""

    messages: list[str] = []
    for result in results:
        if result.ok:
            continue
        command = " ".join(result.command)
        detail = " ".join(part for part in (result.stdout, result.stderr) if part).strip()
        detail = " ".join(detail.split())
        if len(detail) > limit:
            detail = detail[:limit].rstrip() + "..."
        messages.append(f"{command}: {detail or 'no diagnostics'}")
    return "; ".join(messages)


def _run_python_preflight(repo_root: Path, python_files: tuple[str, ...]) -> list[SyntaxPreflightResult]:
    results: list[SyntaxPreflightResult] = []
    for relative_path in python_files:
        path = repo_root / relative_path
        command = ("python3", "-m", "py_compile", relative_path)
        malformed = _detect_malformed_python_constructs(path, relative_path)
        if malformed:
            results.append(SyntaxPreflightResult(command=command, returncode=1, stderr=malformed))
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            results.append(SyntaxPreflightResult(command=command, returncode=1, stderr=str(exc.msg)))
        else:
            results.append(SyntaxPreflightResult(command=command, returncode=0))
    return results


def _detect_malformed_python_constructs(path: Path, relative_path: str) -> str:
    """Return a targeted diagnostic for recurrent proposal syntax mistakes."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return ""

    findings: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _looks_like_cross_language_python(stripped):
            findings.append(
                f"{relative_path}:{line_number}: malformed Python expression; "
                "use explicit operators such as `is None`, `is not None`, `isinstance(...)`, "
                "or a normal return expression. Do not place TypeScript-style type fragments "
                "inside Python control-flow or return statements."
            )
        if len(findings) >= 3:
            break
    return " ".join(findings)


def _looks_like_cross_language_python(stripped: str) -> bool:
    if not PYTHON_CONTROL_FLOW_RE.match(stripped):
        return False
    if MISSING_COMPARISON_OPERATOR_RE.search(stripped):
        return True
    if RETURN_ANNOTATION_FRAGMENT_RE.search(stripped):
        return True
    if " or " in stripped or " and " in stripped:
        return bool(PYTHON_TYPE_EXPR_RE.search(stripped))
    return False


def _run_typescript_preflight(repo_root: Path, typescript_files: tuple[str, ...], *, timeout: int) -> SyntaxPreflightResult:
    quoted_files = " ".join(shlex.quote(path) for path in typescript_files)
    script = (
        "npx tsc --noEmit --target ES2020 --module ESNext "
        "--moduleResolution node --strict --skipLibCheck --types node "
        f"{quoted_files}"
    )
    command = ("bash", "-lc", script)
    completed = subprocess.run(
        list(command),
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return SyntaxPreflightResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
