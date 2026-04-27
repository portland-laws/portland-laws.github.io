import { LogicValidationError } from '../errors';
import {
  DcecCognitiveOperatorValue,
  DcecDeonticOperatorValue,
  DcecFunctionSymbol,
  DcecLogicalConnective,
  DcecLogicalConnectiveValue,
  DcecPredicateSymbol,
  DcecSort,
  DcecTemporalOperatorValue,
  DcecVariable,
} from './dcecTypes';

export type DcecTerm = DcecVariableTerm | DcecFunctionTerm;
export type DcecFormula =
  | DcecAtomicFormula
  | DcecDeonticFormula
  | DcecCognitiveFormula
  | DcecTemporalFormula
  | DcecConnectiveFormula
  | DcecQuantifiedFormula;

export class DcecVariableTerm {
  readonly variable: DcecVariable;

  constructor(variable: DcecVariable) {
    this.variable = variable;
  }

  getSort(): DcecSort {
    return this.variable.sort;
  }

  getFreeVariables(): Set<DcecVariable> {
    return new Set([this.variable]);
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecTerm {
    return sameDcecVariable(this.variable, variable) ? term : this;
  }

  toString(): string {
    return String(this.variable);
  }
}

export class DcecFunctionTerm {
  readonly functionSymbol: DcecFunctionSymbol;
  readonly arguments: DcecTerm[];

  constructor(functionSymbol: DcecFunctionSymbol, args: DcecTerm[]) {
    if (args.length !== functionSymbol.arity()) {
      throw new LogicValidationError(`Function arity mismatch for '${functionSymbol.name}'`, {
        value: args.length,
        expectedType: `${functionSymbol.arity()} arguments`,
        suggestion: `Provide exactly ${functionSymbol.arity()} arguments to function '${functionSymbol.name}'`,
      });
    }
    this.functionSymbol = functionSymbol;
    this.arguments = [...args];
  }

  getSort(): DcecSort {
    return this.functionSymbol.returnSort;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables(this.arguments.flatMap((arg) => [...arg.getFreeVariables()]));
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecTerm {
    return new DcecFunctionTerm(this.functionSymbol, this.arguments.map((arg) => arg.substitute(variable, term)));
  }

  toString(): string {
    return `${this.functionSymbol.name}(${this.arguments.map(String).join(', ')})`;
  }
}

export class DcecAtomicFormula {
  readonly predicate: DcecPredicateSymbol;
  readonly arguments: DcecTerm[];

  constructor(predicate: DcecPredicateSymbol, args: DcecTerm[]) {
    if (args.length !== predicate.arity()) {
      throw new LogicValidationError(`Predicate arity mismatch for '${predicate.name}'`, {
        value: args.length,
        expectedType: `${predicate.arity()} arguments`,
        suggestion: `Provide exactly ${predicate.arity()} arguments to predicate '${predicate.name}'`,
      });
    }
    this.predicate = predicate;
    this.arguments = [...args];
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables(this.arguments.flatMap((arg) => [...arg.getFreeVariables()]));
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    return new DcecAtomicFormula(this.predicate, this.arguments.map((arg) => arg.substitute(variable, term)));
  }

  toString(): string {
    return `${this.predicate.name}(${this.arguments.map(String).join(', ')})`;
  }
}

export class DcecDeonticFormula {
  readonly operator: DcecDeonticOperatorValue;
  readonly formula: DcecFormula;
  readonly agent?: DcecTerm;

  constructor(operator: DcecDeonticOperatorValue, formula: DcecFormula, agent?: DcecTerm) {
    this.operator = operator;
    this.formula = formula;
    this.agent = agent;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables([
      ...this.formula.getFreeVariables(),
      ...(this.agent ? this.agent.getFreeVariables() : []),
    ]);
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    return new DcecDeonticFormula(
      this.operator,
      this.formula.substitute(variable, term),
      this.agent?.substitute(variable, term),
    );
  }

  toString(): string {
    return this.agent
      ? `${this.operator}[${this.agent}](${this.formula.toString()})`
      : `${this.operator}(${this.formula.toString()})`;
  }
}

export class DcecCognitiveFormula {
  readonly operator: DcecCognitiveOperatorValue;
  readonly agent: DcecTerm;
  readonly formula: DcecFormula;

