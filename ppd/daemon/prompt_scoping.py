"""Prompt scoping helpers for PP&D daemon retry instructions.

The daemon uses these helpers after syntax_preflight failures so the next LLM
attempt is narrow, JSON-only, and limited to a single syntax-relevant repair.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable, Mapping, Sequence


PARSER_BEARING_SUFFIXES = frozenset({".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})
DAEMON_REPAIR_PREFIX = "ppd/daemon/"
PPD_PREFIX = "ppd/"


@dataclass(frozen=True)
class SyntaxPreflightHistoryItem:
    """A compact daemon failure-history entry relevant to retry scoping."""

    failure_kind: str
    target_task: str
    file_paths: tuple[str, ...]
    summary: str = ""


@dataclass(frozen=True)
class RetryPromptScope:
    """The single-file scope the daemon should impose on a retry prompt."""

    target_task: str
    allowed_file: str
    reason: str
    json_only: bool = True

    def to_retry_instruction(self) -> dict[str, object]:
        return {
            "response_format": "json_only",
            "target_task": self.target_task,
            "retry_scope": {
                "allowed_files": [self.allowed_file],
                "max_files": 1,
                "reason": self.reason,
            },
            "constraints": [
                "Return only one JSON object.",
                "Use complete file replacements in the files array.",
                "Do not include markdown fences or prose outside JSON.",
                "Repair exactly one parser-bearing PP&D file or exactly one daemon repair file.",
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_retry_instruction(), sort_keys=True, separators=(",", ":"))


def build_syntax_preflight_retry_scope(
    target_task: str,
    history: Sequence[SyntaxPreflightHistoryItem | Mapping[str, object]],
    daemon_repair_file: str = "ppd/daemon/prompt_scoping.py",
) -> RetryPromptScope | None:
    """Return a one-file retry scope when recent history contains syntax_preflight.

    Domain-task syntax failures should not invite broad rewrites. The preferred
    scope is the most recent PP&D parser-bearing file named by syntax preflight.
    If no such file is present, fall back to one daemon repair file.
    """

    normalized_history = tuple(_history_item(item) for item in history)
    syntax_items = [item for item in normalized_history if item.failure_kind == "syntax_preflight"]
    if not syntax_items:
        return None

    latest = syntax_items[-1]
    parser_file = _first_parser_bearing_ppd_file(latest.file_paths)
    if parser_file is not None:
        return RetryPromptScope(
            target_task=target_task,
            allowed_file=parser_file,
            reason="recent syntax_preflight failure in parser-bearing PP&D file",
        )

    repair_file = _normalize_ppd_path(daemon_repair_file)
    if not _is_daemon_repair_file(repair_file):
        raise ValueError(f"daemon repair file must live under {DAEMON_REPAIR_PREFIX}: {daemon_repair_file}")

    return RetryPromptScope(
        target_task=target_task,
        allowed_file=repair_file,
        reason="recent syntax_preflight failure without a parser-bearing file; repair daemon retry scoping",
    )


def build_syntax_preflight_retry_instruction_json(
    target_task: str,
    history: Sequence[SyntaxPreflightHistoryItem | Mapping[str, object]],
    daemon_repair_file: str = "ppd/daemon/prompt_scoping.py",
) -> str | None:
    """Build the JSON-only retry instruction string for syntax_preflight history."""

    scope = build_syntax_preflight_retry_scope(target_task, history, daemon_repair_file)
    if scope is None:
        return None
    return scope.to_json()


def validate_retry_instruction_scope(instruction_json: str) -> list[str]:
    """Validate the retry instruction is JSON-only and scoped to one legal file."""

    errors: list[str] = []
    try:
        instruction = json.loads(instruction_json)
    except json.JSONDecodeError as exc:
        return [f"retry instruction is not valid JSON: {exc}"]

    if not isinstance(instruction, dict):
        return ["retry instruction must be a JSON object"]
    if instruction.get("response_format") != "json_only":
        errors.append("retry instruction must declare json_only response_format")

    retry_scope = instruction.get("retry_scope")
    if not isinstance(retry_scope, dict):
        errors.append("retry instruction must include retry_scope object")
        return errors

    allowed_files = retry_scope.get("allowed_files")
    if not isinstance(allowed_files, list) or len(allowed_files) != 1:
        errors.append("retry_scope.allowed_files must contain exactly one file")
        return errors

    allowed_file = allowed_files[0]
    if not isinstance(allowed_file, str):
        errors.append("retry_scope.allowed_files[0] must be a string")
        return errors

    normalized = _normalize_ppd_path(allowed_file)
    if normalized != allowed_file:
        errors.append("allowed file must be a normalized relative PP&D path")
    if not (_is_parser_bearing_ppd_file(normalized) or _is_daemon_repair_file(normalized)):
        errors.append("allowed file must be one parser-bearing PP&D file or one daemon repair file")

    if retry_scope.get("max_files") != 1:
        errors.append("retry_scope.max_files must be 1")

    return errors


def _history_item(item: SyntaxPreflightHistoryItem | Mapping[str, object]) -> SyntaxPreflightHistoryItem:
    if isinstance(item, SyntaxPreflightHistoryItem):
        return item

    file_paths_value = item.get("file_paths", item.get("files", ()))
    file_paths = tuple(str(path) for path in _iter_stringish(file_paths_value))
    return SyntaxPreflightHistoryItem(
        failure_kind=str(item.get("failure_kind", item.get("failureKind", ""))),
        target_task=str(item.get("target_task", item.get("targetTask", ""))),
        file_paths=file_paths,
        summary=str(item.get("summary", "")),
    )


def _iter_stringish(value: object) -> Iterable[object]:
    if isinstance(value, (list, tuple, set)):
        return value
    if value is None:
        return ()
    return (value,)


def _first_parser_bearing_ppd_file(paths: Sequence[str]) -> str | None:
    for path in paths:
        normalized = _normalize_ppd_path(path)
        if _is_parser_bearing_ppd_file(normalized):
            return normalized
    return None


def _is_parser_bearing_ppd_file(path: str) -> bool:
    parsed = PurePosixPath(path)
    return path.startswith(PPD_PREFIX) and parsed.suffix in PARSER_BEARING_SUFFIXES


def _is_daemon_repair_file(path: str) -> bool:
    return path.startswith(DAEMON_REPAIR_PREFIX) and PurePosixPath(path).suffix in PARSER_BEARING_SUFFIXES


def _normalize_ppd_path(path: str) -> str:
    path_text = path.replace("\\", "/").strip()
    parts = []
    for part in PurePosixPath(path_text).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)
