#!/usr/bin/env python3
"""Autonomous PP&D implementation daemon.

This daemon borrows the safe operating pattern from the TypeScript logic-port
daemon, but keeps all PP&D work in the isolated ``ppd/`` workspace.

It accepts model output only as JSON file replacements and never executes
commands returned by the model.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ppd.daemon.accepted_work_ledger import (
    AcceptedWorkArtifacts,
    append_accepted_work_ledger as append_accepted_work_jsonl,
    build_accepted_work_ledger_entry,
)
from ppd.daemon.syntax_preflight import run_apply_flow_syntax_preflight


CHECKBOX_RE = re.compile(r"^(?P<prefix>\s*-\s+\[)(?P<mark>[ xX~!])(?P<suffix>\]\s+)(?P<title>.+)$")
JSON_BLOCK_RE = re.compile(r"```json\s*([\s\S]*?)\s*```", re.IGNORECASE)
TASK_BOARD_STATUS_RE = re.compile(
    r"\n?<!-- ppd-daemon-task-board:start -->[\s\S]*?<!-- ppd-daemon-task-board:end -->\n?",
    re.MULTILINE,
)

ALLOWED_WRITE_PREFIXES = (
    "ppd/",
    "docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md",
)

DISALLOWED_WRITE_PREFIXES = (
    "src/lib/logic/",
    "public/corpus/portland-or/current/",
    "ipfs_datasets_py/.daemon/",
    "docs/IPFS_DATASETS_LOGIC_TYPESCRIPT_PORT_PLAN.md",
    "docs/IPFS_DATASETS_LOGIC_PORT_DAEMON_ACCEPTED.md",
)

PRIVATE_WRITE_PATH_FRAGMENTS = (
    "ppd/data/private/",
    "storage-state",
    "storage_state",
    "auth-state",
    "auth_state",
)
PRIVATE_WRITE_PATH_TOKENS = {"session", "sessions"}

DEFAULT_VALIDATION_COMMANDS = (
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
    ("python3", "-m", "unittest", "discover", "-s", "ppd/tests", "-p", "test_*.py"),
    (
        "bash",
        "-lc",
        "files=$(find ppd -name '*.ts' -not -path '*/node_modules/*' -print); "
        "test -z \"$files\" || npx tsc --noEmit --target ES2020 --module ESNext "
        "--moduleResolution node --strict --skipLibCheck --types node $files",
    ),
)

FORBIDDEN_ABSENCE_MARKERS = (
    "cookie",
    "cookies",
    "screenshot",
    "screenshots",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
)

PROTECTED_BLOCKED_REVISIT_CHECKBOX_IDS = frozenset(
    {
        178,
        182,
        186,
        187,
        191,
        193,
        194,
        195,
        197,
        198,
        203,
        208,
        209,
        210,
    }
)


@dataclass(frozen=True)
class Task:
    index: int
    title: str
    status: str
    checkbox_id: int

    @property
    def label(self) -> str:
        return f"Task checkbox-{self.checkbox_id}: {self.title}"


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def compact(self, limit: int = 5000) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": compact_message(self.stdout, limit=limit),
            "stderr": compact_message(self.stderr, limit=limit),
        }


@dataclass
class Proposal:
    summary: str = ""
    impact: str = ""
    files: list[dict[str, str]] = field(default_factory=list)
    validation_commands: list[list[str]] = field(default_factory=list)
    raw_response: str = ""
    errors: list[str] = field(default_factory=list)
    failure_kind: str = ""
    target_task: str = ""
    changed_files: list[str] = field(default_factory=list)
    validation_results: list[CommandResult] = field(default_factory=list)
    applied: bool = False
    dry_run: bool = True

    @property
    def valid(self) -> bool:
        return self.applied and not self.errors and all(result.ok for result in self.validation_results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "impact": self.impact,
            "target_task": self.target_task,
            "files": [item.get("path", "") for item in self.files],
            "changed_files": self.changed_files,
            "applied": self.applied,
            "dry_run": self.dry_run,
            "validation_passed": bool(self.validation_results) and all(result.ok for result in self.validation_results),
            "validation_results": [result.compact() for result in self.validation_results],
            "errors": [compact_message(error) for error in self.errors],
            "failure_kind": self.failure_kind,
        }


@dataclass
class Config:
    repo_root: Path
    task_board: Path = Path("ppd/daemon/task-board.md")
    plan_doc: Path = Path("docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md")
    readme: Path = Path("ppd/README.md")
    status_file: Path = Path("ppd/daemon/status.json")
    progress_file: Path = Path("ppd/daemon/progress.json")
    result_log: Path = Path("ppd/daemon/ppd-daemon.jsonl")
    accepted_dir: Path = Path("ppd/daemon/accepted-work")
    failed_dir: Path = Path("ppd/daemon/failed-patches")
    model_name: str = "gpt-5.5"
    provider: Optional[str] = None
    apply: bool = False
    watch: bool = False
    iterations: int = 1
    interval_seconds: float = 0.0
    heartbeat_seconds: float = 30.0
    command_timeout_seconds: int = 300
    llm_timeout_seconds: int = 300
    max_prompt_chars: int = 60000
    max_compact_prompt_chars: int = 4200
    allow_local_fallback: bool = False
    revisit_blocked: bool = False
    max_task_failures_before_block: int = 3
    validation_commands: tuple[tuple[str, ...], ...] = DEFAULT_VALIDATION_COMMANDS

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.repo_root / path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_text(path: Path, limit: Optional[int] = None) -> str:
    text = path.read_text(encoding="utf-8")
    if limit is not None and len(text) > limit:
        return text[:limit] + "\n\n[truncated]\n"
    return text


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def parse_tasks(markdown: str) -> list[Task]:
    tasks: list[Task] = []
    for line in markdown.splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        mark = match.group("mark")
        raw_title = match.group("title").strip()
        checkbox_id = len(tasks) + 1
        title = raw_title
        id_match = re.match(r"Task checkbox-(?P<id>\d+):\s*(?P<title>.+)$", raw_title)
        if id_match:
            checkbox_id = int(id_match.group("id"))
            title = id_match.group("title").strip()
        status = "needed"
        if mark.lower() == "x":
            status = "complete"
        elif mark == "~":
            status = "in-progress"
        elif mark == "!":
            status = "blocked"
        tasks.append(Task(index=len(tasks) + 1, title=title, status=status, checkbox_id=checkbox_id))
    return tasks


def select_task(tasks: Iterable[Task], *, revisit_blocked: bool = False) -> Optional[Task]:
    task_list = list(tasks)
    for task in task_list:
        if task.status in {"needed", "in-progress"}:
            return task
    if revisit_blocked:
        for task in task_list:
            if task.status == "blocked" and task.checkbox_id not in PROTECTED_BLOCKED_REVISIT_CHECKBOX_IDS:
                return task
    return None


def replace_task_mark(markdown: str, selected: Task, mark: str) -> str:
    seen = 0
    lines = markdown.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        match = CHECKBOX_RE.match(line.rstrip("\n"))
        if not match:
            continue
        seen += 1
        if seen == selected.index:
            lines[idx] = f"{match.group('prefix')}{mark}{match.group('suffix')}{match.group('title')}\n"
            break
    return "".join(lines)


def count_unmanaged_generated_status_sections(markdown: str) -> int:
    """Count generated-status headings outside the daemon-managed marker block."""

    count = 0
    in_managed_block = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped == "<!-- ppd-daemon-task-board:start -->":
            in_managed_block = True
            continue
        if stripped == "<!-- ppd-daemon-task-board:end -->":
            in_managed_block = False
            continue
        if not in_managed_block and stripped == "## Generated Status":
            count += 1
    return count


def strip_unmanaged_generated_status_sections(markdown: str) -> str:
    """Remove stale generated-status sections outside the managed marker block."""

    lines = markdown.splitlines()
    cleaned: list[str] = []
    in_managed_block = False
    skipping_unmanaged_status = False
    for line in lines:
        stripped = line.strip()
        if stripped == "<!-- ppd-daemon-task-board:start -->":
            in_managed_block = True
            skipping_unmanaged_status = False
            cleaned.append(line)
            continue
        if stripped == "<!-- ppd-daemon-task-board:end -->":
            in_managed_block = False
            cleaned.append(line)
            continue
        if skipping_unmanaged_status:
            if stripped.startswith("## ") or stripped == "<!-- ppd-daemon-task-board:start -->":
                skipping_unmanaged_status = False
            else:
                continue
        if not in_managed_block and stripped == "## Generated Status":
            skipping_unmanaged_status = True
            continue
        cleaned.append(line)
    return "\n".join(cleaned).rstrip() + ("\n" if markdown.endswith("\n") else "")


def update_generated_status(markdown: str, *, latest: dict[str, Any], tasks: list[Task]) -> str:
    markdown = strip_unmanaged_generated_status_sections(markdown)
    counts = {
        "needed": sum(1 for task in tasks if task.status == "needed"),
        "in_progress": sum(1 for task in tasks if task.status == "in-progress"),
        "complete": sum(1 for task in tasks if task.status == "complete"),
        "blocked": sum(1 for task in tasks if task.status == "blocked"),
    }
    block = f"""
