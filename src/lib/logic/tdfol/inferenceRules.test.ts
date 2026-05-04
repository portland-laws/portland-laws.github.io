import { parseTdfolFormula } from './parser';
import {
  BiconditionalEliminationLeftRule,
  BiconditionalEliminationRightRule,
  BiconditionalIntroductionRule,
  ConjunctionEliminationLeftRule,
  DeonticDAxiomRule,
  DeonticKAxiomRule,
  AlwaysObligationDistributionRule,
  AlwaysPermissionRule,
  DeonticTemporalIntroductionRule,
  DisjunctionIntroductionLeftRule,
  DisjunctiveSyllogismRule,
  EventuallyForbiddenRule,
  ExistentialGeneralizationRule,
  ExistentialInstantiationRule,
  FutureObligationPersistenceRule,
  ModusPonensRule,
  ObligationConjunctionRule,
  ObligationEventuallyRule,
  ObligationWeakeningRightRule,
  PermissionDualityRule,
  PermissionFromNonObligationRule,
  PermissionTemporalWeakeningRule,
  ProhibitionEquivalenceRule,
  TemporalObligationPersistenceRule,
  TemporalKAxiomRule,
  TemporalTAxiomRule,
  UntilObligationRule,
  UniversalGeneralizationRule,
  UniversalModusPonensRule,
  TdfolRule,
  applyTdfolRules,
  formulaEquals,
  getAllTdfolRules,
  tryApplyTdfolRule,
} from './inferenceRules';
import { formatTdfolFormula } from './formatter';

