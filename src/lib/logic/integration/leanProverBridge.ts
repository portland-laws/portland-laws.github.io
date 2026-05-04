import type { TdfolBinaryOperator, TdfolFormula, TdfolTerm } from '../tdfol/ast';
import { parseTdfolFormula } from '../tdfol/parser';
import { proveTdfol, type TdfolProverOptions } from '../tdfol/prover';
import type { ProofResult } from '../types';
import type { BrowserNativeProofAdapter, BrowserNativeProofRequest } from './proverAdapters';

export interface LeanCompatibilityMetadata {
  adapter: 'browser-native-lean-prover-bridge';
  sourcePythonModule: 'logic/external_provers/interactive/lean_prover_bridge.py';
  externalBinaryAllowed: false;
  serverCallsAllowed: false;
  pythonRuntime: false;
  command: null;
  leanVersion: null;
  imports: string[];
  theoremDeclaration: string;
  statusMapping: 'proved' | 'unknown' | 'timeout' | 'error';
  warnings: string[];
}

export interface BrowserNativeLeanProofResult extends ProofResult {
  lean: LeanCompatibilityMetadata;
}

export function createBrowserNativeLeanProverBridge(
  options: TdfolProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'browser-native-lean-prover-bridge',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'local',
    },
    supports: (logic) => logic === 'tdfol',
    prove(request) {
      return proveLeanCompatibleTdfol(request, options);
    },
  };
}

export function proveLeanCompatibleTdfol(
  request: BrowserNativeProofRequest,
  options: TdfolProverOptions = {},
): BrowserNativeLeanProofResult {
  const theorem = parseTdfolFormula(request.theorem);
  const axioms = request.axioms.map(parseTdfolFormula);
  const theorems = request.theorems?.map(parseTdfolFormula);
  const result = proveTdfol(
    theorem,
    { axioms, theorems },
    {
      ...options,
      maxSteps: request.maxSteps ?? options.maxSteps,
      maxDerivedFormulas: request.maxDerivedFormulas ?? options.maxDerivedFormulas,
    },
  );
  const leanAxioms = axioms.map((axiom, index) => `axiom h${index + 1} : ${tdfolToLean(axiom)}`);
  const leanTheorem = `theorem target : ${tdfolToLean(theorem)} := by\n  exact ${
    result.status === 'proved' ? 'h1' : 'by_contra (fun h => False.elim (by contradiction))'
  }`;

  return {
    ...result,
    method: `lean-compatible:${result.method ?? 'tdfol'}`,
    lean: {
      adapter: 'browser-native-lean-prover-bridge',
      sourcePythonModule: 'logic/external_provers/interactive/lean_prover_bridge.py',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntime: false,
      command: null,
      leanVersion: null,
      imports: [],
      theoremDeclaration: [...leanAxioms, leanTheorem].join('\n'),
      statusMapping: mapLeanStatus(result.status),
      warnings: [
        'Lean process execution and RPC are unavailable in the browser; proof search used the local TypeScript TDFOL engine.',
      ],
    },
  };
}

export const create_browser_native_lean_prover_bridge = createBrowserNativeLeanProverBridge;
export const prove_lean_compatible_tdfol = proveLeanCompatibleTdfol;

function tdfolToLean(formula: TdfolFormula): string {
  switch (formula.kind) {
    case 'predicate':
      return formula.args.length === 0
        ? leanSymbol(formula.name)
        : `(${leanSymbol(formula.name)} ${formula.args.map(tdfolTermToLean).join(' ')})`;
    case 'unary':
      return `(Not ${tdfolToLean(formula.formula)})`;
    case 'binary':
      return `(${tdfolToLean(formula.left)} ${leanBinarySymbol(formula.operator)} ${tdfolToLean(
        formula.right,
      )})`;
    case 'quantified':
      return `forall (${leanSymbol(formula.variable.name)} : Prop), ${tdfolToLean(formula.formula)}`;
    case 'deontic':
      return `(${leanSymbol(formula.operator.toLowerCase())} ${tdfolToLean(formula.formula)})`;
    case 'temporal':
      return `(${leanSymbol(formula.operator.toLowerCase())} ${tdfolToLean(formula.formula)})`;
  }
}

function tdfolTermToLean(term: TdfolTerm): string {
  switch (term.kind) {
    case 'variable':
    case 'constant':
      return leanSymbol(term.name);
    case 'function':
      return `(${leanSymbol(term.name)} ${term.args.map(tdfolTermToLean).join(' ')})`;
  }
}

function leanBinarySymbol(operator: TdfolBinaryOperator): string {
  if (operator === 'AND') return '/\\';
  if (operator === 'OR') return '\\/';
  if (operator === 'IMPLIES') return '->';
  if (operator === 'IFF') return '<->';
  if (operator === 'XOR') return 'xor';
  return 'until';
}

function leanSymbol(value: string): string {
  const normalized = value.replace(/[^A-Za-z0-9_]/g, '_');
  return /^[A-Za-z_]/.test(normalized) ? normalized : `_${normalized}`;
}

function mapLeanStatus(status: ProofResult['status']): LeanCompatibilityMetadata['statusMapping'] {
  if (status === 'proved') return 'proved';
  if (status === 'timeout') return 'timeout';
  if (status === 'error') return 'error';
  return 'unknown';
}
