from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_freshness"
    / "public_source_freshness_manifest.json"
)

FORBIDDEN_KEYS = {
    "authState",
    "cookies",
    "rawBody",
    "rawHtml",
    "rawResponse",
    "rawResponseBody",
    "sessionState",
    "tracePath",
}

FORBIDDEN_FRAGMENTS = (
    "devhub.portlandoregon.gov/secure",
    "/data/private/",
    "/data/raw/",
    "storage_state",
    "trace.zip",
)


class PublicSourceFreshnessManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            self.manifest = json.load(handle)

    def test_manifest_is_fixture_only_and_blocks_live_crawl_planning(self) -> None:
        errors = validate_manifest(self.manifest)

        self.assertEqual([], errors)
        self.assertTrue(self.manifest["fixtureOnly"])
        self.assertFalse(self.manifest["liveCrawlPlanned"])
        self.assertFalse(self.manifest["networkAccessAllowed"])
        self.assertFalse(self.manifest["rawResponseBodiesStored"])
        self.assertFalse(self.manifest["privateDevhubArtifactsStored"])

    def test_sources_have_timestamps_citations_and_hash_or_cache_placeholders(self) -> None:
        for source in self.manifest["sources"]:
            source_id = source["sourceId"]
            self.assertTrue(source["lastSeenAt"].endswith("Z"), source_id)
            self.assertTrue(source["sourceEvidenceId"], source_id)
            self.assertIsInstance(source["reviewNeeded"], bool, source_id)
            self.assertFalse(source["stale"], source_id)

            parsed_source = urlparse(source["sourceUrl"])
            parsed_canonical = urlparse(source["canonicalUrl"])
            self.assertEqual("https", parsed_source.scheme, source_id)
            self.assertEqual("www.portland.gov", parsed_source.netloc, source_id)
            self.assertEqual("https", parsed_canonical.scheme, source_id)
            self.assertEqual("www.portland.gov", parsed_canonical.netloc, source_id)
            self.assertTrue(_has_hash_or_cache_placeholder(source), source_id)

    def test_rejection_cases_fail_closed_before_live_crawl_planning(self) -> None:
        expected_reasons = {case["expectedReason"] for case in self.manifest["rejectionCases"]}
        observed_reasons: set[str] = set()

        for case in self.manifest["rejectionCases"]:
            mutated = copy.deepcopy(self.manifest)
            mutation = case.get("mutation")
            payload = case.get("payload")
            if isinstance(mutation, dict):
                _apply_source_mutation(mutated, mutation)
            if isinstance(payload, dict):
                mutated["sources"].append(payload)
            observed_reasons.update(validate_manifest(mutated))

        self.assertTrue(expected_reasons.issubset(observed_reasons), observed_reasons)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("fixtureOnly") is not True:
        errors.append("manifest must be fixture-only")
    if manifest.get("liveCrawlPlanned") is not False:
        errors.append("live crawl planning must be disabled")
    if manifest.get("networkAccessAllowed") is not False:
        errors.append("network access must be disabled")
    if _contains_forbidden_artifact(manifest, allow_rejection_cases=True):
        errors.append("private DevHub artifacts are not allowed")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("at least one source is required")
        return errors

    seen_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source entries must be objects")
            continue
        source_id = str(source.get("sourceId", ""))
        if not source_id:
            errors.append("sourceId is required")
        elif source_id in seen_ids:
            errors.append(f"duplicate sourceId {source_id}")
        seen_ids.add(source_id)

        if not str(source.get("lastSeenAt", "")).endswith("Z"):
            errors.append("lastSeenAt timestamp is required")
        if not source.get("sourceEvidenceId"):
            errors.append("sourceEvidenceId is required")
        if not _is_public_portland_url(source.get("sourceUrl")):
            errors.append("sourceUrl must be a public Portland.gov HTTPS URL")
        if not _is_public_portland_url(source.get("canonicalUrl")):
            errors.append("canonicalUrl must be a public Portland.gov HTTPS URL")
        if not _has_hash_or_cache_placeholder(source):
            errors.append("content hash or HTTP cache placeholder is required")
        if not isinstance(source.get("reviewNeeded"), bool):
            errors.append("reviewNeeded boolean is required")

    if _contains_forbidden_artifact(manifest, allow_rejection_cases=True):
        errors.append("raw response bodies are not allowed")
    return list(dict.fromkeys(errors))


def _apply_source_mutation(manifest: dict[str, Any], mutation: dict[str, Any]) -> None:
    target_id = mutation.get("sourceId")
    for source in manifest.get("sources", []):
        if not isinstance(source, dict) or source.get("sourceId") != target_id:
            continue
        remove_field = mutation.get("removeField")
        if isinstance(remove_field, str):
            source.pop(remove_field, None)
        set_fields = mutation.get("setFields")
        if isinstance(set_fields, dict):
            source.update(set_fields)


def _has_hash_or_cache_placeholder(source: dict[str, Any]) -> bool:
    content_hash = source.get("contentHashPlaceholder")
    if isinstance(content_hash, str) and content_hash.startswith("sha256:"):
        return True
    cache = source.get("httpCacheMetadataPlaceholder")
    if not isinstance(cache, dict):
        return False
    return any(cache.get(key) for key in ("etag", "lastModified", "cacheControl"))


def _is_public_portland_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc == "www.portland.gov"


def _contains_forbidden_artifact(value: Any, *, allow_rejection_cases: bool, path: str = "root") -> bool:
    if allow_rejection_cases and path.startswith("root.rejectionCases"):
        return False
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                return True
            if _contains_forbidden_artifact(child, allow_rejection_cases=allow_rejection_cases, path=f"{path}.{key}"):
                return True
        return False
    if isinstance(value, list):
        return any(
            _contains_forbidden_artifact(child, allow_rejection_cases=allow_rejection_cases, path=f"{path}[{index}]")
            for index, child in enumerate(value)
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(fragment in lowered for fragment in FORBIDDEN_FRAGMENTS)
    return False


if __name__ == "__main__":
    unittest.main()
