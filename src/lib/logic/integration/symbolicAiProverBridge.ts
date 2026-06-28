import { parseTdfolFormula } from '../tdfol/parser';
import { proveTdfol, type TdfolProverOptions } from '../tdfol/prover';
import type { ProofResult } from '../types';
import type { BrowserNativeProofAdapter, BrowserNativeProofRequest } from './proverAdapters';

export interface SymbolicAiCompatibilityMetadata {
  adapter: 'browser-native-symbolicai-prover-bridge';
  sourcePythonModule: 'logic/external_provers/neural/symbolicai_prover_bridge.py';
  externalPackageAllowed: false;
  serverCallsAllowed: false;
  pythonRuntime: false;
  neuralRuntime: 'deterministic-local-tdfol';
  confidence: number;
  premiseOverlap: number;
  symbolicProgram: string;
  statusMapping: 'success' | 'failed' | 'timeout' | 'error';
  warnings: string[];
}

export interface BrowserNativeSymbolicAiProofResult extends ProofResult {
  symbolicAi: SymbolicAiCompatibilityMetadata;
}

export function createBrowserNativeSymbolicAiProverBridge(
  options: TdfolProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'browser-native-symbolicai-prover-bridge',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'local',
    },
    supports: (logic) => logic === 'tdfol',
    prove(request) {
      return proveSymbolicAiCompatibleTdfol(request, options);
    },
  };
}

export function proveSymbolicAiCompatibleTdfol(
  request: BrowserNativeProofRequest,
  options: TdfolProverOptions = {},
): BrowserNativeSymbolicAiProofResult {
  const startedAt = performance.now();
  try {
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
    const compatibilityResult: BrowserNativeSymbolicAiProofResult = {
      ...result,
      method: `symbolicai-compatible:${result.method ?? 'tdfol'}`,
      symbolicAi: buildSymbolicAiMetadata(request, result),
    };
    return compatibilityResult;
  } catch (error) {
    const errorResult: ProofResult = {
      status: 'error',
      theorem: request.theorem,
      steps: [],
      method: 'symbolicai-compatible:parse-error',
      timeMs: performance.now() - startedAt,
      error: error instanceof Error ? error.message : String(error),
    };
    return {
      ...errorResult,
      symbolicAi: buildSymbolicAiMetadata(request, errorResult),
    };
  }
}

export const create_browser_native_symbolicai_prover_bridge =
  createBrowserNativeSymbolicAiProverBridge;
export const prove_symbolicai_compatible_tdfol = proveSymbolicAiCompatibleTdfol;

function buildSymbolicAiMetadata(
  request: BrowserNativeProofRequest,
  result: ProofResult,
): SymbolicAiCompatibilityMetadata {
  const premiseOverlap = calculatePremiseOverlap(request.theorem, request.axioms);
  return {
    adapter: 'browser-native-symbolicai-prover-bridge',
    sourcePythonModule: 'logic/external_provers/neural/symbolicai_prover_bridge.py',
    externalPackageAllowed: false,
    serverCallsAllowed: false,
    pythonRuntime: false,
    neuralRuntime: 'deterministic-local-tdfol',
    confidence: result.status === 'proved' ? Math.max(0.75, premiseOverlap) : premiseOverlap,
    premiseOverlap,
    symbolicProgram: renderSymbolicProgram(request),
    statusMapping: mapSymbolicAiStatus(result.status),
    warnings: [
      'SymbolicAI package execution and neural service calls are unavailable in the browser; proof search used the local TypeScript TDFOL engine with deterministic compatibility metadata.',
    ],
  };
}

function calculatePremiseOverlap(theorem: string, axioms: string[]): number {
  const theoremTokens = tokenizeLogicText(theorem);
  if (theoremTokens.length === 0) return 0;
  const axiomTokens = new Set(axioms.flatMap(tokenizeLogicText));
  const matches = theoremTokens.filter((token) => axiomTokens.has(token)).length;
  return Number((matches / theoremTokens.length).toFixed(3));
}

function tokenizeLogicText(value: string): string[] {
  return Array.from(new Set(value.toLowerCase().match(/[a-z][a-z0-9_]*/g) ?? []));
}

function renderSymbolicProgram(request: BrowserNativeProofRequest): string {
  const axioms = request.axioms.map((axiom, index) => `premise_${index + 1}: ${axiom}`);
  return [...axioms, `target: ${request.theorem}`].join('\n');
}

function mapSymbolicAiStatus(
  status: ProofResult['status'],
): SymbolicAiCompatibilityMetadata['statusMapping'] {
  if (status === 'proved') return 'success';
  if (status === 'timeout') return 'timeout';
  if (status === 'error') return 'error';
  return 'failed';
}
