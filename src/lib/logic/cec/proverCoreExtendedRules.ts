import type { CecExpression } from './ast';
import {
  applyCecRules,
  CecAbsorptionRule,
  CecAssociationRule,
  CecBiconditionalEliminationRule,
  CecBiconditionalIntroductionRule,
  CecClaviusLawRule,
  CecCommutativityConjunctionRule,
  CecCommutativityDisjunctionRule,
  CecConstructiveDilemmaRule,
  CecDestructiveDilemmaRule,
  CecDistributionRule,
  CecExportationRule,
  CecIdempotenceRule,
  CecMaterialImplicationRule,
  CecTautologyRule,
  CecTranspositionRule,
  type CecInferenceRule,
  type CecRuleApplication,
} from './inferenceRules';
import {
  CecProver,
  type CecKnowledgeBase,
  type CecProofResult,
  type CecProverOptions,
} from './prover';

export type CecProverCoreExtendedRuntime = {
  module: 'logic/CEC/native/prover_core_extended_rules.py';
  runtime: 'browser-native-typescript';
  pythonRuntime: false;
  serverDelegation: false;
};

export const CEC_PROVER_CORE_EXTENDED_RUNTIME: CecProverCoreExtendedRuntime = {
  module: 'logic/CEC/native/prover_core_extended_rules.py',
  runtime: 'browser-native-typescript',
  pythonRuntime: false,
  serverDelegation: false,
};

export type CecProverCoreExtendedRuleName =
  | 'CecBiconditionalIntroduction'
  | 'CecBiconditionalElimination'
  | 'CecConstructiveDilemma'
  | 'CecDestructiveDilemma'
  | 'CecExportation'
  | 'CecAbsorption'
  | 'CecTautology'
  | 'CecCommutativityConjunction'
  | 'CecCommutativityDisjunction'
  | 'CecDistribution'
  | 'CecAssociation'
  | 'CecTransposition'
  | 'CecMaterialImplication'
  | 'CecClaviusLaw'
  | 'CecIdempotence';

const CEC_PROVER_CORE_EXTENDED_RULES: readonly CecInferenceRule[] = [
  CecBiconditionalIntroductionRule,
  CecBiconditionalEliminationRule,
  CecConstructiveDilemmaRule,
  CecDestructiveDilemmaRule,
  CecExportationRule,
  CecAbsorptionRule,
  CecTautologyRule,
  CecCommutativityConjunctionRule,
  CecCommutativityDisjunctionRule,
  CecDistributionRule,
  CecAssociationRule,
  CecTranspositionRule,
  CecMaterialImplicationRule,
  CecClaviusLawRule,
  CecIdempotenceRule,
];

export function getCecProverCoreExtendedRules(): readonly CecInferenceRule[] {
  return CEC_PROVER_CORE_EXTENDED_RULES;
}

export function getCecProverCoreExtendedRule(
  name: CecProverCoreExtendedRuleName,
): CecInferenceRule {
  const rule = CEC_PROVER_CORE_EXTENDED_RULES.find((candidate) => candidate.name === name);
  if (!rule) {
    throw new Error(`Unknown CEC prover-core extended rule: ${name}`);
  }
  return rule;
}

export function applyCecProverCoreExtendedRules(
  expressions: CecExpression[],
  rules: readonly CecInferenceRule[] = CEC_PROVER_CORE_EXTENDED_RULES,
): CecRuleApplication[] {
  return applyCecRules(expressions, [...rules]);
}

export function proveCecWithExtendedRules(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions = {},
): CecProofResult {
  const rules = dedupeRules([...(options.rules ?? []), ...CEC_PROVER_CORE_EXTENDED_RULES]);
  return new CecProver({ ...options, rules }).prove(theorem, kb);
}

function dedupeRules(rules: CecInferenceRule[]): CecInferenceRule[] {
  const seen = new Set<string>();
  const unique: CecInferenceRule[] = [];
  for (const rule of rules) {
    if (seen.has(rule.name)) continue;
    seen.add(rule.name);
    unique.push(rule);
  }
  return unique;
}
