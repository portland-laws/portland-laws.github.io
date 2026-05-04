import {
  buildDeonticProverSyntaxRecordFromIr,
  normalizeDeonticProverFormula,
  validateDeonticProverSyntax,
} from './proverSyntax';

describe('deontic prover syntax', () => {
  it('validates deontic prover formulas without Python or server dependencies', () => {
    expect(
      normalizeDeonticProverFormula('O(\u2200x (Tenant(x) \u2227 Notice(x) \u2192 PayRent(x)))'),
    ).toBe('O(forall x (Tenant(x) and Notice(x) -> PayRent(x)))');
    const validation = validateDeonticProverSyntax(
      'O(\u2200x (Tenant(x) \u2227 not Exempt(x) \u2192 PayRent(x)))',
    );

    expect(validation).toMatchObject({
      valid: true,
      normalized_formula: 'O(forall x (Tenant(x) and not Exempt(x) -> PayRent(x)))',
      modality: 'O',
      consequent: 'PayRent(x)',
      blockers: [],
    });
    expect(validation.antecedents).toEqual(['Tenant(x)', 'not Exempt(x)']);
  });

  it('fails closed for unsupported prover syntax', () => {
    expect(validateDeonticProverSyntax('O(Tenant(x) -> PayRent(x))')).toMatchObject({
      valid: false,
      blockers: ['unsupported_deontic_prover_syntax'],
    });
  });

  it('builds proof readiness records from IR-like parser rows', () => {
    const record = buildDeonticProverSyntaxRecordFromIr({
      source_id: 'sec-2',
      norm_type: 'obligation',
      actor: 'Tenant',
      modality: 'O',
      action: 'pay rent',
      proof_ready: true,
    });

    expect(record).toMatchObject({
      target_logic: 'deontic_fol',
      normalized_formula: 'O(forall x (Tenant(x) -> PayRent(x)))',
      proof_ready: true,
      server_calls_allowed: false,
      python_runtime: false,
    });
  });

  it('preserves omitted slots as validation blockers in syntax records', () => {
    const record = buildDeonticProverSyntaxRecordFromIr({
      source_id: 'sec-2',
      norm_type: 'obligation',
      actor: 'Tenant',
      modality: 'O',
      action: '',
      proof_ready: true,
    });

    expect(record.proof_ready).toBe(false);
    expect(record.requires_validation).toBe(true);
    expect(record.omitted_formula_slots).toEqual(['action']);
    expect(record.blockers).toContain('missing_formula_slot:action');
  });
});
