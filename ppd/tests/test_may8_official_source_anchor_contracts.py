import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "may8_official_source_anchor_contracts.json"


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_has_may8_public_source_contracts():
    data = load_fixture()

    assert data["fixture_id"] == "may8_official_source_anchor_contracts"
    assert data["fixture_date"] == "2026-05-08"
    assert data["jurisdiction"] == "portland_or_ppd"
    assert data["sources"]

    source_types = {source["source_type"] for source in data["sources"]}
    assert {"html", "pdf"}.issubset(source_types)

    for source in data["sources"]:
        assert source["official_url"].startswith("https://www.portland.gov/")
        assert source["retrieved_anchor_date"] == "2026-05-08"
        assert "expected_contract" in source


def test_html_sources_contract_heading_steps_and_tables():
    data = load_fixture()
    html_sources = [source for source in data["sources"] if source["source_type"] == "html"]

    assert html_sources
    assert any(source["expected_contract"].get("tables") for source in html_sources)

    for source in html_sources:
        contract = source["expected_contract"]
        headings = contract["heading_hierarchy"]
        steps = contract["ordered_steps"]

        assert headings[0]["level"] == 1
        assert all(isinstance(item["level"], int) for item in headings)
        assert all(item["text"] for item in headings)
        assert [step["position"] for step in steps] == list(range(1, len(steps) + 1))
        assert all(step["text"] for step in steps)

        for table in contract.get("tables", []):
            assert table["headers"]
            assert table["rows"]
            assert all(len(row) == len(table["headers"]) for row in table["rows"])


def test_pdf_source_contract_page_anchors_and_public_form_fields():
    data = load_fixture()
    pdf_sources = [source for source in data["sources"] if source["source_type"] == "pdf"]

    assert pdf_sources

    for source in pdf_sources:
        contract = source["expected_contract"]
        page_anchors = contract["pdf_page_anchors"]
        field_manifest = contract["public_form_field_manifest"]

        assert page_anchors
        assert field_manifest
        assert all(anchor["page"] >= 1 for anchor in page_anchors)
        assert all(anchor["anchor_id"] for anchor in page_anchors)
        assert all(anchor["label"] for anchor in page_anchors)

        for field in field_manifest:
            assert field["name"]
            assert field["field_type"] in {"checkbox", "date", "email", "number", "select", "text", "textarea"}
            assert isinstance(field["required"], bool)
            assert field["page"] >= 1
