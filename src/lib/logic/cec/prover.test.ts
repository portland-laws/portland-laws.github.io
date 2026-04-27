import {
  CecHypotheticalSyllogismRule,
  CecModusPonensRule,
  CecTemporalTRule,
  CecUniversalModusPonensRule,
  type CecInferenceRule,
} from './inferenceRules';
import { parseCecExpression } from './parser';
import { CecProver, proveCec } from './prover';

describe('CEC prover', () => {
  it('proves direct knowledge-base expressions', () => {
    const theorem = parseCecExpression('(subject_to agent code)');
    const result = proveCec(theorem, { axioms: [theorem] });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(subject_to agent code)',
      steps: [],
      method: 'cec-forward-chaining',
    });
  });

  it('derives expressions with bounded native CEC rules', () => {
    const prover = new CecProver({ rules: [CecModusPonensRule, CecTemporalTRule], maxSteps: 5 });
    const result = prover.prove(parseCecExpression('(comply_with agent code)'), {
      axioms: [
        parseCecExpression('(always (subject_to agent code))'),
        parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
      ],
    });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(comply_with agent code)',
      method: 'cec-forward-chaining',
    });
    expect(result.steps.map((step) => step.rule)).toEqual(['CecTemporalT', 'CecModusPonens']);
  });

  it('derives quantified Portland-style DCEC facts without Python delegation', () => {
    const result = proveCec(parseCecExpression('(P (always (comply_with ada portland_city_code_1_05_040)))'), {
      axioms: [
        parseCecExpression('(subject_to ada portland_city_code_1_05_040)'),
        parseCecExpression('(forall agent (implies (subject_to agent portland_city_code_1_05_040) (P (always (comply_with agent portland_city_code_1_05_040)))))'),
      ],
    }, { rules: [CecUniversalModusPonensRule], maxSteps: 3 });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining',
    });
    expect(result.steps.map((step) => step.rule)).toEqual(['CecUniversalModusPonens']);
  });

  it('chains implication transitivity before modus ponens', () => {
    const result = proveCec(parseCecExpression('(c)'), {
      axioms: [
        parseCecExpression('(a)'),
        parseCecExpression('(implies (a) (b))'),
        parseCecExpression('(implies (b) (c))'),
      ],
    }, { rules: [CecHypotheticalSyllogismRule, CecModusPonensRule], maxSteps: 4 });

    expect(result).toMatchObject({ status: 'proved' });
    expect(result.steps.map((step) => step.rule)).toEqual(expect.arrayContaining([
      'CecHypotheticalSyllogism',
      'CecModusPonens',
    ]));
  });

  it('returns unknown when no CEC rule can prove the theorem', () => {
    const result = proveCec(parseCecExpression('(comply_with agent code)'), {
      axioms: [parseCecExpression('(subject_to agent code)')],
    }, { rules: [CecModusPonensRule] });

    expect(result).toMatchObject({
      status: 'unknown',
      error: undefined,
    });
  });

  it('respects the derived expression budget', () => {
    const expandingRule: CecInferenceRule = {
      name: 'CecEventuallyExpansion',
      description: 'Wraps every expression in eventually',
      arity: 1,
      canApply: () => true,
      apply: (expression) => ({ kind: 'unary', operator: 'eventually', expression }),
    };
    const prover = new CecProver({ rules: [expandingRule], maxDerivedExpressions: 2 });
    const result = prover.prove(parseCecExpression('(unreachable agent code)'), {
      axioms: [parseCecExpression('(subject_to agent code)')],
    });

    expect(result).toMatchObject({
      status: 'timeout',
      error: 'Derived expression budget exceeded',
    });
  });
});
