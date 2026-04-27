import { formatCecExpression } from './formatter';
import {
  CecConjunctionIntroductionRule,
  CecConjunctionEliminationLeftRule,
  CecBeliefDistributionRule,
  CecBeliefConjunctionRule,
  CecBeliefMonotonicityRule,
  CecBeliefNegationRule,
  CecBeliefRevisionRule,
  CecDeonticDRule,
  CecDoubleNegationEliminationRule,
  CecEventuallyIntroductionRule,
  CecExistentialGeneralizationRule,
  CecExistentialInstantiationRule,
  CecHypotheticalSyllogismRule,
  CecIntentionCommitmentRule,
  CecIntentionMeansEndRule,
  CecIntentionPersistenceRule,
  CecKnowledgeConjunctionRule,
  CecKnowledgeDistributionRule,
  CecKnowledgeImpliesBeliefRule,
  CecKnowledgeMonotonicityRule,
  CecModusPonensRule,
  CecPerceptionImpliesKnowledgeRule,
  CecCaseAnalysisRule,
  CecFactoringRule,
  CecProofByContradictionRule,
  CecResolutionRule,
  CecSubsumptionRule,
  CecUnitResolutionRule,
  CecProhibitionFromObligationRule,
  CecProhibitionEquivalenceRule,
  CecTemporalTRule,
  CecUniversalGeneralizationRule,
  CecUniversalModusPonensRule,
  applyCecRules,
  cecExpressionEquals,
  getAllCecRules,
  getCognitiveCecRules,
  getGenerativeCecRules,
  getResolutionCecRules,
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

  it('applies cognitive CEC belief and knowledge rules', () => {
    expect(formatCecExpression(CecBeliefDistributionRule.apply(
      parseCecExpression('(B alice (and (raining) (cold)))'),
    ))).toBe('(and (B alice (raining)) (B alice (cold)))');

    expect(formatCecExpression(CecKnowledgeImpliesBeliefRule.apply(
      parseCecExpression('(K alice (true_fact))'),
    ))).toBe('(B alice (true_fact))');

    expect(formatCecExpression(CecBeliefMonotonicityRule.apply(
      parseCecExpression('(B alice (raining))'),
      parseCecExpression('(implies (raining) (wet))'),
    ))).toBe('(B alice (wet))');

    expect(formatCecExpression(CecKnowledgeDistributionRule.apply(
      parseCecExpression('(K alice (and (p) (q)))'),
    ))).toBe('(and (K alice (p)) (K alice (q)))');

    expect(formatCecExpression(CecBeliefNegationRule.apply(
      parseCecExpression('(B alice (not (raining)))'),
    ))).toBe('(not (B alice (raining)))');

    expect(formatCecExpression(CecKnowledgeMonotonicityRule.apply(
      parseCecExpression('(K alice (human socrates))'),
      parseCecExpression('(implies (human socrates) (mortal socrates))'),
    ))).toBe('(K alice (mortal socrates))');
  });

  it('applies cognitive CEC intention and perception rules', () => {
    expect(formatCecExpression(CecIntentionCommitmentRule.apply(
      parseCecExpression('(I alice (go_store))'),
      parseCecExpression('(B alice (implies (go_store) (buy_milk)))'),
    ))).toBe('(I alice (buy_milk))');

    expect(formatCecExpression(CecIntentionMeansEndRule.apply(
      parseCecExpression('(I alice (arrive_work))'),
      parseCecExpression('(B alice (implies (take_bus) (arrive_work)))'),
    ))).toBe('(I alice (take_bus))');

    expect(formatCecExpression(CecPerceptionImpliesKnowledgeRule.apply(
      parseCecExpression('(Perceives alice (light_on))'),
    ))).toBe('(K alice (light_on))');

    expect(formatCecExpression(CecIntentionPersistenceRule.apply(
      parseCecExpression('(I alice (go_store))'),
      parseCecExpression('(not (B alice (go_store)))'),
    ))).toBe('(I alice (go_store))');

    expect(formatCecExpression(CecBeliefRevisionRule.apply(
      parseCecExpression('(B alice (light_off))'),
      parseCecExpression('(Perceives alice (not (light_off)))'),
    ))).toBe('(B alice (not (light_off)))');
  });

  it('keeps cognitive conjunction generation opt-in', () => {
    expect(formatCecExpression(CecBeliefConjunctionRule.apply(
      parseCecExpression('(B alice (raining))'),
      parseCecExpression('(B alice (cold))'),
    ))).toBe('(B alice (and (raining) (cold)))');

    expect(formatCecExpression(CecKnowledgeConjunctionRule.apply(
      parseCecExpression('(K alice (p))'),
      parseCecExpression('(K alice (q))'),
    ))).toBe('(K alice (and (p) (q)))');
  });

  it('applies resolution CEC rules', () => {
    expect(formatCecExpression(CecResolutionRule.apply(
      parseCecExpression('(or (home alice) (work alice))'),
      parseCecExpression('(or (not (home alice)) (busy alice))'),
    ))).toBe('(or (work alice) (busy alice))');

    expect(formatCecExpression(CecUnitResolutionRule.apply(
      parseCecExpression('(home alice)'),
      parseCecExpression('(or (not (home alice)) (busy alice))'),
    ))).toBe('(busy alice)');

    expect(formatCecExpression(CecFactoringRule.apply(
      parseCecExpression('(or (busy alice) (busy alice))'),
    ))).toBe('(busy alice)');

    expect(formatCecExpression(CecSubsumptionRule.apply(
      parseCecExpression('(or (p) (q))'),
      parseCecExpression('(or (p) (or (q) (r)))'),
    ))).toBe('(or (p) (q))');

    expect(formatCecExpression(CecCaseAnalysisRule.apply(
      parseCecExpression('(or (home alice) (work alice))'),
      parseCecExpression('(implies (home alice) (reachable alice))'),
      parseCecExpression('(implies (work alice) (reachable alice))'),
    ))).toBe('(reachable alice)');

    expect(formatCecExpression(CecProofByContradictionRule.apply(
      parseCecExpression('(busy alice)'),
      parseCecExpression('(not (busy alice))'),
    ))).toBe('contradiction');
  });

  it('enumerates three-premise resolution applications', () => {
    const applications = applyCecRules([
      parseCecExpression('(or (home alice) (work alice))'),
      parseCecExpression('(implies (home alice) (reachable alice))'),
      parseCecExpression('(implies (work alice) (reachable alice))'),
    ], [CecCaseAnalysisRule]);

    expect(applications).toHaveLength(1);
    expect(applications[0].premises).toHaveLength(3);
    expect(formatCecExpression(applications[0].conclusion)).toBe('(reachable alice)');
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
    expect(getAllCecRules().map((rule) => rule.name)).not.toContain('CecBeliefConjunction');
    expect(getCognitiveCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecKnowledgeImpliesBelief',
      'CecBeliefMonotonicity',
      'CecPerceptionImpliesKnowledge',
      'CecBeliefRevision',
    ]));
    expect(getGenerativeCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecConjunctionIntroduction',
      'CecEventuallyIntroduction',
      'CecBeliefConjunction',
    ]));
    expect(getResolutionCecRules().map((rule) => rule.name)).toEqual(expect.arrayContaining([
      'CecResolution',
      'CecUnitResolution',
      'CecFactoring',
      'CecCaseAnalysis',
    ]));
  });
});
