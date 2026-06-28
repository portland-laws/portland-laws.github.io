import {
  TDFOL_INFERENCE_RULES_METADATA,
  TDFOL_INFERENCE_RULES,
  getTdfolInferenceRule,
  listTdfolInferenceRules,
  validateTdfolRuleApplication,
} from './tdfolInferenceRules';

describe('TDFOL inference rules', () => {
  it('exports the deterministic Python parity rule catalog', () => {
    expect(listTdfolInferenceRules().map((rule) => rule.id)).toEqual(
      expect.arrayContaining([
        'modus_ponens',
        'modus_tollens',
        'hypothetical_syllogism',
        'disjunctive_syllogism',
        'conjunction_introduction',
        'conjunction_elimination',
        'disjunction_introduction',
        'double_negation_elimination',
        'biconditional_introduction',
        'biconditional_elimination',
        'temporal_k_axiom',
        'temporal_t_axiom',
        'eventually_introduction',
        'deontic_k_axiom',
        'deontic_d_axiom',
        'prohibition_equivalence',
        'permission_duality',
        'temporal_obligation_persistence',
        'until_obligation',
        'future_obligation_persistence',
        'universal_instantiation',
        'universal_generalization',
        'existential_instantiation',
        'existential_generalization',
      ]),
    );
    expect(listTdfolInferenceRules().length).toBeGreaterThanOrEqual(34);
  });

  it('resolves Python names and common natural-deduction aliases', () => {
    expect(getTdfolInferenceRule('modus_ponens')?.id).toBe('modus_ponens');
    expect(getTdfolInferenceRule('Modus Ponens')?.id).toBe('modus_ponens');
    expect(getTdfolInferenceRule('ui')?.id).toBe('universal_instantiation');
    expect(getTdfolInferenceRule('Temporal K Axiom')?.id).toBe('temporal_k_axiom');
    expect(getTdfolInferenceRule('Permission Duality')?.id).toBe('permission_duality');
    expect(getTdfolInferenceRule('Future Obligation Persistence')?.id).toBe(
      'future_obligation_persistence',
    );
    expect(getTdfolInferenceRule('Existential Generalization')?.id).toBe(
      'existential_generalization',
    );
  });

  it('keeps monolithic rule categories marked separately', () => {
    const categoryCounts = TDFOL_INFERENCE_RULES.reduce<Record<string, number>>((counts, rule) => {
      counts[rule.kind] = (counts[rule.kind] ?? 0) + 1;
      return counts;
    }, {});
    const quantifierRuleIds = TDFOL_INFERENCE_RULES.filter(
      (rule) => rule.kind === 'quantifier',
    ).map((rule) => rule.id);

    expect(categoryCounts).toMatchObject({
      propositional: 10,
      temporal: 3,
      deontic: 8,
      temporal_deontic: 9,
      quantifier: 4,
    });
    expect(quantifierRuleIds).toEqual([
      'universal_instantiation',
      'universal_generalization',
      'existential_instantiation',
      'existential_generalization',
    ]);
  });

  it('validates browser-native rule applications fail-closed', () => {
    expect(
      validateTdfolRuleApplication({
        rule: 'mp',
        premises: ['P', 'P -> Q'],
        conclusions: ['Q'],
      }),
    ).toMatchObject({ ok: true, rule: { id: 'modus_ponens' } });

    expect(
      validateTdfolRuleApplication({
        rule: 'temporal_obligation_persistence',
        premises: ['O(always Pay(x))'],
        conclusions: ['always O(Pay(x))'],
      }),
    ).toMatchObject({ ok: true, rule: { kind: 'temporal_deontic' } });

    expect(
      validateTdfolRuleApplication({
        rule: 'modus_ponens',
        premises: ['P'],
      }),
    ).toMatchObject({ ok: false, rule: { id: 'modus_ponens' } });

    expect(
      validateTdfolRuleApplication({
        rule: 'server_backed_rule',
        premises: [],
      }),
    ).toMatchObject({ ok: false });
  });

  it('records browser-native monolithic Python module metadata without runtime dependencies', () => {
    expect(TDFOL_INFERENCE_RULES_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/tdfol_inference_rules.py',
      browserNative: true,
      runtimeDependencies: [],
    });
    expect(
      TDFOL_INFERENCE_RULES.every(
        (rule) => rule.sourcePythonModule === 'logic/TDFOL/tdfol_inference_rules.py',
      ),
    ).toBe(true);
  });
});
