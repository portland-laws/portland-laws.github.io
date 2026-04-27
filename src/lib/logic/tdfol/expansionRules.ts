import type { TdfolBinaryFormula, TdfolFormula, TdfolUnaryFormula } from './ast';

export interface TdfolExpansionContext {
  formula: TdfolFormula;
  negated?: boolean;
  worldId?: number;
}

export type TdfolSignedFormula = [formula: TdfolFormula, negated: boolean];

export interface TdfolExpansionResult {
  kind: 'linear' | 'branching';
  formulas?: TdfolSignedFormula[];
  branches?: TdfolSignedFormula[][];
}

export interface TdfolExpansionRule {
  readonly name: string;
  readonly description: string;
  canExpand(formula: TdfolFormula, negated?: boolean): boolean;
  expand(context: TdfolExpansionContext): TdfolExpansionResult;
}

export class TdfolAndExpansionRule implements TdfolExpansionRule {
  readonly name = 'AndExpansionRule';
  readonly description = 'Positive conjunction expands linearly; negated conjunction branches.';

  canExpand(formula: TdfolFormula): formula is TdfolBinaryFormula {
    return formula.kind === 'binary' && formula.operator === 'AND';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertBinary(context.formula, 'AND', this.name);
    return context.negated
      ? branching([[context.formula.left, true]], [[context.formula.right, true]])
      : linear([context.formula.left, false], [context.formula.right, false]);
  }
}

export class TdfolOrExpansionRule implements TdfolExpansionRule {
  readonly name = 'OrExpansionRule';
  readonly description = 'Positive disjunction branches; negated disjunction expands linearly.';

  canExpand(formula: TdfolFormula): formula is TdfolBinaryFormula {
    return formula.kind === 'binary' && formula.operator === 'OR';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertBinary(context.formula, 'OR', this.name);
    return context.negated
      ? linear([context.formula.left, true], [context.formula.right, true])
      : branching([[context.formula.left, false]], [[context.formula.right, false]]);
  }
}

export class TdfolImpliesExpansionRule implements TdfolExpansionRule {
  readonly name = 'ImpliesExpansionRule';
  readonly description = 'Positive implication branches into negated antecedent or consequent; negated implication is linear.';

  canExpand(formula: TdfolFormula): formula is TdfolBinaryFormula {
    return formula.kind === 'binary' && formula.operator === 'IMPLIES';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertBinary(context.formula, 'IMPLIES', this.name);
    return context.negated
      ? linear([context.formula.left, false], [context.formula.right, true])
      : branching([[context.formula.left, true]], [[context.formula.right, false]]);
  }
}

export class TdfolIffExpansionRule implements TdfolExpansionRule {
  readonly name = 'IffExpansionRule';
  readonly description = 'Bi-implication expands into equivalent truth-value branches.';

  canExpand(formula: TdfolFormula): formula is TdfolBinaryFormula {
    return formula.kind === 'binary' && formula.operator === 'IFF';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertBinary(context.formula, 'IFF', this.name);
    return context.negated
      ? branching(
          [[context.formula.left, false], [context.formula.right, true]],
          [[context.formula.left, true], [context.formula.right, false]],
        )
      : branching(
          [[context.formula.left, false], [context.formula.right, false]],
          [[context.formula.left, true], [context.formula.right, true]],
        );
  }
}

export class TdfolNotExpansionRule implements TdfolExpansionRule {
  readonly name = 'NotExpansionRule';
  readonly description = 'Unary negation flips the signed formula polarity.';

  canExpand(formula: TdfolFormula): formula is TdfolUnaryFormula {
    return formula.kind === 'unary' && formula.operator === 'NOT';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    if (context.formula.kind !== 'unary' || context.formula.operator !== 'NOT') {
      throw new Error(`${this.name} cannot expand the supplied formula`);
    }
    return linear([context.formula.formula, !Boolean(context.negated)]);
  }
}

export function getAllTdfolExpansionRules(): TdfolExpansionRule[] {
  return [
    new TdfolAndExpansionRule(),
    new TdfolOrExpansionRule(),
    new TdfolImpliesExpansionRule(),
    new TdfolIffExpansionRule(),
    new TdfolNotExpansionRule(),
  ];
}

export function selectTdfolExpansionRule(formula: TdfolFormula, negated = false): TdfolExpansionRule | undefined {
  return getAllTdfolExpansionRules().find((rule) => rule.canExpand(formula, negated));
}

export function expandTdfolFormula(formula: TdfolFormula, negated = false): TdfolExpansionResult | undefined {
  return selectTdfolExpansionRule(formula, negated)?.expand({ formula, negated });
}

function linear(...formulas: TdfolSignedFormula[]): TdfolExpansionResult {
  return { kind: 'linear', formulas };
}

function branching(...branches: TdfolSignedFormula[][]): TdfolExpansionResult {
  return { kind: 'branching', branches };
}

function assertBinary(formula: TdfolFormula, operator: TdfolBinaryFormula['operator'], ruleName: string): asserts formula is TdfolBinaryFormula {
  if (formula.kind !== 'binary' || formula.operator !== operator) {
    throw new Error(`${ruleName} cannot expand the supplied formula`);
  }
}
