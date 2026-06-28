from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class SurfaceDriftStatus:
    PASS = "pass"
    ATTENDED_REVIEW = "attended_review"
    BLOCKED = "blocked"


PRIVATE_VALUE_KEYS = frozenset(
    {
        "value",
        "values",
        "current_value",
        "input_value",
        "selected_value",
        "selected_values",
        "checked_value",
        "field_value",
        "private_value",
        "raw_value",
    }
)

CONSEQUENTIAL_ACTION_WORDS = frozenset(
    {
        "acknowledge",
        "captcha",
        "cancel",
        "certify",
        "create_account",
        "login",
        "mfa",
        "pay",
        "payment",
        "password",
        "schedule",
        "sign_in",
        "submit",
        "upload",
    }
)

UNCERTAIN_WORDS = frozenset(
    {
        "dynamic",
        "generated",
        "new",
        "other",
        "unknown",
        "unlabeled",
        "unmapped",
        "uncertain",
    }
)


@dataclass(frozen=True)
class SurfaceControl:
    key: str
    label: str
    control_type: str
    action: str
    selector_hint: str = ""
    requires_attendance: bool = False
    requires_exact_confirmation: bool = False
    source: str = "redacted_manifest"

    @classmethod
    def from_mapping(cls, item: Mapping[str, object]) -> "SurfaceControl":
        forbidden = sorted(PRIVATE_VALUE_KEYS.intersection(item.keys()))
        if forbidden:
            raise ValueError(
                "DevHub surface manifests must not include private page values: "
                + ", ".join(forbidden)
            )

        return cls(
            key=_as_text(item.get("key")),
            label=_as_text(item.get("label")),
            control_type=_as_text(item.get("control_type")),
            action=_as_text(item.get("action")),
            selector_hint=_as_text(item.get("selector_hint")),
            requires_attendance=_as_bool(item.get("requires_attendance")),
            requires_exact_confirmation=_as_bool(item.get("requires_exact_confirmation")),
            source=_as_text(item.get("source")) or "redacted_manifest",
        )

    @property
    def signature(self) -> str:
        identity = self.key or self.label
        return "|".join(
            [_norm(identity), _norm(self.control_type), _norm(self.action)]
        )

    @property
    def is_consequential(self) -> bool:
        haystack = " ".join([self.key, self.label, self.control_type, self.action]).lower()
        return any(word in haystack for word in CONSEQUENTIAL_ACTION_WORDS)

    @property
    def is_uncertain(self) -> bool:
        haystack = " ".join([self.key, self.label, self.control_type, self.action]).lower()
        return any(word in haystack for word in UNCERTAIN_WORDS) or not (self.key or self.label)


@dataclass(frozen=True)
class DriftFinding:
    status: str
    reason: str
    control_key: str
    label: str
    action: str


@dataclass(frozen=True)
class DriftReport:
    status: str
    findings: tuple[DriftFinding, ...]

    @property
    def blocked(self) -> bool:
        return self.status == SurfaceDriftStatus.BLOCKED

    @property
    def requires_attended_review(self) -> bool:
        return self.status in {
            SurfaceDriftStatus.ATTENDED_REVIEW,
            SurfaceDriftStatus.BLOCKED,
        }


def load_surface_manifest(path: str | Path) -> tuple[SurfaceControl, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return controls_from_manifest(data)


def controls_from_manifest(manifest: object) -> tuple[SurfaceControl, ...]:
    if isinstance(manifest, Mapping):
        controls = manifest.get("controls", ())
    else:
        controls = manifest

    if not isinstance(controls, Sequence) or isinstance(controls, (str, bytes)):
        raise TypeError("DevHub surface manifest must be a list or an object with controls")

    parsed: list[SurfaceControl] = []
    for item in controls:
        if not isinstance(item, Mapping):
            raise TypeError("Each DevHub surface control must be an object")
        parsed.append(SurfaceControl.from_mapping(item))
    return tuple(parsed)


def classify_surface_drift(
    baseline: Iterable[SurfaceControl | Mapping[str, object]],
    observed: Iterable[SurfaceControl | Mapping[str, object]],
) -> DriftReport:
    baseline_controls = _coerce_controls(baseline)
    observed_controls = _coerce_controls(observed)
    baseline_signatures = {control.signature for control in baseline_controls}

    findings: list[DriftFinding] = []
    for control in observed_controls:
        if control.signature not in baseline_signatures:
            if control.is_uncertain:
                findings.append(_finding(SurfaceDriftStatus.BLOCKED, "uncertain_new_control", control))
            elif control.is_consequential:
                findings.append(_finding(SurfaceDriftStatus.BLOCKED, "new_consequential_control", control))
            else:
                findings.append(_finding(SurfaceDriftStatus.ATTENDED_REVIEW, "new_control", control))
            continue

        if control.requires_attendance or control.requires_exact_confirmation or control.is_consequential:
            findings.append(
                _finding(
                    SurfaceDriftStatus.ATTENDED_REVIEW,
                    "known_control_requires_attended_review",
                    control,
                )
            )

    if any(finding.status == SurfaceDriftStatus.BLOCKED for finding in findings):
        status = SurfaceDriftStatus.BLOCKED
    elif findings:
        status = SurfaceDriftStatus.ATTENDED_REVIEW
    else:
        status = SurfaceDriftStatus.PASS

    return DriftReport(status=status, findings=tuple(findings))


def _coerce_controls(
    controls: Iterable[SurfaceControl | Mapping[str, object]],
) -> tuple[SurfaceControl, ...]:
    parsed: list[SurfaceControl] = []
    for control in controls:
        if isinstance(control, SurfaceControl):
            parsed.append(control)
        elif isinstance(control, Mapping):
            parsed.append(SurfaceControl.from_mapping(control))
        else:
            raise TypeError("Surface controls must be SurfaceControl objects or mappings")
    return tuple(parsed)


def _finding(status: str, reason: str, control: SurfaceControl) -> DriftFinding:
    return DriftFinding(
        status=status,
        reason=reason,
        control_key=control.key,
        label=control.label,
        action=control.action,
    )


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
