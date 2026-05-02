"""Prompt guardrail for repeated PP&D daemon rounds without accepted work."""

from __future__ import annotations

from typing import Any, Iterable


NO_ACCEPTED_PATCH_THRESHOLD = 4


FORBIDDEN_RETRY_ACTIONS = (
    "live DevHub sessions",
    "browser state",
    "screenshots",
    "traces",
    "uploads",
    "submissions",
    "payments",
    "MFA",
    "CAPTCHA",
    "cancellation",
    "certification",
    "inspection scheduling",
    "broad contract rewrites",
)


REQUIRED_RETRY_PHRASES = (
    "one narrow fixture-first file set",
    "complete JSON file replacements",
    "live DevHub sessions",
    "broad contract rewrites",
    "Do not implement the DevHub form-state domain test",
)


def proposal_was_accepted(proposal: dict[str, Any]) -> bool:
    return bool(proposal.get("applied")) and bool(proposal.get("validation_passed")) and not proposal.get("errors")


def proposal_had_no_accepted_patch(proposal: dict[str, Any]) -> bool:
    if proposal_was_accepted(proposal):
        return False
    changed_files = proposal.get("changed_files")
    files = proposal.get("files")
    if proposal.get("failure_kind") in {
        "llm",
        "parse",
        "empty_proposal",
        "no_change",
        "syntax_preflight",
        "validation",
        "preflight",
    }:
        return True
    if isinstance(changed_files, list) and not changed_files:
        return True
    if isinstance(files, list) and not files:
        return True
    return False


def count_consecutive_no_accepted_rounds(proposals: Iterable[dict[str, Any]]) -> int:
    count = 0
    for proposal in proposals:
        if proposal_was_accepted(proposal):
            break
        if not proposal_had_no_accepted_patch(proposal):
            break
        count += 1
    return count


def should_apply_repeated_no_patch_guardrail(
    count: int,
    threshold: int = NO_ACCEPTED_PATCH_THRESHOLD,
) -> bool:
    return count >= threshold


def build_repeated_no_patch_prompt_guidance(
    count: int,
    threshold: int = NO_ACCEPTED_PATCH_THRESHOLD,
) -> str:
    if not should_apply_repeated_no_patch_guardrail(count, threshold=threshold):
        return "No repeated no-accepted-patch guardrail is active."
    forbidden = ", ".join(FORBIDDEN_RETRY_ACTIONS)
    return (
        f"Guardrail active: {count} consecutive LLM rounds ended without an accepted patch. "
        "The next proposal must use one narrow fixture-first file set under ppd/daemon/ only, "
        "must provide complete JSON file replacements in the files array, and must not open or rely on "
        f"{forbidden}. "
        "Do not implement the DevHub form-state domain test in this retry; repair the daemon prompt or "
        "preflight guardrail only."
    )


def synthetic_repeated_no_patch_self_test() -> list[str]:
    errors: list[str] = []
    failed_round = {
        "applied": False,
        "validation_passed": False,
        "failure_kind": "syntax_preflight",
        "files": ["ppd/daemon/repeated_no_patch_guardrail.py"],
        "changed_files": [],
        "errors": ["py_compile failed"],
    }
    empty_round = {
        "applied": False,
        "validation_passed": False,
        "failure_kind": "empty_proposal",
        "files": [],
        "changed_files": [],
        "errors": ["LLM returned no files"],
    }
    accepted_round = {
        "applied": True,
        "validation_passed": True,
        "failure_kind": "",
        "files": ["ppd/daemon/ppd_daemon.py"],
        "changed_files": ["ppd/daemon/ppd_daemon.py"],
        "errors": [],
    }
    stopped_count = count_consecutive_no_accepted_rounds(
        [failed_round, empty_round, accepted_round, failed_round]
    )
    if stopped_count != 2:
        errors.append(
            f"repeated no-patch counter did not stop at accepted proposal: {stopped_count}"
        )
    active_count = count_consecutive_no_accepted_rounds(
        [failed_round, empty_round, failed_round, empty_round]
    )
    if active_count != 4:
        errors.append(f"expected four consecutive failed or empty rounds, got {active_count}")
    guidance = build_repeated_no_patch_prompt_guidance(active_count)
    for phrase in REQUIRED_RETRY_PHRASES:
        if phrase not in guidance:
            errors.append(f"repeated no-patch guidance missing phrase: {phrase}")
    inactive = build_repeated_no_patch_prompt_guidance(3)
    if "Guardrail active" in inactive:
        errors.append("repeated no-patch guidance activated before four failed or empty rounds")
    return errors


def main() -> int:
    errors = synthetic_repeated_no_patch_self_test()
    if errors:
        for error in errors:
            print(error)
        return 1
    print("repeated no-accepted-patch guardrail self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
