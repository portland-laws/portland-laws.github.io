#!/usr/bin/env python3
"""Agentic supervisor for the isolated PP&D daemon.

The worker daemon advances PP&D implementation tasks. The supervisor watches the
worker's health and can ask Codex for a narrow daemon/supervisor patch when the
worker is stuck, repeatedly blocked, or no longer making meaningful progress.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ppd.daemon.ppd_daemon import (  # noqa: E402
    Config as DaemonConfig,
    Proposal,
    apply_files_with_validation,
    atomic_write_json,
    compact_message,
    is_private_write_path,
    parse_proposal,
    parse_tasks,
    read_result_log,
    read_text,
    run_validation,
    utc_now,
)

SYNTAX_OR_COMPILE_FAILURE_MARKERS = (
    "syntaxerror",
    "failed py_compile",
    "py_compile",
    "invalid syntax",
    "unterminated string literal",
    "unmatched ')'",
    "unexpected indent",
    "expected an indented block",
    "ts1005",
    "ts1109",
    "ts1128",
    "declaration or statement expected",
    "expression expected",
)

MALFORMED_PYTHON_PROPOSAL_MARKERS = (
    "confidence 1",
    "confidence 1.0",
    "return 0.0 list[str]",
)

TASK_TITLE_RE = re.compile(r"Task checkbox-\d+:\s*")


@dataclass(frozen=True)
class SupervisorConfig:
    repo_root: Path
    pid_file: Path = Path("ppd/daemon/ppd-daemon.pid")
    status_file: Path = Path("ppd/daemon/status.json")
    progress_file: Path = Path("ppd/daemon/progress.json")
    result_log: Path = Path("ppd/daemon/ppd-daemon.jsonl")
    task_board: Path = Path("ppd/daemon/task-board.md")
    plan_doc: Path = Path("docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md")
    supervisor_status_file: Path = Path("ppd/daemon/supervisor-status.json")
    supervisor_log: Path = Path("ppd/daemon/supervisor-actions.jsonl")
    control_script: Path = Path("ppd/daemon/control.sh")
    stall_seconds: int = 900
    blocked_task_threshold: int = 1
    repeated_failure_threshold: int = 3
    active_state_timeout_seconds: int = 420
    max_prompt_chars: int = 50000
    llm_timeout_seconds: int = 300
    model_name: str = "gpt-5.5"
    provider: Optional[str] = None
    apply: bool = False
    self_heal: bool = False
    restart_daemon: bool = False

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.repo_root / path


@dataclass(frozen=True)
class SupervisorDecision:
    action: str
    reason: str
    severity: str
    should_invoke_codex: bool = False
    should_restart_daemon: bool = False


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_invalid_json": True}
    return parsed if isinstance(parsed, dict) else {}


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_seconds(value: Any, *, now: Optional[datetime] = None) -> Optional[float]:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    current = now or datetime.now(timezone.utc)
    return max(0.0, (current - parsed).total_seconds())


def read_pid(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def process_running(pid: Optional[int]) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def latest_repeated_failure_count(rows: list[dict[str, Any]], *, completed_task_labels: Optional[set[str]] = None) -> int:
    completed = completed_task_labels or set()
    count = 0
    for proposal in reversed(rows):
        if str(proposal.get("target_task") or "") in completed:
            continue
        if proposal.get("applied") and proposal.get("validation_passed") and not proposal.get("errors"):
            break
        count += 1
    return count


def proposal_validation_text(proposal: dict[str, Any]) -> str:
    parts: list[str] = []
    for error in proposal.get("errors", []) or []:
        parts.append(str(error))
    for result in proposal.get("validation_results", []) or []:
        if not isinstance(result, dict):
            continue
        parts.append(" ".join(str(part) for part in result.get("command", []) or []))
        parts.append(str(result.get("stdout", "")))
        parts.append(str(result.get("stderr", "")))
    return "\n".join(parts).lower()


def is_syntax_or_compile_failure(proposal: dict[str, Any]) -> bool:
    if str(proposal.get("failure_kind") or "") not in {"validation", "syntax_preflight"}:
        return False
    text = proposal_validation_text(proposal)
    return any(marker in text for marker in SYNTAX_OR_COMPILE_FAILURE_MARKERS)


def has_malformed_python_proposal_syntax(proposal: dict[str, Any]) -> bool:
    text = proposal_validation_text(proposal)
    return any(marker in text for marker in MALFORMED_PYTHON_PROPOSAL_MARKERS)


def recent_syntax_failure_count(
    rows: list[dict[str, Any]], *, limit: int = 6, completed_task_labels: Optional[set[str]] = None
) -> int:
    completed = completed_task_labels or set()
    count = 0
    inspected = 0
    for proposal in reversed(rows):
        if str(proposal.get("target_task") or "") in completed:
            continue
        if proposal.get("applied") and proposal.get("validation_passed") and not proposal.get("errors"):
            break
        inspected += 1
        if not is_syntax_or_compile_failure(proposal):
            break
        count += 1
        if inspected >= limit:
            break
    return count


def repeated_malformed_syntax_count(
    rows: list[dict[str, Any]], *, completed_task_labels: Optional[set[str]] = None
) -> int:
    completed = completed_task_labels or set()
    latest_task = ""
    count = 0
    for proposal in reversed(rows):
        target = str(proposal.get("target_task") or "")
        if target in completed:
            continue
        if proposal.get("applied") and proposal.get("validation_passed") and not proposal.get("errors"):
            break
        if not latest_task:
            latest_task = target
        if target != latest_task:
            break
        if not is_syntax_or_compile_failure(proposal):
            break
        if has_malformed_python_proposal_syntax(proposal):
            count += 1
    return count


def is_private_session_preflight_false_positive(proposal: dict[str, Any]) -> bool:
    if str(proposal.get("failure_kind") or "") != "preflight":
        return False
    errors = [str(error).lower() for error in proposal.get("errors", []) or []]
    if not any("private/session artifacts" in error for error in errors):
        return False
    files = [str(path) for path in proposal.get("files", []) or [] if isinstance(path, str)]
    return any("session" in path.lower() and not is_private_write_path(path) for path in files)


def should_blocked_tasks_interrupt(blocked_count: int, selectable_count: int, threshold: int) -> bool:
    return blocked_count >= threshold and selectable_count == 0


def title_from_task_label(label: str) -> str:
    """Return the innermost checkbox task title from a daemon target label."""

    text = str(label or "").strip()
    while True:
        replaced = TASK_TITLE_RE.sub("", text, count=1).strip()
        if replaced == text:
            return text
        text = replaced


def builtin_repair_task_board(markdown: str, rows: list[dict[str, Any]]) -> tuple[str, tuple[str, ...]]:
    """Park a repeated syntax-loop task so the daemon can advance autonomously."""

    syntax_failures = []
    for row in reversed(rows):
        if row.get("applied") and row.get("validation_passed") and not row.get("errors"):
            break
        if not is_syntax_or_compile_failure(row):
            break
        syntax_failures.append(row)
    if len(syntax_failures) < 2:
        return markdown, ()

    target_title = title_from_task_label(str(syntax_failures[0].get("target_task") or ""))
    if not target_title:
        return markdown, ()

    changed = False
    repaired_lines: list[str] = []
    for line in markdown.splitlines(keepends=True):
        match = None
        stripped = line.rstrip("\n")
        if target_title in stripped:
            match = stripped
        if match and "- [~]" in stripped:
            line = line.replace("- [~]", "- [!]", 1)
            changed = True
        elif match and "- [ ]" in stripped:
            line = line.replace("- [ ]", "- [!]", 1)
            changed = True
        repaired_lines.append(line)

    if not changed:
        return markdown, ()

    note = (
        "\n"
        "## Built-In Supervisor Repair Notes\n\n"
        f"- Parked repeated syntax-preflight loop for `{target_title}` so the daemon can continue with independent selectable work. "
        "The task should be resumed only after a narrow syntax-valid fixture/test repair is available.\n"
    )
    repaired = "".join(repaired_lines).rstrip() + note
    return repaired + "\n", (target_title,)


def diagnose(config: SupervisorConfig, *, now: Optional[datetime] = None) -> SupervisorDecision:
    pid = read_pid(config.resolve(config.pid_file))
    running = process_running(pid)
    status = load_json(config.resolve(config.status_file))
    progress = load_json(config.resolve(config.progress_file))
    board = read_text(config.resolve(config.task_board)) if config.resolve(config.task_board).exists() else ""
    tasks = parse_tasks(board)
    completed_task_labels = {task.label for task in tasks if task.status == "complete"}
    rows = read_result_log(config.resolve(config.result_log))
    latest = progress.get("latest") if isinstance(progress.get("latest"), dict) else {}

    if tasks and all(task.status == "complete" for task in tasks):
        return SupervisorDecision(
            action="plan_next_tasks",
            reason="all PP&D daemon tasks are complete; review the original PP&D goal and add the next task-board tranche",
            severity="info",
            should_invoke_codex=True,
        )

    if latest.get("failure_kind") == "no_eligible_tasks" and tasks and all(task.status == "complete" for task in tasks):
        return SupervisorDecision(
            action="plan_next_tasks",
            reason="daemon has no eligible tasks; review completed work against the PP&D plan and add the next backlog tranche",
            severity="info",
            should_invoke_codex=True,
        )

    if is_private_session_preflight_false_positive(latest):
        return SupervisorDecision(
            action="repair_daemon_programming",
            reason=(
                "daemon private/session write-path preflight rejected an allowed non-private path; "
                "patch the path classifier before retrying the worker"
            ),
            severity="warning",
            should_invoke_codex=True,
            should_restart_daemon=True,
        )

    if not running:
        return SupervisorDecision(
            action="restart_daemon",
            reason="daemon process is not running",
            severity="warning",
            should_restart_daemon=True,
        )

    heartbeat_age = age_seconds(status.get("updated_at"), now=now)
    active_state = str(status.get("active_state") or status.get("state") or "")
    active_state_age = age_seconds(status.get("active_state_started_at"), now=now)
    if heartbeat_age is None:
        return SupervisorDecision(
            action="invoke_codex",
            reason="daemon status timestamp is missing or invalid",
            severity="warning",
            should_invoke_codex=True,
        )
    if heartbeat_age > config.stall_seconds:
        return SupervisorDecision(
            action="invoke_codex",
            reason=f"daemon heartbeat is stale for {int(heartbeat_age)} seconds in state {active_state or ''}",
            severity="critical",
            should_invoke_codex=True,
            should_restart_daemon=True,
        )
    if active_state in {"calling_llm", "applying_files"} and active_state_age is not None:
        if active_state_age > config.active_state_timeout_seconds:
            target = status.get("active_target_task") or status.get("target_task") or ""
            return SupervisorDecision(
                action="invoke_codex",
                reason=(
                    f"daemon has been in {active_state} for {int(active_state_age)} seconds "
                    f"on {target}; repair or restart the worker so it can keep making progress"
                ),
                severity="warning",
                should_invoke_codex=True,
                should_restart_daemon=True,
            )

    malformed_count = repeated_malformed_syntax_count(rows, completed_task_labels=completed_task_labels)
    if malformed_count >= 2:
        return SupervisorDecision(
            action="repair_daemon_programming",
            reason=(
                f"{malformed_count} recent validation rollbacks for the same target contained malformed Python "
                "comparison or annotation-like syntax; stop retrying that target until a syntax-first guard passes"
            ),
            severity="warning",
            should_invoke_codex=True,
            should_restart_daemon=True,
        )

    blocked = [task for task in tasks if task.status == "blocked"]
    selectable = [task for task in tasks if task.status in {"needed", "in-progress"}]
    if should_blocked_tasks_interrupt(len(blocked), len(selectable), config.blocked_task_threshold):
        return SupervisorDecision(
            action="invoke_codex",
            reason=f"{len(blocked)} task(s) are blocked and no independent selectable task remains: "
            + "; ".join(task.label for task in blocked[:3]),
            severity="warning",
            should_invoke_codex=True,
        )

    syntax_failures = recent_syntax_failure_count(rows, completed_task_labels=completed_task_labels)
    if syntax_failures >= 2:
        return SupervisorDecision(
            action="repair_daemon_programming",
            reason=(
                f"{syntax_failures} recent validation rollbacks were syntax or compile failures; "
                "patch daemon prompt, preflight, or repair guidance before more worker attempts"
            ),
            severity="warning",
            should_invoke_codex=True,
            should_restart_daemon=True,
        )

    repeated_failures = latest_repeated_failure_count(rows, completed_task_labels=completed_task_labels)
    if repeated_failures >= config.repeated_failure_threshold:
        return SupervisorDecision(
            action="invoke_codex",
            reason=f"{repeated_failures} consecutive daemon rounds failed without an accepted patch",
            severity="warning",
            should_invoke_codex=True,
        )

    if active_state == "sleeping" and latest and not latest.get("applied") and not latest.get("validation_passed"):
        return SupervisorDecision(
            action="invoke_codex",
            reason="daemon is sleeping after a non-accepted latest proposal",
            severity="info",
            should_invoke_codex=True,
        )

    return SupervisorDecision(action="observe", reason="daemon appears healthy", severity="info")


def build_supervisor_prompt(config: SupervisorConfig, decision: SupervisorDecision) -> str:
    files = {
        "ppd/daemon/control.sh": read_text(config.resolve(Path("ppd/daemon/control.sh")), limit=8000),
        "ppd/daemon/ppd_daemon.py": read_text(config.resolve(Path("ppd/daemon/ppd_daemon.py")), limit=22000),
        "ppd/daemon/ppd_supervisor.py": read_text(config.resolve(Path("ppd/daemon/ppd_supervisor.py")), limit=16000),
        "ppd/daemon/task-board.md": read_text(config.resolve(Path("ppd/daemon/task-board.md")), limit=8000),
        "ppd/daemon/OPERATIONS.md": read_text(config.resolve(Path("ppd/daemon/OPERATIONS.md")), limit=8000)
        if config.resolve(Path("ppd/daemon/OPERATIONS.md")).exists()
        else "",
    }
    plan = read_text(config.resolve(config.plan_doc), limit=18000) if config.resolve(config.plan_doc).exists() else ""
    status = load_json(config.resolve(config.status_file))
    progress = load_json(config.resolve(config.progress_file))
    recent_results = read_result_log(config.resolve(config.result_log))[-8:]
    failed_manifests: list[str] = []
    failed_dir = config.resolve(Path("ppd/daemon/failed-patches"))
    if failed_dir.exists():
        for path in sorted(failed_dir.glob("*.json"))[-5:]:
            failed_manifests.append(f"--- {path.relative_to(config.repo_root).as_posix()} ---\n{read_text(path, limit=2500)}")

    if decision.action == "plan_next_tasks":
        goal = "Review completed work against the original PP&D goal and update `ppd/daemon/task-board.md` with the next narrow, ordered tranche of unfinished tasks. Do not implement those tasks in this proposal; create the backlog so the worker daemon can continue."
    elif decision.action == "repair_daemon_programming":
        goal = "Patch the PP&D daemon or supervisor programming so repeated syntax/compile validation failures are detected earlier and the worker is prompted toward smaller, syntactically valid proposals."
    else:
        goal = "Improve the PP&D daemon or supervisor programming so the worker can resume meaningful autonomous progress."

    prompt = f"""
