import {
  TDFOL_INFERENCE_RULES,
  getTdfolInferenceRule,
  listTdfolInferenceRules,
  validateTdfolRuleApplication,
} from './tdfolInferenceRules';

describe('TDFOL inference rules', () => {
  it('exports the deterministic Python parity rule catalog', () => {
    expect(listTdfolInferenceRules().map((rule) => rule.id)).toEqual([
      'modus_ponens',
      'modus_tollens',
      'hypothetical_syllogism',
      'disjunctive_syllogism',
      'conjunction_introduction',
      'conjunction_elimination',
      'disjunction_introduction',
      'biconditional_introduction',
      'biconditional_elimination',
      'universal_instantiation',
      'universal_generalization',
      'existential_instantiation',
      'existential_generalization',
    ]);
  });

  it('resolves Python names and common natural-deduction aliases', () => {
    expect(getTdfolInferenceRule('modus_ponens')?.id).toBe('modus_ponens');
    expect(getTdfolInferenceRule('Modus Ponens')?.id).toBe('modus_ponens');
    expect(getTdfolInferenceRule('ui')?.id).toBe('universal_instantiation');
    expect(getTdfolInferenceRule('Existential Generalization')?.id).toBe(
      'existential_generalization',
    );
  });

  it('keeps quantifier rules marked separately from propositional rules', () => {
    const quantifierRuleIds = TDFOL_INFERENCE_RULES.filter(
      (rule) => rule.kind === 'quantifier',
    ).map((rule) => rule.id);

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
});
