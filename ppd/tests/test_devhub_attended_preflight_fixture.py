import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub_attended_preflight" / "manual_handoffs.json"
REQUIRED_HANDOFF_STATES = {"login", "mfa", "captcha", "account_creation"}
PRIVATE_ARTIFACT_MARKERS = (
    "storage_state",
    "storageState",
    "auth-state",
    "cookies",
    "tokens",
    "trace.zip",
    ".har",
    "screenshot",
    "raw_crawl",
)


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def walk_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_values(item)
    elif isinstance(value, str):
        yield value


def test_devhub_preflight_fixture_declares_required_manual_handoffs():
    fixture = load_fixture()
    states = {state["state_id"]: state for state in fixture["manual_handoff_states"]}

    assert REQUIRED_HANDOFF_STATES.issubset(states.keys())

    for state_id in REQUIRED_HANDOFF_STATES:
        state = states[state_id]
        assert state["automation_policy"] == "manual_handoff"
        assert state["requires_user_attendance"] is True
        assert state["may_store_authenticated_browser_state"] is False
        assert state["allowed_committed_artifacts"] == ["redacted_attended_preflight_event"]
        assert state["blocked_automation"]
        assert "manual" in state["handoff_message"].lower()


def test_authenticated_browser_state_is_never_commit_safe():
    fixture = load_fixture()
    browser_state = fixture["authenticated_browser_state"]

    assert browser_state["commit_policy"] == "never_commit"
    assert browser_state["storage_state_path"] is None
    assert browser_state["trace_path"] is None
    assert browser_state["har_path"] is None
    assert browser_state["screenshot_path"] is None
    assert browser_state["raw_crawl_output_path"] is None
    assert browser_state["downloaded_document_path"] is None
    assert browser_state["redaction_required_before_any_journal_event"] is True

    for artifact in browser_state["prohibited_committed_artifacts"]:
        assert artifact["commit_safe"] is False
        assert artifact["example_names"]

    assert fixture["expected_preflight_outcome"]["authenticated_state_commit_attempt"] == "refuse"


def test_committed_fixture_inventory_contains_no_private_devhub_artifacts():
    fixture = load_fixture()

    for fixture_path in fixture["committed_fixture_paths"]:
        assert fixture_path.startswith("ppd/tests/fixtures/devhub_attended_preflight/")

    for artifact in fixture["artifact_inventory"]:
        assert artifact["commit_safe"] is True
        assert artifact["contains_credentials"] is False
        assert artifact["contains_cookies"] is False
        assert artifact["contains_tokens"] is False
        assert artifact["contains_authenticated_browser_state"] is False
        assert artifact["contains_private_devhub_values"] is False
        assert artifact["contains_screenshots"] is False
        assert artifact["contains_traces"] is False
        assert artifact["contains_har"] is False
        assert artifact["contains_raw_crawl_output"] is False


def test_fixture_does_not_point_to_committed_runtime_artifacts():
    fixture = load_fixture()
    committed_paths = "\n".join(fixture["committed_fixture_paths"])

    for marker in PRIVATE_ARTIFACT_MARKERS:
        assert marker not in committed_paths

    for value in walk_values(fixture):
        if isinstance(value, str) and value.startswith("ppd/"):
            assert value.startswith("ppd/tests/fixtures/")
