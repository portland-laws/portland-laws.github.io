from ppd.extraction.requirement_review_queue import validate_review_queue_packet


def test_accepts_cited_review_owned_candidate() -> None:
    packet = {
        "source_registry": [
            {
                "source_id": "ppd-devhub-faq",
                "canonical_url": "https://www.portland.gov/ppd/devhub-faqs",
            }
        ],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-1",
                "requirement_text": "Applicants may need a DevHub account for online permitting services.",
                "citations": [
                    {
                        "source_id": "ppd-devhub-faq",
                        "canonical_url": "https://www.portland.gov/ppd/devhub-faqs#accounts",
                        "span_id": "accounts",
                    }
                ],
                "human_review_status": "needs_review",
                "formalization_status": "draft",
                "reviewer_owner": "ppd-requirements-review",
            }
        ],
    }

    assert validate_review_queue_packet(packet) == []


def test_rejects_uncited_requirement_candidate() -> None:
    packet = {
        "source_registry": ["ppd-apply-permits"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-uncited",
                "requirement_text": "A permit may be required.",
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "uncited_requirement_candidate" in codes


def test_rejects_unknown_source_id() -> None:
    packet = {
        "source_registry": ["ppd-known-source"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-unknown-source",
                "citations": [{"source_id": "ppd-missing-source"}],
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "unknown_source_id" in codes


def test_rejects_private_authenticated_and_tokenized_urls() -> None:
    packet = {
        "source_registry": ["devhub-private", "tokenized-public"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-private-url",
                "citations": [
                    {
                        "source_id": "devhub-private",
                        "url": "https://devhub.portlandoregon.gov/PermitDetails/12345",
                    },
                    {
                        "source_id": "tokenized-public",
                        "url": "https://www.portland.gov/ppd/devhub-faqs?token=secret",
                    },
                ],
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = [error.code for error in validate_review_queue_packet(packet)]

    assert codes.count("private_or_authenticated_url") >= 2


def test_rejects_raw_source_text_and_downloaded_document_references() -> None:
    packet = {
        "source_registry": ["ppd-source"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-raw-text",
                "citations": [{"source_id": "ppd-source"}],
                "raw_source_text": "Full copied page body must not be queued for review.",
                "downloaded_document_ref": "tmp/downloads/private-form.pdf",
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "raw_source_text_present" in codes
    assert "downloaded_document_reference" in codes


def test_rejects_live_extraction_claims() -> None:
    packet = {
        "source_registry": ["ppd-source"],
        "live_extraction_claim": True,
        "requirement_candidates": [
            {
                "requirement_id": "candidate-live",
                "citations": [{"source_id": "ppd-source"}],
                "browser_session_id": "session-123",
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = [error.code for error in validate_review_queue_packet(packet)]

    assert codes.count("live_extraction_claim") >= 2


def test_rejects_formalized_requirement_without_review_status() -> None:
    packet = {
        "source_registry": ["ppd-source"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-formalized",
                "citations": [{"source_id": "ppd-source"}],
                "formalization_status": "formalized",
                "reviewer_owner": "ppd-requirements-review",
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "formalized_without_review_status" in codes


def test_rejects_missing_reviewer_owner() -> None:
    packet = {
        "source_registry": ["ppd-source"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-no-owner",
                "citations": [{"source_id": "ppd-source"}],
                "human_review_status": "needs_review",
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "missing_reviewer_owner" in codes


def test_rejects_active_requirement_mutation_flags() -> None:
    packet = {
        "source_registry": ["ppd-source"],
        "requirement_candidates": [
            {
                "requirement_id": "candidate-mutating",
                "citations": [{"source_id": "ppd-source"}],
                "reviewer_owner": "ppd-requirements-review",
                "human_review_status": "needs_review",
                "mutation_flags": ["replace-active-requirement"],
            }
        ],
    }

    codes = {error.code for error in validate_review_queue_packet(packet)}

    assert "active_requirement_mutation_flag" in codes
