#!/usr/bin/env python3
"""Fixture-backed PP&D public crawl dry-run report command."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Optional

from .public_dry_run import FetchResponse, run_public_crawl_dry_run


DEFAULT_INJECTED_RESPONSES_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "public_crawl_report"
    / "injected_responses.json"
)


def load_injected_fixture(path: Path = DEFAULT_INJECTED_RESPONSES_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("injected response fixture must be a JSON object")
    return data


def write_seed_manifest_from_fixture(fixture: dict, path: Path) -> Path:
    seeds = fixture.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("injected response fixture must include non-empty seeds")
    normalized: list[dict[str, str]] = []
    for item in seeds:
        if not isinstance(item, dict):
            raise ValueError("seed entries must be objects")
        seed_id = item.get("id")
        url = item.get("url")
        if not isinstance(seed_id, str) or not isinstance(url, str):
            raise ValueError("seed entries require string id and url")
        normalized.append({"id": seed_id, "url": url})
    path.write_text(json.dumps({"seeds": normalized}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_injected_fetcher(fixture: dict):
    responses = fixture.get("responses")
    if not isinstance(responses, dict):
        raise ValueError("injected response fixture must include responses object")

    def fetch(url: str) -> FetchResponse:
        response = responses.get(url)
        if not isinstance(response, dict):
            raise KeyError(f"no injected response for {url}")
        body_text = response.get("body", "")
        body_base64 = response.get("bodyBase64")
        if isinstance(body_base64, str):
            body = base64.b64decode(body_base64)
        elif isinstance(body_text, str):
            body = body_text.encode("utf-8")
        else:
            raise ValueError(f"injected response body for {url} must be text or base64")
        return FetchResponse(
            url=str(response.get("url") or url),
            status_code=int(response.get("statusCode", 200)),
            content_type=str(response.get("contentType", "")),
            body=body,
        )

    return fetch


def build_public_crawl_report(*, fixture_path: Path = DEFAULT_INJECTED_RESPONSES_PATH) -> dict:
    fixture = load_injected_fixture(fixture_path)
    temp_seed_manifest = fixture_path.with_suffix(".seeds.tmp.json")
    try:
        write_seed_manifest_from_fixture(fixture, temp_seed_manifest)
        report = run_public_crawl_dry_run(
            seed_manifest_path=temp_seed_manifest,
            max_seed_fetches=int(fixture.get("maxSeedFetches", 2)),
            fetcher=build_injected_fetcher(fixture),
            robots_text_by_host={
                str(host): str(text)
                for host, text in (fixture.get("robotsTextByHost") or {}).items()
            },
        ).to_dict()
    finally:
        try:
            temp_seed_manifest.unlink()
        except FileNotFoundError:
            pass

    report["mode"] = "fixture_backed_public_crawl_report"
    report["fixture_id"] = str(fixture.get("fixtureId", ""))
    report["raw_output_persisted"] = False
    report["raw_response_bodies_included"] = False
    for item in report.get("items", []):
        if isinstance(item, dict):
            item.pop("body", None)
            item.pop("raw_body", None)
            item.pop("rawHtml", None)
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a fixture-backed PP&D public crawl dry-run report.")
    parser.add_argument("--fixture", default=str(DEFAULT_INJECTED_RESPONSES_PATH))
    args = parser.parse_args(argv)
    print(json.dumps(build_public_crawl_report(fixture_path=Path(args.fixture)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
