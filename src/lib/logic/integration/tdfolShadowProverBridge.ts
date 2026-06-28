import type { CecShadowModalLogic, CecShadowProofStatus } from '../cec/shadowProver';
import { createCecShadowProver, type CecShadowProverOptions } from '../cec/shadowProver';
import { formatCecExpression } from '../cec/formatter';
import type { ProofResult, ProofStatus } from '../types';
import { parseTdfolFormula } from '../tdfol/parser';
import { formatTdfolFormula } from '../tdfol/formatter';
import type { TdfolFormula } from '../tdfol/ast';
import { tdfolToCecExpression } from '../tdfol/strategies';

export const TDFOL_SHADOW_PROVER_BRIDGE_METADATA = {
  sourcePythonModule: 'logic/integration/tdfol_shadowprover_bridge.py',
  legacySourcePythonModules: ['logic/integration/bridges/tdfol_shadowprover_bridge.py'],
  browserNative: true,
  runtime: 'typescript-wasm-browser',
  serverCallsAllowed: false,
  pythonRuntime: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  failClosed: true,
  backend: 'cec-shadow-prover-local-typescript',
} as const;

export type TdfolShadowProverBridgeInput = string | TdfolFormula;

export interface TdfolShadowProverBridgeConversion {
  status: 'success' | 'failed';
  source: string;
  shadowFormula: string;
  warnings: Array<string>;
  metadata: typeof TDFOL_SHADOW_PROVER_BRIDGE_METADATA;
  error?: string;
}

export interface TdfolShadowProverBridgeProofRequest {
  theorem: TdfolShadowProverBridgeInput;
  axioms?: Array<TdfolShadowProverBridgeInput>;
  theorems?: Array<TdfolShadowProverBridgeInput>;
  logic?: CecShadowModalLogic;
}

export interface TdfolShadowProverBridgeProofResult extends ProofResult {
  sourcePythonModule: typeof TDFOL_SHADOW_PROVER_BRIDGE_METADATA.sourcePythonModule;
  legacySourcePythonModules: typeof TDFOL_SHADOW_PROVER_BRIDGE_METADATA.legacySourcePythonModules;
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  shadowLogic: CecShadowModalLogic;
  cecTheorem: string;
  shadowProofStatus: CecShadowProofStatus;
  shadowProofMetadata: Record<string, unknown>;
}

type ShadowResultFields = ProofResult & {
  logic: CecShadowModalLogic;
  cecTheorem: string;
  shadowProofStatus: CecShadowProofStatus;
  shadowProofMetadata: Record<string, unknown>;
};

export class BrowserNativeTdfolShadowProverBridge {
  readonly metadata = TDFOL_SHADOW_PROVER_BRIDGE_METADATA;

  constructor(
    private readonly options: CecShadowProverOptions = {},
    private readonly defaultLogic: CecShadowModalLogic = 'K',
  ) {}

  convert(input: TdfolShadowProverBridgeInput): TdfolShadowProverBridgeConversion {
    try {
      const formula = normalizeInput(input);
      return conversion(
        'success',
        formatTdfolFormula(formula),
        formatCecExpression(tdfolToCecExpression(formula)),
      );
    } catch (error) {
      return conversion('failed', inputSource(input), '', errorMessage(error));
    }
  }

  prove(request: TdfolShadowProverBridgeProofRequest): TdfolShadowProverBridgeProofResult {
    const start = nowMs();
    const logic = request.logic ?? this.defaultLogic;
    try {
      const theorem = normalizeInput(request.theorem);
      const cecTheorem = tdfolToCecExpression(theorem);
      const assumptions = [...(request.axioms ?? []), ...(request.theorems ?? [])]
        .map(normalizeInput)
        .map(tdfolToCecExpression);
      const proof = createCecShadowProver(logic, this.options).proveTheorem(
        cecTheorem,
        assumptions,
      );
      const method = proof.metadata.method;
      return proofResult({
        status: mapShadowStatus(proof.status),
        theorem: formatTdfolFormula(theorem),
        steps: proof.steps,
        method: `tdfol_shadowprover_bridge:${typeof method === 'string' ? method : 'local'}`,
        timeMs: Math.max(0, nowMs() - start),
        error: proof.status === 'success' ? undefined : shadowProofError(proof.status),
        logic,
        cecTheorem: formatCecExpression(cecTheorem),
        shadowProofStatus: proof.status,
        shadowProofMetadata: { ...proof.metadata },
      });
    } catch (error) {
      return proofResult({
        status: 'error',
        theorem: inputSource(request.theorem),
        steps: [],
        method: 'tdfol_shadowprover_bridge:fail_closed',
        timeMs: Math.max(0, nowMs() - start),
        error: errorMessage(error),
        logic,
        cecTheorem: '',
        shadowProofStatus: 'error',
        shadowProofMetadata: { failClosed: true },
      });
    }
  }

