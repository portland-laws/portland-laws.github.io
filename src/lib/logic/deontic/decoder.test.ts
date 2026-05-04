import { decodeLegalNormIr, decode_legal_norm_ir, type LegalNormIrLike } from './decoder';

function norm(overrides: Partial<LegalNormIrLike> = {}): LegalNormIrLike {
  return {
    source_id: 'sec-1',
    actor: 'Tenant',
    modality: 'O',
    action: 'pay rent monthly',
    support_span: [0, 30],
    field_spans: { actor: [4, 10], action: [16, 32] },
    quality: { parser_warnings: [] },
    ...overrides,
  };
}

describe('deontic decoder', () => {
  it('reconstructs deontic IR without temporal or recipient duplication', () => {
    const decoded = decodeLegalNormIr(
      norm({
        action: 'provide notice to the applicant',
        recipient: 'to the applicant',
        temporal_constraints: [{ value: 'monthly', span: [24, 31] }],
      }),
    );

    expect(decoded.text).toBe('Tenant shall provide notice to the applicant monthly.');
    expect(decoded.missingSlots).toEqual([]);
    expect(decoded.phrases.map((phrase) => phrase.slot)).toEqual([
      'actor',
      'modality',
      'action',
      'temporal_constraints',
    ]);
  });

  it('splits a source-grounded mental state from the rendered action', () => {
    const decoded = decodeLegalNormIr(
      norm({
        actor: 'Inspector',
        action: 'knowingly approve the discharge',
        mental_state: 'knowingly',
        field_spans: { actor: [4, 13], mental_state: [20, 29], action: [20, 51] },
      }),
    );

    expect(decoded.text).toBe('Inspector shall knowingly approve the discharge.');
    expect(decoded.phrases.map((phrase) => phrase.slot)).toEqual([
      'actor',
      'modality',
      'mental_state',
      'action',
    ]);
    expect(decoded.phrases[2]).toMatchObject({ text: 'knowingly', spans: [[20, 29]] });
  });

  it('renders applicability and keeps cross references as provenance only', () => {
    const decoded = decode_legal_norm_ir(
      norm({
        norm_type: 'applicability',
        modality: 'APP',
        actor: 'This section',
        action: 'applies to food carts',
        cross_references: [{ normalized_text: 'section this section', span: [0, 12] }],
      }),
    );

    expect(decoded.text).toBe('This section applies to food carts.');
    expect(decoded.phrases.at(-1)).toMatchObject({
      slot: 'cross_references',
      text: 'section this section',
      provenanceOnly: true,
    });
    expect(decoded.text).not.toContain('section this section');
  });

  it('reports missing lifecycle slots fail-closed instead of inventing text', () => {
    const decoded = decodeLegalNormIr({ modality: 'LIFE', sourceId: 'license-1' });

    expect(decoded.text).toBe('');
    expect(decoded.missingSlots).toEqual(['instrument', 'lifecycle_action']);
    expect(decoded.sourceId).toBe('license-1');
  });
});
