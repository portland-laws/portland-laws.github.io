import type { CecExpression } from './ast';
import {
  DcecFunctionSymbol,
  DcecPredicateSymbol,
  DcecSort,
  DcecVariable,
} from './dcecTypes';

export interface DcecNamespaceErrorDetails {
  symbol?: string;
  operation?: string;
  suggestion?: string;
}

export class DcecNamespaceError extends Error {
  readonly symbol?: string;
  readonly operation?: string;
  readonly suggestion?: string;

  constructor(message: string, details: DcecNamespaceErrorDetails = {}) {
    super(message);
    this.name = 'DcecNamespaceError';
    this.symbol = details.symbol;
    this.operation = details.operation;
    this.suggestion = details.suggestion;
  }
}

export interface DcecNamespaceStatistics {
  sorts: number;
  variables: number;
  functions: number;
  predicates: number;
}

export interface DcecStatement<Formula = CecExpression | string> {
  formula: Formula;
  label?: string;
  metadata: Record<string, unknown>;
}

export interface DcecContainerStatistics {
  total_statements: number;
  axioms: number;
  theorems: number;
  labeled_statements: number;
  namespace: DcecNamespaceStatistics;
}

export class DcecNamespace {
  readonly sorts = new Map<string, DcecSort>();
  readonly variables = new Map<string, DcecVariable>();
  readonly functions = new Map<string, DcecFunctionSymbol>();
  readonly predicates = new Map<string, DcecPredicateSymbol>();

  constructor() {
    this.initBuiltinSorts();
  }

  addSort(name: string, parent?: string): DcecSort {
    if (this.sorts.has(name)) {
      throw new DcecNamespaceError(`Duplicate sort name '${name}'`, {
        symbol: name,
        operation: 'add_sort',
        suggestion: `Use a different name or remove the existing sort '${name}' first`,
      });
    }

    const parentSort = parent === undefined ? undefined : this.sorts.get(parent);
    if (parent !== undefined && parentSort === undefined) {
      throw this.missingSortError(parent, 'lookup', `Parent sort '${parent}' does not exist`);
    }

    const sort = new DcecSort(name, parentSort);
    this.sorts.set(name, sort);
    return sort;
  }

  getSort(name: string): DcecSort | undefined {
    return this.sorts.get(name);
  }

  addVariable(name: string, sortName: string): DcecVariable {
    if (this.variables.has(name)) {
      throw new DcecNamespaceError(`Duplicate variable name '${name}'`, {
        symbol: name,
        operation: 'add_variable',
        suggestion: `Use a different variable name or remove the existing variable '${name}' first`,
      });
    }

    const sort = this.requireSort(sortName, 'lookup', `Sort '${sortName}' does not exist for variable`);
    const variable = new DcecVariable(name, sort);
    this.variables.set(name, variable);
    return variable;
  }

  getVariable(name: string): DcecVariable | undefined {
    return this.variables.get(name);
  }

  addFunction(name: string, argumentSortNames: string[], returnSortName: string): DcecFunctionSymbol {
    if (this.functions.has(name)) {
      throw new DcecNamespaceError(`Duplicate function name '${name}'`, {
        symbol: name,
        operation: 'add_function',
        suggestion: `Use a different function name or remove the existing function '${name}' first`,
      });
    }

    const argumentSorts = argumentSortNames.map((sortName) => (
      this.requireSort(sortName, 'lookup', `Sort '${sortName}' does not exist for function argument`)
    ));
    const returnSort = this.requireSort(returnSortName, 'lookup', `Return sort '${returnSortName}' does not exist`);
    const func = new DcecFunctionSymbol(name, argumentSorts, returnSort);
    this.functions.set(name, func);
    return func;
  }

  getFunction(name: string): DcecFunctionSymbol | undefined {
    return this.functions.get(name);
  }

  addPredicate(name: string, argumentSortNames: string[]): DcecPredicateSymbol {
    if (this.predicates.has(name)) {
      throw new DcecNamespaceError(`Duplicate predicate name '${name}'`, {
        symbol: name,
        operation: 'add_predicate',
        suggestion: `Use a different predicate name or remove the existing predicate '${name}' first`,
      });
    }

    const argumentSorts = argumentSortNames.map((sortName) => (
      this.requireSort(sortName, 'lookup', `Sort '${sortName}' does not exist for predicate argument`)
    ));
    const predicate = new DcecPredicateSymbol(name, argumentSorts);
    this.predicates.set(name, predicate);
    return predicate;
  }

