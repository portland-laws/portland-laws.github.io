import type { CecInferenceRule } from './inferenceRules';
import {
  CecAbsorptionRule,
  CecAdditionRule,
  CecAssociationRule,
  CecBeliefConjunctionRule,
  CecBeliefDistributionRule,
  CecBeliefMonotonicityRule,
  CecBeliefNegationRule,
  CecBeliefRevisionRule,
  CecBiconditionalEliminationRule,
  CecBiconditionalIntroductionRule,
  CecCaseAnalysisRule,
  CecClaviusLawRule,
  CecCommonBeliefIntroductionRule,
  CecCommonKnowledgeDistributionRule,
  CecCommonKnowledgeImpliesKnowledgeRule,
  CecCommonKnowledgeIntroductionRule,
  CecCommonKnowledgeMonotonicityRule,
  CecCommonKnowledgeNegationRule,
  CecCommonKnowledgeTransitivityRule,
  CecCommutativityConjunctionRule,
  CecCommutativityDisjunctionRule,
  CecConjunctionEliminationLeftRule,
  CecConjunctionEliminationRightRule,
  CecConjunctionIntroductionRule,
  CecConstructiveDilemmaRule,
  CecDeonticDRule,
  CecDestructiveDilemmaRule,
  CecDistributionRule,
  CecDoubleNegationEliminationRule,
  CecEventuallyDistributionRule,
  CecEventuallyFromAlwaysRule,
  CecEventuallyImplicationRule,
  CecEventuallyIntroductionRule,
  CecEventuallyTransitiveRule,
  CecExistentialGeneralizationRule,
  CecExistentialInstantiationRule,
  CecExportationRule,
  CecFactoringRule,
  CecFixedPointInductionRule,
  CecHypotheticalSyllogismRule,
  CecIdempotenceRule,
  CecIntentionCommitmentRule,
  CecIntentionMeansEndRule,
  CecIntentionPersistenceRule,
  CecKnowledgeConjunctionRule,
  CecKnowledgeDistributionRule,
  CecKnowledgeImpliesBeliefRule,
  CecKnowledgeMonotonicityRule,
  CecMaterialImplicationRule,
  CecModalNecessitationIntroductionRule,
  CecModusPonensRule,
  CecNecessityConjunctionRule,
  CecNecessityDistributionRule,
  CecNecessityEliminationRule,
  CecNextDistributionRule,
  CecNextImplicationRule,
  CecObligationConjunctionRule,
  CecObligationConsistencyRule,
  CecObligationDistributionRule,
  CecObligationImplicationRule,
  CecPerceptionImpliesKnowledgeRule,
  CecPermissionDistributionRule,
  CecPermissionFromNonObligationRule,
  CecPossibilityDualityRule,
  CecPossibilityIntroductionRule,
  CecProhibitionEquivalenceRule,
  CecProhibitionFromObligationRule,
  CecProofByContradictionRule,
  CecResolutionRule,
  CecSinceWeakeningRule,
  CecSubsumptionRule,
  CecTautologyRule,
  CecTemporalNegationRule,
  CecTemporalTRule,
  CecTemporalUntilEliminationRule,
  CecTemporallyInducedCommonKnowledgeRule,
  CecTranspositionRule,
  CecUnitResolutionRule,
  CecUntilWeakeningRule,
  CecUniversalGeneralizationRule,
  CecUniversalModusPonensRule,
} from './inferenceRules';

export type CecNativeRuleGroupName =
  | 'propositional'
  | 'modal'
  | 'temporal'
  | 'deontic'
  | 'cognitive'
  | 'specialized'
  | 'resolution';

export type CecNativeRuleGroup = {
  name: CecNativeRuleGroupName;
  rules: readonly CecInferenceRule[];
};

export const CecPropositionalNativeRuleGroup: CecNativeRuleGroup = {
  name: 'propositional',
  rules: [
    CecModusPonensRule,
    CecHypotheticalSyllogismRule,
    CecConjunctionIntroductionRule,
    CecConjunctionEliminationLeftRule,
    CecConjunctionEliminationRightRule,
    CecDoubleNegationEliminationRule,
    CecMaterialImplicationRule,
    CecBiconditionalIntroductionRule,
    CecBiconditionalEliminationRule,
    CecTranspositionRule,
    CecTautologyRule,
    CecClaviusLawRule,
    CecAssociationRule,
    CecCommutativityConjunctionRule,
    CecCommutativityDisjunctionRule,
    CecDistributionRule,
    CecAbsorptionRule,
    CecIdempotenceRule,
    CecConstructiveDilemmaRule,
    CecDestructiveDilemmaRule,
    CecExportationRule,
    CecAdditionRule,
  ],
};

