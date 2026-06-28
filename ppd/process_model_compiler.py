"""Deterministic fixture compiler for archived PP&D requirement sets.

This module intentionally keeps the first process-model compiler small: it maps
already-normalized archived requirement fixtures into the process model contract
used by validation tests. Live crawling and document extraction should feed this
shape rather than changing the compiler to depend on network state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def compile_archived_requirement_set(requirement_set: dict[str, Any]) -> dict[str, Any]:
    """Compile one archived PP&D requirement set into a process model."""
    source_archive = requirement_set["source_archive"]
    requirements = requirement_set.get("requirements", [])

    eligibility_rules: list[dict[str, Any]] = []
    required_user_facts: list[dict[str, Any]] = []
    required_documents: list[dict[str, Any]] = []
    file_rules: list[dict[str, Any]] = []
    fees: list[dict[str, Any]] = []
    stages: list[dict[str, Any]] = []
    unsupported_paths: list[dict[str, Any]] = []
    guardrail_bundle_refs: list[str] = []

    for requirement in requirements:
        requirement_id = requirement["id"]

        for item in requirement.get("eligibility_rules", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            eligibility_rules.append(mapped)

        for item in requirement.get("required_user_facts", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            required_user_facts.append(mapped)

        for item in requirement.get("required_documents", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            required_documents.append(mapped)

        for item in requirement.get("file_rules", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            file_rules.append(mapped)

        for item in requirement.get("fees", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            fees.append(mapped)

        for item in requirement.get("stages", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            stages.append(mapped)

        for item in requirement.get("unsupported_paths", []):
            mapped = deepcopy(item)
            mapped.setdefault("requirement_id", requirement_id)
            unsupported_paths.append(mapped)

        guardrail_bundle_refs.extend(requirement.get("guardrail_bundle_refs", []))

    return {
        "process_model_id": requirement_set["process_model_id"],
        "jurisdiction": requirement_set["jurisdiction"],
        "agency": requirement_set["agency"],
        "source_archive": deepcopy(source_archive),
        "compiled_from_requirement_ids": [item["id"] for item in requirements],
        "eligibility_rules": eligibility_rules,
        "required_user_facts": required_user_facts,
        "required_documents": required_documents,
        "file_rules": file_rules,
        "fees": fees,
        "stages": stages,
        "unsupported_paths": unsupported_paths,
        "guardrail_bundle_refs": sorted(set(guardrail_bundle_refs)),
    }
