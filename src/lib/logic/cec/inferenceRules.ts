import type { CecApplication, CecBinaryExpression, CecExpression, CecQuantifiedExpression, CecUnaryExpression } from './ast';
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

export const CecHypotheticalSyllogismRule = new CecRule({
  name: 'CecHypotheticalSyllogism',
  description: 'From (implies phi psi) and (implies psi chi), infer (implies phi chi)',
  arity: 2,
  canApply: (first, second) =>
    isBinary(first, 'implies') &&
    isBinary(second, 'implies') &&
    cecExpressionEquals(first.right, second.left),
  apply: (first, second) => ({
    kind: 'binary',
    operator: 'implies',
    left: (first as CecBinaryExpression).left,
    right: (second as CecBinaryExpression).right,
  }),
});

export const CecConjunctionIntroductionRule = new CecRule({
  name: 'CecConjunctionIntroduction',
  description: 'From phi and psi, infer (and phi psi)',
  arity: 2,
  canApply: (left, right) => !cecExpressionEquals(left, right),
  apply: (left, right) => ({ kind: 'binary', operator: 'and', left, right }),
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

export const CecEventuallyIntroductionRule = new CecRule({
  name: 'CecEventuallyIntroduction',
  description: 'From phi, infer (eventually phi)',
  arity: 1,
  canApply: (expression) => !isUnary(expression, 'eventually'),
  apply: (expression) => ({ kind: 'unary', operator: 'eventually', expression }),
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

export const CecProhibitionFromObligationRule = new CecRule({
  name: 'CecProhibitionFromObligation',
  description: 'From (O (not phi)), infer (F phi)',
  arity: 1,
  canApply: (expression) =>
    isUnary(expression, 'O') &&
    expression.expression.kind === 'unary' &&
    expression.expression.operator === 'not',
  apply: (expression) => {
    if (!isUnary(expression, 'O') || !isUnary(expression.expression, 'not')) {
      throw new Error('Invalid CEC obligation prohibition premise');
    }
    return { kind: 'unary', operator: 'F', expression: expression.expression.expression };
  },
});

export const CecUniversalModusPonensRule = new CecRule({
  name: 'CecUniversalModusPonens',
  description: 'From (forall x (implies phi(x) psi(x))) and phi(a), infer psi(a)',
  arity: 2,
  canApply: (universal, premise) => {
    if (!isQuantified(universal, 'forall') || !isBinary(universal.expression, 'implies')) {
      return false;
    }
    return matchCecExpressionForVariable(universal.expression.left, premise, universal.variable) !== undefined;
  },
  apply: (universal, premise) => {
    if (!isQuantified(universal, 'forall') || !isBinary(universal.expression, 'implies')) {
      throw new Error('Invalid CEC universal premise');
    }
    const binding = matchCecExpressionForVariable(universal.expression.left, premise, universal.variable);
    if (!binding) throw new Error('CEC universal premise does not match supplied fact');
    return substituteCecAtom(universal.expression.right, universal.variable, binding);
  },
});

export const CecExistentialInstantiationRule = new CecRule({
  name: 'CecExistentialInstantiation',
  description: 'From (exists x phi(x)), infer phi(skolem_x)',
  arity: 1,
  canApply: (expression) => isQuantified(expression, 'exists'),
  apply: (expression) => {
    if (!isQuantified(expression, 'exists')) throw new Error('Invalid CEC existential premise');
    return substituteCecAtom(expression.expression, expression.variable, `skolem_${expression.variable}`);
  },
});

export const CecExistentialGeneralizationRule = new CecRule({
  name: 'CecExistentialGeneralization',
  description: 'From phi(a), infer (exists x phi(x)) by replacing the first atom argument',
  arity: 1,
  canApply: (expression) => findFirstSubstitutableAtom(expression) !== undefined,
  apply: (expression) => {
    const atom = findFirstSubstitutableAtom(expression);
    if (!atom) throw new Error('No CEC atom available for existential generalization');
    return {
      kind: 'quantified',
      quantifier: 'exists',
      variable: 'x',
      expression: substituteCecAtom(expression, atom, 'x'),
    };
  },
});

export const CecUniversalGeneralizationRule = new CecRule({
  name: 'CecUniversalGeneralization',
  description: 'From phi(x), infer (forall x phi(x)) for a free variable-like atom',
  arity: 1,
  canApply: (expression) => findFirstVariableLikeAtom(expression) !== undefined,
  apply: (expression) => {
    const variable = findFirstVariableLikeAtom(expression);
    if (!variable) throw new Error('No CEC variable-like atom available for universal generalization');
    return {
      kind: 'quantified',
      quantifier: 'forall',
      variable,
      expression,
    };
  },
});

export function getAllCecRules(): CecInferenceRule[] {
  return [
    CecModusPonensRule,
    CecHypotheticalSyllogismRule,
    CecConjunctionEliminationLeftRule,
    CecConjunctionEliminationRightRule,
    CecDoubleNegationEliminationRule,
    CecTemporalTRule,
    CecDeonticDRule,
    CecProhibitionEquivalenceRule,
    CecProhibitionFromObligationRule,
    CecUniversalModusPonensRule,
    CecExistentialInstantiationRule,
  ];
}

export function getGenerativeCecRules(): CecInferenceRule[] {
  return [
    CecConjunctionIntroductionRule,
    CecEventuallyIntroductionRule,
    CecExistentialGeneralizationRule,
    CecUniversalGeneralizationRule,
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

function isQuantified(
  expression: CecExpression,
  quantifier: CecQuantifiedExpression['quantifier'],
): expression is CecQuantifiedExpression {
  return expression.kind === 'quantified' && expression.quantifier === quantifier;
}

function matchCecExpressionForVariable(
  pattern: CecExpression,
  target: CecExpression,
  variableName: string,
): string | undefined {
  const bindings = new Map<string, string>();
  return matchCecExpression(pattern, target, variableName, bindings) ? bindings.get(variableName) : undefined;
}

function matchCecExpression(
  pattern: CecExpression,
  target: CecExpression,
  variableName: string,
  bindings: Map<string, string>,
): boolean {
  if (pattern.kind === 'atom' && pattern.name === variableName) {
    if (target.kind !== 'atom') return false;
    const existing = bindings.get(variableName);
    if (!existing) {
      bindings.set(variableName, target.name);
      return true;
    }
    return existing === target.name;
  }
  if (pattern.kind !== target.kind) return false;
  switch (pattern.kind) {
    case 'atom':
      return target.kind === 'atom' && pattern.name === target.name;
    case 'application':
      return target.kind === 'application' &&
        pattern.name === target.name &&
        pattern.args.length === target.args.length &&
        pattern.args.every((arg, index) => matchCecExpression(arg, target.args[index], variableName, bindings));
    case 'quantified':
      return target.kind === 'quantified' &&
        pattern.quantifier === target.quantifier &&
        matchCecExpression(pattern.expression, target.expression, variableName, bindings);
    case 'unary':
      return target.kind === 'unary' &&
        pattern.operator === target.operator &&
        matchCecExpression(pattern.expression, target.expression, variableName, bindings);
    case 'binary':
      return target.kind === 'binary' &&
        pattern.operator === target.operator &&
        matchCecExpression(pattern.left, target.left, variableName, bindings) &&
        matchCecExpression(pattern.right, target.right, variableName, bindings);
  }
}

function substituteCecAtom(expression: CecExpression, atomName: string, replacementName: string): CecExpression {
  switch (expression.kind) {
    case 'atom':
      return expression.name === atomName ? { kind: 'atom', name: replacementName } : expression;
    case 'application':
      return {
        ...expression,
        args: expression.args.map((arg) => substituteCecAtom(arg, atomName, replacementName)),
      } satisfies CecApplication;
    case 'quantified':
      return {
        ...expression,
        expression: expression.variable === atomName
          ? expression.expression
          : substituteCecAtom(expression.expression, atomName, replacementName),
      };
    case 'unary':
      return { ...expression, expression: substituteCecAtom(expression.expression, atomName, replacementName) };
    case 'binary':
      return {
        ...expression,
        left: substituteCecAtom(expression.left, atomName, replacementName),
        right: substituteCecAtom(expression.right, atomName, replacementName),
      };
  }
}

function findFirstSubstitutableAtom(expression: CecExpression): string | undefined {
  if (expression.kind === 'application') {
    const atomArg = expression.args.find((arg) => arg.kind === 'atom' && !isVariableLikeAtom(arg.name));
    if (atomArg?.kind === 'atom') return atomArg.name;
  }
  return findFirstNestedAtom(expression, (name) => !isVariableLikeAtom(name));
}

function findFirstVariableLikeAtom(expression: CecExpression): string | undefined {
  return findFirstNestedAtom(expression, isVariableLikeAtom);
}

function findFirstNestedAtom(expression: CecExpression, predicate: (name: string) => boolean): string | undefined {
  switch (expression.kind) {
    case 'atom':
      return predicate(expression.name) ? expression.name : undefined;
    case 'application':
      return expression.args.map((arg) => findFirstNestedAtom(arg, predicate)).find(Boolean);
    case 'quantified':
    case 'unary':
      return findFirstNestedAtom(expression.expression, predicate);
    case 'binary':
      return findFirstNestedAtom(expression.left, predicate) ?? findFirstNestedAtom(expression.right, predicate);
  }
}

function isVariableLikeAtom(name: string) {
  return /^[xyzuvw]$/.test(name) || /^(agent|person|actor|subject|entity)$/i.test(name);
}
