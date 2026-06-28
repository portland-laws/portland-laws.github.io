"""Fixture-only compliance coverage for PP&D Single PDF preparation rules."""

import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "file_preparation"
    / "single_pdf_supporting_documents_case.json"
)


def _slug(value):
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _matching_rule(rules, declared_document_type):
    for rule in rules:
        if declared_document_type in rule["input_types"]:
            return rule
    raise AssertionError("No rule matched document type: " + declared_document_type)


def _normalize_file_preparation(fixture):
    rules = fixture["required_document_rules"]
    grouped_documents = {}
    missing_questions = []
    upload_staging_considered = False

    for document in fixture["raw_documents"]:
        rule = _matching_rule(rules, document["declared_document_type"])
        normalized_type = rule["normalized_document_type"]
        filename = document.get("filename")
        suffix = Path(filename).suffix.lower() if filename else ""
        is_pdf = suffix == ".pdf"

        if not document.get("provided"):
            missing_questions.append(
                {
                    "question_id": "missing_" + normalized_type,
                    "normalized_document_type": normalized_type,
                    "prompt": "Please provide the "
                    + normalized_type.replace("_", " ")
                    + " as a PDF before upload staging can be evaluated.",
                }
            )
            continue

        if rule["requires_pdf"] and not is_pdf:
            missing_questions.append(
                {
                    "question_id": "non_pdf_"
                    + normalized_type
                    + "_"
                    + _slug(Path(filename).stem),
                    "normalized_document_type": normalized_type,
                    "prompt": "Please provide "
                    + filename
                    + " as a PDF before upload staging can be evaluated.",
                }
            )
            continue

        grouping = rule["upload_grouping"]
        if grouping == "combine_all_matching_documents_into_one_pdf":
            upload_name = "DrawingPlanSet_123Main_2026-05-14.pdf"
            grouped_documents.setdefault(
                normalized_type,
                {
                    "normalized_document_type": normalized_type,
                    "upload_grouping": grouping,
                    "requires_pdf": rule["requires_pdf"],
                    "source_evidence_ids": rule["source_evidence_ids"],
                    "filename_evidence": [],
                    "planned_upload_filename": upload_name,
                },
            )["filename_evidence"].append(filename)
        else:
            grouped_documents[normalized_type] = {
                "normalized_document_type": normalized_type,
                "upload_grouping": grouping,
                "requires_pdf": rule["requires_pdf"],
                "source_evidence_ids": rule["source_evidence_ids"],
                "filename_evidence": [filename],
                "planned_upload_filename": filename,
            }

    if not missing_questions:
        upload_staging_considered = True

    return {
        "normalized_documents": list(grouped_documents.values()),
        "missing_questions": missing_questions,
        "upload_staging_considered": upload_staging_considered,
    }


def test_single_pdf_file_preparation_is_normalized_before_upload_staging():
    fixture = _load_fixture()
    normalized = _normalize_file_preparation(fixture)

    expected_questions = fixture["expected_missing_questions"]
    assert normalized["missing_questions"] == expected_questions
    assert normalized["upload_staging_considered"] is False

    order = fixture["normalization_order"]
    assert order.index("normalize_missing_document_questions") < order.index(
        "consider_upload_staging"
    )


def test_drawing_plans_are_grouped_but_application_and_calculations_stay_separate():
    fixture = _load_fixture()
    normalized = _normalize_file_preparation(fixture)
    documents_by_type = {
        document["normalized_document_type"]: document
        for document in normalized["normalized_documents"]
    }

    drawing_set = documents_by_type["drawing_plan_set"]
    assert drawing_set["upload_grouping"] == "combine_all_matching_documents_into_one_pdf"
    assert drawing_set["planned_upload_filename"].endswith(".pdf")
    assert drawing_set["filename_evidence"] == [
        "A0_CoverSheet_123Main_2026-05-14.pdf",
        "A1_SitePlan_123Main_2026-05-14.pdf",
    ]

    application = documents_by_type["permit_application"]
    calculations = documents_by_type["calculations"]
    assert application["upload_grouping"] == "separate_pdf"
    assert calculations["upload_grouping"] == "separate_pdf"
    assert application["planned_upload_filename"] == "BuildingPermitApplication_123Main_2026-05-14.pdf"
    assert calculations["planned_upload_filename"] == "StructuralCalculations_123Main_2026-05-14.pdf"


def test_pdf_requirements_and_filename_evidence_are_source_cited():
    fixture = _load_fixture()
    normalized = _normalize_file_preparation(fixture)
    evidence_ids = {evidence["evidence_id"] for evidence in fixture["source_evidence"]}

    for document in normalized["normalized_documents"]:
        assert document["requires_pdf"] is True
        assert document["filename_evidence"]
        assert all(filename.endswith(".pdf") for filename in document["filename_evidence"])
        assert set(document["source_evidence_ids"]).issubset(evidence_ids)
        assert "single_pdf_guidance_drawings_001" in document["source_evidence_ids"]
        assert "file_standards_pdf_001" in document["source_evidence_ids"]

    for rule in fixture["required_document_rules"]:
        assert rule["requires_pdf"] is True
        assert set(rule["source_evidence_ids"]).issubset(evidence_ids)
