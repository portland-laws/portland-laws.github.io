import json
import tempfile
import unittest
from pathlib import Path

from ppd.daemon.fixture_failure_guidance import (
    append_fixture_failure_guidance,
    build_fixture_failure_guidance,
)


class FixtureFailureGuidanceTest(unittest.TestCase):
    def test_missing_field_failure_includes_committed_fixture_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fixture_path = 'ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json'
            fixture = repo_root / fixture_path
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                json.dumps(
                    {
                        'schemaVersion': 1,
                        'plannedSeeds': [
                            {
                                'id': 'seed-ppd-landing',
                                'url': 'https://www.portland.gov/ppd',
                                'preflight': {'robots': 'respect', 'timeoutSeconds': 20},
                            }
                        ],
                        'skippedUrls': [
                            {'url': 'mailto:test@example.invalid', 'reasonCode': 'unsupported-scheme'}
                        ],
                    },
                    sort_keys=True,
                ),
                encoding='utf-8',
            )
            failure_text = (
                'AssertionError: missing required field; expected one of: seedUrls, seeds\n'
                f'while validating fixture {fixture_path}\n'
                'missing preflight policy fields'
            )

            guidance = build_fixture_failure_guidance(failure_text, repo_root=repo_root)

        self.assertIsNotNone(guidance)
        assert guidance is not None
        self.assertEqual(fixture_path, guidance.fixture_path)
        self.assertIn('Inspect the committed JSON fixture shape', guidance.guidance)
        self.assertIn('Use the daemon fixture-shape diagnostic', guidance.guidance)
        self.assertIn('Do not add broad shared contracts', guidance.guidance)
        self.assertIn('live crawl code', guidance.guidance)
        self.assertIn('authenticated automation', guidance.guidance)
        self.assertIn('top_level_keys: plannedSeeds, schemaVersion, skippedUrls', guidance.guidance)
        self.assertIn('list_fields: plannedSeeds, skippedUrls', guidance.guidance)
        self.assertIn('first_object_keys[plannedSeeds]: id, preflight, url', guidance.guidance)

    def test_keyerror_for_absent_fixture_key_includes_committed_fixture_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fixture_path = self._write_devhub_preview_fixture(repo_root)
            failure_text = (
                "KeyError: 'draftActionPreviews'\n"
                f'while validating fixture {fixture_path}\n'
                'Synthetic DevHub preview validator expected a missing fixture key'
            )

            guidance = build_fixture_failure_guidance(failure_text, repo_root=repo_root)

        self.assertIsNotNone(guidance)
        assert guidance is not None
        self.assertEqual(fixture_path, guidance.fixture_path)
        self.assertIn('Inspect the committed JSON fixture shape', guidance.guidance)
        self.assertIn('Absent fixture keys reported by the failure: draftActionPreviews', guidance.guidance)
        self.assertIn('Treat KeyError or assertion failures for those absent keys', guidance.guidance)
        self.assertIn('Committed fixture to inspect: ppd/tests/fixtures/devhub/draft_action_preview.json', guidance.guidance)
        self.assertIn('top_level_keys: previewActions, previewMode, schemaVersion', guidance.guidance)
        self.assertIn('list_fields: previewActions', guidance.guidance)
        self.assertIn('first_object_keys[previewActions]: actionClass, previewId', guidance.guidance)

    def test_assertion_for_absent_fixture_key_includes_committed_fixture_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fixture_path = self._write_devhub_preview_fixture(repo_root)
            failure_text = (
                "AssertionError: fixture key 'draftActionPreviews' is absent from the committed JSON fixture\n"
                f'while validating fixture {fixture_path}'
            )

            prompt_parts = append_fixture_failure_guidance(['base'], failure_text, repo_root=repo_root)

        self.assertEqual('base', prompt_parts[0])
        self.assertEqual(2, len(prompt_parts))
        self.assertIn('Inspect the committed JSON fixture shape', prompt_parts[1])
        self.assertIn('Absent fixture keys reported by the failure: draftActionPreviews', prompt_parts[1])
        self.assertIn('top_level_keys: previewActions, previewMode, schemaVersion', prompt_parts[1])

    def test_non_fixture_failure_does_not_add_guidance(self):
        self.assertIsNone(build_fixture_failure_guidance('RuntimeError: network unavailable'))
        self.assertEqual(['base'], append_fixture_failure_guidance(['base'], 'RuntimeError: network unavailable'))

    def _write_devhub_preview_fixture(self, repo_root: Path) -> str:
        fixture_path = 'ppd/tests/fixtures/devhub/draft_action_preview.json'
        fixture = repo_root / fixture_path
        fixture.parent.mkdir(parents=True)
        fixture.write_text(
            json.dumps(
                {
                    'schemaVersion': 1,
                    'previewMode': {
                        'dryRun': True,
                        'enabled': True,
                        'executesBrowserActions': False,
                    },
                    'previewActions': [
                        {
                            'previewId': 'fill-project-description',
                            'actionClass': 'reversible_draft_fill',
                        }
                    ],
                },
                sort_keys=True,
            ),
            encoding='utf-8',
        )
        return fixture_path


if __name__ == '__main__':
    unittest.main()