  constructor(operator: DcecCognitiveOperatorValue, agent: DcecTerm, formula: DcecFormula) {
    this.operator = operator;
    this.agent = agent;
    this.formula = formula;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables([...this.agent.getFreeVariables(), ...this.formula.getFreeVariables()]);
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    return new DcecCognitiveFormula(
      this.operator,
      this.agent.substitute(variable, term),
      this.formula.substitute(variable, term),
    );
  }

  toString(): string {
    return `${this.operator}(${this.agent}, ${this.formula.toString()})`;
  }
}

export class DcecTemporalFormula {
  readonly operator: DcecTemporalOperatorValue;
  readonly formula: DcecFormula;
  readonly time?: DcecTerm;

  constructor(operator: DcecTemporalOperatorValue, formula: DcecFormula, time?: DcecTerm) {
    this.operator = operator;
    this.formula = formula;
    this.time = time;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables([
      ...this.formula.getFreeVariables(),
      ...(this.time ? this.time.getFreeVariables() : []),
    ]);
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    return new DcecTemporalFormula(
      this.operator,
      this.formula.substitute(variable, term),
      this.time?.substitute(variable, term),
    );
  }

  toString(): string {
    const symbol = temporalSymbol(this.operator);
    return this.time
      ? `${symbol}[${this.time}](${this.formula.toString()})`
      : `${symbol}(${this.formula.toString()})`;
  }
}

export class DcecConnectiveFormula {
  readonly connective: DcecLogicalConnectiveValue;
  readonly formulas: DcecFormula[];

  constructor(connective: DcecLogicalConnectiveValue, formulas: DcecFormula[]) {
    validateConnectiveArity(connective, formulas.length);
    this.connective = connective;
    this.formulas = [...formulas];
  }

  get operator(): DcecLogicalConnectiveValue {
    return this.connective;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables(this.formulas.flatMap((formula) => [...formula.getFreeVariables()]));
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    return new DcecConnectiveFormula(this.connective, this.formulas.map((formula) => formula.substitute(variable, term)));
  }

  toString(): string {
    const symbol = connectiveSymbol(this.connective);
    if (this.connective === DcecLogicalConnective.NOT) {
      return `¬(${this.formulas[0].toString()})`;
    }
    if (this.connective === DcecLogicalConnective.IMPLIES || this.connective === DcecLogicalConnective.BICONDITIONAL) {
      return `(${this.formulas[0].toString()} ${symbol} ${this.formulas[1].toString()})`;
    }
    return `(${this.formulas.map(String).join(` ${symbol} `)})`;
  }
}

export class DcecQuantifiedFormula {
  readonly quantifier: DcecLogicalConnectiveValue;
  readonly variable: DcecVariable;
  readonly formula: DcecFormula;

  constructor(quantifier: DcecLogicalConnectiveValue, variable: DcecVariable, formula: DcecFormula) {
    if (quantifier !== DcecLogicalConnective.EXISTS && quantifier !== DcecLogicalConnective.FORALL) {
      throw new LogicValidationError('Invalid quantifier', {
        value: quantifier,
        expectedType: 'EXISTS or FORALL',
        suggestion: 'Use DcecLogicalConnective.EXISTS or DcecLogicalConnective.FORALL as quantifier',
      });
    }
    this.quantifier = quantifier;
    this.variable = variable;
    this.formula = formula;
  }

  getFreeVariables(): Set<DcecVariable> {
    return unionDcecVariables([...this.formula.getFreeVariables()].filter((candidate) => !sameDcecVariable(candidate, this.variable)));
  }

  substitute(variable: DcecVariable, term: DcecTerm): DcecFormula {
    if (sameDcecVariable(variable, this.variable)) return this;
    return new DcecQuantifiedFormula(this.quantifier, this.variable, this.formula.substitute(variable, term));
  }

