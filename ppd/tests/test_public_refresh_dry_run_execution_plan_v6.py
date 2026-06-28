from __future__ import annotations

import copy
from pathlib import Path

from ppd.agent_readiness.public_refresh_dry_run_execution_plan_v6 import (
    BOUNDARIES,
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    assert_valid_public_refresh_dry_run_execution_plan_v6,
    build_public_refresh_dry_run_execution_plan_v6_from_fixture,
    validate_public_refresh_dry_run_execution_plan_v6,
)

FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'public_refresh_dry_run_execution_plan_v6'
SOURCE_FIXTURE = FIXTURE_DIR / 'source_fixture.json'


def _valid_plan():
    return build_public_refresh_dry_run_execution_plan_v6_from_fixture(SOURCE_FIXTURE)


def _problem_text(packet):
    return '\n'.join(validate_public_refresh_dry_run_execution_plan_v6(packet).problems)


def test_public_refresh_dry_run_execution_plan_v6_consumes_authorization_fixture_only():
    plan = _valid_plan()

    assert plan['packet_type'] == 'ppd.public_refresh_dry_run_execution_plan.v6'
    assert plan['mode'] == 'fixture_first_public_refresh_dry_run_execution_plan_v6'
    assert plan['consumes_only'] == {'public_refresh_authorization_packet_v6_fixtures': True}
    assert {row['fixture_role'] for row in plan['source_fixture_refs']} == {'public_refresh_authorization_packet_v6'}
    assert plan['authorization_packet_ref']['packet_type'] == 'ppd.public_refresh_authorization_packet.v6'
    assert plan['boundaries'] == BOUNDARIES
    assert plan['boundaries']['live_crawl_executed'] is False
    assert plan['boundaries']['documents_downloaded'] is False
    assert plan['boundaries']['raw_bodies_persisted'] is False
    assert plan['boundaries']['devhub_opened'] is False
    assert plan['boundaries']['private_documents_read'] is False
    assert plan['boundaries']['active_mutation'] is False


def test_public_refresh_dry_run_execution_plan_v6_assembles_ordered_seed_groups_and_windows():
    plan = _valid_plan()

    assert [row['group_id'] for row in plan['ordered_seed_groups']] == [
        'devhub_public_guidance',
        'file_preparation_and_upload_guidance',
        'fee_payment_public_guidance',
        'forms_index_and_public_forms',
    ]
    assert [row['seed_group_order'] for row in plan['ordered_seed_groups']] == [1, 2, 3, 4]
    assert all(row['source_ids'] for row in plan['ordered_seed_groups'])
    assert all(row['live_crawl_authorized'] is False for row in plan['ordered_seed_groups'])
    assert [row['group_id'] for row in plan['deterministic_crawl_window_placeholders']] == [row['group_id'] for row in plan['ordered_seed_groups']]
    assert all(row['placeholder_start_at'] == 'pending_manual_go_decision' for row in plan['deterministic_crawl_window_placeholders'])
    assert all(row['crawl_window_determined'] is False for row in plan['deterministic_crawl_window_placeholders'])
    assert all(row['live_crawl_authorized'] is False for row in plan['deterministic_crawl_window_placeholders'])


def test_public_refresh_dry_run_execution_plan_v6_keeps_preflight_processor_and_manifest_expectations_offline():
    plan = _valid_plan()

    assert all(row['allowlist_recheck_required'] is True for row in plan['allowlist_and_robots_recheck_expectations'])
    assert all(row['robots_recheck_required'] is True for row in plan['allowlist_and_robots_recheck_expectations'])
    assert all(row['policy_recheck_required'] is True for row in plan['allowlist_and_robots_recheck_expectations'])
    assert all(row['recheck_completed'] is False for row in plan['allowlist_and_robots_recheck_expectations'])
    assert all(row['crawl_authorized'] is False for row in plan['allowlist_and_robots_recheck_expectations'])
    assert all(row['processor_mode'] == 'dry_run_manifest_handoff_only' for row in plan['processor_dry_run_handoff_rows'])
    assert all('no_raw_body_persisted' in row['expected_manifest_fields'] for row in plan['processor_dry_run_handoff_rows'])
    assert all(row['raw_artifact_ref_allowed'] is False for row in plan['processor_dry_run_handoff_rows'])
    assert all(row['handoff_executed'] is False for row in plan['processor_dry_run_handoff_rows'])
    assert all(row['no_raw_body_persisted_required'] is True for row in plan['no_raw_body_manifest_only_output_expectations'])
    assert all(row['manifest_written'] is False for row in plan['no_raw_body_manifest_only_output_expectations'])
    assert all(row['raw_body_written'] is False for row in plan['no_raw_body_manifest_only_output_expectations'])