<!-- ppd-daemon-task-board:start -->
## Generated Status

Last updated: {utc_now()}

- Latest target: `{latest.get("target_task", "")}`
- Latest result: `{latest.get("result", "")}`
- Latest summary: {latest.get("summary", "")}
- Counts: `{json.dumps(counts, sort_keys=True)}`

<!-- ppd-daemon-task-board:end -->
"""
    if TASK_BOARD_STATUS_RE.search(markdown):
        return TASK_BOARD_STATUS_RE.sub("\n" + block.strip() + "\n", markdown).rstrip() + "\n"
    return markdown.rstrip() + "\n\n" + block


def should_sleep_between_watch_cycles(markdown: str, *, revisit_blocked: bool = False) -> bool:
    """Sleep only when there is no immediately selectable work on the board."""

    return select_task(parse_tasks(markdown), revisit_blocked=revisit_blocked) is None


def compact_message(value: Any, limit: int = 700) -> str:
    text = str(value or "")
    text = re.sub(
        r"<!doctype html[\s\S]*",
        "[html response omitted]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<(?:html|head|body|script|style|svg|path|div|meta|noscript)\b[\s\S]*",
        "[html response omitted]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"__cf_chl_[A-Za-z0-9_.=-]+", "__cf_chl_[omitted]", text)
    text = re.sub(r"c[A-Z][A-Za-z0-9_]*:\s*'[^']{80,}'", "cloudflare_token: '[omitted]'", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "..."
    return text


def is_retryable_failure(proposal: Proposal) -> bool:
    if proposal.failure_kind in {"llm", "parse", "empty_proposal"}:
        return True
    text = " ".join(proposal.errors).lower()
    return any(
        marker in text
        for marker in (
            "cloudflare",
            "403 forbidden",
            "plugins/featured",
            "timed out",
            "timeout",
            "could not generate",
            "provider",
        )
    )


def read_result_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        proposal = parsed.get("proposal")
        if isinstance(proposal, dict):
            rows.append(proposal)
    return rows


def read_result_and_diagnostic_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        proposal = parsed.get("proposal")
        diagnostic = parsed.get("diagnostic")
        if isinstance(proposal, dict):
            rows.append(proposal)
        elif isinstance(diagnostic, dict):
            row = dict(diagnostic)
            row["_diagnostic_stage"] = parsed.get("stage", "")
            rows.append(row)
    return rows


def recent_task_failures(config: Config, task_label: str, *, limit: int = 3) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for proposal in reversed(read_result_and_diagnostic_log(config.resolve(config.result_log))):
        if proposal.get("target_task") != task_label:
            continue
        if proposal.get("applied") and proposal.get("validation_passed") and not proposal.get("errors"):
            break
        failures.append(proposal)
        if len(failures) >= limit:
            break
    return failures


def should_use_compact_prompt(failures: list[dict[str, Any]], *, threshold: int = 2) -> bool:
    count = 0
    for failure in failures:
        if str(failure.get("failure_kind") or "") in {"parse", "llm"}:
            count += 1
    return count >= threshold


def effective_prompt_limit(config: Config, *, compact_prompt: bool) -> int:
    if compact_prompt:
        return min(config.max_prompt_chars, config.max_compact_prompt_chars)
    return config.max_prompt_chars


def task_failure_count(config: Config, task_label: str, *, kinds: Optional[set[str]] = None) -> int:
    count = 0
    for proposal in recent_task_failures(config, task_label, limit=100):
        kind = str(proposal.get("failure_kind") or "")
        if kinds is None or kind in kinds:
            count += 1
    return count


def format_failure_context(failures: list[dict[str, Any]]) -> str:
    if not failures:
        return "No recent failures for this task."
    parts: list[str] = []
    for index, failure in enumerate(failures, start=1):
        validation_bits: list[str] = []
        for result in failure.get("validation_results", []) or []:
            if not isinstance(result, dict) or int(result.get("returncode", 0)) == 0:
                continue
            command = " ".join(str(part) for part in result.get("command", []))
            validation_bits.append(
                f"{command}: {compact_message(str(result.get('stdout', '')) + ' ' + str(result.get('stderr', '')), limit=900)}"
            )
        parts.append(
            "\n".join(
                [
                    f"Failure {index}: kind={failure.get('failure_kind', '')}",
                    f"summary={compact_message(failure.get('summary', ''), limit=300)}",
                    f"errors={'; '.join(compact_message(error, limit=300) for error in failure.get('errors', [])[:3])}",
                    f"validation={'; '.join(validation_bits) if validation_bits else '<none>'}",
                ]
            )
        )
    if any(is_forbidden_absence_marker_validation_failure(failure) for failure in failures):
        parts.append(
            "Recovery guidance: a validator found a forbidden artifact marker inside the proposed fixture or test text. "
            "Return only one JSON object on the retry, and use a small file set that fixes the self-triggering field names. "
            "When representing absence, avoid keys or values containing banned substrings such as cookie, screenshot, "
            "auth-state, storage-state, trace.zip, or .har. Use neutral names like `runtimeArtifactsStored`, "
            "`visualArtifactsStored`, `authenticatedArtifactsStored`, or `forbiddenArtifactsAbsent` instead of "
            "`containsCookies`, `screenshotsStored`, or similar self-triggering absence fields."
        )
    return "\n\n".join(parts)


def is_forbidden_absence_marker_validation_failure(failure: dict[str, Any]) -> bool:
    """Detect validation failures caused by fixture/test text containing banned marker words."""

    if str(failure.get("failure_kind") or "") != "validation":
        return False
    text_parts: list[str] = []
    for error in failure.get("errors", []) or []:
        text_parts.append(str(error))
    for result in failure.get("validation_results", []) or []:
        if not isinstance(result, dict):
            continue
        text_parts.append(str(result.get("stdout", "")))
        text_parts.append(str(result.get("stderr", "")))
    text = "\n".join(text_parts).lower()
    if "unexpectedly found" not in text and "assertnotin" not in text:
        return False
    return any(marker in text for marker in FORBIDDEN_ABSENCE_MARKERS)


def extract_json(text: str) -> Optional[dict[str, Any]]:
    match = JSON_BLOCK_RE.search(text)
    candidates = [match.group(1)] if match else []
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def parse_proposal(text: str) -> Proposal:
    parsed = extract_json(text)
    if parsed is None:
        return Proposal(raw_response=text, errors=["LLM response did not contain a JSON object."], failure_kind="parse")
    files: list[dict[str, str]] = []
    raw_files = parsed.get("files", [])
    if isinstance(raw_files, list):
        for item in raw_files:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            content = item.get("content")
            if isinstance(path, str) and isinstance(content, str):
                files.append({"path": path, "content": content})
    commands: list[list[str]] = []
    raw_commands = parsed.get("validation_commands", [])
    if isinstance(raw_commands, list):
        for command in raw_commands:
            if isinstance(command, list) and all(isinstance(part, str) for part in command):
                commands.append(command)
    return Proposal(
        summary=str(parsed.get("summary", "")),
        impact=str(parsed.get("impact", "")),
        files=files,
        validation_commands=commands,
        raw_response=text,
    )


def normalized_relative_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        raise ValueError(f"absolute paths are not allowed: {path}")
    normalized = candidate.as_posix()
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        raise ValueError(f"path traversal is not allowed: {path}")
    return normalized


def validate_write_path(path: str) -> list[str]:
    errors: list[str] = []
    try:
        normalized = normalized_relative_path(path)
    except ValueError as exc:
        return [str(exc)]
    if any(normalized.startswith(prefix) for prefix in DISALLOWED_WRITE_PREFIXES):
        errors.append(f"disallowed PP&D daemon write target: {normalized}")
    if not any(normalized.startswith(prefix) or normalized == prefix.rstrip("/") for prefix in ALLOWED_WRITE_PREFIXES):
        errors.append(f"write target is outside PP&D allowlist: {normalized}")
    if is_private_write_path(normalized):
        errors.append(f"private/session artifacts may not be generated by daemon proposals: {normalized}")
    return errors


def is_private_write_path(normalized: str) -> bool:
    lowered = normalized.lower()
    if any(fragment in lowered for fragment in PRIVATE_WRITE_PATH_FRAGMENTS):
        return True
    tokens = [token for token in re.split(r"[/._-]+", lowered) if token]
    return any(token in PRIVATE_WRITE_PATH_TOKENS for token in tokens)


def run_command(command: tuple[str, ...], *, cwd: Path, timeout: int) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return CommandResult(command=command, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


def run_validation(config: Config) -> list[CommandResult]:
    return [
        run_command(command, cwd=config.repo_root, timeout=config.command_timeout_seconds)
        for command in config.validation_commands
    ]


def diff_for_file(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def apply_files_with_validation(proposal: Proposal, config: Config) -> Proposal:
    preflight_errors: list[str] = []
    for item in proposal.files:
        preflight_errors.extend(validate_write_path(item["path"]))
    if preflight_errors:
        proposal.errors.extend(preflight_errors)
        proposal.failure_kind = "preflight"
        persist_failed_work(proposal, config, patch="", reason="preflight")
        return proposal

    backups: dict[Path, Optional[str]] = {}
    changed: list[str] = []
    patch_parts: list[str] = []
    for item in proposal.files:
        rel = normalized_relative_path(item["path"])
        target = config.resolve(Path(rel))
        before = target.read_text(encoding="utf-8") if target.exists() else None
        after = item["content"]
        if before == after:
            continue
        backups[target] = before
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after, encoding="utf-8")
        changed.append(rel)
        patch_parts.append(diff_for_file(rel, before or "", after))

    proposal.changed_files = changed
    if not changed:
        proposal.errors.append("Proposal made no content changes.")
        proposal.failure_kind = "no_change"
        proposal.validation_results = run_validation(config)
        persist_failed_work(proposal, config, patch="", reason="no_change")
        return proposal

    patch_text = "".join(patch_parts)
    syntax_preflight = run_apply_flow_syntax_preflight(
        config.repo_root,
        changed,
        timeout=config.command_timeout_seconds,
    )
    proposal.validation_results = [
        CommandResult(
            command=result.command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        for result in syntax_preflight.validation_results
    ]
    if not syntax_preflight.ok:
        for path, before in backups.items():
            if before is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                path.write_text(before, encoding="utf-8")
        proposal.errors.extend(syntax_preflight.errors)
        proposal.failure_kind = syntax_preflight.failure_kind
        persist_failed_work(proposal, config, patch=patch_text, reason="syntax_preflight")
        return proposal

    proposal.validation_results = run_validation(config)
    if not all(result.ok for result in proposal.validation_results):
        for path, before in backups.items():
            if before is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                path.write_text(before, encoding="utf-8")
        proposal.errors.append("Validation failed; file edits were rolled back.")
        proposal.failure_kind = "validation"
        persist_failed_work(proposal, config, patch=patch_text, reason="validation")
        return proposal

    proposal.applied = True
    persist_accepted_work(proposal, config, patch=patch_text)
    return proposal


def persist_accepted_work(proposal: Proposal, config: Config, *, patch: str) -> None:
    config.resolve(config.accepted_dir).mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", proposal.summary.lower()).strip("-")[:80] or "accepted-work"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = config.resolve(config.accepted_dir) / f"{stamp}-{slug}"
    manifest = {
        "created_at": utc_now(),
        "target_task": proposal.target_task,
        "summary": proposal.summary,
        "impact": proposal.impact,
        "changed_files": proposal.changed_files,
        "validation_results": [result.compact() for result in proposal.validation_results],
    }
    base.with_suffix(".json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    base.with_suffix(".patch").write_text(patch, encoding="utf-8")
    base.with_suffix(".stat.txt").write_text("\n".join(proposal.changed_files) + "\n", encoding="utf-8")
    append_accepted_work_ledger(proposal, config, base=base)


def append_accepted_work_ledger(proposal: Proposal, config: Config, *, base: Path) -> None:
    entry = build_accepted_work_ledger_entry(
        repo_root=config.repo_root,
        target_task=proposal.target_task,
        summary=proposal.summary,
        impact=proposal.impact,
        changed_files=proposal.changed_files,
        artifacts=AcceptedWorkArtifacts(
            manifest=base.with_suffix(".json"),
            patch=base.with_suffix(".patch"),
            stat=base.with_suffix(".stat.txt"),
        ),
        validation_results=[result.compact() for result in proposal.validation_results],
    )
    append_accepted_work_jsonl(config.resolve(config.accepted_dir), entry)


def persist_failed_work(proposal: Proposal, config: Config, *, patch: str, reason: str) -> None:
    config.resolve(config.failed_dir).mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", (proposal.summary or reason).lower()).strip("-")[:80] or "failed-work"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = config.resolve(config.failed_dir) / f"{stamp}-{reason}-{slug}"
    manifest = {
        "created_at": utc_now(),
        "reason": reason,
        "target_task": proposal.target_task,
        "summary": proposal.summary,
        "impact": proposal.impact,
        "files": [item.get("path", "") for item in proposal.files],
        "changed_files": proposal.changed_files,
        "errors": [compact_message(error) for error in proposal.errors],
        "validation_results": [result.compact() for result in proposal.validation_results],
    }
    base.with_suffix(".json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    base.with_suffix(".patch").write_text(patch, encoding="utf-8")
    base.with_suffix(".stat.txt").write_text("\n".join(proposal.changed_files) + "\n", encoding="utf-8")


def build_prompt(config: Config, selected: Task) -> str:
    failures = recent_task_failures(config, selected.label)
    compact_prompt = should_use_compact_prompt(failures)
    plan = read_text(config.resolve(config.plan_doc), limit=900 if compact_prompt else 22000)
    board = read_text(config.resolve(config.task_board), limit=1800 if compact_prompt else 14000)
    readme = (
        read_text(config.resolve(config.readme), limit=1200 if compact_prompt else 8000)
        if config.resolve(config.readme).exists()
        else ""
    )
    failure_context = format_failure_context(failures)
    context_files: list[str] = []
    if compact_prompt:
        context_files.append(
            "Compact retry mode: omitted broad workspace file contents after repeated LLM parse/runtime failures. "
            "Return a minimal JSON proposal with one fixture and one focused test when possible."
        )
    else:
        for path in sorted((config.repo_root / "ppd").glob("**/*")):
            if not path.is_file():
                continue
            rel = path.relative_to(config.repo_root).as_posix()
            if rel.startswith("ppd/data/") or rel.startswith("ppd/daemon/accepted-work/") or rel.startswith("ppd/daemon/failed-patches/"):
                continue
            if rel.endswith((".py", ".md", ".json", ".ts", ".tsx", ".js", ".mjs")):
                context_files.append(f"--- {rel} ---\n{read_text(path, limit=8000)}")
            if len("\n".join(context_files)) > 18000:
                break

    prompt = f"""
