from __future__ import annotations

import pytest

from ppd.public_capture_validation import PublicCaptureValidationError, validate_fake_public_capture


def valid_payload() -> dict[str, object]:
    return {
        "source_id": "ppd-public-fees",
        "source_url": "https://www.portland.gov/ppd/fees",
        "status": "captured",
        "processor": {"name": "fake-public-capture", "version": "1"},
        "metadata": {"title": "Public PP&D fee page"},
    }


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"source_url": "https://localhost/private"}, "private host"),
        ({"source_url": "http://127.0.0.1/public"}, "private host"),
        ({"source_url": "file:///tmp/private.pdf"}, "http or https"),
        ({"source_url": "https://www.portland.gov/login/session"}, "authenticated URL path"),
        ({"source_id": ""}, "missing source_id"),
        ({"processor": {}}, "missing name"),
        ({"status": "skipped", "sha256": "abc123"}, "skipped captures"),
        ({"raw_body": "not committed"}, "raw body field"),
        ({"downloaded_pdf_path": "/tmp/ppd/file.pdf"}, "downloaded PDF path"),
        ({"metadata": {"source_path": "/home/user/private.pdf"}}, "local private path"),
    ],
)
def test_rejects_unsafe_fake_public_capture_fields(patch: dict[str, object], message: str) -> None:
    payload = valid_payload()
    payload.update(patch)

    with pytest.raises(PublicCaptureValidationError, match=message):
        validate_fake_public_capture(payload)


def test_accepts_public_metadata_only_capture() -> None:
    validate_fake_public_capture(valid_payload())
