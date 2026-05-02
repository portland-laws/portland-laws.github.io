from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ppd.daemon.fixture_shape import describe_json_fixture, describe_json_object


class FixtureShapeDiagnosticsTest(unittest.TestCase):
    def test_reports_only_top_level_lists_and_first_object_keys(self) -> None:
        synthetic = {
            "schemaVersion": 1,
            "seeds": [
                {"id": "seed-a", "url": "https://www.portland.gov/ppd", "kind": "public"},
                {"id": "seed-b", "url": "https://www.portland.gov/ppd/permits", "extra": "ignored"},
            ],
            "policy": {"robots": "respect", "timeoutSeconds": 20},
            "emptyList": [],
        }

        shape = describe_json_object(synthetic).to_dict()

        self.assertEqual(shape["top_level_type"], "object")
        self.assertEqual(shape["top_level_keys"], ["emptyList", "policy", "schemaVersion", "seeds"])
        self.assertEqual(shape["list_fields"], ["emptyList", "seeds"])
        self.assertEqual(shape["first_object_keys"], {
            "policy": ["robots", "timeoutSeconds"],
            "seeds": ["id", "kind", "url"],
        })
        self.assertNotIn("extra", shape["first_object_keys"]["seeds"])

    def test_accepts_repository_relative_fixture_path(self) -> None:
        synthetic = {
            "records": [{"id": "record-a", "sourceUrl": "https://www.portland.gov/ppd"}],
            "generatedAt": "2026-05-02T00:00:00Z",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fixture = repo_root / "ppd/tests/fixtures/shape/synthetic.json"
            fixture.parent.mkdir(parents=True)
            fixture.write_text(json.dumps(synthetic, sort_keys=True), encoding="utf-8")

            shape = describe_json_fixture(repo_root, "ppd/tests/fixtures/shape/synthetic.json").to_dict()

        self.assertEqual(shape["fixture_path"], "ppd/tests/fixtures/shape/synthetic.json")
        self.assertEqual(shape["top_level_keys"], ["generatedAt", "records"])
        self.assertEqual(shape["list_fields"], ["records"])
        self.assertEqual(shape["first_object_keys"], {"records": ["id", "sourceUrl"]})


if __name__ == "__main__":
    unittest.main()
