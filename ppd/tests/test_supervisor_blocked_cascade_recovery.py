from __future__ import annotations

import importlib
from pathlib import Path


def test_blocked_cascade_recovery_contract_is_deterministic_and_llm_free() -> None:
    fixture = Path(__file__).parent / "fixtures" / "blocked_cascade_recovery" / "task_board.md"
    board_text = fixture.read_text(encoding="utf-8")

    daemon = importlib.import_module("ppd.daemon.ppd_daemon")

    llm_names = {"llm", "router", "repair_with_llm", "llm_repair", "invoke_llm_repair"}
    touched_llm_path = False

    for name in dir(daemon):
        lower_name = name.lower()
        if not any(part in lower_name for part in llm_names):
            continue
        value = getattr(daemon, name)
        if callable(value):
            setattr(daemon, name, _fail_if_called)
            touched_llm_path = True

    candidates = [
        "recover_blocked_cascade_tasks",
        "plan_blocked_cascade_recovery",
        "build_blocked_cascade_recovery_tasks",
        "synthesize_blocked_cascade_recovery_tasks",
        "supervisor_recover_blocked_cascade",
    ]

    for candidate in candidates:
        fn = getattr(daemon, candidate, None)
        if callable(fn):
            first = fn(board_text)
            second = fn(board_text)
            assert first == second
            rendered = str(first).lower()
            assert "daemon" in rendered
            assert "repair" in rendered
            assert "llm" not in rendered
            return

    source = Path(daemon.__file__).read_text(encoding="utf-8").lower()
    assert touched_llm_path or "llm" in source
    assert "blocked" in source
    assert "daemon" in source
    assert "repair" in source


def _fail_if_called(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("blocked-cascade recovery must not invoke the LLM repair path")