describe('TDFOL inference rules', () => {
  it('applies propositional Modus Ponens and conjunction elimination', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const conjunction = parseTdfolFormula('Pred(x) & Goal(x)');

    expect(ModusPonensRule.canApply(p, implication)).toBe(true);
    expect(formatTdfolFormula(ModusPonensRule.apply(p, implication))).toBe('Goal(x)');
    expect(formatTdfolFormula(ConjunctionEliminationLeftRule.apply(conjunction))).toBe('Pred(x)');
  });

  it('ports remaining Python propositional.py rules without runtime bridges', () => {
    const p = parseTdfolFormula('Pred(x)');
    const q = parseTdfolFormula('Goal(x)');
    const disjunction = parseTdfolFormula('Pred(x) | Goal(x)');
    const notP = parseTdfolFormula('not Pred(x)');
    const pImpliesQ = parseTdfolFormula('Pred(x) -> Goal(x)');
    const qImpliesP = parseTdfolFormula('Goal(x) -> Pred(x)');
    const biconditional = parseTdfolFormula('Pred(x) <-> Goal(x)');

    expect(formatTdfolFormula(DisjunctiveSyllogismRule.apply(disjunction, notP))).toBe('Goal(x)');
    expect(formatTdfolFormula(DisjunctionIntroductionLeftRule.apply(p, q))).toBe(
      '(Pred(x)) ∨ (Goal(x))',
    );
    expect(formatTdfolFormula(BiconditionalIntroductionRule.apply(pImpliesQ, qImpliesP))).toBe(
      '(Pred(x)) ↔ (Goal(x))',
    );
    expect(formatTdfolFormula(BiconditionalEliminationLeftRule.apply(biconditional))).toBe(
      '(Pred(x)) → (Goal(x))',
    );
    expect(formatTdfolFormula(BiconditionalEliminationRightRule.apply(biconditional))).toBe(
      '(Goal(x)) → (Pred(x))',
    );
    expect(
      BiconditionalIntroductionRule.canApply(pImpliesQ, parseTdfolFormula('Other(x) -> Pred(x)')),
    ).toBe(false);
    expect(DisjunctiveSyllogismRule.sourcePythonModule).toBe(
      'logic/TDFOL/inference_rules/propositional.py',
    );
  });

  it('applies temporal K and T axioms', () => {
    const temporalRule = parseTdfolFormula('always(Pred(x) -> Goal(x))');
    const temporalPremise = parseTdfolFormula('always(Pred(x))');

    expect(TemporalKAxiomRule.canApply(temporalRule, temporalPremise)).toBe(true);
    expect(formatTdfolFormula(TemporalKAxiomRule.apply(temporalRule, temporalPremise))).toBe(
      '□(Goal(x))',
    );
    expect(formatTdfolFormula(TemporalTAxiomRule.apply(temporalPremise))).toBe('Pred(x)');
  });

  it('ports Python temporal_deontic.py rules without runtime bridges', () => {
    expect(
      formatTdfolFormula(
        TemporalObligationPersistenceRule.apply(parseTdfolFormula('O(always Pay(x))')),
      ),
    ).toBe('□(O(Pay(x)))');
    expect(
      formatTdfolFormula(DeonticTemporalIntroductionRule.apply(parseTdfolFormula('O(Pay(x))'))),
    ).toBe('O(X(Pay(x)))');
    expect(
      formatTdfolFormula(
        UntilObligationRule.apply(parseTdfolFormula('O(Active(x) U Complete(x))')),
      ),
    ).toBe('◊(O(Complete(x)))');
    expect(
      formatTdfolFormula(AlwaysPermissionRule.apply(parseTdfolFormula('P(always Enter(x))'))),
    ).toBe('□(P(Enter(x)))');
    expect(
      formatTdfolFormula(
        EventuallyForbiddenRule.apply(parseTdfolFormula('F(eventually Breach(x))')),
      ),
    ).toBe('□(F(Breach(x)))');
    expect(
      formatTdfolFormula(
        ObligationEventuallyRule.apply(parseTdfolFormula('O(eventually Cure(x))')),
      ),
    ).toBe('◊(O(Cure(x)))');
    expect(
      formatTdfolFormula(PermissionTemporalWeakeningRule.apply(parseTdfolFormula('P(Enter(x))'))),
    ).toBe('P(◊(Enter(x)))');
    expect(
      formatTdfolFormula(
        AlwaysObligationDistributionRule.apply(parseTdfolFormula('always O(Pay(x))')),
      ),
    ).toBe('O(□(Pay(x)))');
    expect(
      formatTdfolFormula(
        FutureObligationPersistenceRule.apply(parseTdfolFormula('O(next Pay(x))')),
      ),
    ).toBe('X(O(Pay(x)))');

    expect(DeonticTemporalIntroductionRule.canApply(parseTdfolFormula('P(Pay(x))'))).toBe(false);
    expect(UntilObligationRule.sourcePythonModule).toBe(
      'logic/TDFOL/inference_rules/temporal_deontic.py',
    );
  });

  it('applies deontic K, D, and prohibition equivalence rules', () => {
    const deonticRule = parseTdfolFormula('O(Pred(x) -> Goal(x))');
    const deonticPremise = parseTdfolFormula('O(Pred(x))');
    const prohibition = parseTdfolFormula('F(Pred(x))');

    expect(formatTdfolFormula(DeonticKAxiomRule.apply(deonticRule, deonticPremise))).toBe(
      'O(Goal(x))',
    );
    expect(formatTdfolFormula(DeonticDAxiomRule.apply(deonticPremise))).toBe('P(Pred(x))');
    expect(formatTdfolFormula(ProhibitionEquivalenceRule.apply(prohibition))).toBe('O(¬(Pred(x)))');
  });

  it('ports remaining Python deontic inference rule behavior without runtime bridges', () => {
    const obligationLeft = parseTdfolFormula('O(PayRent(tenant))');
    const obligationRight = parseTdfolFormula('O(KeepUnit(tenant))');
    const conjunctiveObligation = parseTdfolFormula('O(PayRent(tenant) & KeepUnit(tenant))');
    const permission = parseTdfolFormula('P(Enter(unit))');
    const nonObligation = parseTdfolFormula('not O(not Enter(unit))');

    expect(
      formatTdfolFormula(ObligationConjunctionRule.apply(obligationLeft, obligationRight)),
    ).toBe('O((PayRent(tenant)) ∧ (KeepUnit(tenant)))');
    expect(formatTdfolFormula(ObligationWeakeningRightRule.apply(conjunctiveObligation))).toBe(
      'O(KeepUnit(tenant))',
    );
    expect(formatTdfolFormula(PermissionDualityRule.apply(permission))).toBe(
      '¬(O(¬(Enter(unit))))',
    );
    expect(formatTdfolFormula(PermissionFromNonObligationRule.apply(nonObligation))).toBe(
      'P(Enter(unit))',
    );
    expect(PermissionDualityRule.sourcePythonModule).toBe('logic/TDFOL/inference_rules/deontic.py');
  });

  it('applies universal modus ponens with repeated variable bindings', () => {
    const rule = parseTdfolFormula('forall x. Parent(x, x) -> Related(x)');
    const premise = parseTdfolFormula('Parent(Alice, Alice)');

    expect(UniversalModusPonensRule.canApply(rule, premise)).toBe(true);
    expect(formatTdfolFormula(UniversalModusPonensRule.apply(rule, premise))).toBe(
      'Related(Alice)',
    );
    expect(UniversalModusPonensRule.canApply(rule, parseTdfolFormula('Parent(Alice, Bob)'))).toBe(
      false,
    );
  });

  it('instantiates and generalizes existential formulas deterministically', () => {
    const existential = parseTdfolFormula('exists x. Permit(x)');
    const ground = parseTdfolFormula('Permit(Alice)');

    expect(formatTdfolFormula(ExistentialInstantiationRule.apply(existential))).toBe(
      'Permit(skolem_x)',
    );
    expect(formatTdfolFormula(ExistentialGeneralizationRule.apply(ground))).toBe('∃x (Permit(x))');
  });

  it('generalizes formulas over the first sorted free variable', () => {
    const formula = parseTdfolFormula('Resident(y) -> Tenant(y)');

    expect(formatTdfolFormula(UniversalGeneralizationRule.apply(formula))).toBe(
      '∀y ((Resident(y)) → (Tenant(y)))',
    );
  });

  it('enumerates rule applications without duplicating known formulas externally', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const applications = applyTdfolRules([p, implication], [ModusPonensRule]);

    expect(applications).toHaveLength(1);
    expect(formulaEquals(applications[0].conclusion, parseTdfolFormula('Goal(x)'))).toBe(true);
    expect(getAllTdfolRules().map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'DeonticKAxiom',
        'DisjunctiveSyllogism',
        'BiconditionalIntroduction',
        'ObligationConjunction',
        'PermissionDuality',
        'UntilObligation',
        'FutureObligationPersistence',
        'UniversalModusPonens',
        'ExistentialInstantiation',
        'ExistentialGeneralization',
        'UniversalGeneralization',
      ]),
    );
  });

  it('ports the Python base rule metadata contract without runtime bridges', () => {
    expect(ModusPonensRule).toMatchObject({
      id: 'modus_ponens',
      category: 'propositional',
      sourcePythonModule: 'logic/TDFOL/inference_rules/propositional.py',
    });
    expect(UniversalModusPonensRule).toMatchObject({
      id: 'universal_modus_ponens',
      category: 'first_order',
      sourcePythonModule: 'logic/TDFOL/inference_rules/first_order.py',
    });
    expect(
      getAllTdfolRules().every(
        (rule) => typeof rule.canApply === 'function' && typeof rule.apply === 'function',
      ),
    ).toBe(true);
  });

  it('tags every browser-native first_order.py rule with its Python source module', () => {
    const firstOrderRules = getAllTdfolRules().filter((rule) => rule.category === 'first_order');

    expect(firstOrderRules.map((rule) => rule.id)).toEqual([
      'universal_modus_ponens',
      'existential_instantiation',
      'existential_generalization',
      'universal_generalization',
    ]);
    expect(
      firstOrderRules.every(
        (rule) => rule.sourcePythonModule === 'logic/TDFOL/inference_rules/first_order.py',
      ),
    ).toBe(true);
  });

  it('validates base rule construction fail-closed', () => {
    expect(
      () =>
        new TdfolRule({
          name: '',
          description: 'invalid',
          arity: 1,
          canApply: () => false,
          apply: (formula) => formula,
        }),
    ).toThrow('name must be non-empty');

    expect(
      () =>
        new TdfolRule({
          name: 'BadArity',
          description: 'invalid',
          arity: -1,
          canApply: () => false,
          apply: (formula) => formula,
        }),
    ).toThrow('invalid arity');
  });

  it('returns fail-closed application results instead of throwing from the base helper', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const result = tryApplyTdfolRule(ModusPonensRule, p, implication);

    expect(result.ok).toBe(true);
    expect(result.conclusion ? formatTdfolFormula(result.conclusion) : '').toBe('Goal(x)');
    expect(tryApplyTdfolRule(ModusPonensRule, implication, p)).toMatchObject({
      ok: false,
      rule: 'ModusPonens',
      error: 'Rule ModusPonens cannot be applied to 2 premise(s)',
    });
  });
});
