"""Deterministic fixture rows for public recrawl preflight queue v7 tests."""

VALID_PUBLIC_RECRAWL_PREFLIGHT_QUEUE_V7 = [
    {
        "queue_id": "public-recrawl-preflight-v7-001",
        "source_id": "ppd-online-tools-overview",
        "requested_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
        "canonical_url": "https://www.portland.gov/ppd/how-use-online-permitting-tools",
        "authorization_packet_ref": "ppd/tests/fixtures/public_recrawl_preflight_queue_v7/authorization_packet.json",
        "allowlist_fixture_ref": "ppd/tests/fixtures/public_recrawl_preflight_queue_v7/allowlist.json",
        "robots_policy_fixture_ref": "ppd/tests/fixtures/public_recrawl_preflight_queue_v7/robots_policy.json",
        "canonical_url_queue_row_ref": "ppd-public-canonical-url-row-001",
        "redirect_expectation_ref": "ppd-public-redirect-placeholder-001",
        "skip_reason_row_ref": "ppd-public-skip-reason-none-001",
        "host_policy_decision_ref": "ppd-public-host-policy-allow-001",
        "rate_limit_reminder_ref": "ppd-public-rate-limit-reminder-001",
        "processor_handoff_eligibility_note": "Eligible only after validation passes; metadata handoff only; no live crawl executed.",
        "execution_status": "preflight_only",
        "validation_commands": [
            ["python3", "-m", "pytest", "ppd/tests/test_public_recrawl_preflight_queue_v7.py"]
        ],
        "active_mutation": False,
    }
]
