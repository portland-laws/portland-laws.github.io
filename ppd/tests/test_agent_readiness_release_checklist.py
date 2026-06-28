import json
from pathlib import Path

from ppd.guardrails.agent_readiness_release_checklist import (
    NOT_READY,
    REQUIRED_SECTIONS,
    assert_fixture_release_checklist,
    build_release_checklist,
)


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'agent_readiness_release_checklist.json'


def load_fixture():
    with FIXTURE_PATH.open('r', encoding='utf-8') as fixture_file:
        return json.load(fixture_file)


def assert_rejected(fixture, expected_text):
    try:
        build_release_checklist(fixture)
    except ValueError as exc:
        assert expected_text in str(exc)
    else:
        raise AssertionError('expected release checklist validation to fail')


def test_release_checklist_fixture_maps_every_required_section():
    checklist = assert_fixture_release_checklist(load_fixture())

    assert checklist.fixture_name == 'fixture-first cited guardrail API readiness mapping'
    for section in REQUIRED_SECTIONS:
        assert checklist.items_for_section(section), section


def test_release_checklist_keeps_consequential_actions_explicitly_not_ready():
    checklist = build_release_checklist(load_fixture())

    assert checklist.ready_for_agent_release is False
    assert checklist.ready_for_submission is False
    assert checklist.ready_for_payment is False
    assert checklist.ready_for_upload is False
    assert checklist.ready_for_scheduling is False

    not_ready_actions = {
        item.prompt_or_action
        for item in checklist.items_for_section(NOT_READY)
        if item.decision == NOT_READY
    }
    assert not_ready_actions == {'submission', 'payment', 'upload', 'scheduling'}


def test_release_checklist_requires_citations_from_guardrail_response():
    fixture = load_fixture()
    fixture['release_checklist']['local_preview'][0]['citation_ids'] = ['plan.devhub.safe-read-only']

    assert_rejected(fixture, 'checklist item cites evidence not returned by response')


def test_release_checklist_rejects_uncited_answers():
    fixture = load_fixture()
    fixture['guardrail_api_responses'].append(
        {
            'response_id': 'answer.uncited',
            'prompt_or_action': 'ask_for_scope',
            'decision': 'allowed_user_prompt',
            'response': 'Ask for the missing project scope.',
            'citation_ids': [],
        }
    )

    assert_rejected(fixture, 'answer.uncited answer lacks citation_ids')


def test_release_checklist_rejects_private_values():
    fixture = load_fixture()
    fixture['guardrail_api_responses'][0]['value'] = '123 Private Street'

    assert_rejected(fixture, 'private value field is not allowed')


def test_release_checklist_rejects_local_private_paths():
    fixture = load_fixture()
    fixture['guardrail_api_responses'][0]['response'] = '/home/alex/private/devhub-upload.pdf'

    assert_rejected(fixture, 'local private path is not allowed')


def test_release_checklist_rejects_stale_guardrail_bundles():
    fixture = load_fixture()
    fixture['guardrail_bundle'] = {
        'guardrail_bundle_id': 'bundle-stale-release-checklist',
        'freshness_status': 'stale',
        'last_verified_at': '2026-05-28T00:00:00Z',
    }

    assert_rejected(fixture, 'guardrail bundle bundle-stale-release-checklist is stale')


def test_release_checklist_rejects_missing_unresolved_blockers():
    fixture = load_fixture()
    fixture['release_checklist']['unresolved_review_blocker'] = []

    assert_rejected(fixture, 'release_checklist.unresolved_review_blocker must include unresolved fixture-backed items')


def test_release_checklist_rejects_unsupported_ready_to_submit_labels():
    fixture = load_fixture()
    fixture['guardrail_api_responses'][0]['decision'] = 'ready_to_submit'
    fixture['release_checklist']['allowed_user_prompt'][0]['decision'] = 'ready_to_submit'

    assert_rejected(fixture, 'unsupported ready label ready_to_submit')


def test_release_checklist_rejects_consequential_action_outside_blocked_or_handoff_status():
    fixture = load_fixture()
    fixture['guardrail_api_responses'].append(
        {
            'response_id': 'unsafe.payment.preview',
            'prompt_or_action': 'payment',
            'decision': 'local_preview',
            'citation_ids': ['plan.boundaries.no-consequential-actions'],
            'response': 'Preview payment entry as if it were safe.',
        }
    )

    assert_rejected(fixture, 'unsafe.payment.preview consequential action payment must be blocked or manual handoff')


def test_release_checklist_rejects_certification_and_cancellation_when_not_blocked():
    fixture = load_fixture()
    fixture['guardrail_api_responses'].extend(
        [
            {
                'response_id': 'unsafe.certification.preview',
                'prompt_or_action': 'certification',
                'decision': 'local_preview',
                'citation_ids': ['plan.boundaries.no-consequential-actions'],
                'response': 'Preview certification as if it were safe.',
            },
            {
                'response_id': 'unsafe.cancellation.preview',
                'prompt_or_action': 'cancellation',
                'decision': 'reversible_draft_preview',
                'citation_ids': ['plan.boundaries.no-consequential-actions'],
                'response': 'Preview cancellation as if it were reversible.',
            },
        ]
    )

    assert_rejected(fixture, 'unsafe.certification.preview consequential action certification must be blocked or manual handoff')