You are improving the isolated PP&D implementation workspace in a repository.

Current task:
{selected.label}

Prompt mode:
{"Compact retry mode: repeated LLM parse/runtime failures were recorded for this task. Return the smallest useful JSON patch and avoid broad context." if compact_prompt else "Full context mode."}

Hard constraints:
- Return ONLY one JSON object; no markdown fences and no prose outside JSON.
- Use complete file replacements in a `files` array. Do not return shell commands.
- Edit only files under `ppd/`, or `docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md` if the task specifically requires plan updates.
- Do not edit `src/lib/logic/`, `public/corpus/portland-or/current/`, `ipfs_datasets_py/.daemon/`, or the TypeScript logic daemon ledgers.
- Do not create private DevHub session files, auth state, traces, raw crawl output, or downloaded documents.
- Keep the change narrow and directly useful for the selected task.
- Prefer deterministic fixtures and validation before any live crawl or authenticated automation.
- Before returning JSON, ensure every Python file is syntactically valid Python and every TypeScript file is syntactically valid TypeScript. Do not mix TypeScript syntax into Python or Python typing/control-flow syntax into TypeScript.
- Prefer adding narrow new modules and tests over rewriting stable shared contracts such as `ppd/contracts/documents.py`, unless the selected task directly requires a shared contract extension.
- If recent failure context includes `SyntaxError`, `py_compile`, `TS1005`, `TS1109`, or `TS1128`, return a smaller proposal with only the files needed for a syntax-valid implementation or repair.
- Put committed PP&D fixtures under `ppd/tests/fixtures/...`. Tests in `ppd/tests/` should derive fixture paths from their own file location, for example `Path(__file__).parent / "fixtures" / ...`, so they do not accidentally point at repository-root `tests/fixtures`.
- Do not mark task-board checkboxes complete in the same proposal unless the implementation, fixtures, and validation code for the selected task are all included. The daemon will mark the selected task complete after validation passes.
- Do not automate CAPTCHA, MFA, account creation, payment, submission, certification, cancellation, or upload actions.
- If compact retry mode is active, do not inspect or request additional context. Return the smallest useful JSON patch for the current task.

