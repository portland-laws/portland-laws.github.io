import type { TdfolProverOptions } from '../tdfol/prover';
import type { ProofResult } from '../types';
import { proveCvc5CompatibleTdfol, type BrowserNativeCvc5ProofResult } from './cvc5ProverBridge';
import type { BrowserNativeProofAdapter, BrowserNativeProofRequest } from './proverAdapters';

export type Z3CheckSatStatus = 'unsat' | 'sat' | 'unknown' | 'timeout' | 'error';

export interface Z3CompatibilityMetadata {
  adapter: 'browser-native-z3-prover-bridge';
  sourcePythonModule: 'logic/external_provers/smt/z3_prover_bridge.py';
  externalBinaryAllowed: false;
  serverCallsAllowed: false;
  pythonRuntime: false;
  wasmRuntime: 'not-bundled';
  command: null;
  z3Available: false;
  smtLib: string;
  checkSatStatus: Z3CheckSatStatus;
  isValid: boolean;
  isSat: boolean;
  isUnsat: boolean;
  model: null;
  proof: null;
  warnings: string[];
}

export interface BrowserNativeZ3ProofResult extends ProofResult {
  z3: Z3CompatibilityMetadata;
}

export function createBrowserNativeZ3ProverBridge(
  options: TdfolProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'browser-native-z3-prover-bridge',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'local',
    },
    supports: (logic) => logic === 'tdfol',
    prove: (request) => proveZ3CompatibleTdfol(request, options),
  };
}

export function proveZ3CompatibleTdfol(
  request: BrowserNativeProofRequest,
  options: TdfolProverOptions = {},
): BrowserNativeZ3ProofResult {
  const result = proveCvc5CompatibleTdfol(request, options);
  const { cvc5: cvc5Metadata, ...proof } = result;
  return {
    ...proof,
    method: String(result.method ?? 'tdfol').replace(/^cvc5-compatible:/, 'z3-compatible:'),
    z3: {
      adapter: 'browser-native-z3-prover-bridge',
      sourcePythonModule: 'logic/external_provers/smt/z3_prover_bridge.py',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntime: false,
      wasmRuntime: 'not-bundled',
      command: null,
      z3Available: false,
      smtLib: cvc5Metadata.smtLib,
      checkSatStatus: cvc5Metadata.checkSatStatus,
      isValid: cvc5Metadata.isValid,
      isSat: cvc5Metadata.isSat,
      isUnsat: cvc5Metadata.isUnsat,
      model: null,
      proof: null,
      warnings: [warningFor(result)],
    },
  };
}

export const create_browser_native_z3_prover_bridge = createBrowserNativeZ3ProverBridge;
export const prove_z3_compatible_tdfol = proveZ3CompatibleTdfol;

function warningFor(result: BrowserNativeCvc5ProofResult): string {
  return result.status === 'error'
    ? 'Z3-compatible TDFOL parsing failed locally; no external fallback was attempted.'
    : 'Z3 Python bindings, subprocesses, RPC, and server calls are unavailable in the browser; proof search used the local TypeScript TDFOL engine and emitted SMT-LIB compatibility metadata.';
}
