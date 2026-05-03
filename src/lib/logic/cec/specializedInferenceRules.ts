import type { CecBinaryExpression, CecExpression, CecUnaryExpression } from './ast';
import { formatCecExpression } from './formatter';

export type CecSpecializedRuleName =
  | 'specialized-modus-ponens'
  | 'specialized-hypothetical-syllogism'
  | 'specialized-obligation-permission'
  | 'specialized-always-elimination';

export interface CecSpecializedInferenceResult {
  rule: CecSpecializedRuleName;
  premises: CecExpression[];
  conclusion: CecExpression;
  metadata: {
    sourceModule: 'logic/CEC/native/inference_rules/specialized.py';
    browserNative: true;
  };
}

interface ParsedImplicationPremise {
  premise: CecBinaryExpression;
  implication: CecBinaryExpression;
}

const SOURCE_MODULE = 'logic/CEC/native/inference_rules/specialized.py';

function result(
  rule: CecSpecializedRuleName,
  premises: CecExpression[],
  conclusion: CecExpression,
): CecSpecializedInferenceResult {
  return {
    rule,
    premises,
    conclusion,
    metadata: {
      sourceModule: SOURCE_MODULE,
      browserNative: true,
    },
  };
}

function expressionKey(expression: CecExpression): string {
  return formatCecExpression(expression);
}

function isImplication(expression: CecExpression): expression is CecBinaryExpression {
  return expression.kind === 'binary' && expression.operator === 'implies';
}

function isUnaryOperator(
  expression: CecExpression,
  operator: CecUnaryExpression['operator'],
): expression is CecUnaryExpression {
  return expression.kind === 'unary' && expression.operator === operator;
}

function hasConclusion(
  results: CecSpecializedInferenceResult[],
  conclusion: CecExpression,
): boolean {
  const conclusionKey = expressionKey(conclusion);
  return results.some(
    (item: CecSpecializedInferenceResult) => expressionKey(item.conclusion) === conclusionKey,
  );
}

function findMatchingPremise(
  premises: CecExpression[],
  target: CecExpression,
): CecExpression | undefined {
  const targetKey = expressionKey(target);
  return premises.find((premise: CecExpression) => expressionKey(premise) === targetKey);
}

function collectImplications(premises: CecExpression[]): ParsedImplicationPremise[] {
  const implications: ParsedImplicationPremise[] = [];

  for (const premise of premises) {
    if (isImplication(premise)) {
      implications.push({ premise, implication: premise });
    }
  }

  return implications;
}

export function applySpecializedModusPonens(
  premises: CecExpression[],
): CecSpecializedInferenceResult[] {
  const known = new Set(premises.map(expressionKey));
  const results: CecSpecializedInferenceResult[] = [];

  for (const implicationPremise of premises) {
    if (!isImplication(implicationPremise)) {
      continue;
    }

    if (!known.has(expressionKey(implicationPremise.left))) {
      continue;
    }

    const conclusion = implicationPremise.right;
    if (hasConclusion(results, conclusion)) {
      continue;
    }

    const matchedPremise = findMatchingPremise(premises, implicationPremise.left);
    const matchedPremises =
      matchedPremise === undefined ? [implicationPremise] : [matchedPremise, implicationPremise];

    results.push(result('specialized-modus-ponens', matchedPremises, conclusion));
  }

  return results;
}

export function applySpecializedHypotheticalSyllogism(
  premises: CecExpression[],
): CecSpecializedInferenceResult[] {
  const implications = collectImplications(premises);
  const results: CecSpecializedInferenceResult[] = [];

  for (const first of implications) {
    for (const second of implications) {
      if (first.premise === second.premise) {
        continue;
      }

      if (expressionKey(first.implication.right) !== expressionKey(second.implication.left)) {
        continue;
      }

      const conclusion: CecBinaryExpression = {
        kind: 'binary',
        operator: 'implies',
        left: first.implication.left,
        right: second.implication.right,
      };

      if (!hasConclusion(results, conclusion)) {
        results.push(
          result('specialized-hypothetical-syllogism', [first.premise, second.premise], conclusion),
        );
      }
    }
  }

  return results;
}

export function applySpecializedObligationPermission(
  premises: CecExpression[],
): CecSpecializedInferenceResult[] {
  const results: CecSpecializedInferenceResult[] = [];

  for (const premise of premises) {
    if (!isUnaryOperator(premise, 'O')) {
      continue;
    }

    const conclusion: CecUnaryExpression = {
      kind: 'unary',
      operator: 'P',
      expression: premise.expression,
    };

    if (!hasConclusion(results, conclusion)) {
      results.push(result('specialized-obligation-permission', [premise], conclusion));
    }
  }

  return results;
}

export function applySpecializedAlwaysElimination(
  premises: CecExpression[],
): CecSpecializedInferenceResult[] {
  const results: CecSpecializedInferenceResult[] = [];

  for (const premise of premises) {
    if (!isUnaryOperator(premise, 'always')) {
      continue;
    }

    const conclusion = premise.expression;
    if (!hasConclusion(results, conclusion)) {
      results.push(result('specialized-always-elimination', [premise], conclusion));
    }
  }

  return results;
}

export function applySpecializedCecInferenceRules(
  premises: CecExpression[],
): CecSpecializedInferenceResult[] {
  return [
    ...applySpecializedModusPonens(premises),
    ...applySpecializedHypotheticalSyllogism(premises),
    ...applySpecializedObligationPermission(premises),
    ...applySpecializedAlwaysElimination(premises),
  ];
}
