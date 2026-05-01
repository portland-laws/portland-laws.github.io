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
    parse_proposal,
    parse_tasks,
    read_result_log,
    read_text,
    run_validation,
    utc_now,
)


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
    max_prompt_chars: int = 50000
    llm_timeout_seconds: int = 300
    model_name: str = "gpt-5.5"
    provider: Optional[str] = "codex_cli"
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


def latest_repeated_failure_count(rows: list[dict[str, Any]]) -> int:
    count = 0
    for proposal in reversed(rows):
        if proposal.get("applied") and proposal.get("validation_passed") and not proposal.get("errors"):
            break
        count += 1
    return count


def diagnose(config: SupervisorConfig, *, now: Optional[datetime] = None) -> SupervisorDecision:
    pid = read_pid(config.resolve(config.pid_file))
    running = process_running(pid)
    status = load_json(config.resolve(config.status_file))
    progress = load_json(config.resolve(config.progress_file))
    board = read_text(config.resolve(config.task_board)) if config.resolve(config.task_board).exists() else ""
    tasks = parse_tasks(board)
    rows = read_result_log(config.resolve(config.result_log))

    if not running:
        return SupervisorDecision(
            action="restart_daemon",
            reason="daemon process is not running",
            severity="warning",
            should_restart_daemon=True,
        )

    heartbeat_age = age_seconds(status.get("updated_at"), now=now)
    active_state = str(status.get("active_state") or status.get("state") or "")
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
            reason=f"daemon heartbeat is stale for {int(heartbeat_age)} seconds in state {active_state or '<unknown>'}",
            severity="critical",
            should_invoke_codex=True,
            should_restart_daemon=True,
        )

    if tasks and all(task.status == "complete" for task in tasks):
        return SupervisorDecision(
            action="plan_next_tasks",
            reason="all PP&D daemon tasks are complete; review the original PP&D goal and add the next task-board tranche",
            severity="info",
            should_invoke_codex=True,
        )

    blocked = [task for task in tasks if task.status == "blocked"]
    if len(blocked) >= config.blocked_task_threshold:
        return SupervisorDecision(
            action="invoke_codex",
            reason=f"{len(blocked)} task(s) are blocked: " + "; ".join(task.label for task in blocked[:3]),
            severity="warning",
            should_invoke_codex=True,
        )

    latest = progress.get("latest") if isinstance(progress.get("latest"), dict) else {}
    if latest.get("failure_kind") == "no_eligible_tasks" and all(task.status == "complete" for task in tasks):
        return SupervisorDecision(
            action="plan_next_tasks",
            reason="daemon has no eligible tasks; review completed work against the PP&D plan and add the next backlog tranche",
            severity="info",
            should_invoke_codex=True,
        )

    repeated_failures = latest_repeated_failure_count(rows)
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

    prompt = f"""
You are Codex acting as a supervisor repair agent for the isolated PP&D daemon.

Supervisor diagnosis:
- action: {decision.action}
- severity: {decision.severity}
- reason: {decision.reason}

Goal:
{"Review completed work against the original PP&D goal and update `ppd/daemon/task-board.md` with the next narrow, ordered tranche of unfinished tasks. Do not implement those tasks in this proposal; create the backlog so the worker daemon can continue." if decision.action == "plan_next_tasks" else "Improve the PP&D daemon or supervisor programming so the worker can resume meaningful autonomous progress."}

Hard constraints:
- Return ONLY one JSON object; no markdown fences and no prose outside JSON.
- Use complete file replacements in a `files` array. Do not return shell commands.
- For `plan_next_tasks`, edit only `ppd/daemon/task-board.md` and optionally `ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md`.
- For repair actions, edit only `ppd/daemon/`, `ppd/tests/`, `ppd/.gitignore`, or PP&D daemon operations docs.
- Do not edit application/domain artifacts just to mark progress. Fix supervision, validation, task selection, retry, recovery, or diagnostics.
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
    parser.add_argument("--provider", default="codex_cli", help="llm_router provider")
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
