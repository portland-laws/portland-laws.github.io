import {
  EXPORT_TABLE_SPECS,
  buildDecoderRecordFromIr,
  buildDocumentExportTablesFromIr,
  buildFormalLogicRecordFromIr,
  parser_elements_to_export_tables,
  type ExportLegalNormLike,
} from './exports';

function norm(overrides: Partial<ExportLegalNormLike> = {}): ExportLegalNormLike {
  return {
    source_id: 'sec-2',
    canonical_citation: 'PCC 1.02',
    norm_type: 'obligation',
    actor: 'Tenant',
    modality: 'O',
    action: 'pay rent',
    support_span: [0, 22],
    field_spans: { actor: [0, 6], action: [14, 22] },
    proof_ready: true,
    ...overrides,
  };
}

describe('deontic export builders', () => {
  it('defines deterministic table specs without server or Python dependencies', () => {
    expect(EXPORT_TABLE_SPECS.formal_logic).toEqual({
      primary_key: 'formula_id',
      requires_source_id: true,
    });
    expect(EXPORT_TABLE_SPECS.repair_queue.primary_key).toBe('repair_id');
  });

  it('builds canonical, formal, proof, and decoder rows from IR-like records', () => {
    const tables = buildDocumentExportTablesFromIr([norm()]);

    expect(tables.canonical).toHaveLength(1);
    expect(tables.formal_logic[0]).toMatchObject({
      source_id: 'sec-2',
      target_logic: 'deontic_fol',
      proof_ready: true,
      requires_validation: false,
      omitted_formula_slots: [],
    });
    expect(tables.formal_logic[0].formula).toBe('O(forall x (Tenant(x) -> PayRent(x)))');
    expect(tables.proof_obligations[0]).toMatchObject({ theorem_candidate: true });
    expect(tables.decoder_reconstructions[0]).toMatchObject({
      decoded_text: 'Tenant shall pay rent.',
      grounded_decoded_phrase_rate: 1,
    });
    expect(tables.repair_queue).toEqual([]);
  });

  it('fails closed into repair rows when required formula slots are missing', () => {
    const formal = buildFormalLogicRecordFromIr(norm({ action: '', proof_ready: false }));
    const tables = parser_elements_to_export_tables([
      norm({ action: '', proof_ready: false }) as Record<string, unknown>,
    ]);

    expect(formal).toMatchObject({
      proof_ready: false,
      requires_validation: true,
      omitted_formula_slots: ['action'],
    });
    expect(formal.blockers).toEqual(['missing_formula_slot:action']);
    expect(tables.repair_queue[0]).toMatchObject({
      requires_llm_repair: false,
      allow_llm_repair: false,
      reasons: ['missing_formula_slot:action'],
    });
  });

  it('preserves decoder phrase provenance in reconstruction rows', () => {
    const decoded = buildDecoderRecordFromIr(
      norm({ action: 'notify applicant', recipient: 'applicant' }),
    );

    expect(decoded.phrase_provenance).toEqual([
      expect.objectContaining({ slot: 'actor', spans: [[0, 6]] }),
      expect.objectContaining({ slot: 'modality' }),
      expect.objectContaining({ slot: 'action', spans: [[14, 22]] }),
    ]);
  });
});
