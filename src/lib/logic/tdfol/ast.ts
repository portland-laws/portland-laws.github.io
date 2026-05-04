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

export const TDFOL_CORE_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_core.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'terms',
    'formulas',
    'free_variables',
    'bound_variables',
    'capture_avoiding_substitution',
  ] as Array<string>,
} as const;

export function getFreeVariables(formula: TdfolFormula): Set<string> {
  switch (formula.kind) {
    case 'predicate':
      return formula.args.reduce(
        (vars, term) => unionInto(vars, getTermVariables(term)),
        new Set<string>(),
      );
    case 'unary':
    case 'temporal':
      return getFreeVariables(formula.formula);
    case 'binary':
      return unionInto(getFreeVariables(formula.left), getFreeVariables(formula.right));
    case 'deontic': {
      const vars = getFreeVariables(formula.formula);
      return formula.agent ? unionInto(vars, getTermVariables(formula.agent)) : vars;
    }
    case 'quantified': {
      const vars = getFreeVariables(formula.formula);
      vars.delete(formula.variable.name);
      return vars;
    }
  }
}

export function getBoundVariables(formula: TdfolFormula): Set<string> {
  switch (formula.kind) {
    case 'predicate':
      return new Set();
    case 'unary':
    case 'deontic':
    case 'temporal':
      return getBoundVariables(formula.formula);
    case 'binary':
      return unionInto(getBoundVariables(formula.left), getBoundVariables(formula.right));
    case 'quantified': {
      const vars = getBoundVariables(formula.formula);
      vars.add(formula.variable.name);
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
      return substituteQuantifiedFormula(formula, variableName, replacement);
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

function substituteQuantifiedFormula(
  formula: TdfolQuantifiedFormula,
  variableName: string,
  replacement: TdfolTerm,
): TdfolQuantifiedFormula {
  if (!getFreeVariables(formula.formula).has(variableName)) {
    return formula;
  }
  const replacementVariables = getTermVariables(replacement);
  if (!replacementVariables.has(formula.variable.name)) {
    return { ...formula, formula: substituteFormula(formula.formula, variableName, replacement) };
  }
  const freshName = freshVariableName(formula.variable.name, formula.formula, replacement);
  const renamedVariable: TdfolVariable = { ...formula.variable, name: freshName };
  const renamedBody = substituteFormula(formula.formula, formula.variable.name, renamedVariable);
  return {
    ...formula,
    variable: renamedVariable,
    formula: substituteFormula(renamedBody, variableName, replacement),
  };
}

function freshVariableName(
  baseName: string,
  formula: TdfolFormula,
  replacement: TdfolTerm,
): string {
  const used = unionInto(
    unionInto(getFreeVariables(formula), getBoundVariables(formula)),
    getTermVariables(replacement),
  );
  let index = 1;
  let candidate = `${baseName}_${index}`;
  while (used.has(candidate)) {
    index += 1;
    candidate = `${baseName}_${index}`;
  }
  return candidate;
}

function unionInto<T>(target: Set<T>, source: Set<T>): Set<T> {
  for (const value of source) {
    target.add(value);
  }
  return target;
}
