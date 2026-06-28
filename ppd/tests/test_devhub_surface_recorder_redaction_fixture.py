import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_surface_recorder_redaction"
    / "surface_recorder_redaction_fixture.json"
)

ALLOWED_ACCESSIBILITY_KEYS = {
    "allowed_accessibility_metadata",
    "depth",
    "description",
    "disabled",
    "expanded",
    "focused",
    "lang",
    "level",
    "name",
    "nodes",
    "page",
    "path",
    "role",
    "selected",
    "states",
    "title",
    "url",
}

REJECTION_MARKERS = {
    "screenshots": ("screenshot", "image/png", "image/jpeg", "data:image", "pixels"),
    "browser_traces": ("playwright_trace", "browser_trace", "trace_archive", "trace.zip"),
    "har_data": ("network_har", "\"har\"", "\"log\"", "\"entries\""),
    "auth_state": ("auth_state", "storage_state", "localstorage", "sessionstorage"),
    "cookies": ("browser_cookies", "\"cookies\"", "set-cookie"),
    "credentials": ("credential", "authorization", "bearer", "token", "api_key", "password", "secret"),
    "private_values": ("private_value", "private_values", "applicant_email", "phone_number", "ssn"),
    "local_private_paths": ("/home/", "/users/", "c:\\\\users", "file://", ".config/browser"),
}

FORBIDDEN_ALLOWED_METADATA_MARKERS = tuple(
    marker
    for reason, markers in REJECTION_MARKERS.items()
    if reason != "private_values"
    for marker in markers
) + ("private_value", "applicant_email", "phone_number", "ssn")


def _load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _serialized(value):
    return json.dumps(value, sort_keys=True).lower()


class DevHubSurfaceRecorderRedactionFixtureTest(unittest.TestCase):
    def test_fixture_is_synthetic_and_scoped_to_devhub_surface_recorder(self):
        fixture = _load_fixture()

        self.assertEqual(
            fixture["fixture_id"], "devhub_surface_recorder_redaction_v1"
        )
        self.assertEqual(fixture["surface"]["captured_from"], "synthetic-fixture")
        self.assertEqual(
            fixture["surface"]["url"],
            "https://devhub.portland.gov/synthetic/permits",
        )
        self.assertNotIn("raw_crawl_output", fixture)
        self.assertNotIn("downloaded_documents", fixture)

    def test_allowed_accessibility_metadata_uses_only_public_structure_fields(self):
        fixture = _load_fixture()
        metadata = fixture["allowed_accessibility_metadata"]

        unexpected_keys = set(_walk_keys(metadata)) - ALLOWED_ACCESSIBILITY_KEYS
        self.assertEqual(unexpected_keys, set())

        serialized = _serialized(metadata)
        for marker in FORBIDDEN_ALLOWED_METADATA_MARKERS:
            self.assertNotIn(marker, serialized)

        roles = {node["role"] for node in metadata["nodes"]}
        self.assertGreaterEqual(
            roles,
            {"main", "heading", "searchbox", "button", "navigation"},
        )

    def test_negative_samples_are_rejected_for_expected_reason(self):
        fixture = _load_fixture()
        samples = fixture["negative_samples"]

        self.assertEqual(
            {sample["expected_reason"] for sample in samples},
            set(REJECTION_MARKERS),
        )

        for sample in samples:
            expected_reason = sample["expected_reason"]
            payload = _serialized(sample["payload"])
            markers = REJECTION_MARKERS[expected_reason]
            self.assertTrue(
                any(marker in payload for marker in markers),
                f"{expected_reason} sample did not contain its rejection marker",
            )

    def test_policy_lists_allowed_metadata_and_rejected_private_artifacts(self):
        fixture = _load_fixture()
        policy = fixture["redaction_policy"]

        self.assertIn("accessibility roles", policy["allow"])
        self.assertIn("accessible names for public controls", policy["allow"])
        for rejected in (
            "screenshots",
            "browser traces",
            "HAR data",
            "auth state",
            "cookies",
            "credentials",
            "private values",
            "local private paths",
        ):
            self.assertIn(rejected, policy["reject"])


if __name__ == "__main__":
    unittest.main()