export const CecModalNativeRuleGroup: CecNativeRuleGroup = {
  name: 'modal',
  rules: [
    CecNecessityEliminationRule,
    CecPossibilityIntroductionRule,
    CecNecessityDistributionRule,
    CecPossibilityDualityRule,
    CecNecessityConjunctionRule,
    CecModalNecessitationIntroductionRule,
  ],
};

export const CecTemporalNativeRuleGroup: CecNativeRuleGroup = {
  name: 'temporal',
  rules: [
    CecTemporalTRule,
    CecEventuallyIntroductionRule,
    CecEventuallyDistributionRule,
    CecEventuallyFromAlwaysRule,
    CecEventuallyImplicationRule,
    CecEventuallyTransitiveRule,
    CecNextDistributionRule,
    CecNextImplicationRule,
    CecUntilWeakeningRule,
    CecSinceWeakeningRule,
    CecTemporalUntilEliminationRule,
    CecTemporalNegationRule,
  ],
};

export const CecDeonticNativeRuleGroup: CecNativeRuleGroup = {
  name: 'deontic',
  rules: [
    CecDeonticDRule,
    CecProhibitionEquivalenceRule,
    CecProhibitionFromObligationRule,
    CecObligationDistributionRule,
    CecObligationImplicationRule,
    CecPermissionFromNonObligationRule,
    CecObligationConjunctionRule,
    CecPermissionDistributionRule,
    CecObligationConsistencyRule,
  ],
};

export const CecCognitiveNativeRuleGroup: CecNativeRuleGroup = {
  name: 'cognitive',
  rules: [
    CecBeliefDistributionRule,
    CecBeliefConjunctionRule,
    CecBeliefMonotonicityRule,
    CecBeliefNegationRule,
    CecBeliefRevisionRule,
    CecKnowledgeImpliesBeliefRule,
    CecKnowledgeDistributionRule,
    CecKnowledgeConjunctionRule,
    CecKnowledgeMonotonicityRule,
    CecCommonBeliefIntroductionRule,
    CecCommonKnowledgeDistributionRule,
    CecCommonKnowledgeImpliesKnowledgeRule,
    CecCommonKnowledgeIntroductionRule,
    CecCommonKnowledgeMonotonicityRule,
    CecCommonKnowledgeNegationRule,
    CecCommonKnowledgeTransitivityRule,
    CecIntentionCommitmentRule,
    CecIntentionMeansEndRule,
    CecIntentionPersistenceRule,
    CecPerceptionImpliesKnowledgeRule,
    CecTemporallyInducedCommonKnowledgeRule,
  ],
};

export const CecSpecializedNativeRuleGroup: CecNativeRuleGroup = {
  name: 'specialized',
  rules: [
    CecUniversalModusPonensRule,
    CecExistentialInstantiationRule,
    CecExistentialGeneralizationRule,
    CecUniversalGeneralizationRule,
    CecFixedPointInductionRule,
  ],
};

export const CecResolutionNativeRuleGroup: CecNativeRuleGroup = {
  name: 'resolution',
  rules: [
    CecResolutionRule,
    CecUnitResolutionRule,
    CecSubsumptionRule,
    CecFactoringRule,
    CecProofByContradictionRule,
    CecCaseAnalysisRule,
  ],
};

export const CecNativeRuleGroups: readonly CecNativeRuleGroup[] = [
  CecPropositionalNativeRuleGroup,
  CecModalNativeRuleGroup,
  CecTemporalNativeRuleGroup,
  CecDeonticNativeRuleGroup,
  CecCognitiveNativeRuleGroup,
  CecSpecializedNativeRuleGroup,
  CecResolutionNativeRuleGroup,
];

export function getCecNativeRuleGroups(): readonly CecNativeRuleGroup[] {
  return CecNativeRuleGroups;
}

export function getCecNativeRuleGroup(name: CecNativeRuleGroupName): CecNativeRuleGroup {
  const group = CecNativeRuleGroups.find((candidate) => candidate.name === name);
  if (!group) {
    throw new Error(`Unknown CEC native inference rule group: ${name}`);
  }
  return group;
}

export function getCecNativeRulesByGroup(
  name: CecNativeRuleGroupName,
): readonly CecInferenceRule[] {
  return getCecNativeRuleGroup(name).rules;
}