  toString(): string {
    return `${quantifierSymbol(this.quantifier)}${this.variable}(${this.formula.toString()})`;
  }
}

export interface DcecCoreStatement {
  formula: DcecFormula;
  label?: string;
  metadata: Record<string, unknown>;
}

export function createDcecStatement(
  formula: DcecFormula,
  label?: string,
  metadata: Record<string, unknown> = {},
): DcecCoreStatement {
  return { formula, label, metadata };
}

export function formatDcecStatement(statement: DcecCoreStatement): string {
  return statement.label ? `${statement.label}: ${statement.formula.toString()}` : statement.formula.toString();
}

export function dcecAtom(predicateOrName: string | DcecPredicateSymbol, args: DcecTerm[] = []): DcecAtomicFormula {
  const predicate = typeof predicateOrName === 'string' ? new DcecPredicateSymbol(predicateOrName, []) : predicateOrName;
  return new DcecAtomicFormula(predicate, args);
}

export function dcecConjunction(...formulas: DcecFormula[]): DcecConnectiveFormula {
  return new DcecConnectiveFormula(DcecLogicalConnective.AND, formulas);
}

export function dcecDisjunction(...formulas: DcecFormula[]): DcecConnectiveFormula {
  return new DcecConnectiveFormula(DcecLogicalConnective.OR, formulas);
}

export function dcecNegation(formula: DcecFormula): DcecConnectiveFormula {
  return new DcecConnectiveFormula(DcecLogicalConnective.NOT, [formula]);
}

export function dcecImplication(antecedent: DcecFormula, consequent: DcecFormula): DcecConnectiveFormula {
  return new DcecConnectiveFormula(DcecLogicalConnective.IMPLIES, [antecedent, consequent]);
}

export function sameDcecFormula(left: DcecFormula, right: DcecFormula): boolean {
  return left.toString() === right.toString();
}

export function sameDcecVariable(left: DcecVariable, right: DcecVariable): boolean {
  return left.name === right.name && sameDcecSort(left.sort, right.sort);
}

function sameDcecSort(left: DcecSort, right: DcecSort): boolean {
  return left.name === right.name && (
    (left.parent === undefined && right.parent === undefined)
    || (left.parent !== undefined && right.parent !== undefined && sameDcecSort(left.parent, right.parent))
  );
}

function unionDcecVariables(variables: Iterable<DcecVariable>): Set<DcecVariable> {
  const result = new Map<string, DcecVariable>();
  for (const variable of variables) {
    result.set(variableKey(variable), variable);
  }
  return new Set(result.values());
}

function variableKey(variable: DcecVariable): string {
  return `${variable.name}:${variable.sort.name}`;
}

function validateConnectiveArity(connective: DcecLogicalConnectiveValue, arity: number) {
  if (connective === DcecLogicalConnective.NOT && arity !== 1) {
    throw new LogicValidationError('NOT connective arity mismatch', {
      value: arity,
      expectedType: 'exactly 1 formula',
      suggestion: 'Provide exactly one formula for NOT operation',
    });
  }
  if ((connective === DcecLogicalConnective.AND || connective === DcecLogicalConnective.OR) && arity < 2) {
    throw new LogicValidationError(`${connective.toUpperCase()} connective arity mismatch`, {
      value: arity,
      expectedType: 'at least 2 formulas',
      suggestion: `Provide at least 2 formulas for ${connective.toUpperCase()} operation`,
    });
  }
  if ((connective === DcecLogicalConnective.IMPLIES || connective === DcecLogicalConnective.BICONDITIONAL) && arity !== 2) {
    throw new LogicValidationError(`${connective.toUpperCase()} connective arity mismatch`, {
      value: arity,
      expectedType: 'exactly 2 formulas',
      suggestion: `Provide exactly 2 formulas for ${connective.toUpperCase()} operation`,
    });
  }
}

function connectiveSymbol(connective: DcecLogicalConnectiveValue): string {
  switch (connective) {
    case DcecLogicalConnective.AND:
      return '∧';
    case DcecLogicalConnective.OR:
      return '∨';
    case DcecLogicalConnective.NOT:
      return '¬';
    case DcecLogicalConnective.IMPLIES:
      return '→';
    case DcecLogicalConnective.BICONDITIONAL:
    case DcecLogicalConnective.IFF:
      return '↔';
    default:
      return connective;
  }
}

function quantifierSymbol(quantifier: DcecLogicalConnectiveValue): string {
  return quantifier === DcecLogicalConnective.FORALL ? '∀' : '∃';
}

function temporalSymbol(operator: DcecTemporalOperatorValue): string {
  switch (operator) {
    case 'always':
      return '□';
    case 'eventually':
      return '◊';
    case 'next':
      return 'X';
    case 'until':
      return 'U';
    case 'since':
      return 'S';
    default:
      return operator;
  }
}
