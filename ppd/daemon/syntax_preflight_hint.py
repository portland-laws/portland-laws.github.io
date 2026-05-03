"""Helpers for turning syntax preflight failures into daemon repair hints."""

from __future__ import annotations

from pathlib import Path


def build_syntax_preflight_next_action_hint(path: str | Path, py_compile_detail: str) -> str:
    """Return the narrow next action for a py_compile syntax failure.

    Syntax failures are repair blockers. The daemon should ask for replacing only
    the failing Python file, or a daemon repair file, before any domain retry.
    """

    failing_path = Path(path).as_posix()
    detail = " ".join(str(py_compile_detail).split())
    if detail:
        detail = f" py_compile detail: {detail}"

    repair_kind = "daemon repair file" if "/daemon/" in f"/{failing_path}" else "syntactically failing Python file"
    return (
        "Before any domain retry, replace only one "
        f"{repair_kind}: {failing_path}.{detail}"
    )
