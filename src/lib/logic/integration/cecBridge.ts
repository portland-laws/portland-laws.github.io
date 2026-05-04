import type { CecExpression } from '../cec/ast';
import { formatCecExpression } from '../cec/formatter';
import { parseCecExpression, validateCecExpression } from '../cec/parser';
import {
  proveCec,
  type CecKnowledgeBase,
  type CecProofResult,
  type CecProverOptions,
} from '../cec/prover';

export const CEC_BRIDGE_METADATA = {
  sourcePythonModule: 'logic/integration/cec_bridge.py',
  browserNative: true,
  runtime: 'typescript-wasm-browser',
  serverCallsAllowed: false,
  pythonRuntime: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  failClosed: true,
} as const;

export type CecBridgeInput = string | CecExpression;
export type CecBridgeTarget = 'cec' | 'json';

export type CecBridgeConversion = {
  status: 'success' | 'failed';
  source: string;
  target: CecBridgeTarget;
  expression: CecExpression | null;
  output: string;
  warnings: string[];
  metadata: typeof CEC_BRIDGE_METADATA;
  error?: string;
};

export interface CecBridgeProofRequest {
  theorem: CecBridgeInput;
  axioms: Array<CecBridgeInput>;
  theorems?: Array<CecBridgeInput>;
  maxSteps?: number;
  maxDerivedExpressions?: number;
}

export interface CecBridgeProofResult extends CecProofResult {
  sourcePythonModule: typeof CEC_BRIDGE_METADATA.sourcePythonModule;
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
}

export class BrowserNativeCecBridge {
  readonly metadata = CEC_BRIDGE_METADATA;

  constructor(private readonly options: CecProverOptions = {}) {}

  convert(input: CecBridgeInput, target: CecBridgeTarget = 'cec'): CecBridgeConversion {
    try {
      const expression = parseInput(input);
      const source = formatCecExpression(expression);
      return {
        status: 'success',
        source,
        target,
        expression,
        output: target === 'json' ? JSON.stringify(expression) : source,
        warnings: [],
        metadata: this.metadata,
      };
    } catch (error) {
      return {
        status: 'failed',
        source: cecBridgeInputSource(input),
        target,
        expression: null,
        output: '',
        warnings: [
          'CEC bridge failed closed without Python, server, RPC, subprocess, or filesystem fallback.',
        ],
        metadata: this.metadata,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  validate(input: CecBridgeInput): CecBridgeValidationResult {
    if (typeof input !== 'string') {
      return {
        valid: true,
        formula: formatCecExpression(input),
        errors: [],
        metadata: this.metadata,
      };
    }
    const result = validateCecExpression(input);
    return result.ok
      ? {
          valid: true,
          formula: formatCecExpression(result.expression),
          errors: [],
          metadata: this.metadata,
        }
      : { valid: false, formula: input, errors: [result.error], metadata: this.metadata };
  }

  prove(request: CecBridgeProofRequest): CecBridgeProofResult {
    try {
      const theorem = parseInput(request.theorem);
      const kb: CecKnowledgeBase = {
        axioms: request.axioms.map(parseInput),
        theorems: request.theorems?.map(parseInput),
      };
      const result = proveCec(theorem, kb, {
        ...this.options,
        maxSteps: request.maxSteps ?? this.options.maxSteps,
        maxDerivedExpressions: request.maxDerivedExpressions ?? this.options.maxDerivedExpressions,
      });
      return decorateCecBridgeProofResult(result, this.metadata.sourcePythonModule);
    } catch (error) {
      return decorateCecBridgeProofResult(
        {
          status: 'error',
          theorem: cecBridgeInputSource(request.theorem),
          steps: [],
          method: 'cec-forward-chaining',
          error: error instanceof Error ? error.message : String(error),
          ruleGroups: [],
          trace: [],
        },
        this.metadata.sourcePythonModule,
        'fail_closed',
      );
    }
  }
}

export function createBrowserNativeCecBridge(
  options: CecProverOptions = {},
): BrowserNativeCecBridge {
  return new BrowserNativeCecBridge(options);
}

export type CecBridgeValidationResult = {
  valid: boolean;
  formula: string;
  errors: string[];
  metadata: typeof CEC_BRIDGE_METADATA;
};

function parseInput(input: CecBridgeInput): CecExpression {
  return typeof input === 'string' ? parseCecExpression(input) : input;
}

function cecBridgeInputSource(input: CecBridgeInput): string {
  return typeof input === 'string' ? input : formatCecExpression(input);
}

function decorateCecBridgeProofResult(
  result: CecProofResult,
  sourcePythonModule: typeof CEC_BRIDGE_METADATA.sourcePythonModule,
  suffix?: string,
): CecBridgeProofResult {
  return {
    ...result,
    method: `cec_bridge:${suffix ?? result.method ?? 'local'}`,
    sourcePythonModule,
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntime: false,
  };
}
