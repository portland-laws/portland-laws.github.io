"""Supervisor replenishment tranche rotation checks.

The PP&D supervisor can append broad batches of new fixture-first tasks when a
board is complete. The first two completed replenishment tranches may share a
broad title while the direction settles, but the third and later completed
tranches must rotate away from titles already used by earlier completed
tranches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReplenishmentTranche:
    """A committed supervisor replenishment tranche summary."""

    tranche_id: str
    broad_title: str
    completed: bool


@dataclass(frozen=True)
class ReplenishmentRotationFinding:
    """A rotation validation finding for a completed replenishment tranche."""

    tranche_id: str
    broad_title: str
    reason: str
    previous_tranche_id: str | None = None


def replenishment_tranche_from_dict(data: Mapping[str, Any]) -> ReplenishmentTranche:
    """Build a replenishment tranche record from a JSON-like mapping."""

    return ReplenishmentTranche(
        tranche_id=str(data.get("trancheId", data.get("tranche_id", ""))),
        broad_title=str(data.get("broadTitle", data.get("broad_title", ""))),
        completed=bool(data.get("completed", False)),
    )


def validate_completed_tranche_rotation(
    tranches: Iterable[ReplenishmentTranche],
    *,
    unrestricted_completed_prefix: int = 2,
) -> list[ReplenishmentRotationFinding]:
    """Return findings for late completed tranches that repeat prior titles.

    Completed tranches are evaluated in the order supplied. The first two
    completed tranches are allowed to reuse a broad title. Beginning with the
    third completed tranche, each normalized broad title must be new among all
    previous completed tranches.
    """

    findings: list[ReplenishmentRotationFinding] = []
    previous_titles: dict[str, str] = {}
    completed_count = 0

    for tranche in tranches:
        if not tranche.completed:
            continue

        completed_count += 1
        normalized_title = _normalize_title(tranche.broad_title)
        if not tranche.tranche_id.strip():
            findings.append(
                ReplenishmentRotationFinding(
                    tranche_id=tranche.tranche_id,
                    broad_title=tranche.broad_title,
                    reason="completed replenishment tranche requires a tranche_id",
                )
            )
        if not normalized_title:
            findings.append(
                ReplenishmentRotationFinding(
                    tranche_id=tranche.tranche_id,
                    broad_title=tranche.broad_title,
                    reason="completed replenishment tranche requires a broad_title",
                )
            )
            continue

        previous_tranche_id = previous_titles.get(normalized_title)
        if completed_count > unrestricted_completed_prefix and previous_tranche_id is not None:
            findings.append(
                ReplenishmentRotationFinding(
                    tranche_id=tranche.tranche_id,
                    broad_title=tranche.broad_title,
                    previous_tranche_id=previous_tranche_id,
                    reason="third and later completed replenishment tranches must not duplicate previous broad titles",
                )
            )
            continue

        previous_titles.setdefault(normalized_title, tranche.tranche_id)

    return findings


def _normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())
