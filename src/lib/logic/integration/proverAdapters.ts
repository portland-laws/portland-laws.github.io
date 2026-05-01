import { parseCecExpression } from '../cec/parser';
import { proveCec, type CecProverOptions } from '../cec/prover';
import { LogicBridgeError } from '../errors';
import { parseTdfolFormula } from '../tdfol/parser';
import { proveTdfol, type TdfolProverOptions } from '../tdfol/prover';
import type { ProofResult } from '../types';

export type BrowserNativeProofLogic = 'tdfol' | 'cec' | 'dcec';

export interface BrowserNativeProofRequest {
  logic: BrowserNativeProofLogic;
  theorem: string;
  axioms: string[];
  theorems?: string[];
  maxSteps?: number;
  maxDerivedFormulas?: number;
}

export interface BrowserNativeProofAdapterMetadata {
  logic: BrowserNativeProofLogic;
  name: string;
  runtime: 'typescript-wasm-browser';
  requiresExternalProver: false;
}

export interface BrowserNativeProofAdapter {
  metadata: BrowserNativeProofAdapterMetadata;
  supports(logic: BrowserNativeProofLogic): boolean;
  prove(request: BrowserNativeProofRequest): ProofResult;
}

export interface BrowserNativeProofAdapterOptions {
  tdfol?: TdfolProverOptions;
  cec?: CecProverOptions;
}

export class BrowserNativeProverRouter {
  private readonly adapters: BrowserNativeProofAdapter[];

  constructor(adapters: BrowserNativeProofAdapter[] = createDefaultProverAdapters()) {
    this.adapters = [...adapters];
  }

  listAdapters(): BrowserNativeProofAdapterMetadata[] {
    return this.adapters.map((adapter) => ({ ...adapter.metadata }));
  }

  supports(logic: BrowserNativeProofLogic): boolean {
    return this.adapters.some((adapter) => adapter.supports(logic));
  }

  prove(request: BrowserNativeProofRequest): ProofResult {
    const adapter = this.adapters.find((candidate) => candidate.supports(request.logic));
    if (!adapter) {
      throw new LogicBridgeError(`Unsupported browser-native proof logic: ${request.logic}`);
    }

    const startedAt = performance.now();
    const result = adapter.prove(request);
    return {
      ...result,
      timeMs: performance.now() - startedAt,
      method: `adapter:${adapter.metadata.name}:${result.method ?? request.logic}`,
    };
  }
}

export function createDefaultProverAdapters(
  options: BrowserNativeProofAdapterOptions = {},
): BrowserNativeProofAdapter[] {
  return [
    createTdfolProofAdapter(options.tdfol),
    createCecProofAdapter('cec', options.cec),
    createCecProofAdapter('dcec', options.cec),
  ];
}

export function createBrowserNativeProverRouter(
  options: BrowserNativeProofAdapterOptions = {},
): BrowserNativeProverRouter {
  return new BrowserNativeProverRouter(createDefaultProverAdapters(options));
}

function createTdfolProofAdapter(options: TdfolProverOptions = {}): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'local-tdfol-forward-prover',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
    },
    supports: (logic) => logic === 'tdfol',
    prove(request) {
      const theorem = parseTdfolFormula(request.theorem);
      return proveTdfol(
        theorem,
        {
          axioms: request.axioms.map(parseTdfolFormula),
          theorems: request.theorems?.map(parseTdfolFormula),
        },
        {
          ...options,
          maxSteps: request.maxSteps ?? options.maxSteps,
          maxDerivedFormulas: request.maxDerivedFormulas ?? options.maxDerivedFormulas,
        },
      );
    },
  };
}

function createCecProofAdapter(
  logic: 'cec' | 'dcec',
  options: CecProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic,
      name: logic === 'cec' ? 'local-cec-forward-prover' : 'local-dcec-forward-prover',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
    },
    supports: (candidate) => candidate === logic,
    prove(request) {
      const theorem = parseCecExpression(request.theorem);
      return proveCec(
        theorem,
        {
          axioms: request.axioms.map(parseCecExpression),
          theorems: request.theorems?.map(parseCecExpression),
        },
        {
          ...options,
          maxSteps: request.maxSteps ?? options.maxSteps,
          maxDerivedExpressions: request.maxDerivedFormulas ?? options.maxDerivedExpressions,
        },
      );
    },
  };
}
