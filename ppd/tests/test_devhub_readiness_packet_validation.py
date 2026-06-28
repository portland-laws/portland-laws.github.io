from __future__ import annotations

import unittest

from ppd.devhub.readiness_packet_validation import (
    assert_read_only_pilot_readiness_packet,
    validate_read_only_pilot_readiness_packet,
)


class DevHubReadinessPacketValidationTests(unittest.TestCase):
    def test_accepts_redacted_read_only_packet(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "mode": "read_only",
            "observations": [
                "Manual attended sign-in boundary was noted, but no login was automated.",
                "No official upload, submission, payment, scheduling, cancellation, or certification was completed.",
            ],
            "reconciliation": {
                "ready": True,
                "evidence": ["public DevHub guide citation", "redacted surface checklist"],
            },
            "redaction_attestation": {
                "attested": True,
                "scope": [
                    "screenshots",
                    "traces",
                    "HAR",
                    "cookies",
                    "auth state",
                    "private values",
                    "credentials",
                ],
                "statement": "I attest screenshots, traces, HAR, cookies, auth state, private values, and credentials are absent or redacted.",
            },
        }

        result = validate_read_only_pilot_readiness_packet(packet)

        self.assertTrue(result.ok, result.violations)
        assert_read_only_pilot_readiness_packet(packet)

    def test_rejects_browser_artifacts_and_sensitive_fields(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "screenshot_path": "fixtures/devhub/login.png",
            "trace": "run.trace.zip",
            "network": {"har": "devhub.har"},
            "cookies": [{"name": "session", "value": "private"}],
            "auth_state": {"storage": "private"},
            "redaction_attestation": _complete_attestation(),
        }

        result = validate_read_only_pilot_readiness_packet(packet)
        codes = {violation.code for violation in result.violations}

        self.assertFalse(result.ok)
        self.assertIn("prohibited_browser_artifact", codes)
        self.assertIn("prohibited_sensitive_field", codes)

    def test_rejects_credential_prompts_and_forbidden_automation_claims(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "notes": [
                "The worker prompted for password entry during the readiness run.",
                "The script completed MFA and solved CAPTCHA before it created account records.",
            ],
            "redaction_attestation": _complete_attestation(),
        }

        result = validate_read_only_pilot_readiness_packet(packet)
        codes = {violation.code for violation in result.violations}

        self.assertFalse(result.ok)
        self.assertIn("credential_prompt_claim", codes)
        self.assertIn("forbidden_automation_claim", codes)

    def test_rejects_consequential_and_official_action_completion_claims(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "outcome": "The pilot completed consequential action handling.",
            "claims": [
                "submitted application",
                "paid fees",
                "scheduled inspection",
                "cancelled permit",
                "signed certification",
                "uploaded documents",
            ],
            "redaction_attestation": _complete_attestation(),
        }

        result = validate_read_only_pilot_readiness_packet(packet)
        codes = {violation.code for violation in result.violations}

        self.assertFalse(result.ok)
        self.assertIn("consequential_completion_claim", codes)
        self.assertIn("official_action_completion_claim", codes)

    def test_rejects_missing_redaction_attestation(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "mode": "read_only",
            "observations": ["Read-only surface reconciliation only."],
        }

        result = validate_read_only_pilot_readiness_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn(
            "missing_redaction_attestation",
            {violation.code for violation in result.violations},
        )

    def test_rejects_incomplete_redaction_attestation(self) -> None:
        packet = {
            "pilot_id": "devhub-read-only-pilot",
            "mode": "read_only",
            "redaction_attestation": {
                "attested": True,
                "scope": ["screenshots", "traces"],
            },
        }

        result = validate_read_only_pilot_readiness_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn(
            "missing_redaction_attestation",
            {violation.code for violation in result.violations},
        )


def _complete_attestation() -> dict[str, object]:
    return {
        "attested": True,
        "scope": [
            "screenshots",
            "traces",
            "HAR",
            "cookies",
            "auth state",
            "private values",
            "credentials",
        ],
    }


if __name__ == "__main__":
    unittest.main()
