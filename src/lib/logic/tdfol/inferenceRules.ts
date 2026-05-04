import { getFreeVariables, substituteFormula } from './ast';
import type { TdfolBinaryFormula, TdfolFormula, TdfolTerm } from './ast';
import { formatTdfolFormula } from './formatter';

export type TdfolRuleArity = number | 'any';
export type TdfolRuleCategory =
  | 'base'
  | 'propositional'
  | 'first_order'
  | 'temporal'
  | 'deontic'
  | 'temporal_deontic';

export interface TdfolInferenceRule {
  name: string;
  description: string;
  arity: TdfolRuleArity;
  id?: string;
  category?: TdfolRuleCategory;
  sourcePythonModule?: string;
  canApply(...formulas: TdfolFormula[]): boolean;
  apply(...formulas: TdfolFormula[]): TdfolFormula;
}

export interface TdfolRuleApplication {
  rule: string;
  premises: TdfolFormula[];
  conclusion: TdfolFormula;
}

export interface TdfolRuleApplicationResult {
  ok: boolean;
  rule: string;
  premises: TdfolFormula[];
  conclusion?: TdfolFormula;
  error?: string;
}

type RuleSpec = {
  name: string;
  description: string;
  arity: TdfolRuleArity;
  id?: string;
  category?: TdfolRuleCategory;
  sourcePythonModule?: string;
  canApply: (...formulas: TdfolFormula[]) => boolean;
  apply: (...formulas: TdfolFormula[]) => TdfolFormula;
};

const DEONTIC_RULE_SOURCE = 'logic/TDFOL/inference_rules/deontic.py';
const FIRST_ORDER_RULE_SOURCE = 'logic/TDFOL/inference_rules/first_order.py';
const PROPOSITIONAL_RULE_SOURCE = 'logic/TDFOL/inference_rules/propositional.py';

export class TdfolRule implements TdfolInferenceRule {
  readonly name: string;
  readonly description: string;
  readonly arity: TdfolRuleArity;
  readonly id: string;
  readonly category: TdfolRuleCategory;
  readonly sourcePythonModule: string;
  private readonly canApplyImpl: RuleSpec['canApply'];
  private readonly applyImpl: RuleSpec['apply'];

  constructor(spec: RuleSpec) {
    if (!spec.name.trim()) {
      throw new Error('TDFOL inference rule name must be non-empty');
    }
    if (!spec.description.trim()) {
      throw new Error(`TDFOL inference rule ${spec.name} must include a description`);
    }
    if (typeof spec.arity === 'number' && (!Number.isInteger(spec.arity) || spec.arity < 0)) {
      throw new Error(`TDFOL inference rule ${spec.name} has invalid arity ${spec.arity}`);
    }
    this.name = spec.name;
    this.description = spec.description;
    this.arity = spec.arity;
    this.id = spec.id ?? normalizeRuleId(spec.name);
    this.category = spec.category ?? 'base';
    this.sourcePythonModule = spec.sourcePythonModule ?? 'logic/TDFOL/inference_rules/base.py';
    this.canApplyImpl = spec.canApply;
    this.applyImpl = spec.apply;
  }

