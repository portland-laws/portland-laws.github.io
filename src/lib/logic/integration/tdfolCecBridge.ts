import { formatCecExpression } from '../cec/formatter';
import type { CecExpression } from '../cec/ast';
import type { ProofResult } from '../types';
import { parseTdfolFormula } from '../tdfol/parser';
import { formatTdfolFormula } from '../tdfol/formatter';
import type { TdfolFormula } from '../tdfol/ast';
import type { TdfolKnowledgeBase } from '../tdfol/prover';
import {
  TdfolLocalCecDelegate,
  tdfolToCecExpression,
  type TdfolLocalCecDelegateOptions,
} from '../tdfol/strategies';

export const TDFOL_CEC_BRIDGE_METADATA = {
  sourcePythonModule: 'logic/integration/bridges/tdfol_cec_bridge.py',
  browserNative: true,
  runtime: 'typescript-wasm-browser',
  serverCallsAllowed: false,
  pythonRuntime: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  failClosed: true,
} as const;

export type TdfolCecBridgeInput = string | TdfolFormula;

export interface TdfolCecBridgeConversion {
  status: 'success' | 'failed';
  source: string;
  cec: CecExpression | null;
  cecText: string;
  warnings: string[];
  metadata: typeof TDFOL_CEC_BRIDGE_METADATA;
  error?: string;
}

export interface TdfolCecBridgeProofRequest {
  theorem: TdfolCecBridgeInput;
  axioms: Array<TdfolCecBridgeInput>;
  theorems?: Array<TdfolCecBridgeInput>;
  timeoutMs?: number;
}

export interface TdfolCecBridgeProofResult extends ProofResult {
  sourcePythonModule: typeof TDFOL_CEC_BRIDGE_METADATA.sourcePythonModule;
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  cecTheorem: string;
}

function bridgeInputSource(input: TdfolCecBridgeInput): string {
  return typeof input === 'string' ? input : formatTdfolFormula(input);
}

export class BrowserNativeTdfolCecBridge {
  readonly metadata = TDFOL_CEC_BRIDGE_METADATA;
  private readonly delegate: TdfolLocalCecDelegate;

  constructor(options: TdfolLocalCecDelegateOptions = {}) {
    this.delegate = new TdfolLocalCecDelegate(options);
  }

  convert(input: TdfolCecBridgeInput): TdfolCecBridgeConversion {
    try {
      const formula = normalizeTdfolBridgeInput(input);
      const cec = tdfolToCecExpression(formula);
      return {
        status: 'success',
        source: formatTdfolFormula(formula),
        cec,
        cecText: formatCecExpression(cec),
        warnings: [],
        metadata: this.metadata,
      };
    } catch (error) {
      return {
        status: 'failed',
        source: bridgeInputSource(input),
        cec: null,
        cecText: '',
        warnings: ['TDFOL to CEC bridge failed closed without external fallback.'],
        metadata: this.metadata,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  prove(request: TdfolCecBridgeProofRequest): TdfolCecBridgeProofResult {
    const theorem = normalizeTdfolBridgeInput(request.theorem);
    const kb: TdfolKnowledgeBase = {
      axioms: request.axioms.map(normalizeTdfolBridgeInput),
      theorems: request.theorems?.map(normalizeTdfolBridgeInput),
    };
    const cecTheorem = formatCecExpression(tdfolToCecExpression(theorem));
    const result = this.delegate.prove(theorem, kb, request.timeoutMs);
    return {
      ...result,
      method: `tdfol_cec_bridge:${result.method ?? 'local'}`,
      sourcePythonModule: this.metadata.sourcePythonModule,
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      cecTheorem,
    };
  }

  validate(input: TdfolCecBridgeInput) {
    const conversion = this.convert(input);
    return {
      valid: conversion.status === 'success',
      errors: conversion.error ? [conversion.error] : [],
      metadata: this.metadata,
    };
  }
}

export function createBrowserNativeTdfolCecBridge(
  options: TdfolLocalCecDelegateOptions = {},
): BrowserNativeTdfolCecBridge {
  return new BrowserNativeTdfolCecBridge(options);
}

function normalizeTdfolBridgeInput(input: TdfolCecBridgeInput): TdfolFormula {
  return typeof input === 'string' ? parseTdfolFormula(input) : input;
}
