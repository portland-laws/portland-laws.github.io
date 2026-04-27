import { formatCecExpression } from './formatter';
import {
  CecConjunctionEliminationLeftRule,
  CecDeonticDRule,
  CecDoubleNegationEliminationRule,
  CecModusPonensRule,
  CecProhibitionEquivalenceRule,
  CecTemporalTRule,
  applyCecRules,
  cecExpressionEquals,
  getAllCecRules,
} from './inferenceRules';
import { parseCecExpression } from './parser';

describe('CEC inference rules', () => {
  it('applies propositional CEC rules', () => {
    const premise = parseCecExpression('(subject_to agent code)');
    const implication = parseCecExpression('(implies (subject_to agent code) (comply_with agent code))');
    const conjunction = parseCecExpression('(and (subject_to agent code) (active code))');
    const doubleNegation = parseCecExpression('(not (not (active code)))');

    expect(CecModusPonensRule.canApply(premise, implication)).toBe(true);
    expect(formatCecExpression(CecModusPonensRule.apply(premise, implication))).toBe('(comply_with agent code)');
    expect(formatCecExpression(CecConjunctionEliminationLeftRule.apply(conjunction))).toBe('(subject_to agent code)');
    expect(formatCecExpression(CecDoubleNegationEliminationRule.apply(doubleNegation))).toBe('(active code)');
  });

  it('applies temporal and deontic CEC rules', () => {
    const always = parseCecExpression('(always (comply_with agent code))');
    const obligation = parseCecExpression('(O (comply_with agent code))');
    const prohibition = parseCecExpression('(F (enter agent code))');

    expect(formatCecExpression(CecTemporalTRule.apply(always))).toBe('(comply_with agent code)');
    expect(formatCecExpression(CecDeonticDRule.apply(obligation))).toBe('(P (comply_with agent code))');
    expect(formatCecExpression(CecProhibitionEquivalenceRule.apply(prohibition))).toBe('(O (not (enter agent code)))');
  });

  it('enumerates CEC rule applications and compares expressions by normalized form', () => {
    const premise = parseCecExpression('(subject_to agent code)');
    const implication = parseCecExpression('(implies (subject_to agent code) (comply_with agent code))');
    const applications = applyCecRules([premise, implication], [CecModusPonensRule]);

    expect(applications).toHaveLength(1);
    expect(cecExpressionEquals(applications[0].conclusion, parseCecExpression('(comply_with agent code)'))).toBe(true);
    expect(getAllCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecModusPonens',
      'CecTemporalT',
      'CecDeonticD',
      'CecProhibitionEquivalence',
    ]));
  });
});
