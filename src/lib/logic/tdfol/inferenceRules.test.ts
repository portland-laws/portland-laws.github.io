import { parseTdfolFormula } from './parser';
import {
  ConjunctionEliminationLeftRule,
  DeonticDAxiomRule,
  DeonticKAxiomRule,
  ExistentialGeneralizationRule,
  ExistentialInstantiationRule,
  ModusPonensRule,
  ProhibitionEquivalenceRule,
  TemporalKAxiomRule,
  TemporalTAxiomRule,
  UniversalGeneralizationRule,
  UniversalModusPonensRule,
  applyTdfolRules,
  formulaEquals,
  getAllTdfolRules,
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

  it('applies temporal K and T axioms', () => {
    const temporalRule = parseTdfolFormula('always(Pred(x) -> Goal(x))');
    const temporalPremise = parseTdfolFormula('always(Pred(x))');

    expect(TemporalKAxiomRule.canApply(temporalRule, temporalPremise)).toBe(true);
    expect(formatTdfolFormula(TemporalKAxiomRule.apply(temporalRule, temporalPremise))).toBe('□(Goal(x))');
    expect(formatTdfolFormula(TemporalTAxiomRule.apply(temporalPremise))).toBe('Pred(x)');
  });

  it('applies deontic K, D, and prohibition equivalence rules', () => {
    const deonticRule = parseTdfolFormula('O(Pred(x) -> Goal(x))');
    const deonticPremise = parseTdfolFormula('O(Pred(x))');
    const prohibition = parseTdfolFormula('F(Pred(x))');

    expect(formatTdfolFormula(DeonticKAxiomRule.apply(deonticRule, deonticPremise))).toBe('O(Goal(x))');
    expect(formatTdfolFormula(DeonticDAxiomRule.apply(deonticPremise))).toBe('P(Pred(x))');
    expect(formatTdfolFormula(ProhibitionEquivalenceRule.apply(prohibition))).toBe('O(¬(Pred(x)))');
  });

  it('applies universal modus ponens with repeated variable bindings', () => {
    const rule = parseTdfolFormula('forall x. Parent(x, x) -> Related(x)');
    const premise = parseTdfolFormula('Parent(Alice, Alice)');

    expect(UniversalModusPonensRule.canApply(rule, premise)).toBe(true);
    expect(formatTdfolFormula(UniversalModusPonensRule.apply(rule, premise))).toBe('Related(Alice)');
    expect(UniversalModusPonensRule.canApply(rule, parseTdfolFormula('Parent(Alice, Bob)'))).toBe(false);
  });

  it('instantiates and generalizes existential formulas deterministically', () => {
    const existential = parseTdfolFormula('exists x. Permit(x)');
    const ground = parseTdfolFormula('Permit(Alice)');

    expect(formatTdfolFormula(ExistentialInstantiationRule.apply(existential))).toBe('Permit(skolem_x)');
    expect(formatTdfolFormula(ExistentialGeneralizationRule.apply(ground))).toBe('∃x (Permit(x))');
  });

  it('generalizes formulas over the first sorted free variable', () => {
    const formula = parseTdfolFormula('Resident(y) -> Tenant(y)');

    expect(formatTdfolFormula(UniversalGeneralizationRule.apply(formula))).toBe('∀y ((Resident(y)) → (Tenant(y)))');
  });

  it('enumerates rule applications without duplicating known formulas externally', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const applications = applyTdfolRules([p, implication], [ModusPonensRule]);

    expect(applications).toHaveLength(1);
    expect(formulaEquals(applications[0].conclusion, parseTdfolFormula('Goal(x)'))).toBe(true);
    expect(getAllTdfolRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'DeonticKAxiom',
      'UniversalModusPonens',
      'ExistentialInstantiation',
      'ExistentialGeneralization',
      'UniversalGeneralization',
    ]));
  });
});