  canApply(...formulas: TdfolFormula[]): boolean {
    return this.arity === 'any' || formulas.length === this.arity
      ? this.canApplyImpl(...formulas)
      : false;
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

export function tryApplyTdfolRule(
  rule: TdfolInferenceRule,
  ...formulas: TdfolFormula[]
): TdfolRuleApplicationResult {
  try {
    if (!rule.canApply(...formulas)) {
      return {
        ok: false,
        rule: rule.name,
        premises: formulas,
        error: `Rule ${rule.name} cannot be applied to ${formulas.length} premise(s)`,
      };
    }
    return { ok: true, rule: rule.name, premises: formulas, conclusion: rule.apply(...formulas) };
  } catch (error) {
    return {
      ok: false,
      rule: rule.name,
      premises: formulas,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export const ModusPonensRule = new TdfolRule({
  name: 'ModusPonens',
  description: 'From phi and phi -> psi, infer psi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (left, right) => isImplication(right) && formulaEquals(right.left, left),
  apply: (_left, right) => (right as TdfolBinaryFormula).right,
});

export const ModusTollensRule = new TdfolRule({
  name: 'ModusTollens',
  description: 'From phi -> psi and not psi, infer not phi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (implication, negatedConsequent) =>
    isImplication(implication) &&
    negatedConsequent.kind === 'unary' &&
    negatedConsequent.operator === 'NOT' &&
    formulaEquals(negatedConsequent.formula, implication.right),
  apply: (implication) => ({
    kind: 'unary',
    operator: 'NOT',
    formula: (implication as TdfolBinaryFormula).left,
  }),
});

export const HypotheticalSyllogismRule = new TdfolRule({
  name: 'HypotheticalSyllogism',
  description: 'From phi -> psi and psi -> chi, infer phi -> chi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (first, second) =>
    isImplication(first) && isImplication(second) && formulaEquals(first.right, second.left),
  apply: (first, second) => ({
    kind: 'binary',
    operator: 'IMPLIES',
    left: (first as TdfolBinaryFormula).left,
    right: (second as TdfolBinaryFormula).right,
  }),
});

export const DisjunctiveSyllogismRule = new TdfolRule({
  name: 'DisjunctiveSyllogism',
  description: 'From phi or psi and not phi, infer psi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (disjunction, negated) =>
    disjunction.kind === 'binary' &&
    disjunction.operator === 'OR' &&
    negated.kind === 'unary' &&
    negated.operator === 'NOT' &&
    (formulaEquals(negated.formula, disjunction.left) ||
      formulaEquals(negated.formula, disjunction.right)),
  apply: (disjunction, negated) => {
    if (disjunction.kind !== 'binary' || negated.kind !== 'unary') {
      throw new Error('Invalid disjunctive syllogism premises');
    }
    return formulaEquals(negated.formula, disjunction.left) ? disjunction.right : disjunction.left;
  },
});

export const ConjunctionIntroductionRule = new TdfolRule({
  name: 'ConjunctionIntroduction',
  description: 'From phi and psi, infer phi and psi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: () => true,
  apply: (left, right) => ({ kind: 'binary', operator: 'AND', left, right }),
});

export const ConjunctionEliminationLeftRule = new TdfolRule({
  name: 'ConjunctionEliminationLeft',
  description: 'From phi and psi, infer phi',
  arity: 1,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'AND',
  apply: (formula) => (formula as TdfolBinaryFormula).left,
});

export const ConjunctionEliminationRightRule = new TdfolRule({
  name: 'ConjunctionEliminationRight',
  description: 'From phi and psi, infer psi',
  arity: 1,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'AND',
  apply: (formula) => (formula as TdfolBinaryFormula).right,
});

export const DisjunctionIntroductionLeftRule = new TdfolRule({
  name: 'DisjunctionIntroductionLeft',
  description: 'From phi and psi, infer phi or psi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: () => true,
  apply: (left, right) => ({ kind: 'binary', operator: 'OR', left, right }),
});

export const DisjunctionIntroductionRightRule = new TdfolRule({
  name: 'DisjunctionIntroductionRight',
  description: 'From phi and psi, infer psi or phi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: () => true,
  apply: (left, right) => ({ kind: 'binary', operator: 'OR', left: right, right: left }),
});

export const DoubleNegationEliminationRule = new TdfolRule({
  name: 'DoubleNegationElimination',
  description: 'From not not phi, infer phi',
  arity: 1,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (formula) =>
    formula.kind === 'unary' &&
    formula.operator === 'NOT' &&
    formula.formula.kind === 'unary' &&
    formula.formula.operator === 'NOT',
  apply: (formula) => {
    if (formula.kind !== 'unary' || formula.formula.kind !== 'unary')
      throw new Error('Invalid double negation');
    return formula.formula.formula;
  },
});

export const BiconditionalIntroductionRule = new TdfolRule({
  name: 'BiconditionalIntroduction',
  description: 'From phi -> psi and psi -> phi, infer phi iff psi',
  arity: 2,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (left, right) =>
    isImplication(left) &&
    isImplication(right) &&
    formulaEquals(left.left, right.right) &&
    formulaEquals(left.right, right.left),
  apply: (left) => {
    if (!isImplication(left)) throw new Error('Invalid biconditional introduction premise');
    return { kind: 'binary', operator: 'IFF', left: left.left, right: left.right };
  },
});

export const BiconditionalEliminationLeftRule = new TdfolRule({
  name: 'BiconditionalEliminationLeft',
  description: 'From phi iff psi, infer phi -> psi',
  arity: 1,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'IFF',
  apply: (formula) => {
    if (formula.kind !== 'binary') throw new Error('Invalid biconditional premise');
    return { kind: 'binary', operator: 'IMPLIES', left: formula.left, right: formula.right };
  },
});

export const BiconditionalEliminationRightRule = new TdfolRule({
  name: 'BiconditionalEliminationRight',
  description: 'From phi iff psi, infer psi -> phi',
  arity: 1,
  category: 'propositional',
  sourcePythonModule: PROPOSITIONAL_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'binary' && formula.operator === 'IFF',
  apply: (formula) => {
    if (formula.kind !== 'binary') throw new Error('Invalid biconditional premise');
    return { kind: 'binary', operator: 'IMPLIES', left: formula.right, right: formula.left };
  },
});

export const TemporalKAxiomRule = new TdfolRule({
  name: 'TemporalKAxiom',
  description: 'From always(phi -> psi) and always(phi), infer always(psi)',
  arity: 2,
  category: 'temporal',
  canApply: (rule, premise) =>
    rule.kind === 'temporal' &&
    rule.operator === 'ALWAYS' &&
    isImplication(rule.formula) &&
    premise.kind === 'temporal' &&
    premise.operator === 'ALWAYS' &&
    formulaEquals(rule.formula.left, premise.formula),
  apply: (rule) => {
    if (rule.kind !== 'temporal' || !isImplication(rule.formula))
      throw new Error('Invalid temporal K premise');
    return { kind: 'temporal', operator: 'ALWAYS', formula: rule.formula.right };
  },
});

export const TemporalTAxiomRule = new TdfolRule({
  name: 'TemporalTAxiom',
  description: 'From always(phi), infer phi',
  arity: 1,
  category: 'temporal',
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
  category: 'temporal',
  canApply: () => true,
  apply: (formula) => ({ kind: 'temporal', operator: 'EVENTUALLY', formula }),
});

export const DeonticKAxiomRule = new TdfolRule({
  name: 'DeonticKAxiom',
  description: 'From O(phi -> psi) and O(phi), infer O(psi)',
  arity: 2,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (rule, premise) =>
    rule.kind === 'deontic' &&
    rule.operator === 'OBLIGATION' &&
    isImplication(rule.formula) &&
    premise.kind === 'deontic' &&
    premise.operator === 'OBLIGATION' &&
    formulaEquals(rule.formula.left, premise.formula),
  apply: (rule) => {
    if (rule.kind !== 'deontic' || !isImplication(rule.formula))
      throw new Error('Invalid deontic K premise');
    return { kind: 'deontic', operator: 'OBLIGATION', formula: rule.formula.right };
  },
});

export const DeonticDAxiomRule = new TdfolRule({
  name: 'DeonticDAxiom',
  description: 'From O(phi), infer P(phi)',
  arity: 1,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
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
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
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
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (formula) =>
    formula.kind === 'deontic' &&
    formula.operator === 'OBLIGATION' &&
    formula.formula.kind === 'unary' &&
    formula.formula.operator === 'NOT',
  apply: (formula) => {
    if (formula.kind !== 'deontic' || formula.formula.kind !== 'unary')
      throw new Error('Invalid obligation premise');
    return { kind: 'deontic', operator: 'PROHIBITION', formula: formula.formula.formula };
  },
});

export const ObligationWeakeningRule = new TdfolRule({
  name: 'ObligationWeakening',
  description: 'From O(phi and psi), infer O(phi)',
  arity: 1,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (formula) =>
    formula.kind === 'deontic' &&
    formula.operator === 'OBLIGATION' &&
    formula.formula.kind === 'binary' &&
    formula.formula.operator === 'AND',
  apply: (formula) => {
    if (formula.kind !== 'deontic' || formula.formula.kind !== 'binary')
      throw new Error('Invalid obligation premise');
    return { kind: 'deontic', operator: 'OBLIGATION', formula: formula.formula.left };
  },
});

export const ObligationWeakeningRightRule = new TdfolRule({
  name: 'ObligationWeakeningRight',
  description: 'From O(phi and psi), infer O(psi)',
  arity: 1,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (formula) =>
    formula.kind === 'deontic' &&
    formula.operator === 'OBLIGATION' &&
    formula.formula.kind === 'binary' &&
    formula.formula.operator === 'AND',
  apply: (formula) => {
    if (formula.kind !== 'deontic' || formula.formula.kind !== 'binary')
      throw new Error('Invalid obligation premise');
    return { kind: 'deontic', operator: 'OBLIGATION', formula: formula.formula.right };
  },
});

export const ObligationConjunctionRule = new TdfolRule({
  name: 'ObligationConjunction',
  description: 'From O(phi) and O(psi), infer O(phi and psi)',
  arity: 2,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (left, right) =>
    left.kind === 'deontic' &&
    left.operator === 'OBLIGATION' &&
    right.kind === 'deontic' &&
    right.operator === 'OBLIGATION',
  apply: (left, right) => {
    if (left.kind !== 'deontic' || right.kind !== 'deontic')
      throw new Error('Invalid obligation premises');
    return {
      kind: 'deontic',
      operator: 'OBLIGATION',
      formula: { kind: 'binary', operator: 'AND', left: left.formula, right: right.formula },
    };
  },
});

export const PermissionDualityRule = new TdfolRule({
  name: 'PermissionDuality',
  description: 'From P(phi), infer not O(not phi)',
  arity: 1,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'deontic' && formula.operator === 'PERMISSION',
  apply: (formula) => {
    if (formula.kind !== 'deontic') throw new Error('Invalid permission premise');
    return {
      kind: 'unary',
      operator: 'NOT',
      formula: {
        kind: 'deontic',
        operator: 'OBLIGATION',
        formula: { kind: 'unary', operator: 'NOT', formula: formula.formula },
      },
    };
  },
});

export const PermissionFromNonObligationRule = new TdfolRule({
  name: 'PermissionFromNonObligation',
  description: 'From not O(not phi), infer P(phi)',
  arity: 1,
  category: 'deontic',
  sourcePythonModule: DEONTIC_RULE_SOURCE,
  canApply: (formula) =>
    formula.kind === 'unary' &&
    formula.operator === 'NOT' &&
    formula.formula.kind === 'deontic' &&
    formula.formula.operator === 'OBLIGATION' &&
    formula.formula.formula.kind === 'unary' &&
    formula.formula.formula.operator === 'NOT',
  apply: (formula) => {
    if (
      formula.kind !== 'unary' ||
      formula.formula.kind !== 'deontic' ||
      formula.formula.formula.kind !== 'unary'
    ) {
      throw new Error('Invalid non-obligation premise');
    }
    return {
      kind: 'deontic',
      operator: 'PERMISSION',
      formula: formula.formula.formula.formula,
    };
  },
});

export const UniversalModusPonensRule = new TdfolRule({
  name: 'UniversalModusPonens',
  description: 'From forall x. (phi(x) -> psi(x)) and phi(a), infer psi(a)',
  arity: 2,
  category: 'first_order',
  sourcePythonModule: FIRST_ORDER_RULE_SOURCE,
  canApply: (universal, premise) => {
    if (
      universal.kind !== 'quantified' ||
      universal.quantifier !== 'FORALL' ||
      !isImplication(universal.formula)
    ) {
      return false;
    }
    return (
      matchFormulaForVariable(universal.formula.left, premise, universal.variable.name) !==
      undefined
    );
  },
  apply: (universal, premise) => {
    if (universal.kind !== 'quantified' || !isImplication(universal.formula)) {
      throw new Error('Invalid universal premise');
    }
    const binding = matchFormulaForVariable(
      universal.formula.left,
      premise,
      universal.variable.name,
    );
    if (!binding) throw new Error('Universal premise does not match supplied fact');
    return substituteFormula(universal.formula.right, universal.variable.name, binding);
  },
});

export const ExistentialInstantiationRule = new TdfolRule({
  name: 'ExistentialInstantiation',
  description: 'From exists x. phi(x), infer phi(skolem_x)',
  arity: 1,
  category: 'first_order',
  sourcePythonModule: FIRST_ORDER_RULE_SOURCE,
  canApply: (formula) => formula.kind === 'quantified' && formula.quantifier === 'EXISTS',
  apply: (formula) => {
    if (formula.kind !== 'quantified') throw new Error('Invalid existential premise');
    return substituteFormula(formula.formula, formula.variable.name, {
      kind: 'constant',
      name: `skolem_${formula.variable.name}`,
      sort: formula.variable.sort,
    });
  },
});

export const ExistentialGeneralizationRule = new TdfolRule({
  name: 'ExistentialGeneralization',
  description: 'From phi(a), infer exists x. phi(x) by replacing the first constant',
  arity: 1,
  category: 'first_order',
  sourcePythonModule: FIRST_ORDER_RULE_SOURCE,
  canApply: (formula) => findFirstConstant(formula) !== undefined,
  apply: (formula) => {
    const constant = findFirstConstant(formula);
    if (!constant) throw new Error('No constant available for existential generalization');
    const variable: TdfolTerm = { kind: 'variable', name: 'x', sort: constant.sort };
    return {
      kind: 'quantified',
      quantifier: 'EXISTS',
      variable,
      formula: replaceFirstTerm(formula, constant, variable),
    };
  },
});

export const UniversalGeneralizationRule = new TdfolRule({
  name: 'UniversalGeneralization',
  description: 'From phi(x), infer forall x. phi(x) for a free variable',
  arity: 1,
  category: 'first_order',
  sourcePythonModule: FIRST_ORDER_RULE_SOURCE,
  canApply: (formula) => getFreeVariables(formula).size > 0,
  apply: (formula) => {
    const [variableName] = [...getFreeVariables(formula)].sort();
    return {
      kind: 'quantified',
      quantifier: 'FORALL',
      variable: { kind: 'variable', name: variableName },
      formula,
    };
  },
});

export function getAllTdfolRules(): TdfolInferenceRule[] {
  return [
    ModusPonensRule,
    ModusTollensRule,
    HypotheticalSyllogismRule,
    DisjunctiveSyllogismRule,
    ConjunctionIntroductionRule,
    ConjunctionEliminationLeftRule,
    ConjunctionEliminationRightRule,
    DisjunctionIntroductionLeftRule,
    DisjunctionIntroductionRightRule,
    DoubleNegationEliminationRule,
    BiconditionalIntroductionRule,
    BiconditionalEliminationLeftRule,
    BiconditionalEliminationRightRule,
    TemporalKAxiomRule,
    TemporalTAxiomRule,
    EventuallyIntroductionRule,
    DeonticKAxiomRule,
    DeonticDAxiomRule,
    ProhibitionEquivalenceRule,
    ProhibitionFromObligationRule,
    ObligationWeakeningRule,
    ObligationWeakeningRightRule,
    ObligationConjunctionRule,
    PermissionDualityRule,
    PermissionFromNonObligationRule,
    UniversalModusPonensRule,
    ExistentialInstantiationRule,
    ExistentialGeneralizationRule,
    UniversalGeneralizationRule,
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
          applications.push({
            rule: rule.name,
            premises: [formula],
            conclusion: rule.apply(formula),
          });
        }
      }
    } else if (rule.arity === 2) {
      for (const left of formulas) {
        for (const right of formulas) {
          if (rule.canApply(left, right)) {
            applications.push({
              rule: rule.name,
              premises: [left, right],
              conclusion: rule.apply(left, right),
            });
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

function matchFormulaForVariable(
  pattern: TdfolFormula,
  target: TdfolFormula,
  variableName: string,
): TdfolTerm | undefined {
  const bindings = new Map<string, TdfolTerm>();
  return matchFormula(pattern, target, variableName, bindings)
    ? bindings.get(variableName)
    : undefined;
}

function matchFormula(
  pattern: TdfolFormula,
  target: TdfolFormula,
  variableName: string,
  bindings: Map<string, TdfolTerm>,
): boolean {
  if (pattern.kind !== target.kind) return false;
  switch (pattern.kind) {
    case 'predicate':
      return (
        target.kind === 'predicate' &&
        pattern.name === target.name &&
        pattern.args.length === target.args.length &&
        pattern.args.every((term, index) =>
          matchTerm(term, target.args[index], variableName, bindings),
        )
      );
    case 'unary':
      return (
        target.kind === 'unary' &&
        pattern.operator === target.operator &&
        matchFormula(pattern.formula, target.formula, variableName, bindings)
      );
    case 'binary':
      return (
        target.kind === 'binary' &&
        pattern.operator === target.operator &&
        matchFormula(pattern.left, target.left, variableName, bindings) &&
        matchFormula(pattern.right, target.right, variableName, bindings)
      );
    case 'quantified':
      return (
        target.kind === 'quantified' &&
        pattern.quantifier === target.quantifier &&
        matchFormula(pattern.formula, target.formula, variableName, bindings)
      );
    case 'deontic':
      return (
        target.kind === 'deontic' &&
        pattern.operator === target.operator &&
        matchFormula(pattern.formula, target.formula, variableName, bindings)
      );
    case 'temporal':
      return (
        target.kind === 'temporal' &&
        pattern.operator === target.operator &&
        matchFormula(pattern.formula, target.formula, variableName, bindings)
      );
  }
}

function matchTerm(
  pattern: TdfolTerm,
  target: TdfolTerm,
  variableName: string,
  bindings: Map<string, TdfolTerm>,
): boolean {
  if (pattern.kind === 'variable' && pattern.name === variableName) {
    const existing = bindings.get(variableName);
    if (!existing) {
      bindings.set(variableName, target);
      return true;
    }
    return formatTermKey(existing) === formatTermKey(target);
  }
  if (pattern.kind !== target.kind || pattern.name !== target.name) return false;
  if (pattern.kind === 'function' && target.kind === 'function') {
    return (
      pattern.args.length === target.args.length &&
      pattern.args.every((arg, index) => matchTerm(arg, target.args[index], variableName, bindings))
    );
  }
  return true;
}

function findFirstConstant(formula: TdfolFormula): TdfolTerm | undefined {
  switch (formula.kind) {
    case 'predicate':
      return formula.args.map(findFirstConstantInTerm).find(Boolean);
    case 'unary':
    case 'deontic':
    case 'temporal':
    case 'quantified':
      return findFirstConstant(formula.formula);
    case 'binary':
      return findFirstConstant(formula.left) ?? findFirstConstant(formula.right);
  }
}

function findFirstConstantInTerm(term: TdfolTerm): TdfolTerm | undefined {
  if (term.kind === 'constant') return term;
  if (term.kind === 'function') return term.args.map(findFirstConstantInTerm).find(Boolean);
  return undefined;
}

function replaceFirstTerm(
  formula: TdfolFormula,
  target: TdfolTerm,
  replacement: TdfolTerm,
): TdfolFormula {
  let replaced = false;
  const replaceTermOnce = (term: TdfolTerm): TdfolTerm => {
    if (!replaced && formatTermKey(term) === formatTermKey(target)) {
      replaced = true;
      return replacement;
    }
    if (term.kind === 'function') {
      return { ...term, args: term.args.map(replaceTermOnce) };
    }
    return term;
  };

  const walk = (node: TdfolFormula): TdfolFormula => {
    switch (node.kind) {
      case 'predicate':
        return { ...node, args: node.args.map(replaceTermOnce) };
      case 'unary':
        return { ...node, formula: walk(node.formula) };
      case 'binary':
        return { ...node, left: walk(node.left), right: walk(node.right) };
      case 'quantified':
      case 'deontic':
      case 'temporal':
        return { ...node, formula: walk(node.formula) };
    }
  };

  return walk(formula);
}

function formatTermKey(term: TdfolTerm): string {
  if (term.kind === 'function') {
    return `${term.name}(${term.args.map(formatTermKey).join(',')})`;
  }
  return `${term.kind}:${term.name}:${term.sort ?? ''}`;
}

function normalizeRuleId(name: string): string {
  return name
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase();
}
