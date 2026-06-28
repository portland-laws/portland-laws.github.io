import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / 'fixtures'
    / 'plan_review_process_dependency_graph'
    / 'single_dwelling_plan_review_permit.json'
)


COLLECTIONS_WITH_STAGES = (
    'required_user_facts',
    'required_documents',
    'file_rules',
    'fees',
    'action_gates',
    'unsupported_paths',
    'next_safe_actions',
)


def load_fixture():
    with FIXTURE_PATH.open(encoding='utf-8') as fixture_file:
        return json.load(fixture_file)


def stage_index(process_model, stage):
    return process_model['stages'].index(stage)


def records_by_id(process_model):
    records = {}
    for collection_name in COLLECTIONS_WITH_STAGES:
        for record in process_model[collection_name]:
            record_id = record['id']
            assert record_id not in records
            records[record_id] = record
    return records


def test_fixture_uses_standard_plan_review_stage_order():
    process_model = load_fixture()

    assert process_model['permit_type'] == 'building permit requiring plan review'
    assert process_model['stages'] == [
        'pre-application research',
        'account setup or manual login',
        'property lookup',
        'permit type selection',
        'eligibility screening',
        'document preparation',
        'application data entry',
        'upload staging',
        'acknowledgement/certification review',
        'submission',
        'prescreen/intake',
        'fee payment',
        'plan review',
        'corrections/checksheets',
        'approval/issuance',
        'inspections',
        'closeout, cancellation, expiration, extension, or reactivation',
    ]


def test_required_facts_documents_rules_fees_gates_unsupported_paths_and_safe_actions_are_staged():
    process_model = load_fixture()
    stages = set(process_model['stages'])

    expected_counts = {
        'required_user_facts': 4,
        'required_documents': 3,
        'file_rules': 3,
        'fees': 1,
        'action_gates': 4,
        'unsupported_paths': 3,
        'next_safe_actions': 5,
    }

    for collection_name, expected_count in expected_counts.items():
        collection = process_model[collection_name]
        assert len(collection) == expected_count
        assert all(record['stage'] in stages for record in collection)
        assert all(record['id'] for record in collection)
        assert all(record['label'] for record in collection)

    gate_ids = {gate['id'] for gate in process_model['action_gates']}
    assert {
        'gate_acknowledgement_review',
        'gate_certification',
        'gate_final_submission',
        'gate_payment_submit',
    } == gate_ids
    for gate in process_model['action_gates']:
        assert gate['requires_attendance'] is True
        assert gate['requires_exact_confirmation'] is True

    unsupported_actions = {path['blocked_action'] for path in process_model['unsupported_paths']}
    assert 'automate_certification_submission_upload_or_payment' in unsupported_actions
    assert 'purchase_standard_trade_permit' in unsupported_actions


def test_dependency_graph_references_only_known_nodes_and_never_moves_backwards_by_stage():
    process_model = load_fixture()
    graph_nodes = {node['id']: node for node in process_model['dependency_graph']}
    staged_records = records_by_id(process_model)

    assert set(staged_records).issubset(set(graph_nodes))

    for node_id, node in graph_nodes.items():
        assert node['stage'] in process_model['stages']
        for dependency_id in node['depends_on']:
            assert dependency_id in graph_nodes
            dependency = graph_nodes[dependency_id]
            assert stage_index(process_model, dependency['stage']) <= stage_index(
                process_model,
                node['stage'],
            ), f'{node_id} depends on later-stage node {dependency_id}'


def test_safe_actions_are_ordered_before_consequential_actions_or_at_manual_handoff():
    process_model = load_fixture()
    graph_nodes = {node['id']: node for node in process_model['dependency_graph']}

    safe_actions = process_model['next_safe_actions']
    safe_action_stages = [stage_index(process_model, action['stage']) for action in safe_actions]
    assert safe_action_stages == sorted(safe_action_stages)

    submission_stage = stage_index(process_model, 'submission')
    fee_payment_stage = stage_index(process_model, 'fee payment')
    for action in safe_actions:
        action_stage = stage_index(process_model, action['stage'])
        assert action_stage < submission_stage
        assert action_stage < fee_payment_stage
        assert action['id'] in graph_nodes
        for requirement_id in action['requires']:
            assert requirement_id in graph_nodes
            assert stage_index(process_model, graph_nodes[requirement_id]['stage']) <= action_stage

    handoff = safe_actions[-1]
    assert handoff['id'] == 'safe_action_manual_handoff_for_acknowledgement'
    assert handoff['stage'] == 'acknowledgement/certification review'
    assert 'gate_certification' in handoff['requires']


def test_fee_trigger_remains_after_submission_and_before_payment_submit_gate():
    process_model = load_fixture()
    graph_nodes = {node['id']: node for node in process_model['dependency_graph']}

    submission = graph_nodes['gate_final_submission']
    fee_trigger = graph_nodes['fee_trigger_intake_or_review_fee']
    payment_gate = graph_nodes['gate_payment_submit']

    assert stage_index(process_model, submission['stage']) < stage_index(
        process_model,
        fee_trigger['stage'],
    )
    assert fee_trigger['stage'] == 'fee payment'
    assert payment_gate['stage'] == 'fee payment'
    assert 'gate_final_submission' in fee_trigger['depends_on']
    assert 'fee_trigger_intake_or_review_fee' in payment_gate['depends_on']
