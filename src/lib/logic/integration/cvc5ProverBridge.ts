import type { TdfolBinaryOperator, TdfolFormula, TdfolTerm } from '../tdfol/ast';
import { parseTdfolFormula } from '../tdfol/parser';
import { proveTdfol, type TdfolProverOptions } from '../tdfol/prover';
import type { ProofResult } from '../types';
import type { BrowserNativeProofAdapter, BrowserNativeProofRequest } from './proverAdapters';

export type Cvc5CheckSatStatus = 'unsat' | 'sat' | 'unknown' | 'timeout' | 'error';
export interface Cvc5CompatibilityMetadata {
  adapter: 'browser-native-cvc5-prover-bridge';
  sourcePythonModule: 'logic/external_provers/smt/cvc5_prover_bridge.py';
  externalBinaryAllowed: false;
  serverCallsAllowed: false;
  pythonRuntime: false;
  wasmRuntime: 'not-bundled';
  command: null;
  cvc5Available: false;
  smtLib: string;
  checkSatStatus: Cvc5CheckSatStatus;
  isValid: boolean;
  isSat: boolean;
  isUnsat: boolean;
  model: null;
  proof: null;
  warnings: string[];
}
export interface BrowserNativeCvc5ProofResult extends ProofResult {
  cvc5: Cvc5CompatibilityMetadata;
}

export function createBrowserNativeCvc5ProverBridge(
  options: TdfolProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'browser-native-cvc5-prover-bridge',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'local',
    },
    supports: (logic) => logic === 'tdfol',
    prove: (request) => proveCvc5CompatibleTdfol(request, options),
  };
}
export function proveCvc5CompatibleTdfol(
  request: BrowserNativeProofRequest,
  options: TdfolProverOptions = {},
): BrowserNativeCvc5ProofResult {
  try {
    const theorem = parseTdfolFormula(request.theorem);
    const axioms = request.axioms.map(parseTdfolFormula);
    const result = proveTdfol(
      theorem,
      { axioms, theorems: request.theorems?.map(parseTdfolFormula) },
      {
        ...options,
        maxSteps: request.maxSteps ?? options.maxSteps,
        maxDerivedFormulas: request.maxDerivedFormulas ?? options.maxDerivedFormulas,
      },
    );
    return {
      ...result,
      method: `cvc5-compatible:${result.method ?? 'tdfol'}`,
      cvc5: metadata(result, smtLib(theorem, axioms)),
    };
  } catch (error) {
    const result: ProofResult = {
      status: 'error',
      theorem: request.theorem,
      steps: [],
      method: 'cvc5-compatible:parse-error',
      error: error instanceof Error ? error.message : String(error),
    };
    return {
      ...result,
      cvc5: metadata(result, `; invalid TDFOL request\n; theorem: ${request.theorem}`),
    };
  }
}
export const create_browser_native_cvc5_prover_bridge = createBrowserNativeCvc5ProverBridge;
export const prove_cvc5_compatible_tdfol = proveCvc5CompatibleTdfol;

function metadata(result: ProofResult, smtLibText: string): Cvc5CompatibilityMetadata {
  const checkSatStatus = mapCvc5Status(result.status);
  return {
    adapter: 'browser-native-cvc5-prover-bridge',
    sourcePythonModule: 'logic/external_provers/smt/cvc5_prover_bridge.py',
    externalBinaryAllowed: false,
    serverCallsAllowed: false,
    pythonRuntime: false,
    wasmRuntime: 'not-bundled',
    command: null,
    cvc5Available: false,
    smtLib: smtLibText,
    checkSatStatus,
    isValid: checkSatStatus === 'unsat',
    isSat: checkSatStatus === 'sat',
    isUnsat: checkSatStatus === 'unsat',
    model: null,
    proof: null,
    warnings: [
      result.status === 'error'
        ? 'CVC5-compatible TDFOL parsing failed locally; no external fallback was attempted.'
        : 'CVC5 native bindings, subprocesses, and RPC are unavailable in the browser; proof search used the local TypeScript TDFOL engine and emitted SMT-LIB compatibility metadata.',
    ],
  };
}

function smtLib(theorem: TdfolFormula, axioms: TdfolFormula[]): string {
  return [
    '(set-logic ALL)',
    '(set-option :produce-models true)',
    ...axioms.map((axiom) => `(assert ${smt(axiom)})`),
    `(assert (not ${smt(theorem)}))`,
    '(check-sat)',
  ].join('\n');
}

function smt(formula: TdfolFormula): string {
  switch (formula.kind) {
    case 'predicate':
      return formula.args.length === 0
        ? sym(formula.name)
        : `(${sym(formula.name)} ${formula.args.map(term).join(' ')})`;
    case 'unary':
      return `(not ${smt(formula.formula)})`;
    case 'binary':
      return `(${op(formula.operator)} ${smt(formula.left)} ${smt(formula.right)})`;
    case 'quantified':
      return `(${formula.quantifier.toLowerCase()} ((${sym(formula.variable.name)} Object)) ${smt(formula.formula)})`;
    case 'deontic':
    case 'temporal':
      return `(${sym(formula.operator.toLowerCase())} ${smt(formula.formula)})`;
  }
}

function term(value: TdfolTerm): string {
  return value.kind === 'function'
    ? `(${sym(value.name)} ${value.args.map(term).join(' ')})`
    : sym(value.name);
}

function op(operator: TdfolBinaryOperator): string {
  if (operator === 'AND') return 'and';
  if (operator === 'OR') return 'or';
  if (operator === 'IMPLIES') return '=>';
  if (operator === 'IFF') return '=';
  return operator === 'XOR' ? 'xor' : 'until';
}

function sym(value: string): string {
  const normalized = value.replace(/[^A-Za-z0-9_.$-]/g, '_');
  return /^[A-Za-z_.$]/.test(normalized) ? normalized : `_${normalized}`;
}

function mapCvc5Status(status: ProofResult['status']): Cvc5CheckSatStatus {
  if (status === 'proved') return 'unsat';
  if (status === 'disproved') return 'sat';
  if (status === 'timeout') return 'timeout';
  return status === 'error' ? 'error' : 'unknown';
}
