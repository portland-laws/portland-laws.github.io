import { parseCecExpression } from '../cec/parser';
import { proveCec, type CecProverOptions } from '../cec/prover';
import { LogicBridgeError } from '../errors';
import { convertTdfolFormula } from '../tdfol/converter';
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
  proverFamily?: 'local' | 'e-prover';
}

export interface BrowserNativeProofAdapter {
  metadata: BrowserNativeProofAdapterMetadata;
  supports(logic: BrowserNativeProofLogic): boolean;
  prove(request: BrowserNativeProofRequest): ProofResult;
}

export interface BrowserNativeProofAdapterOptions {
  tdfol?: TdfolProverOptions;
  cec?: CecProverOptions;
  includeEProverCompatibilityAdapter?: boolean;
}

export interface EProverCompatibilityMetadata {
  adapter: 'browser-native-e-prover-adapter';
  externalBinaryAllowed: false;
  serverCallsAllowed: false;
  command: null;
  tptpProblem: string;
  tptpAxioms: string[];
  tptpTheorem: string;
  statusMapping: 'Theorem' | 'GaveUp' | 'ResourceOut' | 'InputError';
  warnings: string[];
}

export interface EProverCompatibilityResult extends ProofResult {
  eProver: EProverCompatibilityMetadata;
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
  const adapters = [
    createTdfolProofAdapter(options.tdfol),
    createCecProofAdapter('cec', options.cec),
    createCecProofAdapter('dcec', options.cec),
  ];
  if (options.includeEProverCompatibilityAdapter === true) {
    adapters.push(createBrowserNativeEProverAdapter(options.tdfol));
  }
  return adapters;
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
      proverFamily: 'local',
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

export function createBrowserNativeEProverAdapter(
  options: TdfolProverOptions = {},
): BrowserNativeProofAdapter {
  return {
    metadata: {
      logic: 'tdfol',
      name: 'browser-native-e-prover-adapter',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'e-prover',
    },
    supports: (logic) => logic === 'tdfol',
    prove(request) {
      if (request.logic !== 'tdfol') {
        throw new LogicBridgeError('Browser-native E prover adapter only accepts TDFOL requests.');
      }

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
      const tptpAxioms = axioms.map((axiom) => String(convertTdfolFormula(axiom, 'tptp').output));
      const tptpTheorem = String(convertTdfolFormula(theorem, 'tptp').output).replace(
        'fof(tdfol_formula, axiom,',
        'fof(tdfol_conjecture, conjecture,',
      );
      const compatibilityResult: EProverCompatibilityResult = {
        ...result,
        method: `e-prover-compatible:${result.method ?? 'tdfol'}`,
        eProver: {
          adapter: 'browser-native-e-prover-adapter',
          externalBinaryAllowed: false,
          serverCallsAllowed: false,
          command: null,
          tptpProblem: [...tptpAxioms, tptpTheorem].join('\n'),
          tptpAxioms,
          tptpTheorem,
          statusMapping: mapEProverStatus(result.status),
          warnings: [
            'External E prover process execution is unavailable in the browser; proof search used the local TypeScript TDFOL engine.',
          ],
        },
      };
      return compatibilityResult;
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
      proverFamily: 'local',
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

function mapEProverStatus(
  status: ProofResult['status'],
): EProverCompatibilityMetadata['statusMapping'] {
  if (status === 'proved') return 'Theorem';
  if (status === 'timeout') return 'ResourceOut';
  if (status === 'error') return 'InputError';
  return 'GaveUp';
}
