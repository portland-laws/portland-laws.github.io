from pathlib import Path

from ppd.post_release_audit_findings import build_packet_from_fixture_paths


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_release_audit"


def test_post_release_audit_findings_packet_is_fixture_first() -> None:
    packet = build_packet_from_fixture_paths(
        FIXTURE_DIR / "seed_packet.json",
        FIXTURE_DIR / "safe_next_action_checklist.json",
    )

    assert packet["packet_type"] == "post_release_audit_findings_packet"
    assert packet["generated_from"] == {
        "seed_packet_id": "post-release-audit-seed-20260528",
        "handoff_checklist_id": "safe-next-action-handoff-20260528",
    }
    assert packet["live_action_attestations"] == {
        "crawls_started": False,
        "devhub_launched": False,
        "llm_called": False,
        "private_files_read": False,
        "captcha_or_mfa_automated": False,
        "submissions_or_uploads_performed": False,
    }


def test_findings_include_cited_ids_severity_owners_blockers_and_follow_up() -> None:
    packet = build_packet_from_fixture_paths(
        FIXTURE_DIR / "seed_packet.json",
        FIXTURE_DIR / "safe_next_action_checklist.json",
    )

    findings = packet["findings"]
    assert [finding["finding_id"] for finding in findings] == ["PPAF-001", "PPAF-002"]
    assert findings[0]["severity"] == "high"
    assert findings[0]["reviewer_owner"] == "records-reviewer"
    assert findings[0]["citation_refs"] == ["seed:release-note:claim-4", "checklist:safe-next-action-001"]
    assert findings[0]["unresolved_blocker_refs"] == ["blocker:citation-required-before-publication"]
    assert findings[0]["recommended_daemon_follow_up_category"] == "reviewer-owned-remediation"
    assert findings[1]["recommended_daemon_follow_up_category"] == "scheduled-daemon-follow-up"
    assert packet["unresolved_blockers"] == [
        {
            "finding_id": "PPAF-001",
            "blocker_ref": "blocker:citation-required-before-publication",
            "reviewer_owner": "records-reviewer",
        }
    ]
    assert packet["recommended_daemon_follow_up_categories"] == [
        "reviewer-owned-remediation",
        "scheduled-daemon-follow-up",
    ]
