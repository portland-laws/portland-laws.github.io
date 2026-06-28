import json
import re
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf_draft_preview"
    / "local_pdf_draft_preview.json"
)

PRIVATE_PATH_PATTERNS = [
    re.compile(r"/home/[^\s]+"),
    re.compile(r"/Users/[^\s]+"),
    re.compile(r"[A-Za-z]:\\\\[^\s]+"),
    re.compile(r"file://"),
]

REDACTION_PATTERN = re.compile(r"^\[REDACTED:[A-Z_]+\]$")
CONSEQUENTIAL_ACTION_TERMS = ("sign", "certif", "upload", "submit")


def _load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def test_local_pdf_preview_fixture_is_offline_and_fixture_only():
    preview = _load_fixture()

    assert preview["preview_kind"] == "local_pdf_draft_preview"
    assert preview["generated_from"] == {
        "fixture_only": True,
        "live_crawl": False,
        "authenticated_session": False,
        "downloaded_document": False,
    }


def test_field_mappings_cite_source_evidence_and_user_facts():
    preview = _load_fixture()
    evidence_ids = {item["evidence_id"] for item in preview["source_evidence"]}
    fact_ids = {item["fact_id"] for item in preview["known_user_facts"]}

    assert preview["field_mappings"]
    for mapping in preview["field_mappings"]:
        assert mapping["source_evidence_ids"]
        assert mapping["user_fact_ids"]
        assert set(mapping["source_evidence_ids"]).issubset(evidence_ids)
        assert set(mapping["user_fact_ids"]).issubset(fact_ids)


def test_preview_omits_local_private_file_paths():
    preview = _load_fixture()

    for string_value in _walk_strings(preview):
        assert not any(pattern.search(string_value) for pattern in PRIVATE_PATH_PATTERNS)

    assert preview["privacy_controls"]["omits_local_private_file_paths"] is True


def test_preview_redacts_sensitive_values():
    preview = _load_fixture()
    sensitive_fact_ids = {
        fact["fact_id"]
        for fact in preview["known_user_facts"]
        if fact["sensitivity"] != "ordinary"
    }

    assert sensitive_fact_ids
    for fact in preview["known_user_facts"]:
        if fact["fact_id"] in sensitive_fact_ids:
            assert REDACTION_PATTERN.match(fact["value"])

    for mapping in preview["field_mappings"]:
        if set(mapping["user_fact_ids"]) & sensitive_fact_ids:
            assert REDACTION_PATTERN.match(mapping["draft_value"])
            assert mapping["mapping_status"] == "redacted_for_preview"

    assert preview["privacy_controls"]["redacts_sensitive_values"] is True


def test_preview_surfaces_missing_facts_without_mapping_them_as_complete():
    preview = _load_fixture()
    missing_fact_ids = {fact["fact_id"] for fact in preview["missing_facts"]}
    mapped_fact_ids = {
        fact_id
        for mapping in preview["field_mappings"]
        for fact_id in mapping["user_fact_ids"]
    }
    evidence_ids = {item["evidence_id"] for item in preview["source_evidence"]}

    assert missing_fact_ids
    assert missing_fact_ids.isdisjoint(mapped_fact_ids)
    for missing_fact in preview["missing_facts"]:
        assert missing_fact["label"]
        assert missing_fact["reason"]
        assert set(missing_fact["source_evidence_ids"]).issubset(evidence_ids)


def test_preview_stops_before_signatures_certifications_uploads_or_submission():
    preview = _load_fixture()
    allowed_actions = preview["allowed_actions"]
    blocked_actions = preview["blocked_actions"]

    assert allowed_actions == [
        {
            "action": "render_local_pdf_draft_preview",
            "status": "allowed",
            "requires_user_confirmation": False,
        }
    ]

    blocked_action_names = {action["action"] for action in blocked_actions}
    for term in CONSEQUENTIAL_ACTION_TERMS:
        assert any(term in action_name for action_name in blocked_action_names)

    for action in blocked_actions:
        assert action["status"] == "blocked"
        assert action["reason"]

    assert preview["privacy_controls"]["stores_credentials"] is False
    assert preview["privacy_controls"]["stores_session_state"] is False
    assert preview["privacy_controls"]["stores_payment_details"] is False
