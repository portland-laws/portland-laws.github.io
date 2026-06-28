"""Deterministic consistency checks for PP&D requirements and process models.

The checker intentionally operates on small, committed fixture-shaped mappings. It
keeps validation source-grounded by comparing public-source-derived requirement
records against process model coverage for the requirement categories that affect
agent guardrails: required documents, file rules, fee triggers, and unsupported
paths.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


REQUIRED_DOCUMENT = "required_document"
FILE_RULE = "file_rule"
FEE_TRIGGER = "fee_trigger"
UNSUPPORTED_PATH = "unsupported_path"

SUPPORTED_CATEGORIES = frozenset(
    (REQUIRED_DOCUMENT, FILE_RULE, FEE_TRIGGER, UNSUPPORTED_PATH)
)

_CATEGORY_TO_MODEL_FIELD = {
    REQUIRED_DOCUMENT: "required_documents",
    FILE_RULE: "file_rules",
    FEE_TRIGGER: "fee_triggers",
    UNSUPPORTED_PATH: "unsupported_paths",
}


@dataclass(frozen=True, order=True)
class ConsistencyIssue:
    """A stable, serializable consistency finding."""

    issue_type: str
    process_id: str
    permit_type: str
    category: str
    key: str
    requirement_id: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "issue_type": self.issue_type,
            "process_id": self.process_id,
            "permit_type": self.permit_type,
            "category": self.category,
            "key": self.key,
            "requirement_id": self.requirement_id,
            "message": self.message,
        }


@dataclass(frozen=True)
class ConsistencyReport:
    """Result of a requirement-to-process consistency check."""

    checked_requirement_count: int
    checked_process_count: int
    issues: Tuple[ConsistencyIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checked_requirement_count": self.checked_requirement_count,
            "checked_process_count": self.checked_process_count,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON fixture or model file as an object mapping."""

    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("expected top-level JSON object in {0}".format(path))
    return value


