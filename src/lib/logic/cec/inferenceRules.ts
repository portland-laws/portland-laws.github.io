import type { CecBinaryExpression, CecExpression, CecUnaryExpression } from './ast';
import { formatCecExpression } from './formatter';

export interface CecInferenceRule {
  name: string;
  description: string;
  arity: 1 | 2;
  canApply(...expressions: CecExpression[]): boolean;
  apply(...expressions: CecExpression[]): CecExpression;
}

export interface CecRuleApplication {
  rule: string;
  premises: CecExpression[];
  conclusion: CecExpression;
}

type CecRuleSpec = {
  name: string;
  description: string;
  arity: 1 | 2;
  canApply: (...expressions: CecExpression[]) => boolean;
  apply: (...expressions: CecExpression[]) => CecExpression;
};

export class CecRule implements CecInferenceRule {
  readonly name: string;
  readonly description: string;
  readonly arity: 1 | 2;
  private readonly canApplyImpl: CecRuleSpec['canApply'];
  private readonly applyImpl: CecRuleSpec['apply'];

  constructor(spec: CecRuleSpec) {
    this.name = spec.name;
    this.description = spec.description;
    this.arity = spec.arity;
    this.canApplyImpl = spec.canApply;
    this.applyImpl = spec.apply;
  }

  canApply(...expressions: CecExpression[]): boolean {
    return expressions.length === this.arity && this.canApplyImpl(...expressions);
  }

  apply(...expressions: CecExpression[]): CecExpression {
    if (!this.canApply(...expressions)) {
      throw new Error(`CEC rule ${this.name} cannot be applied to the supplied expressions`);
    }
    return this.applyImpl(...expressions);
  }
}

export const CecModusPonensRule = new CecRule({
  name: 'CecModusPonens',
  description: 'From phi and (implies phi psi), infer psi',
  arity: 2,
  canApply: (left, right) => isBinary(right, 'implies') && cecExpressionEquals(right.left, left),
  apply: (_left, right) => (right as CecBinaryExpression).right,
});

export const CecConjunctionEliminationLeftRule = new CecRule({
  name: 'CecConjunctionEliminationLeft',
  description: 'From (and phi psi), infer phi',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'and'),
  apply: (expression) => (expression as CecBinaryExpression).left,
});

export const CecConjunctionEliminationRightRule = new CecRule({
  name: 'CecConjunctionEliminationRight',
  description: 'From (and phi psi), infer psi',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'and'),
  apply: (expression) => (expression as CecBinaryExpression).right,
});

export const CecDoubleNegationEliminationRule = new CecRule({
  name: 'CecDoubleNegationElimination',
  description: 'From (not (not phi)), infer phi',
  arity: 1,
  canApply: (expression) =>
    isUnary(expression, 'not') && expression.expression.kind === 'unary' && expression.expression.operator === 'not',
  apply: (expression) => {
    if (!isUnary(expression, 'not') || !isUnary(expression.expression, 'not')) {
      throw new Error('Invalid CEC double negation premise');
    }
    return expression.expression.expression;
  },
});

export const CecTemporalTRule = new CecRule({
  name: 'CecTemporalT',
  description: 'From (always phi), infer phi',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'always'),
  apply: (expression) => {
    if (!isUnary(expression, 'always')) throw new Error('Invalid CEC temporal premise');
    return expression.expression;
  },
});

export const CecDeonticDRule = new CecRule({
  name: 'CecDeonticD',
  description: 'From (O phi), infer (P phi)',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'O'),
  apply: (expression) => {
    if (!isUnary(expression, 'O')) throw new Error('Invalid CEC deontic premise');
    return { kind: 'unary', operator: 'P', expression: expression.expression };
  },
});

export const CecProhibitionEquivalenceRule = new CecRule({
  name: 'CecProhibitionEquivalence',
  description: 'From (F phi), infer (O (not phi))',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'F'),
  apply: (expression) => {
    if (!isUnary(expression, 'F')) throw new Error('Invalid CEC prohibition premise');
    return {
      kind: 'unary',
      operator: 'O',
      expression: { kind: 'unary', operator: 'not', expression: expression.expression },
    };
  },
});

export function getAllCecRules(): CecInferenceRule[] {
  return [
    CecModusPonensRule,
    CecConjunctionEliminationLeftRule,
    CecConjunctionEliminationRightRule,
    CecDoubleNegationEliminationRule,
    CecTemporalTRule,
    CecDeonticDRule,
    CecProhibitionEquivalenceRule,
  ];
}

export function applyCecRules(
  expressions: CecExpression[],
  rules: CecInferenceRule[] = getAllCecRules(),
): CecRuleApplication[] {
  const applications: CecRuleApplication[] = [];
  for (const rule of rules) {
    if (rule.arity === 1) {
      for (const expression of expressions) {
        if (rule.canApply(expression)) {
          applications.push({ rule: rule.name, premises: [expression], conclusion: rule.apply(expression) });
        }
      }
    } else {
      for (const left of expressions) {
        for (const right of expressions) {
          if (rule.canApply(left, right)) {
            applications.push({ rule: rule.name, premises: [left, right], conclusion: rule.apply(left, right) });
          }
        }
      }
    }
  }
  return applications;
}

export function cecExpressionEquals(left: CecExpression, right: CecExpression): boolean {
  return cecExpressionKey(left) === cecExpressionKey(right);
}

export function cecExpressionKey(expression: CecExpression): string {
  return formatCecExpression(expression);
}

function isBinary(expression: CecExpression, operator: CecBinaryExpression['operator']): expression is CecBinaryExpression {
  return expression.kind === 'binary' && expression.operator === operator;
}

function isUnary(expression: CecExpression, operator: CecUnaryExpression['operator']): expression is CecUnaryExpression {
  return expression.kind === 'unary' && expression.operator === operator;
}
