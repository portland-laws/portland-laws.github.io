import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFunctionTerm,
  DcecQuantifiedFormula,
  DcecTemporalFormula,
  DcecVariableTerm,
  createDcecStatement,
  dcecAtom,
  dcecConjunction,
  dcecDisjunction,
  dcecImplication,
  dcecNegation,
  formatDcecStatement,
  sameDcecFormula,
} from './dcecCore';
import type { DcecCoreStatement, DcecFormula, DcecTerm } from './dcecCore';
import {
  DcecCognitiveOperator,
  DcecDeonticOperator,
  DcecFunctionSymbol,
  DcecLogicalConnective,
  DcecPredicateSymbol,
  DcecSort,
  DcecTemporalOperator,
  DcecVariable,
} from './dcecTypes';
import type {
  DcecCognitiveOperatorValue,
  DcecDeonticOperatorValue,
  DcecLogicalConnectiveValue,
  DcecTemporalOperatorValue,
} from './dcecTypes';

export {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFunctionTerm,
  DcecQuantifiedFormula,
  DcecTemporalFormula,
  DcecVariableTerm,
  createDcecStatement,
  dcecAtom,
  dcecConjunction,
  dcecDisjunction,
  dcecImplication,
  dcecNegation,
  formatDcecStatement,
  sameDcecFormula,
};
export type { DcecCoreStatement, DcecFormula, DcecTerm };
export {
  DcecCognitiveOperator,
  DcecDeonticOperator,
  DcecFunctionSymbol,
  DcecLogicalConnective,
  DcecPredicateSymbol,
  DcecSort,
  DcecTemporalOperator,
  DcecVariable,
};
export type {
  DcecCognitiveOperatorValue,
  DcecDeonticOperatorValue,
  DcecLogicalConnectiveValue,
  DcecTemporalOperatorValue,
};

export const Sort = DcecSort;
export const Variable = DcecVariable;
export const PredicateSymbol = DcecPredicateSymbol;
export const FunctionSymbol = DcecFunctionSymbol;
export const VariableTerm = DcecVariableTerm;
export const FunctionTerm = DcecFunctionTerm;
export const AtomicFormula = DcecAtomicFormula;
export const DeonticFormula = DcecDeonticFormula;
export const CognitiveFormula = DcecCognitiveFormula;
export const TemporalFormula = DcecTemporalFormula;
export const ConnectiveFormula = DcecConnectiveFormula;
export const QuantifiedFormula = DcecQuantifiedFormula;
export const DeonticOperator = DcecDeonticOperator;
export const CognitiveOperator = DcecCognitiveOperator;
export const TemporalOperator = DcecTemporalOperator;
export const LogicalConnective = DcecLogicalConnective;

export function get_sort(term: DcecTerm): DcecSort {
  return term.getSort();
}

export function get_free_variables(value: DcecTerm | DcecFormula): Set<unknown> {
  return value.getFreeVariables();
}

export function substitute_term(
  term: DcecTerm,
  variable: DcecVariable,
  replacement: DcecTerm,
): DcecTerm {
  return term.substitute(variable, replacement);
}

export function substitute_formula(
  formula: DcecFormula,
  variable: DcecVariable,
  replacement: DcecTerm,
): DcecFormula {
  return formula.substitute(variable, replacement);
}

export function atom(name: string, args: DcecTerm[] = []): DcecAtomicFormula {
  return dcecAtom(name, args);
}

export function conjunction(...formulas: DcecFormula[]): DcecConnectiveFormula {
  return dcecConjunction(...formulas);
}

export function disjunction(...formulas: DcecFormula[]): DcecConnectiveFormula {
  return dcecDisjunction(...formulas);
}

export function implication(left: DcecFormula, right: DcecFormula): DcecConnectiveFormula {
  return dcecImplication(left, right);
}

export function negation(formula: DcecFormula): DcecConnectiveFormula {
  return dcecNegation(formula);
}

export function same_formula(left: DcecFormula, right: DcecFormula): boolean {
  return sameDcecFormula(left, right);
}