  prove_theorem(
    theorem: TdfolShadowProverBridgeInput,
    axioms: Array<TdfolShadowProverBridgeInput> = [],
    logic: CecShadowModalLogic = this.defaultLogic,
  ): TdfolShadowProverBridgeProofResult {
    return this.prove({ theorem, axioms, logic });
  }

  validate(input: TdfolShadowProverBridgeInput): {
    valid: boolean;
    errors: Array<string>;
    warnings: Array<string>;
    metadata: typeof TDFOL_SHADOW_PROVER_BRIDGE_METADATA;
  } {
    const result = this.convert(input);
    return {
      valid: result.status === 'success',
      errors: result.error ? [result.error] : [],
      warnings: result.warnings,
      metadata: this.metadata,
    };
  }
}

export function createBrowserNativeTdfolShadowProverBridge(
  options: CecShadowProverOptions = {},
  defaultLogic: CecShadowModalLogic = 'K',
): BrowserNativeTdfolShadowProverBridge {
  return new BrowserNativeTdfolShadowProverBridge(options, defaultLogic);
}

export function convertTdfolToShadowProver(
  input: TdfolShadowProverBridgeInput,
): TdfolShadowProverBridgeConversion {
  return createBrowserNativeTdfolShadowProverBridge().convert(input);
}

export function proveTdfolWithShadowProver(
  request: TdfolShadowProverBridgeProofRequest,
  options: CecShadowProverOptions = {},
): TdfolShadowProverBridgeProofResult {
  return createBrowserNativeTdfolShadowProverBridge(options, request.logic ?? 'K').prove(request);
}

export function validateTdfolShadowProverBridgeInput(input: TdfolShadowProverBridgeInput): {
  valid: boolean;
  errors: Array<string>;
  warnings: Array<string>;
  metadata: typeof TDFOL_SHADOW_PROVER_BRIDGE_METADATA;
} {
  return createBrowserNativeTdfolShadowProverBridge().validate(input);
}

function conversion(
  status: 'success' | 'failed',
  source: string,
  shadowFormula: string,
  error?: string,
): TdfolShadowProverBridgeConversion {
  return {
    status,
    source,
    shadowFormula,
    warnings: error ? ['TDFOL ShadowProver bridge failed closed without external fallback.'] : [],
    metadata: TDFOL_SHADOW_PROVER_BRIDGE_METADATA,
    error,
  };
}

function proofResult(result: ShadowResultFields): TdfolShadowProverBridgeProofResult {
  return {
    ...result,
    sourcePythonModule: TDFOL_SHADOW_PROVER_BRIDGE_METADATA.sourcePythonModule,
    legacySourcePythonModules: TDFOL_SHADOW_PROVER_BRIDGE_METADATA.legacySourcePythonModules,
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntime: false,
    shadowLogic: result.logic,
    cecTheorem: result.cecTheorem,
    shadowProofStatus: result.shadowProofStatus,
    shadowProofMetadata: result.shadowProofMetadata,
  };
}

function normalizeInput(input: TdfolShadowProverBridgeInput): TdfolFormula {
  return typeof input === 'string' ? parseTdfolFormula(input) : input;
}

function inputSource(input: TdfolShadowProverBridgeInput): string {
  return typeof input === 'string' ? input : formatTdfolFormula(input);
}

function mapShadowStatus(status: CecShadowProofStatus): ProofStatus {
  if (status === 'success') return 'proved';
  if (status === 'failure') return 'disproved';
  if (status === 'timeout') return 'timeout';
  if (status === 'error') return 'error';
  return 'unknown';
}

function shadowProofError(status: CecShadowProofStatus): string | undefined {
  const errors: Record<CecShadowProofStatus, string | undefined> = {
    success: undefined,
    failure: 'Browser-native ShadowProver found an open tableau.',
    unknown: 'Browser-native ShadowProver could not prove the theorem.',
    timeout: 'Browser-native ShadowProver timed out.',
    error: 'Browser-native ShadowProver failed closed.',
  };
  return errors[status];
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}
