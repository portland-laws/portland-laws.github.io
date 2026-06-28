"""Offline release candidate bundle validation for PP&D artifacts.

The checks in this module are intentionally text based and deterministic. They are
meant to fail closed on release-candidate bundles that contain live-operation
signals, private/session artifacts, uncited readiness language, or enabled
high-risk capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Sequence


TEXT_EXTENSIONS = {
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".html",
}

CITATION_RE = re.compile(r"(https?://\S+|\[[A-Za-z0-9_.:/# -]+\])")
PREREQUISITE_RE = re.compile(r"\b(prerequisite|precondition|required before|depends on)\b", re.I)
READINESS_CLAIM_RE = re.compile(
    r"\b(ready|readiness|validated|verified|approved|certified|complete|compliant)\b",
    re.I,
)
ROLLBACK_RE = re.compile(r"\b(rollback|roll back|revert|restore previous|backout|back out)\b", re.I)
PRODUCTION_READY_RE = re.compile(r"\b(production[- ]ready|ready for production|prod[- ]ready|ship to production)\b", re.I)

PRIVATE_PATH_RE = re.compile(
    r"(^|[/_.-])(auth|cookie|cookies|credential|credentials|secret|secrets|session|storage_state|trace|har|devhub-session)([/_.-]|$)",
    re.I,
)
RAW_REFERENCE_RE = re.compile(
    r"\b(raw crawl|raw-crawl|crawl output|crawl-output|downloaded document|downloads/|archive dump|archive\.org|warc|wget\s|curl\s+-O|curl\s+--output)\b",
    re.I,
)
LIVE_EXECUTION_RE = re.compile(
    r"\b(--live|live_network\s*[:=]\s*true|network\s*[:=]\s*true|devhub_execute\s*[:=]\s*true|execute_devhub\s*[:=]\s*true|playwright\s+test|browser\s*[:=]\s*live)\b",
    re.I,
)
ENABLED_CAPABILITY_RE = re.compile(
    r"\b(payment|upload|submission|submit|scheduling|schedule|cancellation|cancel|certification|certify)\b[^\n]{0,80}\b(enabled|true|on|active|allowed)\b",
    re.I,
)
DISABLED_CAPABILITY_RE = re.compile(
    r"\b(payment|upload|submission|submit|scheduling|schedule|cancellation|cancel|certification|certify)\b[^\n]{0,80}\b(disabled|false|off|inactive|blocked|not allowed)\b",
    re.I,
)


@dataclass(frozen=True)
class BundleFinding:
    code: str
    path: str
    line: int
    message: str


def validate_release_candidate_bundle(bundle_root: str | Path) -> list[BundleFinding]:
    root = Path(bundle_root)
    findings: list[BundleFinding] = []

    if not root.exists():
        return [BundleFinding("bundle_missing", str(root), 0, "release candidate bundle path does not exist")]
    if not root.is_dir():
        return [BundleFinding("bundle_not_directory", str(root), 0, "release candidate bundle path must be a directory")]

    saw_rollback_reference = False

    for path in sorted(_iter_bundle_files(root)):
        rel_path = path.relative_to(root).as_posix()
        if PRIVATE_PATH_RE.search(rel_path):
            findings.append(BundleFinding("private_or_session_artifact", rel_path, 0, "private/session artifact paths are not allowed in offline release candidates"))
        if _looks_raw_artifact_path(rel_path):
            findings.append(BundleFinding("raw_artifact_path", rel_path, 0, "raw crawl/download/archive artifact paths are not allowed in offline release candidates"))
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = _read_text(path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if PREREQUISITE_RE.search(stripped) and not CITATION_RE.search(stripped):
                findings.append(BundleFinding("missing_prerequisite_link", rel_path, line_number, "prerequisite/precondition statements must include a URL or bracket citation"))
            if READINESS_CLAIM_RE.search(stripped) and not CITATION_RE.search(stripped):
                findings.append(BundleFinding("uncited_readiness_claim", rel_path, line_number, "readiness claims must be cited"))
            if RAW_REFERENCE_RE.search(stripped):
                findings.append(BundleFinding("raw_reference", rel_path, line_number, "raw crawl/download/archive references are not allowed"))
            if LIVE_EXECUTION_RE.search(stripped):
                findings.append(BundleFinding("live_execution_flag", rel_path, line_number, "live network or DevHub execution flags are not allowed"))
            if PRODUCTION_READY_RE.search(stripped):
                findings.append(BundleFinding("production_ready_label", rel_path, line_number, "production-ready labels are not allowed for offline PP&D release candidates"))
            if ENABLED_CAPABILITY_RE.search(stripped) and not DISABLED_CAPABILITY_RE.search(stripped):
                findings.append(BundleFinding("enabled_high_risk_capability", rel_path, line_number, "payment/upload/submission/scheduling/cancellation/certification capabilities must remain disabled"))
            if ROLLBACK_RE.search(stripped) and CITATION_RE.search(stripped):
                saw_rollback_reference = True

    if not saw_rollback_reference:
        findings.append(BundleFinding("missing_rollback_reference", ".", 0, "release candidate bundle must include a cited rollback reference"))

    return findings


def assert_release_candidate_bundle(bundle_root: str | Path) -> None:
    findings = validate_release_candidate_bundle(bundle_root)
    if findings:
        rendered = "\n".join(f"{f.code}: {f.path}:{f.line}: {f.message}" for f in findings)
        raise ValueError(rendered)


def _iter_bundle_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def _looks_raw_artifact_path(rel_path: str) -> bool:
    lowered = rel_path.lower()
    raw_tokens: Sequence[str] = (
        "/raw/",
        "raw_crawl",
        "raw-crawl",
        "/downloads/",
        "/downloaded/",
        "/archives/",
        "/archive/",
        ".warc",
        ".har",
    )
    return any(token in f"/{lowered}" for token in raw_tokens)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
