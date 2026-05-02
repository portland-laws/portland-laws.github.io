"""Supervisor diagnostics for stale blocked fixture-shape tasks.

The PP&D daemon sometimes blocks a domain task after repeated fixture-shape
validation failures. If a later accepted validation task proves the same fixture
shape, the daemon should avoid retrying the stale blocked task broadly. This
module keeps that decision narrow and data-only: compare a blocked task's
expected fixture shape with already accepted validation tasks and emit a compact
recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class FixtureShape:
    """Minimal shape signature used for supervisor reconciliation."""

    fixture_path: str
    required_fields: tuple[str, ...]

    def is_satisfied_by(self, other: "FixtureShape") -> bool:
        if self.fixture_path != other.fixture_path:
            return False
        return set(self.required_fields).issubset(set(other.required_fields))


@dataclass(frozen=True)
class AcceptedValidationTask:
    task_id: str
    summary: str
    fixture_shape: FixtureShape


@dataclass(frozen=True)
class BlockedValidationTask:
    task_id: str
    summary: str
    fixture_shape: FixtureShape


@dataclass(frozen=True)
class FixtureShapeReconciliationDiagnostic:
    blocked_task_id: str
    accepted_task_id: str
    fixture_path: str
    matched_fields: tuple[str, ...]
    recommendation: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "blockedTaskId": self.blocked_task_id,
            "acceptedTaskId": self.accepted_task_id,
            "fixturePath": self.fixture_path,
            "matchedFields": list(self.matched_fields),
            "recommendation": self.recommendation,
            "reason": self.reason,
        }


def reconcile_blocked_fixture_shape(
    blocked_task: BlockedValidationTask,
    accepted_tasks: Sequence[AcceptedValidationTask],
) -> FixtureShapeReconciliationDiagnostic | None:
    """Return a diagnostic when accepted work satisfies a blocked fixture shape."""

    for accepted_task in accepted_tasks:
        if blocked_task.fixture_shape.is_satisfied_by(accepted_task.fixture_shape):
            matched_fields = tuple(
                field
                for field in blocked_task.fixture_shape.required_fields
                if field in accepted_task.fixture_shape.required_fields
            )
            return FixtureShapeReconciliationDiagnostic(
                blocked_task_id=blocked_task.task_id,
                accepted_task_id=accepted_task.task_id,
                fixture_path=blocked_task.fixture_shape.fixture_path,
                matched_fields=matched_fields,
                recommendation="supersede_blocked_or_resume_one_file",
                reason=(
                    "accepted validation task fixture shape contains every field "
                    "required by the blocked validation task"
                ),
            )
    return None


def blocked_task_from_dict(data: Mapping[str, Any]) -> BlockedValidationTask:
    return BlockedValidationTask(
        task_id=str(data.get("taskId", data.get("task_id", ""))),
        summary=str(data.get("summary", "")),
        fixture_shape=_fixture_shape_from_dict(data.get("fixtureShape", data.get("fixture_shape", {}))),
    )


def accepted_task_from_dict(data: Mapping[str, Any]) -> AcceptedValidationTask:
    return AcceptedValidationTask(
        task_id=str(data.get("taskId", data.get("task_id", ""))),
        summary=str(data.get("summary", "")),
        fixture_shape=_fixture_shape_from_dict(data.get("fixtureShape", data.get("fixture_shape", {}))),
    )


def _fixture_shape_from_dict(value: Any) -> FixtureShape:
    if not isinstance(value, Mapping):
        value = {}
    fields = value.get("requiredFields", value.get("required_fields", ()))
    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)):
        fields = ()
    return FixtureShape(
        fixture_path=str(value.get("fixturePath", value.get("fixture_path", ""))),
        required_fields=tuple(str(field) for field in fields if str(field).strip()),
    )