You are Codex acting as a supervisor repair agent for the isolated PP&D daemon.

Supervisor diagnosis:
- action: {decision.action}
- severity: {decision.severity}
- reason: {decision.reason}

Goal:
{goal}

Hard constraints:
- Return ONLY one JSON object; no markdown fences and no prose outside JSON.
- Use complete file replacements in a `files` array. Do not return shell commands.
- For `plan_next_tasks`, edit only `ppd/daemon/task-board.md` and optionally `ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md`.
- For repair actions, edit only `ppd/daemon/`, `ppd/tests/`, `ppd/.gitignore`, or PP&D daemon operations docs.
- Do not edit application/domain artifacts just to mark progress. Fix supervision, validation, task selection, retry, recovery, or diagnostics.
- For `repair_daemon_programming`, focus on daemon prompt/preflight/retry logic and supervisor diagnostics; do not implement the selected PP&D domain task.
- When recent failures include Python `SyntaxError`, `py_compile`, or TypeScript `TS1005`/`TS1109`/`TS1128`, prefer smaller file sets and explicit syntactic-validity guardrails over broader contract rewrites.
- When planning next tasks, preserve completed tasks, append new `[ ]` tasks, keep each task narrow enough for one daemon cycle, and include fixture-first/validation-first work before live or authenticated automation.
- Do not create private DevHub session files, auth state, traces, raw crawl output, or downloaded documents.
- Do not automate CAPTCHA, MFA, account creation, payment, submission, certification, cancellation, official upload, or inspection scheduling.
- Keep the change narrow and deterministic.

