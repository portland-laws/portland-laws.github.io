"""PP&D daemon write-path and visible-change policy."""

from __future__ import annotations

from typing import Iterable

from ipfs_datasets_py.optimizers.todo_daemon.engine import PathPolicy


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

RUNTIME_ONLY_CHANGE_PATHS = frozenset(
    {
        "ppd/daemon/builtin-repair-status.json",
        "ppd/daemon/deterministic-progress.json",
        "ppd/daemon/task-board.md",
    }
)

PPD_PATH_POLICY = PathPolicy(
    allowed_write_prefixes=ALLOWED_WRITE_PREFIXES,
    disallowed_write_prefixes=DISALLOWED_WRITE_PREFIXES,
    private_write_path_fragments=PRIVATE_WRITE_PATH_FRAGMENTS,
    private_write_path_tokens=PRIVATE_WRITE_PATH_TOKENS,
    runtime_only_change_paths=RUNTIME_ONLY_CHANGE_PATHS,
    ignored_visible_prefixes=(
        "ppd/daemon/accepted-work/",
        "ppd/daemon/failed-patches/",
        "ppd/daemon/worktrees/",
    ),
    visible_source_prefixes=("ppd/",),
)


def validate_write_path(path: str) -> list[str]:
    return PPD_PATH_POLICY.validate_write_path(path, daemon_label="PP&D daemon")


def is_private_write_path(normalized: str) -> bool:
    return PPD_PATH_POLICY.is_private_write_path(normalized)


def has_visible_source_change(changed_files: Iterable[str]) -> bool:
    """Return True when accepted work changes source or fixture files, not only runtime state."""

    return PPD_PATH_POLICY.has_visible_source_change(changed_files)
