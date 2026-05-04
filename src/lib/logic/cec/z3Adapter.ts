import type { ProofResult, ProofStatus } from '../types';
import type { CecExpression } from './ast';
import { parseCecExpression } from './parser';
import { proveCec, type CecProverOptions } from './prover';

export type CecZ3Logic = 'ALL' | 'UF' | 'QF_UF';
export type CecZ3CheckSatStatus = 'unsat' | 'sat' | 'unknown' | 'error';

export interface CecZ3AdapterOptions extends CecProverOptions {
  readonly logic?: CecZ3Logic;
}

export interface CecZ3Metadata {
  readonly adapter: 'browser-native-cec-z3-adapter';
  readonly sourcePythonModule: 'logic/CEC/provers/z3_adapter.py';
  readonly runtime: 'typescript-wasm-browser';
  readonly externalBinaryAllowed: false;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly command: null;
  readonly smtLibProblem: string;
  readonly smtLibAxioms: string[];
  readonly smtLibNegatedTheorem: string;
  readonly checkSatStatus: CecZ3CheckSatStatus;
  readonly warnings: string[];
}

export class CecZ3Adapter {
  constructor(private readonly options: CecZ3AdapterOptions = {}) {}

  prove(
    theorem: string | CecExpression,
    axioms: readonly (string | CecExpression)[] = [],
  ): ProofResult & { readonly z3: CecZ3Metadata } {
    const parsedTheorem = normalizeCecExpression(theorem);
    const parsedAxioms = axioms.map(normalizeCecExpression);
    const result = proveCec(parsedTheorem, { axioms: parsedAxioms }, this.options);
    const smt = createCecZ3SmtLibProblem(parsedTheorem, parsedAxioms, this.options.logic ?? 'ALL');
    return {
      ...result,
      method: `z3-compatible:${result.method ?? 'cec-forward-chaining'}`,
      z3: z3Metadata(smt, mapCecZ3Status(result.status)),
    };
  }
}

export function proveCecWithZ3Adapter(
  theorem: string | CecExpression,
  axioms: readonly (string | CecExpression)[] = [],
  options: CecZ3AdapterOptions = {},
): ProofResult & { readonly z3: CecZ3Metadata } {
  return new CecZ3Adapter(options).prove(theorem, axioms);
}

export function mapCecZ3Status(status: ProofStatus): CecZ3CheckSatStatus {
  if (status === 'proved') return 'unsat';
  if (status === 'disproved') return 'sat';
  if (status === 'error') return 'error';
  return 'unknown';
}

export function createCecZ3SmtLibProblem(
  theorem: CecExpression,
  axioms: readonly CecExpression[] = [],
  logic: CecZ3Logic = 'ALL',
): { readonly problem: string; readonly axioms: string[]; readonly negatedTheorem: string } {
  const declarations = collectDeclarations([theorem, ...axioms]);
  const smtAxioms = axioms.map((axiom) => `(assert ${toSmt(axiom)})`);
  const negatedTheorem = `(assert (not ${toSmt(theorem)}))`;
  const predicateDeclarations = [...declarations.predicates.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, arity]) => `(declare-fun ${name} (${'Entity '.repeat(arity).trim()}) Bool)`);
  return {
    problem: [
      '; Browser-native CEC Z3 compatibility problem',
      `(set-logic ${logic})`,
      '(declare-sort Entity 0)',
      ...[...declarations.constants].sort().map((name) => `(declare-const ${name} Entity)`),
      ...[...declarations.booleans].sort().map((name) => `(declare-const ${name} Bool)`),
      ...predicateDeclarations,
      ...smtAxioms,
      negatedTheorem,
      '(check-sat)',
    ].join('\n'),
    axioms: smtAxioms,
    negatedTheorem,
  };
}

function z3Metadata(
  smt: { readonly problem: string; readonly axioms: string[]; readonly negatedTheorem: string },
  checkSatStatus: CecZ3CheckSatStatus,
): CecZ3Metadata {
  return {
    adapter: 'browser-native-cec-z3-adapter',
    sourcePythonModule: 'logic/CEC/provers/z3_adapter.py',
    runtime: 'typescript-wasm-browser',
    externalBinaryAllowed: false,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    command: null,
    smtLibProblem: smt.problem,
    smtLibAxioms: smt.axioms,
    smtLibNegatedTheorem: smt.negatedTheorem,
    checkSatStatus,
    warnings: [
      'External Z3 process and Python z3 bindings are unavailable in the browser; proof search used the local TypeScript CEC engine.',
    ],
  };
}

function toSmt(expression: CecExpression): string {
  if (expression.kind === 'atom') return symbol(expression.name, 'atom');
  if (expression.kind === 'application') {
    const name = symbol(expression.name, 'predicate');
    return expression.args.length === 0
      ? name
      : `(${name} ${expression.args.map(toSmt).join(' ')})`;
  }
  if (expression.kind === 'unary') {
    const inner = toSmt(expression.expression);
    return expression.operator === 'not'
      ? `(not ${inner})`
      : `(${symbol(expression.operator, 'modal')} ${inner})`;
  }
  if (expression.kind === 'quantified') {
    const quantifier = expression.quantifier === 'forall' ? 'forall' : 'exists';
    return `(${quantifier} ((${symbol(expression.variable, 'x')} Entity)) ${toSmt(expression.expression)})`;
  }
  return `(${binaryOperator(expression.operator)} ${toSmt(expression.left)} ${toSmt(expression.right)})`;
}

function collectDeclarations(expressions: readonly CecExpression[]): {
  readonly constants: Set<string>;
  readonly booleans: Set<string>;
  readonly predicates: Map<string, number>;
} {
  const constants = new Set<string>();
  const booleans = new Set<string>();
  const predicates = new Map<string, number>();
  const visit = (expression: CecExpression, bound: ReadonlySet<string>, term: boolean): void => {
    if (expression.kind === 'atom') {
      const name = symbol(expression.name, 'atom');
      if (!bound.has(name)) (term ? constants : booleans).add(name);
    } else if (expression.kind === 'application') {
      predicates.set(symbol(expression.name, 'predicate'), expression.args.length);
      expression.args.forEach((arg) => visit(arg, bound, true));
    } else if (expression.kind === 'unary') {
      if (expression.operator !== 'not') predicates.set(symbol(expression.operator, 'modal'), 1);
      visit(expression.expression, bound, false);
    } else if (expression.kind === 'quantified') {
      visit(
        expression.expression,
        new Set<string>([...bound, symbol(expression.variable, 'x')]),
        false,
      );
    } else {
      visit(expression.left, bound, false);
      visit(expression.right, bound, false);
    }
  };
  expressions.forEach((expression) => visit(expression, new Set<string>(), false));
  constants.forEach((name) => booleans.delete(name));
  return { constants, booleans, predicates };
}

function binaryOperator(operator: string): string {
  if (operator === 'implies') return '=>';
  if (operator === 'iff') return '=';
  return ['and', 'or', 'xor'].includes(operator) ? operator : symbol(operator, 'binary');
}

function symbol(value: string, fallback: string): string {
  const normalized = value
    .trim()
    .replace(/[^A-Za-z0-9_.$-]/g, '_')
    .replace(/_+/g, '_');
  const candidate = normalized.length > 0 ? normalized : fallback;
  return /^[A-Za-z_.$-]/.test(candidate) ? candidate : `${fallback}_${candidate}`;
}

function normalizeCecExpression(expression: string | CecExpression): CecExpression {
  return typeof expression === 'string' ? parseCecExpression(expression) : expression;
}
