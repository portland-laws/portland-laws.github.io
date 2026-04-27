import { formatCecExpression } from './formatter';
import {
  CecConjunctionIntroductionRule,
  CecConjunctionEliminationLeftRule,
  CecDeonticDRule,
  CecDoubleNegationEliminationRule,
  CecEventuallyIntroductionRule,
  CecExistentialGeneralizationRule,
  CecExistentialInstantiationRule,
  CecHypotheticalSyllogismRule,
  CecModusPonensRule,
  CecProhibitionFromObligationRule,
  CecProhibitionEquivalenceRule,
  CecTemporalTRule,
  CecUniversalGeneralizationRule,
  CecUniversalModusPonensRule,
  applyCecRules,
  cecExpressionEquals,
  getAllCecRules,
  getGenerativeCecRules,
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
    expect(formatCecExpression(CecHypotheticalSyllogismRule.apply(
      parseCecExpression('(implies (a) (b))'),
      parseCecExpression('(implies (b) (c))'),
    ))).toBe('(implies (a) (c))');
    expect(formatCecExpression(CecConjunctionIntroductionRule.apply(
      parseCecExpression('(a)'),
      parseCecExpression('(b)'),
    ))).toBe('(and (a) (b))');
    expect(formatCecExpression(CecConjunctionEliminationLeftRule.apply(conjunction))).toBe('(subject_to agent code)');
    expect(formatCecExpression(CecDoubleNegationEliminationRule.apply(doubleNegation))).toBe('(active code)');
  });

  it('applies temporal and deontic CEC rules', () => {
    const always = parseCecExpression('(always (comply_with agent code))');
    const obligation = parseCecExpression('(O (comply_with agent code))');
    const prohibition = parseCecExpression('(F (enter agent code))');

    expect(formatCecExpression(CecTemporalTRule.apply(always))).toBe('(comply_with agent code)');
    expect(formatCecExpression(CecEventuallyIntroductionRule.apply(parseCecExpression('(active code)'))))
      .toBe('(eventually (active code))');
    expect(formatCecExpression(CecDeonticDRule.apply(obligation))).toBe('(P (comply_with agent code))');
    expect(formatCecExpression(CecProhibitionEquivalenceRule.apply(prohibition))).toBe('(O (not (enter agent code)))');
    expect(formatCecExpression(CecProhibitionFromObligationRule.apply(parseCecExpression('(O (not (enter agent code)))'))))
      .toBe('(F (enter agent code))');
  });

  it('applies quantified CEC rules', () => {
    expect(formatCecExpression(CecUniversalModusPonensRule.apply(
      parseCecExpression('(forall agent (implies (subject_to agent code) (P (always (comply_with agent code)))))'),
      parseCecExpression('(subject_to ada code)'),
    ))).toBe('(P (always (comply_with ada code)))');

    expect(formatCecExpression(CecExistentialInstantiationRule.apply(
      parseCecExpression('(exists agent (subject_to agent code))'),
    ))).toBe('(subject_to skolem_agent code)');

    expect(formatCecExpression(CecExistentialGeneralizationRule.apply(
      parseCecExpression('(subject_to ada code)'),
    ))).toBe('(exists x (subject_to x code))');

    expect(formatCecExpression(CecUniversalGeneralizationRule.apply(
      parseCecExpression('(subject_to agent code)'),
    ))).toBe('(forall agent (subject_to agent code))');
  });

  it('enumerates CEC rule applications and compares expressions by normalized form', () => {
    const premise = parseCecExpression('(subject_to agent code)');
    const implication = parseCecExpression('(implies (subject_to agent code) (comply_with agent code))');
    const applications = applyCecRules([premise, implication], [CecModusPonensRule]);

    expect(applications).toHaveLength(1);
    expect(cecExpressionEquals(applications[0].conclusion, parseCecExpression('(comply_with agent code)'))).toBe(true);
    expect(getAllCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecModusPonens',
      'CecHypotheticalSyllogism',
      'CecTemporalT',
      'CecDeonticD',
      'CecProhibitionEquivalence',
      'CecUniversalModusPonens',
    ]));
    expect(getAllCecRules().map((rule) => rule.name)).not.toContain('CecConjunctionIntroduction');
    expect(getGenerativeCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecConjunctionIntroduction',
      'CecEventuallyIntroduction',
    ]));
  });
});
