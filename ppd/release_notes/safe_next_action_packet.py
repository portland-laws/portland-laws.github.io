"""Build fixture-first PP&D safe-next-action release note packets.

This module is intentionally offline-only. It accepts already-sanitized fixture
metadata and produces a deterministic packet for agent handoff/release notes.
It does not call an LLM, launch DevHub, crawl public sites, or read private
session files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_INPUT_KEYS = (
    "public_crawl_metadata_dry_run",
    "requirement_regeneration_promotion_decision",
    "devhub_surface_registry_update_candidate",
    "agent_handoff_transcript_expectation_matrix",
)

DISABLED_LIVE_ACTIONS = (
    "live_public_crawl",
    "devhub_launch",
    "authenticated_devhub_session",
    "private_file_read",
    "llm_release_note_generation",
    "document_download",
    "form_submission",
)

ROLLBACK_REFERENCES = (
    "Remove the generated packet fixture and keep the previous PP&D fixture set.",
    "Do not promote regenerated requirements until the offline intake cites pass validation.",
    "Keep DevHub surface registry changes as candidates until a human approves live verification.",
)


def load_packet_input(path: Path) -> dict[str, Any]:
    """Load sanitized packet input from a fixture path."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("safe-next-action packet input must be a JSON object")
    return data


def build_safe_next_action_packet(data: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic release notes packet from sanitized fixtures."""
    missing = [key for key in REQUIRED_INPUT_KEYS if key not in data]
    if missing:
        raise ValueError("missing safe-next-action input keys: " + ", ".join(missing))

    crawl = _mapping(data["public_crawl_metadata_dry_run"], "public_crawl_metadata_dry_run")
    promotion = _mapping(
        data["requirement_regeneration_promotion_decision"],
        "requirement_regeneration_promotion_decision",
    )
    registry = _mapping(
        data["devhub_surface_registry_update_candidate"],
        "devhub_surface_registry_update_candidate",
    )
    matrix = _mapping(
        data["agent_handoff_transcript_expectation_matrix"],
        "agent_handoff_transcript_expectation_matrix",
    )

    return {
        "packet_type": "ppd.safe_next_action.release_notes",
        "mode": "fixture_first_offline_only",
        "offline_only_capabilities": [
            _capability(
                "public_crawl_metadata_dry_run_intake",
                "Summarize public crawl metadata dry-run counts and warnings from committed fixtures.",
                crawl,
            ),
            _capability(
                "requirement_regeneration_promotion_decision",
                "Report whether regenerated requirements remain blocked or are ready for fixture promotion.",
                promotion,
            ),
            _capability(
                "devhub_surface_registry_update_candidate",
                "Describe candidate DevHub surface registry updates without launching DevHub.",
                registry,
            ),
            _capability(
                "agent_handoff_transcript_expectation_matrix",
                "List transcript expectations that a future agent must satisfy before live work resumes.",
                matrix,
            ),
        ],
        "remaining_blockers": _as_list(promotion.get("remaining_blockers"))
        + _as_list(crawl.get("warnings"))
        + _as_list(matrix.get("unmet_expectations")),
        "disabled_live_actions": list(DISABLED_LIVE_ACTIONS),
        "user_facing_escalation_prompts": _escalation_prompts(promotion, registry, matrix),
        "rollback_references": list(ROLLBACK_REFERENCES),
        "next_daemon_work": _next_daemon_work(crawl, promotion, registry, matrix),
        "citations": _citations(crawl, promotion, registry, matrix),
    }


def packet_from_fixture(input_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    """Build a packet from a fixture, optionally writing deterministic JSON."""
    packet = build_safe_next_action_packet(load_packet_input(input_path))
    if output_path is not None:
        output_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _capability(name: str, description: str, source: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "citation": _citation(source),
    }


def _citation(source: dict[str, Any]) -> str:
    citation = source.get("citation") or source.get("source_id") or source.get("fixture")
    if not isinstance(citation, str) or not citation.strip():
        raise ValueError("each packet input source must include citation, source_id, or fixture")
    return citation.strip()


def _citations(*sources: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for source in sources:
        citation = _citation(source)
        if citation not in seen:
            ordered.append(citation)
            seen.add(citation)
    return ordered


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    raise ValueError("expected blocker/warning fields to be strings or string arrays")


def _escalation_prompts(
    promotion: dict[str, Any],
    registry: dict[str, Any],
    matrix: dict[str, Any],
) -> list[str]:
    prompts = _as_list(promotion.get("escalation_prompts"))
    prompts.extend(_as_list(registry.get("escalation_prompts")))
    prompts.extend(_as_list(matrix.get("escalation_prompts")))
    if prompts:
        return prompts
    return [
        "Confirm whether offline fixture evidence is sufficient before enabling any live PP&D crawl or DevHub verification.",
        "Identify the human owner for approving registry promotion and requirement regeneration changes.",
    ]


def _next_daemon_work(
    crawl: dict[str, Any],
    promotion: dict[str, Any],
    registry: dict[str, Any],
    matrix: dict[str, Any],
) -> list[str]:
    work = []
    if crawl.get("ready_for_intake") is True:
        work.append("Promote public crawl dry-run metadata into the offline release packet fixture.")
    else:
        work.append("Keep public crawl metadata in dry-run intake until cited warnings are resolved.")

    if promotion.get("promote") is True:
        work.append("Stage requirement regeneration promotion behind fixture validation.")
    else:
        work.append("Leave regenerated requirements unpromoted and record blockers in the release packet.")

    if registry.get("candidate_ready") is True:
        work.append("Queue DevHub surface registry candidate for human review without launching DevHub.")
    else:
        work.append("Refresh DevHub surface registry candidate fixtures before live verification is considered.")

    if matrix.get("expectations_satisfied") is True:
        work.append("Attach the handoff transcript expectation matrix to the next daemon handoff.")
    else:
        work.append("Resolve unmet handoff transcript expectations before re-enabling live automation.")
    return work
