import { createLegalNormIr, legalNormIrToRecord, validateLegalNormIr } from './ir';

describe('deontic IR', () => {
  it('normalizes Python-style legal norm records into browser-native IR', () => {
    const ir = createLegalNormIr({
      sourceId: 'sec-12',
      normType: 'prohibition',
      actor: ' Operator ',
      action: ' discharge waste ',
      supportSpan: [5, 28],
      fieldSpans: { actor: [5, 13], action: [19, 28] },
      exceptions: [{ text: 'unless authorized', span: [30, 47] }],
      temporalConstraints: [{ value: 'within 10 days' }],
      proof_ready: true,
    });

    expect(ir).toMatchObject({
      source_id: 'sec-12',
      norm_type: 'prohibition',
      modality: 'F',
      actor: 'Operator',
      action: 'discharge waste',
      support_span: [[5, 28]],
      proof_ready: true,
      schema_version: 'ts-deontic-ir-v1',
    });
    expect(ir.field_spans.action).toEqual([[19, 28]]);
    expect(ir.exceptions[0]).toMatchObject({ raw_text: 'unless authorized', span: [30, 47] });
    expect(ir.temporal_constraints[0]).toMatchObject({ value: 'within 10 days' });
  });

  it('fails closed when required IR slots or parser warnings are present', () => {
    const ir = createLegalNormIr({
      norm_type: 'obligation',
      actor: 'Tenant',
      action: '',
      parser_warnings: ['ambiguous_actor_scope'],
      proof_ready: true,
    });

    expect(ir.proof_ready).toBe(false);
    expect(validateLegalNormIr(ir)).toEqual({
      valid: false,
      missing_slots: ['action'],
      blockers: ['ambiguous_actor_scope', 'missing_ir_slot:action'],
    });
  });

  it('serializes stable records without Python runtime dependencies', () => {
    const left = createLegalNormIr({ actor: 'Applicant', action: 'submit forms' });
    const right = createLegalNormIr({ actor: 'Applicant', action: 'submit forms' });
    const record = legalNormIrToRecord(left);

    expect(left.source_id).toBe(right.source_id);
    expect(record).toMatchObject({
      source_id: left.source_id,
      norm_type: 'obligation',
      modality: 'O',
      actor: 'Applicant',
      action: 'submit forms',
      proof_ready: false,
    });
  });
});
