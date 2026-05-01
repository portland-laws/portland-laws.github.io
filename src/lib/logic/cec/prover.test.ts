import type { CecExpression } from './ast';
import {
  CecConjunctionEliminationLeftRule,
  CecHypotheticalSyllogismRule,
  CecKnowledgeImpliesBeliefRule,
  CecModusPonensRule,
  CecObligationDistributionRule,
  CecPerceptionImpliesKnowledgeRule,
  CecTemporalTRule,
  CecUniversalModusPonensRule,
  type CecInferenceRule,
} from './inferenceRules';
import { parseCecExpression } from './parser';
import { PYTHON_CEC_DCEC_PARITY_FIXTURES } from './pythonParityFixtures';
import { parseCecProblemString } from './problemParser';
import { CecProver, proveCec } from './prover';
import type { CecShadowFormula } from './shadowProver';

const PARITY_RULES_BY_NAME: { [name: string]: CecInferenceRule } = {
  CecConjunctionEliminationLeft: CecConjunctionEliminationLeftRule,
  CecKnowledgeImpliesBelief: CecKnowledgeImpliesBeliefRule,
  CecObligationDistribution: CecObligationDistributionRule,
  CecPerceptionImpliesKnowledge: CecPerceptionImpliesKnowledgeRule,
  CecUniversalModusPonens: CecUniversalModusPonensRule,
};

function parseShadowFormula(formula: CecShadowFormula): CecExpression {
  return typeof formula === 'string' ? parseCecExpression(formula) : formula;
}

function getParityRules(ruleNames: string[]): CecInferenceRule[] {
  return ruleNames.map((name) => {
    const rule = PARITY_RULES_BY_NAME[name];
    if (!rule) throw new Error(`Missing CEC parity rule fixture mapping: ${name}`);
    return rule;
  });
}

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
    const result = proveCec(
      parseCecExpression('(P (always (comply_with ada portland_city_code_1_05_040)))'),
      {
        axioms: [
          parseCecExpression('(subject_to ada portland_city_code_1_05_040)'),
          parseCecExpression(
            '(forall agent (implies (subject_to agent portland_city_code_1_05_040) (P (always (comply_with agent portland_city_code_1_05_040)))))',
          ),
        ],
      },
      { rules: [CecUniversalModusPonensRule], maxSteps: 3 },
    );

    expect(result).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining',
    });
    expect(result.steps.map((step) => step.rule)).toEqual(['CecUniversalModusPonens']);
  });

  it('selects native CEC rule groups and emits proof trace metadata', () => {
    const result = proveCec(
      parseCecExpression('(K ada wet_pavement)'),
      {
        axioms: [parseCecExpression('(Perceives ada wet_pavement)')],
      },
      { ruleGroups: ['cognitive'], maxSteps: 3 },
    );

    expect(result).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining',
      ruleGroups: ['cognitive'],
    });
    expect(result.trace).toHaveLength(1);
    expect(result.trace[0]).toMatchObject({
      rule: 'CecPerceptionImpliesKnowledge',
      ruleGroup: 'cognitive',
      premises: ['(Perceives ada wet_pavement)'],
      conclusion: '(K ada wet_pavement)',
      derivedExpressionCount: 2,
    });
    expect(result.trace[0].ruleDescription).toContain('Perceives');
  });

  it('keeps grouped CEC delegate attempts local and scoped to selected native families', () => {
    const result = proveCec(
      parseCecExpression('(comply_with agent code)'),
      {
        axioms: [
          parseCecExpression('(always (subject_to agent code))'),
          parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
        ],
      },
      { ruleGroups: ['temporal'], maxSteps: 3 },
    );

    expect(result).toMatchObject({
      status: 'unknown',
      ruleGroups: ['temporal'],
    });
    expect(result.trace.every((step) => step.ruleGroup === 'temporal')).toBe(true);
    expect(result.trace.map((step) => step.rule)).toContain('CecTemporalT');
    expect(result.trace.map((step) => step.rule)).not.toContain('CecModusPonens');
  });

  it('matches Python-captured CEC/DCEC parser and prover parity fixtures', () => {
    expect(PYTHON_CEC_DCEC_PARITY_FIXTURES.map((fixture) => fixture.id)).toEqual([
      'dcec_quantified_portland_obligation',
      'cec_cognitive_perception_to_belief',
      'dcec_obligation_distribution_capture',
    ]);

    for (const fixture of PYTHON_CEC_DCEC_PARITY_FIXTURES) {
      const problem = parseCecProblemString(fixture.problem, fixture.format);
      expect(problem.name).toBe(fixture.expectedProblem.name);
      expect(problem.logic).toBe(fixture.expectedProblem.logic);
      expect(problem.assumptions).toEqual(fixture.expectedProblem.assumptions);
      expect(problem.goals).toEqual(fixture.expectedProblem.goals);
      expect(problem.metadata).toMatchObject(fixture.expectedProblem.metadata);

      const [goal] = problem.goals;
      const result = proveCec(
        parseShadowFormula(goal),
        {
          axioms: problem.assumptions.map(parseShadowFormula),
        },
        {
          rules: getParityRules(fixture.rules),
          maxSteps: fixture.maxSteps,
          maxDerivedExpressions: fixture.maxDerivedExpressions,
        },
      );

      expect(result.status).toBe(fixture.expectedProof.status);
      expect(result.theorem).toBe(fixture.expectedProof.theorem);
      expect(result.method).toBe(fixture.expectedProof.method);
      expect(result.steps.map((step) => step.rule)).toEqual(fixture.expectedProof.stepRules);
      expect(result.steps.map((step) => step.conclusion)).toEqual(
        fixture.expectedProof.stepConclusions,
      );
    }
  });

  it('chains implication transitivity before modus ponens', () => {
    const result = proveCec(
      parseCecExpression('(c)'),
      {
        axioms: [
          parseCecExpression('(a)'),
          parseCecExpression('(implies (a) (b))'),
          parseCecExpression('(implies (b) (c))'),
        ],
      },
      { rules: [CecHypotheticalSyllogismRule, CecModusPonensRule], maxSteps: 4 },
    );

    expect(result).toMatchObject({ status: 'proved' });
    expect(result.steps.map((step) => step.rule)).toEqual(
      expect.arrayContaining(['CecHypotheticalSyllogism', 'CecModusPonens']),
    );
  });

  it('returns unknown when no CEC rule can prove the theorem', () => {
    const result = proveCec(
      parseCecExpression('(comply_with agent code)'),
      {
        axioms: [parseCecExpression('(subject_to agent code)')],
      },
      { rules: [CecModusPonensRule] },
    );

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