def test_public_refresh_dry_run_execution_plan_v6_includes_abort_and_reviewer_placeholders():
    plan = _valid_plan()

    abort_conditions = {row['condition']: row for row in plan['abort_on_drift_conditions']}
    assert 'robots_disallow_count' in abort_conditions
    assert 'outside_allowlist_count' in abort_conditions
    assert 'raw_body_persistence_attempt_count' in abort_conditions
    assert all(row['abort_required_on_threshold'] is True for row in plan['abort_on_drift_conditions'])
    assert all(row['current_observed_count'] == 0 for row in plan['abort_on_drift_conditions'])
    assert all(row['condition_triggered'] is False for row in plan['abort_on_drift_conditions'])
    assert all(row['decision_status'] == 'pending_manual_go_no_go' for row in plan['reviewer_go_no_go_placeholders'])
    assert all(row['go_authorized'] is False for row in plan['reviewer_go_no_go_placeholders'])
    assert all(row['decided_by'] == '' for row in plan['reviewer_go_no_go_placeholders'])
    assert all(row['decided_at'] == '' for row in plan['reviewer_go_no_go_placeholders'])


def test_public_refresh_dry_run_execution_plan_v6_uses_exact_offline_validation_commands_only():
    plan = _valid_plan()

    assert plan['exact_offline_validation_commands'] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert plan['validation_commands'] == VALIDATION_COMMANDS
    flattened = ' '.join(part for command in plan['exact_offline_validation_commands'] for part in command).lower()
    for forbidden in ['curl', 'wget', 'playwright', 'devhub', 'captcha', 'mfa']:
        assert forbidden not in flattened
    assert_valid_public_refresh_dry_run_execution_plan_v6(plan)
    assert validate_public_refresh_dry_run_execution_plan_v6(plan).valid is True


def test_public_refresh_dry_run_execution_plan_v6_rejects_missing_sections_and_unsafe_claims():
    for field in [
        'source_fixture_refs',
        'ordered_seed_groups',
        'deterministic_crawl_window_placeholders',
        'allowlist_and_robots_recheck_expectations',
        'processor_dry_run_handoff_rows',
        'no_raw_body_manifest_only_output_expectations',
        'abort_on_drift_conditions',
        'reviewer_go_no_go_placeholders',
    ]:
        plan = _valid_plan()
        plan[field] = []
        assert f'{field} must be a non-empty list' in _problem_text(plan)

    plan = _valid_plan()
    plan.pop('authorization_packet_ref')
    assert 'authorization_packet_ref must be present and reference public refresh authorization packet v6' in _problem_text(plan)

    plan = _valid_plan()
    plan['authorization_packet_ref']['packet_id'] = ''
    assert 'authorization_packet_ref.packet_id is required' in _problem_text(plan)

    for command_field in ['exact_offline_validation_commands', 'validation_commands']:
        plan = _valid_plan()
        plan[command_field] = []
        assert f'{command_field} must be a non-empty list' in _problem_text(plan)

    plan = _valid_plan()
    plan['source_fixture_refs'].append({'fixture_role': 'public_source_freshness_watchlist_v6', 'path': 'fixture://not-allowed'})
    assert 'source_fixture_refs must reference only public_refresh_authorization_packet_v6 fixtures' in _problem_text(plan)

    plan = _valid_plan()
    plan['ordered_seed_groups'][0]['live_crawl_authorized'] = True
    assert 'ordered_seed_groups[0].live_crawl_authorized must be false' in _problem_text(plan)

    plan = _valid_plan()
    plan['deterministic_crawl_window_placeholders'][0]['crawl_window_determined'] = True
    assert 'deterministic_crawl_window_placeholders[0] must remain placeholder-only and unauthorized' in _problem_text(plan)

    plan = _valid_plan()
    plan['processor_dry_run_handoff_rows'][0]['handoff_executed'] = True
    assert 'processor_dry_run_handoff_rows[0] must not allow raw artifacts or executed handoff' in _problem_text(plan)

    plan = _valid_plan()
    plan['no_raw_body_manifest_only_output_expectations'][0]['raw_body_written'] = True
    assert 'no_raw_body_manifest_only_output_expectations[0] must be output-expectation only with no writes' in _problem_text(plan)

    plan = _valid_plan()
    plan['reviewer_go_no_go_placeholders'][0]['go_authorized'] = True
    assert 'reviewer_go_no_go_placeholders[0].go_authorized must be false' in _problem_text(plan)

    plan = _valid_plan()
    plan['boundaries']['live_crawl_executed'] = True
    assert 'boundaries must deny live crawl' in _problem_text(plan)
    assert 'packet.boundaries.live_crawl_executed must not be true' in _problem_text(plan)

    plan = _valid_plan()
    plan['downloaded_crawl_artifact_ref'] = 'file://raw-download.pdf'
    assert 'must not contain private' in _problem_text(plan)

    plan = _valid_plan()
    plan['official_action_completed'] = True
    assert 'must not claim official action completion' in _problem_text(plan)

    plan = _valid_plan()
    plan['permitting_approval_guarantee'] = 'permit will be approved'
    assert 'must not contain legal or permitting guarantees' in _problem_text(plan)

    plan = _valid_plan()
    plan['mutation_enabled'] = True
    assert 'must not enable active mutation' in _problem_text(plan)

    plan = _valid_plan()
    plan['unsafe_probe'] = copy.deepcopy({'session_cookie': 'abc'})
    assert 'must not contain private' in _problem_text(plan)