def check_consistency(
    source_requirements: Mapping[str, Any], process_models: Mapping[str, Any]
) -> ConsistencyReport:
    """Compare source-derived requirements to process model coverage.

    Expected input shape is deliberately simple and fixture friendly:

    source_requirements = {
        "requirements": [
            {
                "requirement_id": "REQ-1",
                "process_id": "building-plan-review",
                "permit_type": "building_plan_review",
                "category": "required_document",
                "key": "plans_single_pdf"
            }
        ]
    }

    process_models = {
        "process_models": [
            {
                "process_id": "building-plan-review",
                "permit_type": "building_plan_review",
                "required_documents": [{"key": "plans_single_pdf"}],
                "file_rules": [{"key": "separate_supporting_pdfs"}],
                "fee_triggers": [{"key": "fees_due_after_intake"}],
                "unsupported_paths": [{"key": "some_permits_email_only"}]
            }
        ]
    }
    """

    requirements = _as_sequence(source_requirements.get("requirements"), "requirements")
    models = _as_sequence(process_models.get("process_models"), "process_models")
    model_index = _index_process_models(models)
    requirement_keys = _requirement_keys(requirements)

    issues: List[ConsistencyIssue] = []
    checked_requirement_count = 0

    for requirement in requirements:
        category = _text(requirement.get("category"))
        if category not in SUPPORTED_CATEGORIES:
            continue
        checked_requirement_count += 1
        requirement_id = _text(requirement.get("requirement_id"))
        process_id = _text(requirement.get("process_id"))
        permit_type = _text(requirement.get("permit_type"))
        key = _text(requirement.get("key"))

        if not requirement_id or not process_id or not permit_type or not key:
            issues.append(
                ConsistencyIssue(
                    issue_type="malformed_requirement",
                    process_id=process_id,
                    permit_type=permit_type,
                    category=category,
                    key=key,
                    requirement_id=requirement_id,
                    message="Requirement is missing requirement_id, process_id, permit_type, or key.",
                )
            )
            continue

        model = model_index.get((process_id, permit_type))
        if model is None:
            issues.append(
                ConsistencyIssue(
                    issue_type="missing_process_model",
                    process_id=process_id,
                    permit_type=permit_type,
                    category=category,
                    key=key,
                    requirement_id=requirement_id,
                    message="No process model matches the requirement process_id and permit_type.",
                )
            )
            continue

        model_field = _CATEGORY_TO_MODEL_FIELD[category]
        model_keys = _model_entry_keys(model.get(model_field))
        if key not in model_keys:
            issues.append(
                ConsistencyIssue(
                    issue_type="missing_model_coverage",
                    process_id=process_id,
                    permit_type=permit_type,
                    category=category,
                    key=key,
                    requirement_id=requirement_id,
                    message="Source-derived requirement is not represented in process model field {0}.".format(
                        model_field
                    ),
                )
            )

    for model in models:
        process_id = _text(model.get("process_id"))
        permit_type = _text(model.get("permit_type"))
        if not process_id or not permit_type:
            issues.append(
                ConsistencyIssue(
                    issue_type="malformed_process_model",
                    process_id=process_id,
                    permit_type=permit_type,
                    category="",
                    key="",
                    requirement_id="",
                    message="Process model is missing process_id or permit_type.",
                )
            )
            continue

        for category, model_field in sorted(_CATEGORY_TO_MODEL_FIELD.items()):
            for key in sorted(_model_entry_keys(model.get(model_field))):
                requirement_key = (process_id, permit_type, category, key)
                if requirement_key not in requirement_keys:
                    issues.append(
                        ConsistencyIssue(
                            issue_type="model_entry_without_source_requirement",
                            process_id=process_id,
                            permit_type=permit_type,
                            category=category,
                            key=key,
                            requirement_id="",
                            message="Process model field {0} contains an entry without a matching source-derived requirement.".format(
                                model_field
                            ),
                        )
                    )

    return ConsistencyReport(
        checked_requirement_count=checked_requirement_count,
        checked_process_count=len(models),
        issues=tuple(sorted(issues)),
    )


def check_consistency_files(requirements_path: Path, process_models_path: Path) -> ConsistencyReport:
    """Load two JSON files and run the consistency check."""

    return check_consistency(load_json_file(requirements_path), load_json_file(process_models_path))


def _index_process_models(
    models: Sequence[Mapping[str, Any]]
) -> Dict[Tuple[str, str], Mapping[str, Any]]:
    index: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for model in models:
        process_id = _text(model.get("process_id"))
        permit_type = _text(model.get("permit_type"))
        if process_id and permit_type:
            index[(process_id, permit_type)] = model
    return index


def _requirement_keys(requirements: Sequence[Mapping[str, Any]]) -> Set[Tuple[str, str, str, str]]:
    keys: Set[Tuple[str, str, str, str]] = set()
    for requirement in requirements:
        category = _text(requirement.get("category"))
        if category not in SUPPORTED_CATEGORIES:
            continue
        process_id = _text(requirement.get("process_id"))
        permit_type = _text(requirement.get("permit_type"))
        key = _text(requirement.get("key"))
        if process_id and permit_type and key:
            keys.add((process_id, permit_type, category, key))
    return keys


def _model_entry_keys(value: Any) -> Set[str]:
    keys: Set[str] = set()
    for entry in _coerce_entries(value):
        if isinstance(entry, str):
            key = _text(entry)
        elif isinstance(entry, Mapping):
            key = _text(entry.get("key"))
        else:
            key = ""
        if key:
            keys.add(key)
    return keys


def _coerce_entries(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, tuple):
        return value
    return (value,)


def _as_sequence(value: Any, field_name: str) -> Tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("expected {0} to be a list".format(field_name))
    result: List[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("expected every {0} item to be an object".format(field_name))
        result.append(item)
    return tuple(result)


def _text(value: Optional[Any]) -> str:
    if value is None:
        return ""
    return str(value).strip()
