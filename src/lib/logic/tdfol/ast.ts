export type TdfolSort =
  | 'Agent'
  | 'Action'
  | 'Event'
  | 'Time'
  | 'Proposition'
  | 'Object'
  | 'State'
  | 'Condition'
  | string;

export type TdfolTerm = TdfolVariable | TdfolConstant | TdfolFunctionApplication;

export interface TdfolVariable {
  kind: 'variable';
  name: string;
  sort?: TdfolSort;
}

export interface TdfolConstant {
  kind: 'constant';
  name: string;
  sort?: TdfolSort;
}

export interface TdfolFunctionApplication {
  kind: 'function';
  name: string;
  args: TdfolTerm[];
  sort?: TdfolSort;
}

export type TdfolFormula =
  | TdfolPredicate
  | TdfolUnaryFormula
  | TdfolBinaryFormula
  | TdfolQuantifiedFormula
  | TdfolDeonticFormula
  | TdfolTemporalFormula;

export interface TdfolPredicate {
  kind: 'predicate';
  name: string;
  args: TdfolTerm[];
}

export type TdfolUnaryOperator = 'NOT';
export type TdfolBinaryOperator = 'AND' | 'OR' | 'IMPLIES' | 'IFF' | 'XOR' | 'UNTIL';
export type TdfolQuantifier = 'FORALL' | 'EXISTS';
export type TdfolDeonticOperator = 'OBLIGATION' | 'PERMISSION' | 'PROHIBITION';
export type TdfolTemporalOperator = 'ALWAYS' | 'EVENTUALLY' | 'NEXT';

export interface TdfolUnaryFormula {
  kind: 'unary';
  operator: TdfolUnaryOperator;
  formula: TdfolFormula;
}

export interface TdfolBinaryFormula {
  kind: 'binary';
  operator: TdfolBinaryOperator;
  left: TdfolFormula;
  right: TdfolFormula;
}

export interface TdfolQuantifiedFormula {
  kind: 'quantified';
  quantifier: TdfolQuantifier;
  variable: TdfolVariable;
  formula: TdfolFormula;
}

export interface TdfolDeonticFormula {
  kind: 'deontic';
  operator: TdfolDeonticOperator;
  formula: TdfolFormula;
  agent?: TdfolTerm;
}

export interface TdfolTemporalFormula {
  kind: 'temporal';
  operator: TdfolTemporalOperator;
  formula: TdfolFormula;
}

export function getFreeVariables(formula: TdfolFormula): Set<string> {
  switch (formula.kind) {
    case 'predicate':
      return formula.args.reduce(
        (vars, term) => unionInto(vars, getTermVariables(term)),
        new Set<string>(),
      );
    case 'unary':
    case 'deontic':
    case 'temporal':
      return getFreeVariables(formula.formula);
    case 'binary':
      return unionInto(getFreeVariables(formula.left), getFreeVariables(formula.right));
    case 'quantified': {
      const vars = getFreeVariables(formula.formula);
      vars.delete(formula.variable.name);
      return vars;
    }
  }
}

export function getTermVariables(term: TdfolTerm): Set<string> {
  switch (term.kind) {
    case 'variable':
      return new Set([term.name]);
    case 'constant':
      return new Set();
    case 'function':
      return term.args.reduce(
        (vars, arg) => unionInto(vars, getTermVariables(arg)),
        new Set<string>(),
      );
  }
}

export function substituteFormula(
  formula: TdfolFormula,
  variableName: string,
  replacement: TdfolTerm,
): TdfolFormula {
  switch (formula.kind) {
    case 'predicate':
      return {
        ...formula,
        args: formula.args.map((term) => substituteTerm(term, variableName, replacement)),
      };
    case 'unary':
      return { ...formula, formula: substituteFormula(formula.formula, variableName, replacement) };
    case 'binary':
      return {
        ...formula,
        left: substituteFormula(formula.left, variableName, replacement),
        right: substituteFormula(formula.right, variableName, replacement),
      };
    case 'deontic':
      return {
        ...formula,
        agent: formula.agent ? substituteTerm(formula.agent, variableName, replacement) : undefined,
        formula: substituteFormula(formula.formula, variableName, replacement),
      };
    case 'temporal':
      return { ...formula, formula: substituteFormula(formula.formula, variableName, replacement) };
    case 'quantified':
      if (formula.variable.name === variableName) {
        return formula;
      }
      return { ...formula, formula: substituteFormula(formula.formula, variableName, replacement) };
  }
}

export function substituteTerm(
  term: TdfolTerm,
  variableName: string,
  replacement: TdfolTerm,
): TdfolTerm {
  switch (term.kind) {
    case 'variable':
      return term.name === variableName ? replacement : term;
    case 'constant':
      return term;
    case 'function':
      return {
        ...term,
        args: term.args.map((arg) => substituteTerm(arg, variableName, replacement)),
      };
  }
}

function unionInto<T>(target: Set<T>, source: Set<T>): Set<T> {
  for (const value of source) {
    target.add(value);
  }
  return target;
}