JSON schema:
{{
  "summary": "short summary",
  "impact": "why this improves autonomous supervisor/daemon progress",
  "files": [
    {{"path": "ppd/daemon/...", "content": "complete replacement file content"}}
  ],
  "validation_commands": [["python3", "ppd/tests/validate_ppd.py"]]
}}

Runtime status:
{json.dumps(status, indent=2, sort_keys=True)}

Original PP&D plan:
{plan}

Progress:
{json.dumps(progress, indent=2, sort_keys=True)}

Recent daemon results:
{json.dumps(recent_results, indent=2, sort_keys=True)}

Recent failed manifests:
{chr(10).join(failed_manifests)}

Current source files:
{chr(10).join(f"--- {name} ---\\n{content}" for name, content in files.items())}
"""
    if len(prompt) > config.max_prompt_chars:
        prompt = prompt[: config.max_prompt_chars] + "\n\n[truncated]\n"
    return prompt


def call_codex(prompt: str, config: SupervisorConfig) -> str:
    backend = os.environ.get("PPD_LLM_BACKEND", "llm_router")
    if backend != "llm_router":
        raise RuntimeError(f"Unsupported PP&D LLM backend {backend!r}; expected 'llm_router'.")
    try:
        from ipfs_datasets_py import llm_router
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(f"Could not import ipfs_datasets_py.llm_router: {exc}") from exc
    return llm_router.generate_text(
        prompt,
        model_name=config.model_name,
        provider=config.provider,
        allow_local_fallback=False,
        timeout=config.llm_timeout_seconds,
        max_new_tokens=4096,
        temperature=0.1,
    )


def run_control(config: SupervisorConfig, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(config.resolve(config.control_script)), command],
        cwd=config.repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def supervisor_daemon_config(config: SupervisorConfig) -> DaemonConfig:
    return DaemonConfig(repo_root=config.repo_root, apply=True)


def should_apply_builtin_repair(decision: SupervisorDecision, proposal: Proposal) -> bool:
    """Return True when agentic repair failed and deterministic fallback is useful."""

    if proposal.valid:
        return False
    return decision.action in {
        "invoke_codex",
        "repair_daemon_programming",
        "plan_next_tasks",
    }


def build_builtin_repair_status_payload(
    decision: SupervisorDecision,
    failed_proposal: Proposal,
) -> dict[str, Any]:
    """Build a small runtime-safe repair record for failed self-heal attempts."""

    return {
        "schemaVersion": 1,
        "createdAt": utc_now(),
        "repairKind": "builtin_supervisor_fallback",
        "llmBackend": os.environ.get("PPD_LLM_BACKEND", "llm_router"),
        "decision": {
            "action": decision.action,
            "reason": decision.reason,
            "severity": decision.severity,
        },
        "failedAgenticRepair": {
            "summary": failed_proposal.summary,
            "failureKind": failed_proposal.failure_kind or "not_applied",
            "errors": [compact_message(error) for error in failed_proposal.errors],
            "changedFiles": list(failed_proposal.changed_files),
            "validationResults": [result.compact(limit=900) for result in failed_proposal.validation_results],
        },
        "fallbackActions": [
            "preserve failed repair diagnostics without accepting the invalid patch",
            "run full PP&D daemon validation before restarting unattended worker attempts",
            "restart the worker with PPD_LLM_BACKEND=llm_router after fallback validation passes",
            "keep future retry scope narrow and fixture-first",
        ],
        "safetyBoundaries": [
            "no private DevHub session artifacts",
            "no raw crawl output",
            "no downloaded documents",
            "no browser traces or screenshots",
            "no consequential DevHub actions",
        ],
    }


def invoke_builtin_repair(
    config: SupervisorConfig,
    decision: SupervisorDecision,
    failed_proposal: Proposal,
) -> Proposal:
    """Apply deterministic supervisor fallback when Codex self-heal fails."""

    rows = read_result_log(config.resolve(config.result_log))
    board_path = config.resolve(config.task_board)
    board = read_text(board_path) if board_path.exists() else ""
    repaired_board, parked_titles = builtin_repair_task_board(board, rows)
    payload = build_builtin_repair_status_payload(decision, failed_proposal)
    payload["taskBoardRepair"] = {
        "parkedRepeatedSyntaxLoopTasks": list(parked_titles),
        "taskBoardUpdated": repaired_board != board,
    }
    files = [
        {
            "path": "ppd/daemon/builtin-repair-status.json",
            "content": json.dumps(payload, indent=2, sort_keys=True) + "\n",
        }
    ]
    if repaired_board != board:
        files.append({"path": "ppd/daemon/task-board.md", "content": repaired_board})
    proposal = Proposal(
        summary="Apply built-in supervisor fallback after failed agentic repair.",
        impact=(
            "The supervisor now records the failed self-heal diagnostics, validates the daemon "
            "without accepting the invalid patch, parks repeated syntax-loop tasks when needed, "
            "and can restart the worker on the explicit llm_router path instead of waiting for manual intervention."
        ),
        files=files,
    )
    proposal.target_task = f"Built-in supervisor fallback: {decision.reason}"
    proposal.dry_run = not config.apply
    if config.apply:
        return apply_files_with_validation(proposal, supervisor_daemon_config(config))
    proposal.validation_results = run_validation(supervisor_daemon_config(config))
    return proposal


def invoke_codex_repair(config: SupervisorConfig, decision: SupervisorDecision) -> Proposal:
    if config.apply:
        run_control(config, "stop")
    try:
        raw = call_codex(build_supervisor_prompt(config, decision), config)
        proposal = parse_proposal(raw)
    except Exception as exc:
        proposal = Proposal(
            summary="Supervisor Codex repair failed.",
            errors=[compact_message(exc)],
            failure_kind="llm",
        )
    proposal.target_task = f"Supervisor repair: {decision.reason}"
    proposal.dry_run = not config.apply

    if config.apply and proposal.files:
        proposal = apply_files_with_validation(proposal, supervisor_daemon_config(config))
    else:
        proposal.validation_results = run_validation(supervisor_daemon_config(config))

    if should_apply_builtin_repair(decision, proposal):
        proposal = invoke_builtin_repair(config, decision, proposal)

    if config.apply and config.restart_daemon:
        run_control(config, "start")
    return proposal


def write_supervisor_status(config: SupervisorConfig, decision: SupervisorDecision, proposal: Optional[Proposal]) -> None:
    payload = {
        "updated_at": utc_now(),
        "pid": os.getpid(),
        "decision": {
            "action": decision.action,
            "reason": decision.reason,
            "severity": decision.severity,
            "should_invoke_codex": decision.should_invoke_codex,
            "should_restart_daemon": decision.should_restart_daemon,
        },
        "proposal": proposal.to_dict() if proposal else None,
    }
    atomic_write_json(config.resolve(config.supervisor_status_file), payload)
    append_jsonl(config.resolve(config.supervisor_log), payload)


def run_once(config: SupervisorConfig) -> SupervisorDecision:
    decision = diagnose(config)
    proposal: Optional[Proposal] = None
    if decision.should_restart_daemon and config.apply and config.restart_daemon and not decision.should_invoke_codex:
        result = run_control(config, "start")
        proposal = Proposal(
            summary="Supervisor restarted daemon.",
            impact=compact_message(result.stdout + " " + result.stderr),
            applied=result.returncode == 0,
            dry_run=False,
            failure_kind="" if result.returncode == 0 else "restart",
            errors=[] if result.returncode == 0 else [compact_message(result.stderr or result.stdout)],
            validation_results=run_validation(supervisor_daemon_config(config)),
        )
    elif decision.should_invoke_codex and config.self_heal:
        proposal = invoke_codex_repair(config, decision)
    write_supervisor_status(config, decision, proposal)
    return decision


def self_test(repo_root: Path) -> int:
    config = SupervisorConfig(repo_root=repo_root)
    errors: list[str] = []
    sample_status = {"updated_at": "2026-05-01T00:00:00Z"}
    if age_seconds(sample_status["updated_at"], now=datetime(2026, 5, 1, 0, 1, tzinfo=timezone.utc)) != 60:
        errors.append("timestamp age calculation failed")
    if latest_repeated_failure_count([{"applied": False}, {"applied": False}]) != 2:
        errors.append("repeated failure count failed")
    completed_failure = {"applied": False, "target_task": "Task checkbox-1: Done"}
    if latest_repeated_failure_count([completed_failure], completed_task_labels={"Task checkbox-1: Done"}) != 0:
        errors.append("completed-task failure filtering failed")
    if age_seconds("2026-05-01T00:00:00Z", now=datetime(2026, 5, 1, 0, 7, 1, tzinfo=timezone.utc)) != 421:
        errors.append("active-state age calculation failed")
    syntax_failure = {
        "failure_kind": "validation",
        "target_task": "Task checkbox-80: syntax fixture",
        "validation_results": [
            {
                "command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
                "returncode": 1,
                "stderr": "SyntaxError: invalid syntax",
            }
        ],
    }
    malformed_confidence_failure = {
        "failure_kind": "validation",
        "target_task": "Task checkbox-80: syntax fixture",
        "validation_results": [
            {
                "command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
                "returncode": 1,
                "stderr": "SyntaxError: invalid syntax near confidence 1.0",
            }
        ],
    }
    malformed_return_failure = {
        "failure_kind": "validation",
        "target_task": "Task checkbox-80: syntax fixture",
        "validation_results": [
            {
                "command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
                "returncode": 1,
                "stderr": "SyntaxError: invalid syntax near return 0.0 list[str]",
            }
        ],
    }
    if not is_syntax_or_compile_failure(syntax_failure):
        errors.append("syntax failure classification failed")
    syntax_preflight_failure = dict(syntax_failure)
    syntax_preflight_failure["failure_kind"] = "syntax_preflight"
    if not is_syntax_or_compile_failure(syntax_preflight_failure):
        errors.append("syntax_preflight failure classification failed")
    if recent_syntax_failure_count([syntax_failure, syntax_failure]) != 2:
        errors.append("recent syntax failure count failed")
    if not has_malformed_python_proposal_syntax(malformed_confidence_failure):
        errors.append("malformed confidence syntax marker classification failed")
    if not has_malformed_python_proposal_syntax(malformed_return_failure):
        errors.append("malformed return annotation-like syntax marker classification failed")
    if repeated_malformed_syntax_count([malformed_confidence_failure, malformed_return_failure]) != 2:
        errors.append("repeated malformed syntax count failed")
    false_positive_preflight = {
        "failure_kind": "preflight",
        "errors": [
            "private/session artifacts may not be generated by daemon proposals: "
            "ppd/tests/fixtures/daemon/checkbox_130_checkbox_108_supersession_decision.json"
        ],
        "files": ["ppd/tests/fixtures/daemon/checkbox_130_checkbox_108_supersession_decision.json"],
    }
    if not is_private_session_preflight_false_positive(false_positive_preflight):
        errors.append("private/session preflight false-positive classification failed")
    true_private_preflight = {
        "failure_kind": "preflight",
        "errors": ["private/session artifacts may not be generated by daemon proposals: ppd/data/private/devhub/session.json"],
        "files": ["ppd/data/private/devhub/session.json"],
    }
    if is_private_session_preflight_false_positive(true_private_preflight):
        errors.append("true private/session preflight rejection must not be classified as a false positive")
    invalid_repair = Proposal(summary="bad repair", errors=["Validation failed"], failure_kind="validation")
    repair_decision = SupervisorDecision(
        action="repair_daemon_programming",
        reason="synthetic failed self-heal",
        severity="warning",
        should_invoke_codex=True,
        should_restart_daemon=True,
    )
    if not should_apply_builtin_repair(repair_decision, invalid_repair):
        errors.append("failed agentic repair should trigger built-in fallback")
    accepted_repair = Proposal(summary="accepted repair", applied=True)
    accepted_repair.validation_results = []
    if should_apply_builtin_repair(repair_decision, accepted_repair):
        errors.append("accepted repair must not trigger built-in fallback")
    payload = build_builtin_repair_status_payload(repair_decision, invalid_repair)
    if payload.get("llmBackend") != os.environ.get("PPD_LLM_BACKEND", "llm_router"):
        errors.append("built-in repair payload must preserve llm_router backend")
    if "failedAgenticRepair" not in payload:
        errors.append("built-in repair payload missing failed repair diagnostics")
    nested_title = title_from_task_label("Task checkbox-113: Task checkbox-108: Add frontier checkpoint.")
    if nested_title != "Add frontier checkpoint.":
        errors.append(f"nested task title parsing failed: {nested_title}")
    loop_board = "- [~] Task checkbox-108: Add frontier checkpoint.\n- [ ] Task checkbox-109: Next task.\n"
    loop_rows = [
        {
            "target_task": "Task checkbox-113: Task checkbox-108: Add frontier checkpoint.",
            "failure_kind": "syntax_preflight",
            "validation_results": [{"stderr": "SyntaxError: invalid syntax"}],
        },
        {
            "target_task": "Task checkbox-113: Task checkbox-108: Add frontier checkpoint.",
            "failure_kind": "syntax_preflight",
            "validation_results": [{"stderr": "SyntaxError: invalid syntax"}],
        },
    ]
    repaired_board, parked = builtin_repair_task_board(loop_board, loop_rows)
    if "- [!] Task checkbox-108: Add frontier checkpoint." not in repaired_board:
        errors.append("built-in board repair did not park repeated syntax-loop task")
    if parked != ("Add frontier checkpoint.",):
        errors.append("built-in board repair did not report parked task title")
    non_syntax_failure = {
        "failure_kind": "validation",
        "validation_results": [{"command": ["python3", "-m", "unittest"], "returncode": 1, "stderr": "AssertionError"}],
    }
    if recent_syntax_failure_count([syntax_failure, non_syntax_failure]) != 0:
        errors.append("syntax failure streak should stop at newer non-syntax validation failures")
    if should_blocked_tasks_interrupt(2, 1, 1):
        errors.append("blocked tasks must not interrupt while independent selectable work remains")
    if not should_blocked_tasks_interrupt(2, 0, 1):
        errors.append("blocked tasks should interrupt when no selectable work remains")
    complete_board = "- [x] Finished\n"
    if parse_tasks(complete_board)[0].status != "complete":
        errors.append("task parsing failed for completed board")
    synthetic = SupervisorConfig(repo_root=repo_root)
    if synthetic.plan_doc != Path("docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md"):
        errors.append("supervisor plan document path changed unexpectedly")
    if not config.resolve(config.task_board).exists():
        errors.append("supervisor task board path is missing")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "supervisor": "ppd"}, indent=2))
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Supervise and optionally repair the PP&D daemon.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--once", action="store_true", help="Run one supervision cycle")
    parser.add_argument("--watch", action="store_true", help="Run repeated supervision cycles")
    parser.add_argument("--interval", type=float, default=300.0, help="Seconds between supervisor cycles")
    parser.add_argument("--stall-seconds", type=int, default=900, help="Heartbeat age before the daemon is considered stuck")
    parser.add_argument("--apply", action="store_true", help="Allow restart or validated self-healing edits")
    parser.add_argument("--self-heal", action="store_true", help="Invoke Codex for daemon/supervisor programming repairs")
    parser.add_argument("--restart-daemon", action="store_true", help="Start/restart the worker daemon when appropriate")
    parser.add_argument("--llm-timeout", type=int, default=300, help="Seconds to allow for one Codex repair proposal")
    parser.add_argument("--model", default="gpt-5.5", help="llm_router model")
    parser.add_argument("--provider", default=None, help="llm_router provider (default: auto-select with fallback)")
    parser.add_argument("--self-test", action="store_true", help="Run supervisor self-test and exit")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    if args.self_test:
        return self_test(repo_root)
    config = SupervisorConfig(
        repo_root=repo_root,
        stall_seconds=max(1, int(args.stall_seconds)),
        llm_timeout_seconds=max(1, int(args.llm_timeout)),
        model_name=str(args.model),
        provider=args.provider,
        apply=bool(args.apply),
        self_heal=bool(args.self_heal),
        restart_daemon=bool(args.restart_daemon),
    )
    if args.watch:
        while True:
            run_once(config)
            time.sleep(max(1.0, float(args.interval)))
    decision = run_once(config)
    print(json.dumps({"action": decision.action, "reason": decision.reason, "severity": decision.severity}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