JSON schema:
{{
  "summary": "short summary",
  "impact": "why this advances the PP&D plan",
  "files": [
    {{"path": "ppd/...", "content": "complete replacement file content"}}
  ],
  "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
}}

Recent failure context for this task:
{failure_context}

PP&D plan:
{plan}

PP&D task board:
{board}

PP&D workspace context:
{readme}

Current files:
{chr(10).join(context_files)}
"""
    prompt_limit = effective_prompt_limit(config, compact_prompt=compact_prompt)
    if len(prompt) > prompt_limit:
        prompt = prompt[:prompt_limit] + "\n\n[truncated]\n"
    return prompt


def call_llm(prompt: str, config: Config) -> str:
    backend = os.environ.get("PPD_LLM_BACKEND", "llm_router")
    if backend != "llm_router":
        raise RuntimeError(f"Unsupported PP&D LLM backend {backend!r}; expected 'llm_router'.")
    if len(prompt) > config.max_prompt_chars + len("\n\n[truncated]\n"):
        raise RuntimeError(
            f"LLM prompt exceeds configured budget before llm_router child launch: {len(prompt)} > {config.max_prompt_chars}"
        )
    prompt_file: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            prefix="ppd-llm-prompt-",
            suffix=".txt",
        ) as handle:
            handle.write(prompt)
            prompt_file = Path(handle.name)
        env = os.environ.copy()
        env.update(
            {
                "PPD_LLM_PROMPT_FILE": str(prompt_file),
                "PPD_LLM_MODEL_NAME": config.model_name,
                "PPD_LLM_PROVIDER": config.provider or "",
                "PPD_LLM_ALLOW_LOCAL_FALLBACK": "1" if config.allow_local_fallback else "0",
                "PPD_LLM_TIMEOUT": str(config.llm_timeout_seconds),
            }
        )
        child_code = r"""
