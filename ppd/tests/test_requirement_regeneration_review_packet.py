from __future__ import annotations

from ppd.validation.requirement_regeneration_review_packet import validate_requirement_regeneration_review_packet


def _valid_packet() -> dict:
    return {
        "human_review": {"required": True, "queue": "ppd-requirement-review"},
        "requirement_changes": [
            {
                "id": "req-001",
                "action": "update",
                "target": "draft requirement",
                "old_confidence": "low",
                "new_confidence": "medium",
                "citations": ["sanitized-evidence:chapter-33-001"],
                "confidence_support": "Citation confirms the regenerated requirement text.",
            }
        ],
    }


def _codes(packet: dict) -> set[str]:
    return {error.code for error in validate_requirement_regeneration_review_packet(packet).errors}


def test_accepts_cited_human_routed_packet() -> None:
    result = validate_requirement_regeneration_review_packet(_valid_packet())
    assert result.ok
    assert result.errors == ()


def test_rejects_uncited_requirement_change() -> None:
    packet = _valid_packet()
    packet["requirement_changes"][0].pop("citations")
    assert "uncited_requirement_change" in _codes(packet)


def test_rejects_unsupported_confidence_escalation() -> None:
    packet = _valid_packet()
    packet["requirement_changes"][0].pop("confidence_support")
    assert "unsupported_confidence_escalation" in _codes(packet)


def test_rejects_missing_human_review_routing() -> None:
    packet = _valid_packet()
    packet.pop("human_review")
    assert "missing_human_review_routing" in _codes(packet)


def test_rejects_private_values() -> None:
    packet = _valid_packet()
    packet["metadata"] = {"session_token": "Bearer abcdefghijklmnop"}
    assert "private_value" in _codes(packet)


def test_rejects_raw_crawl_artifacts() -> None:
    packet = _valid_packet()
    packet["raw_html"] = "unsanitized crawl output"
    assert "raw_crawl_artifact" in _codes(packet)


def test_rejects_direct_production_guardrail_replacement() -> None:
    packet = _valid_packet()
    packet["requirement_changes"].append(
        {
            "id": "guardrail-001",
            "kind": "production guardrail",
            "target": "production guardrail",
            "action": "replace",
            "citations": ["sanitized-evidence:guardrail-review"],
        }
    )
    assert "direct_production_guardrail_replacement" in _codes(packet)
