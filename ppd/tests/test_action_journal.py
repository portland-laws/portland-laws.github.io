from __future__ import annotations

import pytest

from ppd.action_journal import ActionJournalValidationError, sanitize_action_journal_event


def test_sanitize_action_journal_event_accepts_minimal_allowed_event() -> None:
    sanitized = sanitize_action_journal_event(
        {
            "event_type": "document_discovered",
            "source": "ppd-public-site",
            "message": "Found permit guide link.",
            "url": " https://www.portland.gov/ppd ",
            "metadata": {"status_code": 200, "reviewed": False},
        }
    )

    assert sanitized == {
        "event_type": "document_discovered",
        "source": "ppd-public-site",
        "message": "Found permit guide link.",
        "url": "https://www.portland.gov/ppd",
        "metadata": {"status_code": 200, "reviewed": False},
    }


@pytest.mark.parametrize(
    "event",
    [
        {
            "event_type": "downloaded_private_session",
            "source": "devhub",
            "message": "Unexpected event type must fail closed.",
        },
        {
            "event_type": "crawl_planned",
            "source": "devhub",
            "message": "Unknown top-level fields must fail closed.",
            "unexpected": "value",
        },
        {
            "event_type": "crawl_planned",
            "source": "devhub",
            "message": "Sensitive top-level fields must fail closed.",
            "token": "secret-token",
        },
        {
            "event_type": "crawl_planned",
            "source": "devhub",
            "message": "Sensitive nested metadata must fail closed.",
            "metadata": {"cookie": "private-cookie"},
        },
        {
            "event_type": "crawl_planned",
            "source": "devhub",
            "message": "Nested metadata structures are not journal-safe.",
            "metadata": {"raw": {"status": "ok"}},
        },
    ],
)
def test_sanitize_action_journal_event_rejects_unsafe_events(event: dict[str, object]) -> None:
    with pytest.raises(ActionJournalValidationError):
        sanitize_action_journal_event(event)