import os
import pathlib
import sys

from ipfs_datasets_py import llm_router

prompt = pathlib.Path(os.environ["PPD_LLM_PROMPT_FILE"]).read_text(encoding="utf-8")
provider = os.environ.get("PPD_LLM_PROVIDER") or None
text = llm_router.generate_text(
    prompt,
    model_name=os.environ["PPD_LLM_MODEL_NAME"],
    provider=provider,
    allow_local_fallback=os.environ.get("PPD_LLM_ALLOW_LOCAL_FALLBACK") == "1",
    timeout=int(os.environ["PPD_LLM_TIMEOUT"]),
    max_new_tokens=4096,
    temperature=0.1,
)
sys.stdout.write("" if text is None else str(text))
"""
        completed = subprocess.run(
            ["python3", "-c", child_code],
            cwd=str(config.repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=config.llm_timeout_seconds + 30,
            check=False,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"llm_router child timed out after {config.llm_timeout_seconds + 30} seconds") from exc
    finally:
        if prompt_file is not None:
            try:
                prompt_file.unlink()
            except FileNotFoundError:
                pass
    if completed.returncode != 0:
        details = compact_message((completed.stdout or "") + " " + (completed.stderr or ""), limit=1200)
        raise RuntimeError(f"llm_router child exited with code {completed.returncode}: {details}")
    return completed.stdout


class Daemon:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._heartbeat_stop = threading.Event()
        self._active_state = "initializing"
        self._active_state_started_at = utc_now()
        self._active_target_task = ""

    def write_status(self, state: str, **extra: Any) -> None:
        if state != "heartbeat":
            target_task = str(extra.get("target_task") or self._active_target_task)
            if state != self._active_state or target_task != self._active_target_task:
                self._active_state_started_at = utc_now()
            self._active_state = state
            self._active_target_task = target_task
        payload = {
            "updated_at": utc_now(),
            "pid": os.getpid(),
            "state": state,
            "active_state": self._active_state,
            "active_state_started_at": self._active_state_started_at,
            "active_target_task": self._active_target_task,
            **extra,
        }
        atomic_write_json(self.config.resolve(self.config.status_file), payload)

    def heartbeat(self) -> None:
        while not self._heartbeat_stop.wait(self.config.heartbeat_seconds):
            self.write_status("heartbeat", active_state=self._active_state)

    def run_cycle(self) -> Proposal:
        board_path = self.config.resolve(self.config.task_board)
        board = read_text(board_path)
        tasks = parse_tasks(board)
        selected = select_task(tasks, revisit_blocked=self.config.revisit_blocked)
        if selected is None:
            proposal = Proposal(summary="No eligible PP&D tasks remain.", failure_kind="no_eligible_tasks")
            proposal.dry_run = not self.config.apply
            self.write_status("no_eligible_tasks")
            self.write_progress([proposal])
            self.write_cycle_diagnostic(proposal, stage="no_eligible_tasks")
            return proposal

        self.write_status("selected_task", target_task=selected.label)
        if selected.status == "needed" and self.config.apply:
            board = replace_task_mark(board, selected, "~")
            board_path.write_text(board, encoding="utf-8")

        self.write_status("calling_llm", target_task=selected.label)
        try:
            raw = call_llm(build_prompt(self.config, selected), self.config)
            proposal = parse_proposal(raw)
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            proposal = Proposal(summary="LLM proposal failed.", errors=[compact_message(exc)], failure_kind="llm")
        proposal.target_task = selected.label
        proposal.dry_run = not self.config.apply
        if proposal.failure_kind in {"parse", "llm"} or not proposal.files:
            self.write_progress([proposal])
            self.write_cycle_diagnostic(proposal, stage="before_validation")

        if self.config.apply and proposal.files:
            self.write_status("applying_files", target_task=selected.label)
            proposal = apply_files_with_validation(proposal, self.config)
        else:
            proposal.validation_results = run_validation(self.config)

        board = read_text(board_path)
        if self.config.apply:
            if proposal.valid:
                board = replace_task_mark(board, selected, "x")
            elif selected.status in {"needed", "in-progress"} and not is_retryable_failure(proposal):
                prior_failures = task_failure_count(
                    self.config,
                    selected.label,
                    kinds={"validation", "preflight", "no_change", "syntax_preflight"},
                )
                mark = "!" if prior_failures + 1 >= self.config.max_task_failures_before_block else " "
                board = replace_task_mark(board, selected, mark)
            elif selected.status in {"needed", "in-progress"}:
                board = replace_task_mark(board, selected, " ")
        tasks_after = parse_tasks(board)
        board = update_generated_status(
            board,
            latest={
                "target_task": selected.label,
                "result": "accepted" if proposal.valid else proposal.failure_kind or "not_applied",
                "summary": proposal.summary,
            },
            tasks=tasks_after,
        )
        board_path.write_text(board, encoding="utf-8")
        self.write_progress([proposal])
        append_jsonl(self.config.resolve(self.config.result_log), {"created_at": utc_now(), "proposal": proposal.to_dict()})
        self.write_status("cycle_completed", valid=proposal.valid, artifact=proposal.to_dict())
        return proposal

    def write_cycle_diagnostic(self, proposal: Proposal, *, stage: str) -> None:
        append_jsonl(
            self.config.resolve(self.config.result_log),
            {
                "created_at": utc_now(),
                "stage": stage,
                "diagnostic": proposal.to_dict(),
            },
        )

    def write_progress(self, proposals: list[Proposal]) -> None:
        board = read_text(self.config.resolve(self.config.task_board))
        tasks = parse_tasks(board)
        payload = {
            "updated_at": utc_now(),
            "task_counts": {
                "needed": sum(1 for task in tasks if task.status == "needed"),
                "in_progress": sum(1 for task in tasks if task.status == "in-progress"),
                "complete": sum(1 for task in tasks if task.status == "complete"),
                "blocked": sum(1 for task in tasks if task.status == "blocked"),
            },
            "latest": proposals[-1].to_dict() if proposals else {},
        }
        atomic_write_json(self.config.resolve(self.config.progress_file), payload)

    def run(self) -> list[Proposal]:
        thread = threading.Thread(target=self.heartbeat, daemon=True)
        thread.start()
        proposals: list[Proposal] = []
        try:
            count = 0
            while True:
                count += 1
                proposal = self.run_cycle()
                proposals.append(proposal)
                if not self.config.watch:
                    break
                if proposal.failure_kind == "no_eligible_tasks":
                    break
                if self.config.iterations > 0 and count >= self.config.iterations:
                    break
                if self.config.interval_seconds > 0:
                    board_now = read_text(self.config.resolve(self.config.task_board))
                    if not should_sleep_between_watch_cycles(
                        board_now,
                        revisit_blocked=self.config.revisit_blocked,
                    ):
                        continue
                    self.write_status("sleeping", seconds=self.config.interval_seconds)
                    time.sleep(self.config.interval_seconds)
        finally:
            self._heartbeat_stop.set()
            thread.join(timeout=1)
        return proposals


def self_test(repo_root: Path) -> int:
    required = [
        repo_root / "ppd/README.md",
        repo_root / "ppd/.gitignore",
        repo_root / "ppd/daemon/task-board.md",
        repo_root / "docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md",
    ]
    missing = [path.as_posix() for path in required if not path.exists()]
    errors: list[str] = []
    if missing:
        errors.append(f"missing required files: {missing}")
    board = (repo_root / "ppd/daemon/task-board.md").read_text(encoding="utf-8") if (repo_root / "ppd/daemon/task-board.md").exists() else ""
    if not parse_tasks(board):
        errors.append("task board has no checkbox tasks")
    gitignore = (repo_root / "ppd/.gitignore").read_text(encoding="utf-8") if (repo_root / "ppd/.gitignore").exists() else ""
    for needle in ("data/private/", "data/raw/", "daemon/failed-patches/"):
        if needle not in gitignore:
            errors.append(f"ppd/.gitignore missing {needle}")
    for prefix in DISALLOWED_WRITE_PREFIXES:
        if not validate_write_path(prefix + "bad.ts"):
            errors.append(f"disallowed prefix unexpectedly passed preflight: {prefix}")
    compacted = CommandResult(
        command=("example",),
        returncode=1,
        stdout="<html><body><script>cloudflare challenge</script></body></html>",
        stderr="token __cf_chl_tk=secret",
    ).compact()
    if "cloudflare challenge" in compacted["stdout"] or "__cf_chl_tk=secret" in compacted["stderr"]:
        errors.append("runtime log compaction failed to redact noisy provider HTML")
    errors.extend(validate_seed_and_allowlist(repo_root))
    errors.extend(validate_python_sources(repo_root))
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "task_count": len(parse_tasks(board))}, indent=2))
    return 0


def load_json_file(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.relative_to(path.parents[2])} is invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return parsed


def validate_seed_and_allowlist(repo_root: Path) -> list[str]:
    errors: list[str] = []
    seed_path = repo_root / "ppd/crawler/seed_manifest.json"
    allowlist_path = repo_root / "ppd/crawler/allowlist.json"
    try:
        seed_manifest = load_json_file(seed_path)
        allowlist = load_json_file(allowlist_path)
    except ValueError as exc:
        return [str(exc)]
    if seed_manifest is None and allowlist is None:
        return errors
    if seed_manifest is None or allowlist is None:
        return ["seed_manifest.json and allowlist.json must be added together"]

    allowed_hosts = allowlist.get("allowed_hosts")
    if not isinstance(allowed_hosts, list) or not allowed_hosts:
        errors.append("allowlist.json must include non-empty allowed_hosts")
        allowed_hosts = []
    host_policies: dict[str, dict[str, Any]] = {}
    for entry in allowed_hosts:
        if not isinstance(entry, dict):
            errors.append("allowlist allowed_hosts entries must be objects")
            continue
        host = entry.get("host")
        if not isinstance(host, str) or not host:
            errors.append("allowlist host entry missing host")
            continue
        host_policies[host] = entry
        if entry.get("scheme") != "https":
            errors.append(f"allowlist host {host} must require https")
        prefixes = entry.get("allowed_path_prefixes")
        if not isinstance(prefixes, list) or not all(isinstance(prefix, str) and prefix.startswith("/") for prefix in prefixes):
            errors.append(f"allowlist host {host} must define allowed_path_prefixes")

    seeds = seed_manifest.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        errors.append("seed_manifest.json must include non-empty seeds")
        seeds = []
    seen_ids: set[str] = set()
    for seed in seeds:
        if not isinstance(seed, dict):
            errors.append("seed entries must be objects")
            continue
        seed_id = seed.get("id")
        url = seed.get("url")
        if not isinstance(seed_id, str) or not seed_id:
            errors.append("seed entry missing id")
        elif seed_id in seen_ids:
            errors.append(f"duplicate seed id: {seed_id}")
        else:
            seen_ids.add(seed_id)
        if not isinstance(url, str) or not url:
            errors.append(f"seed {seed_id or '<unknown>'} missing url")
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https":
            errors.append(f"seed {seed_id} must use https: {url}")
        policy = host_policies.get(parsed.netloc)
        if policy is None:
            errors.append(f"seed {seed_id} host is not allowlisted: {parsed.netloc}")
            continue
        prefixes = policy.get("allowed_path_prefixes", [])
        parsed_path = parsed.path or "/"
        if isinstance(prefixes, list) and not any(parsed_path.startswith(str(prefix)) for prefix in prefixes):
            errors.append(f"seed {seed_id} path is outside host allowlist: {parsed_path}")
        for fragment in policy.get("disallowed_path_fragments", []) or []:
            if isinstance(fragment, str) and fragment.lower() in url.lower():
                errors.append(f"seed {seed_id} includes disallowed path fragment {fragment!r}")
    return errors


def validate_python_sources(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((repo_root / "ppd").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(repo_root).as_posix()
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{rel} failed py_compile: {compact_message(exc.msg, limit=500)}")
    return errors


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the isolated PP&D autonomous daemon.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--apply", action="store_true", help="Apply accepted file replacements after validation")
    parser.add_argument("--watch", action="store_true", help="Run repeated cycles")
    parser.add_argument("--iterations", type=int, default=1, help="Number of cycles; with --watch, 0 means unbounded")
    parser.add_argument("--interval", type=float, default=0.0, help="Seconds between watch cycles")
    parser.add_argument("--llm-timeout", type=int, default=300, help="Seconds to allow for one LLM proposal")
    parser.add_argument("--model", default="gpt-5.5", help="llm_router model")
    parser.add_argument("--provider", default=None, help="llm_router provider")
    parser.add_argument("--allow-local-fallback", action="store_true", help="Allow local fallback providers")
    parser.add_argument("--revisit-blocked", action="store_true", help="Revisit blocked tasks after needed tasks are exhausted")
    parser.add_argument("--max-task-failures-before-block", type=int, default=3, help="Validation/preflight failures before marking a task blocked")
    parser.add_argument("--self-test", action="store_true", help="Run daemon self-test and exit")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.self_test:
        return self_test(repo_root)
    config = Config(
        repo_root=repo_root,
        apply=bool(args.apply),
        watch=bool(args.watch),
        iterations=int(args.iterations),
        interval_seconds=float(args.interval),
        llm_timeout_seconds=int(args.llm_timeout),
        model_name=str(args.model),
        provider=args.provider,
        allow_local_fallback=bool(args.allow_local_fallback),
        revisit_blocked=bool(args.revisit_blocked),
        max_task_failures_before_block=max(1, int(args.max_task_failures_before_block)),
    )
    proposals = Daemon(config).run()
    print(json.dumps([proposal.to_dict() for proposal in proposals], indent=2))
    return 0 if proposals and proposals[-1].valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
