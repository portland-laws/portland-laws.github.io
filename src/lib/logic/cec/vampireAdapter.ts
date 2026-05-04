import type { ProofResult, ProofStatus } from '../types';
import type { CecExpression } from './ast';
import { parseCecExpression } from './parser';
import { proveCec, type CecProverOptions } from './prover';
import { createCecTptpProblem } from './tptpUtils';

export type CecVampireStatus =
  | 'Theorem'
  | 'CounterSatisfiable'
  | 'GaveUp'
  | 'ResourceOut'
  | 'InputError';

export interface CecVampireAdapterOptions extends CecProverOptions {
  readonly problemName?: string;
}

export interface CecVampireMetadata {
  readonly adapter: 'browser-native-cec-vampire-adapter';
  readonly sourcePythonModule: 'logic/CEC/provers/vampire_adapter.py';
  readonly runtime: 'typescript-wasm-browser';
  readonly externalBinaryAllowed: false;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly command: null;
  readonly tptpProblem: string;
  readonly tptpAxioms: string[];
  readonly tptpTheorem: string;
  readonly statusMapping: CecVampireStatus;
  readonly warnings: string[];
}

export interface CecVampireProofResult extends ProofResult {
  readonly vampire: CecVampireMetadata;
}

export const CEC_VAMPIRE_ADAPTER_RUNTIME = {
  module: 'logic/CEC/provers/vampire_adapter.py',
  runtime: 'browser-native-typescript',
  pythonRuntime: false,
  serverDelegation: false,
  subprocessDelegation: false,
} as const;

export class CecVampireAdapter {
  private readonly options: CecVampireAdapterOptions;

  constructor(options: CecVampireAdapterOptions = {}) {
    this.options = { ...options };
  }

  prove(
    theorem: string | CecExpression,
    axioms: readonly (string | CecExpression)[] = [],
  ): CecVampireProofResult {
    const parsedTheorem = normalizeCecExpression(theorem);
    const parsedAxioms = axioms.map(normalizeCecExpression);
    const result = proveCec(
      parsedTheorem,
      { axioms: parsedAxioms },
      {
        ...this.options,
        maxSteps: this.options.maxSteps,
        maxDerivedExpressions: this.options.maxDerivedExpressions,
      },
    );
    const tptpProblem = createCecTptpProblem(parsedTheorem, parsedAxioms, {
      problemName: this.options.problemName ?? 'cec_vampire_problem',
      axiomNamePrefix: 'vampire_ax',
      conjectureName: 'vampire_goal',
    });
    const lines = tptpProblem.split('\n');
    return {
      ...result,
      method: `vampire-compatible:${result.method ?? 'cec-forward-chaining'}`,
      vampire: {
        adapter: 'browser-native-cec-vampire-adapter',
        sourcePythonModule: 'logic/CEC/provers/vampire_adapter.py',
        runtime: 'typescript-wasm-browser',
        externalBinaryAllowed: false,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        command: null,
        tptpProblem,
        tptpAxioms: lines.filter((line) => /,\s*axiom\s*,/.test(line)),
        tptpTheorem: lines.find((line) => /,\s*conjecture\s*,/.test(line)) ?? '',
        statusMapping: mapCecVampireStatus(result.status),
        warnings: [
          'External Vampire process execution is unavailable in the browser; proof search used the local TypeScript CEC engine.',
        ],
      },
    };
  }
}

export function proveCecWithVampireAdapter(
  theorem: string | CecExpression,
  axioms: readonly (string | CecExpression)[] = [],
  options: CecVampireAdapterOptions = {},
): CecVampireProofResult {
  return new CecVampireAdapter(options).prove(theorem, axioms);
}

export function mapCecVampireStatus(status: ProofStatus): CecVampireStatus {
  if (status === 'proved') return 'Theorem';
  if (status === 'disproved') return 'CounterSatisfiable';
  if (status === 'timeout') return 'ResourceOut';
  if (status === 'error') return 'InputError';
  return 'GaveUp';
}

function normalizeCecExpression(expression: string | CecExpression): CecExpression {
  return typeof expression === 'string' ? parseCecExpression(expression) : expression;
}
