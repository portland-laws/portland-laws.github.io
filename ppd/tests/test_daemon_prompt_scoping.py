"""Regression coverage for PP&D daemon syntax_preflight retry scoping."""

from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ppd.daemon.prompt_scoping import (  # noqa: E402
    SyntaxPreflightHistoryItem,
    build_syntax_preflight_retry_instruction_json,
    validate_retry_instruction_scope,
)


def test_syntax_preflight_history_scopes_retry_to_one_parser_bearing_domain_file() -> None:
    instruction_json = build_syntax_preflight_retry_instruction_json(
        target_task="Task checkbox-178: fixture-only DevHub draft-readiness decision matrix",
        history=(
            SyntaxPreflightHistoryItem(
                failure_kind="validation_failed",
                target_task="Task checkbox-178",
                file_paths=("ppd/devhub/draft_readiness.py", "ppd/tests/fixtures/devhub/draft_readiness.json"),
            ),
            SyntaxPreflightHistoryItem(
                failure_kind="syntax_preflight",
                target_task="Task checkbox-178",
                file_paths=("ppd/devhub/draft_readiness.py", "ppd/tests/fixtures/devhub/draft_readiness.json"),
                summary="SyntaxError: if confidence None",
            ),
        ),
    )

    assert instruction_json is not None
    assert instruction_json.strip().startswith("{")
    assert instruction_json.strip().endswith("}")
    assert "```" not in instruction_json
    assert validate_retry_instruction_scope(instruction_json) == []

    instruction = json.loads(instruction_json)
    assert instruction["response_format"] == "json_only"
    assert instruction["retry_scope"]["allowed_files"] == ["ppd/devhub/draft_readiness.py"]
    assert instruction["retry_scope"]["max_files"] == 1
    assert "ppd/tests/fixtures/devhub/draft_readiness.json" not in instruction_json


def test_syntax_preflight_history_without_parser_file_scopes_retry_to_one_daemon_repair_file() -> None:
    instruction_json = build_syntax_preflight_retry_instruction_json(
        target_task="Task checkbox-176: public source lineage rollup",
        history=(
            {
                "failure_kind": "syntax_preflight",
                "target_task": "Task checkbox-176",
                "file_paths": ["ppd/tests/fixtures/lineage/source_lineage_rollup.json"],
                "summary": "parser-bearing file absent from failed proposal",
            },
        ),
        daemon_repair_file="ppd/daemon/prompt_scoping.py",
    )

    assert instruction_json is not None
    assert validate_retry_instruction_scope(instruction_json) == []

    instruction = json.loads(instruction_json)
    assert instruction["retry_scope"]["allowed_files"] == ["ppd/daemon/prompt_scoping.py"]
    assert instruction["retry_scope"]["max_files"] == 1
    assert instruction["response_format"] == "json_only"


def test_retry_instruction_scope_rejects_multiple_files() -> None:
    bad_instruction = json.dumps(
        {
            "response_format": "json_only",
            "retry_scope": {
                "allowed_files": ["ppd/devhub/draft_readiness.py", "ppd/tests/test_devhub_draft_readiness.py"],
                "max_files": 2,
            },
        }
    )

    errors = validate_retry_instruction_scope(bad_instruction)
    assert "retry_scope.allowed_files must contain exactly one file" in errors


def test_prompt_scoping_python_files_compile() -> None:
    py_compile.compile(str(REPO_ROOT / "ppd" / "daemon" / "prompt_scoping.py"), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)


if __name__ == "__main__":
    test_syntax_preflight_history_scopes_retry_to_one_parser_bearing_domain_file()
    test_syntax_preflight_history_without_parser_file_scopes_retry_to_one_daemon_repair_file()
    test_retry_instruction_scope_rejects_multiple_files()
    test_prompt_scoping_python_files_compile()