  getPredicate(name: string, arity?: number): DcecPredicateSymbol | undefined {
    const predicate = this.predicates.get(name);
    if (predicate !== undefined || arity === undefined) return predicate;
    return this.addPredicate(name, []);
  }

  getStatistics(): DcecNamespaceStatistics {
    return {
      sorts: this.sorts.size,
      variables: this.variables.size,
      functions: this.functions.size,
      predicates: this.predicates.size,
    };
  }

  toString(): string {
    const stats = this.getStatistics();
    return `DCECNamespace(sorts=${stats.sorts}, vars=${stats.variables}, funcs=${stats.functions}, preds=${stats.predicates})`;
  }

  private initBuiltinSorts() {
    this.addSort('Entity');
    this.addSort('Boolean');
    this.addSort('Moment');
    this.addSort('Event');
    this.addSort('Action');
    this.addSort('Agent', 'Entity');
    this.addSort('ActionType');
    this.addSort('Obligation', 'Boolean');
    this.addSort('Permission', 'Boolean');
  }

  private requireSort(name: string, operation: string, message: string): DcecSort {
    const sort = this.sorts.get(name);
    if (sort === undefined) throw this.missingSortError(name, operation, message);
    return sort;
  }

  private missingSortError(name: string, operation: string, message: string): DcecNamespaceError {
    return new DcecNamespaceError(message, {
      symbol: name,
      operation,
      suggestion: `Register sort '${name}' first, or use an existing sort: ${[...this.sorts.keys()].join(', ')}`,
    });
  }
}

export class DcecContainer<Formula = CecExpression | string> {
  readonly namespace: DcecNamespace;
  private readonly statements: DcecStatement<Formula>[] = [];
  private readonly statementLabels = new Map<string, DcecStatement<Formula>>();
  private readonly axioms: DcecStatement<Formula>[] = [];
  private readonly theorems: DcecStatement<Formula>[] = [];

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
  }

  addStatement(
    formula: Formula,
    options: { label?: string; isAxiom?: boolean; metadata?: Record<string, unknown> } = {},
  ): DcecStatement<Formula> {
    if (options.label !== undefined && this.statementLabels.has(options.label)) {
      throw new DcecNamespaceError(`Duplicate statement label '${options.label}'`, {
        symbol: options.label,
        operation: 'add_statement',
        suggestion: `Use a different label or remove the existing statement with label '${options.label}' first`,
      });
    }

    const statement: DcecStatement<Formula> = {
      formula,
      label: options.label,
      metadata: options.metadata ?? {},
    };
    this.statements.push(statement);
    if (options.label !== undefined) this.statementLabels.set(options.label, statement);
    if (options.isAxiom) this.axioms.push(statement);
    return statement;
  }

  addAxiom(formula: Formula, label?: string, metadata?: Record<string, unknown>): DcecStatement<Formula> {
    return this.addStatement(formula, { label, isAxiom: true, metadata });
  }

  addTheorem(formula: Formula, label?: string): DcecStatement<Formula> {
    const statement = this.addStatement(formula, { label, isAxiom: false });
    this.theorems.push(statement);
    return statement;
  }

  getStatement(label: string): DcecStatement<Formula> | undefined {
    return this.statementLabels.get(label);
  }

  getAllStatements(): DcecStatement<Formula>[] {
    return [...this.statements];
  }

  getAxioms(): DcecStatement<Formula>[] {
    return [...this.axioms];
  }

  getTheorems(): DcecStatement<Formula>[] {
    return [...this.theorems];
  }

  clear() {
    this.statements.length = 0;
    this.statementLabels.clear();
    this.axioms.length = 0;
    this.theorems.length = 0;
  }

  getStatistics(): DcecContainerStatistics {
    return {
      total_statements: this.statements.length,
      axioms: this.axioms.length,
      theorems: this.theorems.length,
      labeled_statements: this.statementLabels.size,
      namespace: this.namespace.getStatistics(),
    };
  }

  toString(): string {
    const stats = this.getStatistics();
    return `DCECContainer(statements=${stats.total_statements}, axioms=${stats.axioms}, theorems=${stats.theorems})`;
  }
}
