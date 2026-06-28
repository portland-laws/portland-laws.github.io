"""Synthetic PP&D processor-capability adapter.

This module records the ipfs_datasets_py processor capabilities PP&D plans to use
without importing those processors or writing crawl/archive payloads. It is a
commit-safe planning fixture for validating policy handoff behavior before live
captures are enabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


_CAPTURE_TYPES = ("html", "pdf", "warc", "metadata")


@dataclass(frozen=True)
class SyntheticProcessorCapability:
    """A deterministic record of one planned processor capability."""

    capture_type: str
    processor_family: str
    capabilities: List[str]
    ppd_records: List[str]
    raw_archive_written: bool
    imports_network_processor: bool
    notes: str

    def as_dict(self) -> Dict[str, object]:
        return {
            "capture_type": self.capture_type,
            "processor_family": self.processor_family,
            "capabilities": list(self.capabilities),
            "ppd_records": list(self.ppd_records),
            "raw_archive_written": self.raw_archive_written,
            "imports_network_processor": self.imports_network_processor,
            "notes": self.notes,
        }


class SyntheticProcessorCapabilityAdapter:
    """Builds PP&D's synthetic capability plan for processor handoff tests."""

    adapter_name = "ppd.synthetic_processor_capability_adapter"
    fixture_version = "2026-05-15"

    def planned_capabilities(self) -> List[SyntheticProcessorCapability]:
        return [
            SyntheticProcessorCapability(
                capture_type="html",
                processor_family="ipfs_datasets_py.web_html_processors",
                capabilities=[
                    "public_url_fetch_metadata",
                    "html_dom_text_extraction",
                    "link_and_heading_extraction",
                    "content_hashing",
                ],
                ppd_records=["SourceRegistry", "ArchiveManifest", "DocumentRecord"],
                raw_archive_written=False,
                imports_network_processor=False,
                notes="Records intended public HTML processing only; live fetch and raw body persistence stay outside this fixture.",
            ),
            SyntheticProcessorCapability(
                capture_type="pdf",
                processor_family="ipfs_datasets_py.pdf_processors",
                capabilities=[
                    "pdf_text_extraction",
                    "pdf_page_anchors",
                    "pdf_form_field_inventory",
                    "content_hashing",
                ],
                ppd_records=["ArchiveManifest", "DocumentRecord", "RequirementNode"],
                raw_archive_written=False,
                imports_network_processor=False,
                notes="Records intended PDF extraction and form inventory capabilities without downloading or committing PDF bytes.",
            ),
            SyntheticProcessorCapability(
                capture_type="warc",
                processor_family="ipfs_datasets_py.web_archive_processors",
                capabilities=[
                    "warc_manifest_projection",
                    "redirect_chain_capture",
                    "response_header_capture",
                    "archive_artifact_reference",
                ],
                ppd_records=["ArchiveManifest"],
                raw_archive_written=False,
                imports_network_processor=False,
                notes="Records the manifest fields expected from a WARC-capable capture while explicitly avoiding raw archive output.",
            ),
            SyntheticProcessorCapability(
                capture_type="metadata",
                processor_family="ipfs_datasets_py.metadata_processors",
                capabilities=[
                    "processor_name_version_capture",
                    "mime_type_classification",
                    "freshness_signal_capture",
                    "privacy_and_policy_flags",
                ],
                ppd_records=["SourceRegistry", "ArchiveManifest"],
                raw_archive_written=False,
                imports_network_processor=False,
                notes="Records deterministic metadata capture fields used by PP&D freshness and policy checks.",
            ),
        ]

    def as_fixture(self) -> Dict[str, object]:
        capabilities = self.planned_capabilities()
        return {
            "fixture_name": "synthetic_ppd_processor_capabilities",
            "fixture_version": self.fixture_version,
            "adapter_name": self.adapter_name,
            "purpose": "Synthetic record of PP&D processor capabilities planned for ipfs_datasets_py handoff.",
            "constraints": {
                "imports_network_processors": False,
                "writes_raw_archives": False,
                "deterministic": True,
            },
            "capture_types": [capability.capture_type for capability in capabilities],
            "capabilities": [capability.as_dict() for capability in capabilities],
        }


def build_synthetic_processor_capability_fixture() -> Dict[str, object]:
    """Return the deterministic fixture payload used by PP&D tests."""

    return SyntheticProcessorCapabilityAdapter().as_fixture()


def validate_synthetic_processor_capability_fixture(fixture: Dict[str, object]) -> List[str]:
    """Return validation errors for a synthetic processor capability fixture."""

    errors: List[str] = []
    capture_types = fixture.get("capture_types")
    capabilities = fixture.get("capabilities")
    constraints = fixture.get("constraints")

    if capture_types != list(_CAPTURE_TYPES):
        errors.append("capture_types must list html, pdf, warc, and metadata in deterministic order")

    if not isinstance(capabilities, list) or len(capabilities) != len(_CAPTURE_TYPES):
        errors.append("capabilities must contain one entry for each capture type")
        return errors

    if not isinstance(constraints, dict):
        errors.append("constraints must be an object")
    else:
        if constraints.get("imports_network_processors") is not False:
            errors.append("fixture must not import network processors")
        if constraints.get("writes_raw_archives") is not False:
            errors.append("fixture must not write raw archives")
        if constraints.get("deterministic") is not True:
            errors.append("fixture must be deterministic")

    seen_capture_types = []
    for entry in capabilities:
        if not isinstance(entry, dict):
            errors.append("each capability entry must be an object")
            continue

        capture_type = entry.get("capture_type")
        seen_capture_types.append(capture_type)

        if capture_type not in _CAPTURE_TYPES:
            errors.append("unexpected capture_type: {0}".format(capture_type))
        if entry.get("raw_archive_written") is not False:
            errors.append("{0} must not write raw archives".format(capture_type))
        if entry.get("imports_network_processor") is not False:
            errors.append("{0} must not import network processors".format(capture_type))
        if not entry.get("processor_family"):
            errors.append("{0} must name a processor_family".format(capture_type))
        if not entry.get("capabilities"):
            errors.append("{0} must list planned capabilities".format(capture_type))
        if not entry.get("ppd_records"):
            errors.append("{0} must list PP&D records populated by the handoff".format(capture_type))

    if seen_capture_types != list(_CAPTURE_TYPES):
        errors.append("capability entries must follow the deterministic capture type order")

    return errors
