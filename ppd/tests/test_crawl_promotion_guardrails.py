from __future__ import annotations

from ppd.crawl_promotion_guardrails import validate_crawl_promotion_guardrails


def safe_summary() -> dict[str, object]:
    return {
        "robots_preflight": "allowed",
        "policy_preflight": "passed",
        "rate_limit_policy": {"enabled": True, "requests_per_minute": 12},
        "freshness_policy": {"is_stale": False},
        "host_expansion": {
            "allowed_hosts": ["www.portland.gov"],
            "expanded_hosts": ["www.portland.gov"],
            "unexpected_hosts": [],
            "over_broad": False,
        },
        "output_paths": ["ppd/tests/fixtures/crawl/promoted-normalized.json"],
    }


def test_all_safe_inputs_allow_promotion() -> None:
    verdict = validate_crawl_promotion_guardrails(safe_summary())

    assert verdict.allowed is True
    assert verdict.reasons == ()


def test_unknown_robots_or_policy_preflight_blocks_promotion() -> None:
    summary = safe_summary()
    summary["robots_preflight"] = "unknown"
    summary["policy_preflight"] = {"unknown": True}

    verdict = validate_crawl_promotion_guardrails(summary)

    assert verdict.allowed is False
    assert "robots_preflight_unknown" in verdict.reasons
    assert "policy_preflight_unknown" in verdict.reasons


def test_missing_rate_limit_policy_blocks_promotion() -> None:
    summary = safe_summary()
    summary["rate_limit_policy"] = None

    verdict = validate_crawl_promotion_guardrails(summary)

    assert verdict.allowed is False
    assert verdict.reasons == ("rate_limit_policy_missing",)


def test_stale_freshness_policy_blocks_promotion() -> None:
    summary = safe_summary()
    summary["freshness_policy"] = {"stale": True}

    verdict = validate_crawl_promotion_guardrails(summary)

    assert verdict.allowed is False
    assert verdict.reasons == ("freshness_policy_stale",)


def test_over_broad_host_expansion_blocks_promotion() -> None:
    summary = safe_summary()
    summary["host_expansion"] = {
        "allowed_hosts": ["www.portland.gov"],
        "expanded_hosts": ["www.portland.gov", "example.com"],
        "unexpected_hosts": ["example.com"],
    }

    verdict = validate_crawl_promotion_guardrails(summary)

    assert verdict.allowed is False
    assert verdict.reasons == ("host_expansion_over_broad",)


def test_raw_body_or_download_document_output_paths_block_promotion() -> None:
    summary = safe_summary()
    summary["output_paths"] = [
        "ppd/crawl/raw_bodies/page-1.html",
        "ppd/crawl/downloads/permit.pdf",
    ]

    verdict = validate_crawl_promotion_guardrails(summary)

    assert verdict.allowed is False
    assert verdict.reasons == ("raw_output_path_persistence",)
