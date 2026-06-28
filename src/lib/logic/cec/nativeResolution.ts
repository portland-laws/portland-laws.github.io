import type { CecBinaryExpression, CecExpression } from './ast';
import { formatCecExpression } from './formatter';

export type CecNativeResolutionRuleName = 'resolution' | 'unit_resolution';

export interface CecNativeResolutionComplement {
  leftIndex: number;
  rightIndex: number;
  leftLiteral: CecExpression;
  rightLiteral: CecExpression;
}

export interface CecNativeResolutionResult {
  ok: true;
  rule: CecNativeResolutionRuleName;
  resolvent: CecExpression;
  complement: CecNativeResolutionComplement;
  tautology: boolean;
  emptyClause: boolean;
}

interface IndexedLiteral {
  index: number;
  literal: CecExpression;
}

export class CecResolutionRule {
  static resolve(left: CecExpression, right: CecExpression): CecNativeResolutionResult | null {
    const leftLiterals = flattenDisjunction(left);
    const rightLiterals = flattenDisjunction(right);

    for (const leftEntry of withIndexes(leftLiterals)) {
      for (const rightEntry of withIndexes(rightLiterals)) {
        if (areComplements(leftEntry.literal, rightEntry.literal)) {
          const leftRemainder = leftLiterals.filter(
            (_literal: CecExpression, index: number): boolean => index !== leftEntry.index,
          );
          const rightRemainder = rightLiterals.filter(
            (_literal: CecExpression, index: number): boolean => index !== rightEntry.index,
          );
          const resolventLiterals = dedupeLiterals(leftRemainder.concat(rightRemainder));

          return {
            ok: true,
            rule: 'resolution',
            resolvent: buildDisjunction(resolventLiterals),
            complement: {
              leftIndex: leftEntry.index,
              rightIndex: rightEntry.index,
              leftLiteral: leftEntry.literal,
              rightLiteral: rightEntry.literal,
            },
            tautology: containsComplementaryPair(resolventLiterals),
            emptyClause: resolventLiterals.length === 0,
          };
        }
      }
    }

    return null;
  }

  static apply(left: CecExpression, right: CecExpression): CecExpression {
    const result = this.resolve(left, right);
    if (result === null) {
      throw new Error('Resolution requires one complementary literal across the input clauses');
    }
    if (result.tautology) {
      throw new Error('Resolution produced a tautological resolvent');
    }
    return result.resolvent;
  }
}

export class CecUnitResolutionRule {
  static resolve(left: CecExpression, right: CecExpression): CecNativeResolutionResult | null {
    const result = CecResolutionRule.resolve(left, right);
    if (result === null) {
      return null;
    }

    const leftIsUnit = flattenDisjunction(left).length === 1;
    const rightIsUnit = flattenDisjunction(right).length === 1;
    if (!leftIsUnit && !rightIsUnit) {
      return null;
    }

    return {
      ...result,
      rule: 'unit_resolution',
    };
  }

  static apply(left: CecExpression, right: CecExpression): CecExpression {
    const result = this.resolve(left, right);
    if (result === null) {
      throw new Error(
        'Unit resolution requires at least one unit clause and one complementary literal',
      );
    }
    if (result.tautology) {
      throw new Error('Unit resolution produced a tautological resolvent');
    }
    return result.resolvent;
  }
}

export const resolveCecClauses = (
  left: CecExpression,
  right: CecExpression,
): CecNativeResolutionResult | null => CecResolutionRule.resolve(left, right);

export const applyCecResolution = (left: CecExpression, right: CecExpression): CecExpression =>
  CecResolutionRule.apply(left, right);

export const resolveCecUnitClauses = (
  left: CecExpression,
  right: CecExpression,
): CecNativeResolutionResult | null => CecUnitResolutionRule.resolve(left, right);

export const applyCecUnitResolution = (left: CecExpression, right: CecExpression): CecExpression =>
  CecUnitResolutionRule.apply(left, right);

function withIndexes(literals: CecExpression[]): IndexedLiteral[] {
  return literals.map(
    (literal: CecExpression, index: number): IndexedLiteral => ({ index, literal }),
  );
}

function flattenDisjunction(expression: CecExpression): CecExpression[] {
  if (expression.kind === 'binary' && expression.operator === 'or') {
    return flattenDisjunction(expression.left).concat(flattenDisjunction(expression.right));
  }
  return [expression];
}

function buildDisjunction(literals: CecExpression[]): CecExpression {
  if (literals.length === 0) {
    return { kind: 'atom', name: 'false' };
  }
  if (literals.length === 1) {
    return literals[0];
  }

  return literals
    .slice(1)
    .reduce(
      (left: CecExpression, right: CecExpression): CecExpression => buildOr(left, right),
      literals[0],
    );
}

function buildOr(left: CecExpression, right: CecExpression): CecBinaryExpression {
  return {
    kind: 'binary',
    operator: 'or',
    left,
    right,
  };
}

function areComplements(left: CecExpression, right: CecExpression): boolean {
  return (
    literalKey(left) === negatedLiteralKey(right) || negatedLiteralKey(left) === literalKey(right)
  );
}

function containsComplementaryPair(literals: CecExpression[]): boolean {
  const keys = new Set();

  for (const literal of literals) {
    const key = literalKey(literal);
    if (keys.has(negatedLiteralKey(literal))) {
      return true;
    }
    keys.add(key);
  }

  return false;
}

function dedupeLiterals(literals: CecExpression[]): CecExpression[] {
  const seen = new Set();
  const unique: CecExpression[] = [];

  for (const literal of literals) {
    const key = literalKey(literal);
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(literal);
    }
  }

  return unique;
}

function literalKey(expression: CecExpression): string {
  return formatCecExpression(expression).trim();
}

function negatedLiteralKey(expression: CecExpression): string {
  if (expression.kind === 'unary' && expression.operator === 'not') {
    return literalKey(expression.expression);
  }

  return literalKey({
    kind: 'unary',
    operator: 'not',
    expression,
  });
}
