import {
  parserElementsForMetrics,
  summarizeParserElements,
  summarizePhase8ParserMetrics,
} from './metrics';

describe('deontic metrics', () => {
  it('summarizes parser quality, readiness, warnings, and Phase 8 coverage', () => {
    const summary = summarizeParserElements([
      {
        text: 'Tenant must pay rent.',
        source_id: 'sec-1',
        norm_type: 'obligation',
        deontic_operator: 'O',
        actor: 'Tenant',
        action: 'pay rent',
        support_span: [0, 21],
        field_spans: { actor: [0, 6], action: [12, 20] },
        schema_valid: true,
        scaffold_quality: 0.8,
        proof_ready: true,
        parser_warnings: ['weak_condition'],
        resolved_cross_references: [{ resolution_status: 'resolved' }, { target_exists: false }],
      },
      {
        text: 'Tenant may inspect records.',
        source_id: 'sec-2',
        norm_type: 'permission',
        deontic_operator: 'P',
        actor: 'Tenant',
        action: '',
        support_span: [0, 100],
        scaffold_quality: 0.4,
        proof_ready: false,
        repair_required: true,
      },
    ]);

    expect(summary).toMatchObject({
      element_count: 2,
      schema_valid_rate: 0.5,
      source_span_valid_count: 1,
      proof_ready_count: 1,
      repair_required_count: 1,
      average_scaffold_quality: 0.6,
      warning_distribution: { weak_condition: 1 },
      formal_logic_target_distribution: { deontic_fol: 2 },
      norm_type_distribution: { obligation: 1, permission: 1 },
      modality_distribution: { O: 1, P: 1 },
      cross_reference_resolution_rate: 0.5,
      phase8_source_count: 2,
      phase8_quality_requires_validation_count: 1,
    });
  });

  it('normalizes browser parser elements for Phase 8-only metrics', () => {
    const rows = parserElementsForMetrics([
      {
        text: 'Drivers shall stop.',
        sourceId: 'sec-3',
        normType: 'obligation',
        deontic_operator: 'O',
        subjects: ['Drivers'],
        actions: ['stop'],
        startOffset: 0,
        endOffset: 19,
        fieldSpans: { actor: [0, 7], action: [14, 18] },
        confidence: 0.9,
      },
    ]);

    expect(rows[0]).toMatchObject({
      source_id: 'sec-3',
      actor: 'Drivers',
      action: 'stop',
      support_span: [[0, 19]],
    });
    expect(summarizePhase8ParserMetrics(rows)).toMatchObject({
      phase8_decoder_reconstruction_record_count: 1,
      phase8_prover_present_required_target_count: 1,
      phase8_quality_complete_count: 1,
    });
  });
});
