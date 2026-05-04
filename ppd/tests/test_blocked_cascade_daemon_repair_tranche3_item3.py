import json
from dataclasses import dataclass
from pathlib import Path


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair"
    / "tranche3_item3.json"
)


@dataclass(frozen=True)
class BlockedWork:
    blocked_after_generation: int
    parked: bool = True


@dataclass(frozen=True)
class RepairAttempt:
    kind: str
    generation: int
    validated: bool


def status_after_repair(work: BlockedWork, repair: RepairAttempt) -> str:
    fresh_daemon_repair = (
        repair.kind == "daemon-repair"
        and repair.generation > work.blocked_after_generation
    )
    if work.parked and fresh_daemon_repair and repair.validated:
        return "ready"
    return "parked"


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    work = BlockedWork(
        blocked_after_generation=fixture["blocked_work"]["blocked_after_generation"]
    )

    observed = [
        status_after_repair(
            work,
            RepairAttempt(
                kind=attempt["kind"],
                generation=attempt["generation"],
                validated=attempt["validated"],
            ),
        )
        for attempt in fixture["repair_attempts"]
    ]

    expected = [attempt["expected_status"] for attempt in fixture["repair_attempts"]]
    assert observed == expected
    assert observed[:-1] == ["parked", "parked"]
    assert observed[-1] == "ready"
