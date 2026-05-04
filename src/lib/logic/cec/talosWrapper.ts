import type { ProofResult, ProofStatus } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import { parseCecExpression } from './parser';
import { proveCec, type CecProverOptions } from './prover';

export type TalosWrapperStatus = 'valid' | 'invalid' | 'unknown' | 'timeout' | 'error';

export interface TalosWrapperCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmRequired: false;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/talos_wrapper.py';
}

export interface TalosWrapperOptions extends CecProverOptions {
  readonly problemName?: string;
}

export interface TalosWrapperMetadata {
  readonly adapter: 'browser-native-cec-talos-wrapper';
  readonly sourcePythonModule: 'logic/CEC/talos_wrapper.py';
  readonly runtime: 'typescript-wasm-browser';
  readonly externalBinaryAllowed: false;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly command: null;
  readonly problemName: string;
  readonly normalizedTheorem: string;
  readonly normalizedAxioms: string[];
  readonly statusMapping: TalosWrapperStatus;
  readonly warnings: string[];
}

export interface TalosWrapperProofResult extends ProofResult {
  readonly talos: TalosWrapperMetadata;
}

const CAPABILITIES: TalosWrapperCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmRequired: false,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/talos_wrapper.py',
};

export class TalosWrapper {
  private readonly options: TalosWrapperOptions;

  constructor(options: TalosWrapperOptions = {}) {
    this.options = { ...options };
  }

  getCapabilities(): TalosWrapperCapabilities {
    return CAPABILITIES;
  }

  prove(
    theorem: string | CecExpression,
    axioms: readonly (string | CecExpression)[] = [],
  ): TalosWrapperProofResult {
    const parsedTheorem = normalizeCecExpression(theorem);
    const parsedAxioms = axioms.map(normalizeCecExpression);
    const result = proveCec(parsedTheorem, { axioms: parsedAxioms }, this.options);
    return {
      ...result,
      method: `talos-compatible:${result.method ?? 'cec-forward-chaining'}`,
      talos: {
        adapter: 'browser-native-cec-talos-wrapper',
        sourcePythonModule: 'logic/CEC/talos_wrapper.py',
        runtime: 'typescript-wasm-browser',
        externalBinaryAllowed: false,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        command: null,
        problemName: this.options.problemName ?? 'cec_talos_problem',
        normalizedTheorem: formatCecExpression(parsedTheorem),
        normalizedAxioms: parsedAxioms.map(formatCecExpression),
        statusMapping: mapTalosWrapperStatus(result.status),
        warnings: [
          'External Talos/Python execution is unavailable in the browser; proof search used the local TypeScript CEC engine.',
        ],
      },
    };
  }
}

export function createTalosWrapper(options?: TalosWrapperOptions): TalosWrapper {
  return new TalosWrapper(options);
}

export function proveCecWithTalosWrapper(
  theorem: string | CecExpression,
  axioms: readonly (string | CecExpression)[] = [],
  options: TalosWrapperOptions = {},
): TalosWrapperProofResult {
  return createTalosWrapper(options).prove(theorem, axioms);
}

export function mapTalosWrapperStatus(status: ProofStatus): TalosWrapperStatus {
  if (status === 'proved') return 'valid';
  if (status === 'disproved') return 'invalid';
  if (status === 'timeout') return 'timeout';
  if (status === 'error') return 'error';
  return 'unknown';
}

function normalizeCecExpression(expression: string | CecExpression): CecExpression {
  return typeof expression === 'string' ? parseCecExpression(expression) : expression;
}
