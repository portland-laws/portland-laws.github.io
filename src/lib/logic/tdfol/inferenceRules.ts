import type { TdfolBinaryFormula, TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';

export interface TdfolInferenceRule {
  name: string;
  description: string;
  arity: number | 'any';
  canApply(...formulas: TdfolFormula[]): boolean;
  apply(...formulas: TdfolFormula[]): TdfolFormula;
}

export interface TdfolRuleApplication {
  rule: string;
  premises: TdfolFormula[];
  conclusion: TdfolFormula;
}

type RuleSpec = {
  name: string;
  description: string;
  arity: number | 'any';
  canApply: (...formulas: TdfolFormula[]) => boolean;
  apply: (...formulas: TdfolFormula[]) => TdfolFormula;
};

export class TdfolRule implements TdfolInferenceRule {
  readonly name: string;
  readonly description: string;
  readonly arity: number | 'any';
  private readonly canApplyImpl: RuleSpec['canApply'];
  private readonly applyImpl: RuleSpec['apply'];

  constructor(spec: RuleSpec) {
    this.name = spec.name;
    this.description = spec.description;
    this.arity = spec.arity;
    this.canApplyImpl = spec.canApply;
    this.applyImpl = spec.apply;
  }

  canApply(...formulas: TdfolFormula[]): boolean {
    return this.arity === 'any' || formulas.length === this.arity ? this.canApplyImpl(...formulas) : false;
  }

  apply(...formulas: TdfolFormula[]): TdfolFormula {
    if (!this.canApply(...formulas)) {
      throw new Error(`Rule ${this.name} cannot be applied to the supplied formulas`);
    }
    return this.applyImpl(...formulas);
  }

  toString(): string {
    return this.name;
  }
}

export const ModusPonensRule = new TdfolRule({
  name: 'ModusPonens',
  description: 'From phi and phi -> psi, infer psi',
  arity: 2,
  canApply: (left, right) => isImplication(right) && formulaEquals(right.left, left),
  apply: (_left, right) => (right as TdfolBinaryFormula).right,
});

export const ModusTollensRule = new TdfolRule({
  name: 'ModusTollens',
  description: 'From phi -> psi and not psi, infer not phi',
  arity: 2,
  canApply: (implication, negatedConsequent) =>
    isImplication(implication) &&
    negatedConsequent.kind === 'unary' &&
    negatedConsequent.operator === 'NOT' &&
    formulaEquals(negatedConsequent.formula, implication.right),
  apply: (implication) => ({ kind: 'unary', operator: 'NOT', formula: (implication as TdfolBinaryFormula).left }),
});

export const HypotheticalSyllogismRule = new TdfolRule({
  name: 'HypotheticalSyllogism',
  description: 'From phi -> psi and psi -> chi, infer phi -> chi',
  arity: 2,
  canApply: (first, second) => isImplication(first) && isImplication(second) && formulaEquals(first.right, second.left),
  apply: (first, second) => ({
    kind: 'binary',
    operator: 'IMPLIES',
    left: (first as TdfolBinaryFormula).left,
    right: (second as TdfolBinaryFormula).right,
  }),
});

export const ConjunctionIntroductionRule = new TdfolRule({
  name: 'ConjunctionIntroduction',
  description: 'From phi and psi, infer phi and psi',
  arity: 2,
  canApply: () => true,
  apply: (left, right) => ({ kind: 'binary', operator: 'AND', left, right }),
});

export const ConjunctionEliminationLeftRule = new TdfolRule({
  name: 'ConjunctionEliminationLeft',
  description: 'From phi and psi, infer phi',
  arity: 1,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'AND',
  apply: (formula) => (formula as TdfolBinaryFormula).left,
});

export const ConjunctionEliminationRightRule = new TdfolRule({
  name: 'ConjunctionEliminationRight',
  description: 'From phi and psi, infer psi',
  arity: 1,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'AND',
  apply: (formula) => (formula as TdfolBinaryFormula).right,
});

export const DoubleNegationEliminationRule = new TdfolRule({
  name: 'DoubleNegationElimination',
  description: 'From not not phi, infer phi',
  arity: 1,
  canApply: (formula) => formula.kind === 'unary' && formula.operator === 'NOT' && formula.formula.kind === 'unary' && formula.formula.operator === 'NOT',
  apply: (formula) => {
    if (formula.kind !== 'unary' || formula.formula.kind !== 'unary') throw new Error('Invalid double negation');
    return formula.formula.formula;
  },
});

export const TemporalKAxiomRule = new TdfolRule({
  name: 'TemporalKAxiom',
  description: 'From always(phi -> psi) and always(phi), infer always(psi)',
  arity: 2,
  canApply: (rule, premise) =>
    rule.kind === 'temporal' &&
    rule.operator === 'ALWAYS' &&
    isImplication(rule.formula) &&
    premise.kind === 'temporal' &&
    premise.operator === 'ALWAYS' &&
    formulaEquals(rule.formula.left, premise.formula),
  apply: (rule) => {
    if (rule.kind !== 'temporal' || !isImplication(rule.formula)) throw new Error('Invalid temporal K premise');
    return { kind: 'temporal', operator: 'ALWAYS', formula: rule.formula.right };
  },
});

export const TemporalTAxiomRule = new TdfolRule({
  name: 'TemporalTAxiom',
  description: 'From always(phi), infer phi',
  arity: 1,
  canApply: (formula) => formula.kind === 'temporal' && formula.operator === 'ALWAYS',
  apply: (formula) => {
    if (formula.kind !== 'temporal') throw new Error('Invalid temporal premise');
    return formula.formula;
  },
});

export const EventuallyIntroductionRule = new TdfolRule({
  name: 'EventuallyIntroduction',
  description: 'From phi, infer eventually(phi)',
  arity: 1,
  canApply: () => true,
  apply: (formula) => ({ kind: 'temporal', operator: 'EVENTUALLY', formula }),
});

export const DeonticKAxiomRule = new TdfolRule({
  name: 'DeonticKAxiom',
  description: 'From O(phi -> psi) and O(phi), infer O(psi)',
  arity: 2,
  canApply: (rule, premise) =>
    rule.kind === 'deontic' &&
    rule.operator === 'OBLIGATION' &&
    isImplication(rule.formula) &&
    premise.kind === 'deontic' &&
    premise.operator === 'OBLIGATION' &&
    formulaEquals(rule.formula.left, premise.formula),
  apply: (rule) => {
    if (rule.kind !== 'deontic' || !isImplication(rule.formula)) throw new Error('Invalid deontic K premise');
    return { kind: 'deontic', operator: 'OBLIGATION', formula: rule.formula.right };
  },
});

export const DeonticDAxiomRule = new TdfolRule({
  name: 'DeonticDAxiom',
  description: 'From O(phi), infer P(phi)',
  arity: 1,
  canApply: (formula) => formula.kind === 'deontic' && formula.operator === 'OBLIGATION',
  apply: (formula) => {
    if (formula.kind !== 'deontic') throw new Error('Invalid deontic premise');
    return { kind: 'deontic', operator: 'PERMISSION', formula: formula.formula };
  },
});

export const ProhibitionEquivalenceRule = new TdfolRule({
  name: 'ProhibitionEquivalence',
  description: 'From F(phi), infer O(not phi)',
  arity: 1,
  canApply: (formula) => formula.kind === 'deontic' && formula.operator === 'PROHIBITION',
  apply: (formula) => {
    if (formula.kind !== 'deontic') throw new Error('Invalid prohibition premise');
    return {
      kind: 'deontic',
      operator: 'OBLIGATION',
      formula: { kind: 'unary', operator: 'NOT', formula: formula.formula },
    };
  },
});

export const ProhibitionFromObligationRule = new TdfolRule({
  name: 'ProhibitionFromObligation',
  description: 'From O(not phi), infer F(phi)',
  arity: 1,
  canApply: (formula) =>
    formula.kind === 'deontic' &&
    formula.operator === 'OBLIGATION' &&
    formula.formula.kind === 'unary' &&
    formula.formula.operator === 'NOT',
  apply: (formula) => {
    if (formula.kind !== 'deontic' || formula.formula.kind !== 'unary') throw new Error('Invalid obligation premise');
    return { kind: 'deontic', operator: 'PROHIBITION', formula: formula.formula.formula };
  },
});

export const ObligationWeakeningRule = new TdfolRule({
  name: 'ObligationWeakening',
  description: 'From O(phi and psi), infer O(phi)',
  arity: 1,
  canApply: (formula) => formula.kind === 'deontic' && formula.operator === 'OBLIGATION' && formula.formula.kind === 'binary' && formula.formula.operator === 'AND',
  apply: (formula) => {
    if (formula.kind !== 'deontic' || formula.formula.kind !== 'binary') throw new Error('Invalid obligation premise');
    return { kind: 'deontic', operator: 'OBLIGATION', formula: formula.formula.left };
  },
});

export function getAllTdfolRules(): TdfolInferenceRule[] {
  return [
    ModusPonensRule,
    ModusTollensRule,
    HypotheticalSyllogismRule,
    ConjunctionEliminationLeftRule,
    ConjunctionEliminationRightRule,
    DoubleNegationEliminationRule,
    TemporalKAxiomRule,
    TemporalTAxiomRule,
    EventuallyIntroductionRule,
    DeonticKAxiomRule,
    DeonticDAxiomRule,
    ProhibitionEquivalenceRule,
    ProhibitionFromObligationRule,
    ObligationWeakeningRule,
  ];
}

export function applyTdfolRules(
  formulas: TdfolFormula[],
  rules: TdfolInferenceRule[] = getAllTdfolRules(),
): TdfolRuleApplication[] {
  const applications: TdfolRuleApplication[] = [];
  for (const rule of rules) {
    if (rule.arity === 1) {
      for (const formula of formulas) {
        if (rule.canApply(formula)) {
          applications.push({ rule: rule.name, premises: [formula], conclusion: rule.apply(formula) });
        }
      }
    } else if (rule.arity === 2) {
      for (const left of formulas) {
        for (const right of formulas) {
          if (rule.canApply(left, right)) {
            applications.push({ rule: rule.name, premises: [left, right], conclusion: rule.apply(left, right) });
          }
        }
      }
    }
  }
  return applications;
}

export function formulaEquals(left: TdfolFormula, right: TdfolFormula): boolean {
  return formulaKey(left) === formulaKey(right);
}

export function formulaKey(formula: TdfolFormula): string {
  return formatTdfolFormula(formula);
}

function isImplication(formula: TdfolFormula): formula is TdfolBinaryFormula {
  return formula.kind === 'binary' && formula.operator === 'IMPLIES';
}
