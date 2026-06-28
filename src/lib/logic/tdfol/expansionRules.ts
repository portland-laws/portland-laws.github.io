import {
  substituteFormula,
  type TdfolBinaryFormula,
  type TdfolFormula,
  type TdfolQuantifiedFormula,
  type TdfolTerm,
  type TdfolUnaryFormula,
} from './ast';

export interface TdfolExpansionContext {
  formula: TdfolFormula;
  negated?: boolean;
  worldId?: number;
  instantiationTerm?: TdfolTerm;
  branchConstants?: TdfolTerm[];
  witnessPrefix?: string;
}

export type TdfolSignedFormula = [formula: TdfolFormula, negated: boolean];

export interface TdfolExpansionResult {
  kind: 'linear' | 'branching';
  formulas?: TdfolSignedFormula[];
  branches?: TdfolSignedFormula[][];
  witness?: TdfolTerm;
  ruleClass?: 'alpha' | 'beta' | 'gamma' | 'delta';
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
  readonly description =
    'Positive implication branches into negated antecedent or consequent; negated implication is linear.';

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
          [
            [context.formula.left, false],
            [context.formula.right, true],
          ],
          [
            [context.formula.left, true],
            [context.formula.right, false],
          ],
        )
      : branching(
          [
            [context.formula.left, false],
            [context.formula.right, false],
          ],
          [
            [context.formula.left, true],
            [context.formula.right, true],
          ],
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

export class TdfolUniversalExpansionRule implements TdfolExpansionRule {
  readonly name = 'UniversalExpansionRule';
  readonly description =
    'Universal formulas use gamma instantiation when positive and delta witness instantiation when negated.';

  canExpand(formula: TdfolFormula): formula is TdfolQuantifiedFormula {
    return formula.kind === 'quantified' && formula.quantifier === 'FORALL';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertQuantified(context.formula, 'FORALL', this.name);
    const witness = context.negated
      ? makeDeltaWitness(context.formula, context.witnessPrefix)
      : makeGammaWitness(context.formula, context);
    const instantiated = substituteFormula(
      context.formula.formula,
      context.formula.variable.name,
      witness,
    );
    return {
      ...linear([instantiated, Boolean(context.negated)]),
      witness,
      ruleClass: context.negated ? 'delta' : 'gamma',
    };
  }
}

export class TdfolExistentialExpansionRule implements TdfolExpansionRule {
  readonly name = 'ExistentialExpansionRule';
  readonly description =
    'Existential formulas use delta witness instantiation when positive and gamma instantiation when negated.';

  canExpand(formula: TdfolFormula): formula is TdfolQuantifiedFormula {
    return formula.kind === 'quantified' && formula.quantifier === 'EXISTS';
  }

  expand(context: TdfolExpansionContext): TdfolExpansionResult {
    assertQuantified(context.formula, 'EXISTS', this.name);
    const witness = context.negated
      ? makeGammaWitness(context.formula, context)
      : makeDeltaWitness(context.formula, context.witnessPrefix);
    const instantiated = substituteFormula(
      context.formula.formula,
      context.formula.variable.name,
      witness,
    );
    return {
      ...linear([instantiated, Boolean(context.negated)]),
      witness,
      ruleClass: context.negated ? 'gamma' : 'delta',
    };
  }
}

export function getAllTdfolExpansionRules(): TdfolExpansionRule[] {
  return [
    new TdfolAndExpansionRule(),
    new TdfolOrExpansionRule(),
    new TdfolImpliesExpansionRule(),
    new TdfolIffExpansionRule(),
    new TdfolNotExpansionRule(),
    new TdfolUniversalExpansionRule(),
    new TdfolExistentialExpansionRule(),
  ];
}

export function selectTdfolExpansionRule(
  formula: TdfolFormula,
  negated = false,
): TdfolExpansionRule | undefined {
  return getAllTdfolExpansionRules().find((rule) => rule.canExpand(formula, negated));
}

export function expandTdfolFormula(
  formula: TdfolFormula,
  negated = false,
): TdfolExpansionResult | undefined {
  return selectTdfolExpansionRule(formula, negated)?.expand({ formula, negated });
}

function linear(...formulas: TdfolSignedFormula[]): TdfolExpansionResult {
  return { kind: 'linear', formulas };
}

function branching(...branches: TdfolSignedFormula[][]): TdfolExpansionResult {
  return { kind: 'branching', branches };
}

function assertBinary(
  formula: TdfolFormula,
  operator: TdfolBinaryFormula['operator'],
  ruleName: string,
): asserts formula is TdfolBinaryFormula {
  if (formula.kind !== 'binary' || formula.operator !== operator) {
    throw new Error(`${ruleName} cannot expand the supplied formula`);
  }
}

function assertQuantified(
  formula: TdfolFormula,
  quantifier: TdfolQuantifiedFormula['quantifier'],
  ruleName: string,
): asserts formula is TdfolQuantifiedFormula {
  if (formula.kind !== 'quantified' || formula.quantifier !== quantifier) {
    throw new Error(`${ruleName} cannot expand the supplied formula`);
  }
}

function makeGammaWitness(
  formula: TdfolQuantifiedFormula,
  context: TdfolExpansionContext,
): TdfolTerm {
  const [firstConstant] = context.branchConstants ?? [];
  return (
    context.instantiationTerm ??
    firstConstant ??
    makeConstant(`gamma_${formula.variable.name}`, formula)
  );
}

function makeDeltaWitness(formula: TdfolQuantifiedFormula, prefix = 'skolem'): TdfolTerm {
  return makeConstant(`${prefix}_${formula.variable.name}`, formula);
}

function makeConstant(name: string, formula: TdfolQuantifiedFormula): TdfolTerm {
  return { kind: 'constant', name, sort: formula.variable.sort };
}
