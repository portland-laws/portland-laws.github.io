import { parseTdfolFormula } from './parser';
import { proveTdfol, TdfolProver } from './prover';
import { ModusPonensRule, TemporalKAxiomRule, TemporalTAxiomRule } from './inferenceRules';

describe('TdfolProver', () => {
  it('proves direct axioms immediately', () => {
    const theorem = parseTdfolFormula('Pred(x)');
    const result = proveTdfol(theorem, { axioms: [theorem] });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Pred(x)',
      steps: [],
    });
  });

  it('proves via bounded forward chaining', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const q = parseTdfolFormula('Goal(x)');
    const prover = new TdfolProver({ rules: [ModusPonensRule], maxSteps: 5 });

    expect(prover.prove(q, { axioms: [p, implication] })).toMatchObject({
      status: 'proved',
      steps: [{ rule: 'ModusPonens', conclusion: 'Goal(x)' }],
    });
  });

  it('chains temporal rule applications', () => {
    const temporalRule = parseTdfolFormula('always(Pred(x) -> Goal(x))');
    const temporalPremise = parseTdfolFormula('always(Pred(x))');
    const q = parseTdfolFormula('Goal(x)');
    const prover = new TdfolProver({ rules: [TemporalKAxiomRule, TemporalTAxiomRule], maxSteps: 5 });

    expect(prover.prove(q, { axioms: [temporalRule, temporalPremise] })).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
    });
  });

  it('returns unknown when no rule can prove the theorem', () => {
    const prover = new TdfolProver({ rules: [ModusPonensRule], maxSteps: 2 });

    expect(prover.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] })).toMatchObject({
      status: 'unknown',
    });
  });

  it('returns timeout when the derived formula budget is exceeded', () => {
    const prover = new TdfolProver({ maxDerivedFormulas: 1 });

    expect(prover.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] })).toMatchObject({
      status: 'timeout',
      error: 'Derived formula budget exceeded',
    });
  });
});
