"""Deterministic guardrail promotion gate helper.

This module intentionally does not know Portland permit rules. It only loads
committed fixture data and composes caller-provided validators into a promotion
result that another task can use before promoting a guardrail artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

FixtureData = Mapping[str, Any]
Validator = Callable[[FixtureData], Any]


@dataclass(frozen=True)
class PromotionCheck:
    """One validator outcome used by the promotion gate."""

    name: str
    passed: bool
    message: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class PromotionGateResult:
    """Aggregated promotion decision for one deterministic fixture."""

    fixture_path: str
    promoted: bool
    checks: tuple[PromotionCheck, ...]

    @property
    def failures(self) -> tuple[PromotionCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_path": self.fixture_path,
            "promoted": self.promoted,
            "checks": [check.to_dict() for check in self.checks],
            "failures": [check.to_dict() for check in self.failures],
        }


def load_fixture(path: str | Path) -> FixtureData:
    """Load a committed JSON fixture without network or browser side effects."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError(f"promotion fixture must be a JSON object: {fixture_path}")
    return data


def run_guardrail_promotion_gate(
    fixture: str | Path | FixtureData,
    validators: Sequence[Validator] | Mapping[str, Validator],
) -> PromotionGateResult:
    """Run caller-provided validators against fixture data.

    Validators may return a PromotionCheck, a boolean, a mapping with passed /
    message / evidence keys, or a tuple of (passed, message[, evidence]).
    Exceptions are captured as failed checks so the caller gets a deterministic
    decision instead of a partially applied promotion.
    """

    fixture_data: FixtureData
    fixture_path: str
    if isinstance(fixture, (str, Path)):
        fixture_path = str(Path(fixture))
        fixture_data = load_fixture(fixture)
    elif isinstance(fixture, Mapping):
        fixture_path = ""
        fixture_data = fixture
    else:
        raise TypeError("fixture must be a path or mapping")

    named_validators = _normalize_validators(validators)
    checks: list[PromotionCheck] = []

    if not named_validators:
        checks.append(
            PromotionCheck(
                name="validators_present",
                passed=False,
                message="at least one promotion validator is required",
            )
        )

    for name, validator in named_validators:
        try:
            raw_check = validator(fixture_data)
        except Exception as exc:  # pragma: no cover - exact exception type is caller-defined.
            checks.append(
                PromotionCheck(
                    name=name,
                    passed=False,
                    message=f"validator raised {exc.__class__.__name__}: {exc}",
                )
            )
            continue
        checks.append(_coerce_check(name, raw_check))

    promoted = bool(checks) and all(check.passed for check in checks)
    return PromotionGateResult(
        fixture_path=fixture_path,
        promoted=promoted,
        checks=tuple(checks),
    )


def _normalize_validators(
    validators: Sequence[Validator] | Mapping[str, Validator],
) -> tuple[tuple[str, Validator], ...]:
    if isinstance(validators, Mapping):
        items = validators.items()
    else:
        items = ((_validator_name(validator), validator) for validator in validators)

    normalized: list[tuple[str, Validator]] = []
    for name, validator in items:
        if not callable(validator):
            raise TypeError(f"promotion validator is not callable: {name}")
        normalized.append((str(name), validator))
    return tuple(normalized)


def _validator_name(validator: Validator) -> str:
    return getattr(validator, "__name__", validator.__class__.__name__)


def _coerce_check(default_name: str, raw_check: Any) -> PromotionCheck:
    if isinstance(raw_check, PromotionCheck):
        return raw_check

    if isinstance(raw_check, bool):
        return PromotionCheck(
            name=default_name,
            passed=raw_check,
            message="validator passed" if raw_check else "validator failed",
        )

    if isinstance(raw_check, Mapping):
        passed = raw_check.get("passed")
        if not isinstance(passed, bool):
            raise TypeError(f"validator mapping must include boolean passed: {default_name}")
        evidence = _coerce_evidence(raw_check.get("evidence", ()))
        return PromotionCheck(
            name=str(raw_check.get("name", default_name)),
            passed=passed,
            message=str(raw_check.get("message", "validator passed" if passed else "validator failed")),
            evidence=evidence,
        )

    if isinstance(raw_check, tuple):
        return _coerce_tuple_check(default_name, raw_check)

    raise TypeError(f"unsupported promotion validator result for {default_name}: {type(raw_check).__name__}")


def _coerce_tuple_check(default_name: str, raw_check: tuple[Any, ...]) -> PromotionCheck:
    if len(raw_check) not in (2, 3):
        raise TypeError(f"validator tuple must be (passed, message[, evidence]): {default_name}")
    passed, message = raw_check[0], raw_check[1]
    if not isinstance(passed, bool):
        raise TypeError(f"validator tuple passed value must be boolean: {default_name}")
    evidence = _coerce_evidence(raw_check[2] if len(raw_check) == 3 else ())
    return PromotionCheck(
        name=default_name,
        passed=passed,
        message=str(message),
        evidence=evidence,
    )


def _coerce_evidence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    return (str(value),)
