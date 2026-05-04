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
  preferredProverFamily?: BrowserNativeProofAdapterMetadata['proverFamily'];
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

export interface BrowserNativeProverRouterMetadata {
  sourcePythonModule: 'logic/external_provers/prover_router.py';
  runtime: 'typescript-wasm-browser';
  serverCallsAllowed: false;
  pythonRuntime: false;
  subprocessAllowed: false;
  rpcAllowed: false;
  routingStrategy: 'first-supported-local-adapter';
  failClosed: true;
  adapterCount: number;
}

export interface BrowserNativeProverRoutePlan {
  sourcePythonModule: 'logic/external_provers/prover_router.py';
  logic: BrowserNativeProofLogic;
  selectedAdapter: BrowserNativeProofAdapterMetadata | null;
  candidates: BrowserNativeProofAdapterMetadata[];
  blockers: string[];
  serverCallsAllowed: false;
  pythonRuntime: false;
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

  getMetadata(): BrowserNativeProverRouterMetadata {
    return {
      sourcePythonModule: 'logic/external_provers/prover_router.py',
      runtime: 'typescript-wasm-browser',
      serverCallsAllowed: false,
      pythonRuntime: false,
      subprocessAllowed: false,
      rpcAllowed: false,
      routingStrategy: 'first-supported-local-adapter',
      failClosed: true,
      adapterCount: this.adapters.length,
    };
  }

  listAdapters(): BrowserNativeProofAdapterMetadata[] {
    return this.adapters.map((adapter) => ({ ...adapter.metadata }));
  }

  supports(logic: BrowserNativeProofLogic): boolean {
    return this.adapters.some((adapter) => adapter.supports(logic));
  }

  planRoute(
    request: Pick<BrowserNativeProofRequest, 'logic' | 'preferredProverFamily'>,
  ): BrowserNativeProverRoutePlan {
    const candidates = this.adapters
      .filter((candidate) => candidate.supports(request.logic))
      .map((candidate) => ({ ...candidate.metadata }));
    const selectedAdapter = this.selectAdapter(request)?.metadata;
    const blockers =
      candidates.length === 0
        ? [`unsupported_logic:${request.logic}`]
        : selectedAdapter
          ? []
          : [`unsupported_preferred_prover_family:${request.preferredProverFamily ?? 'unknown'}`];

    return {
      sourcePythonModule: 'logic/external_provers/prover_router.py',
      logic: request.logic,
      selectedAdapter: selectedAdapter ? { ...selectedAdapter } : null,
      candidates,
      blockers,
      serverCallsAllowed: false,
      pythonRuntime: false,
    };
  }

  prove(request: BrowserNativeProofRequest): ProofResult {
    const adapter = this.selectAdapter(request);
    if (!adapter) {
      const route = this.planRoute(request);
      throw new LogicBridgeError(
        `Unsupported browser-native proof route: ${route.blockers.join(', ')}`,
      );
    }

    const startedAt = performance.now();
    const result = adapter.prove(request);
    return {
      ...result,
      timeMs: performance.now() - startedAt,
      method: `adapter:${adapter.metadata.name}:${result.method ?? request.logic}`,
    };
  }

  private selectAdapter(
    request: Pick<BrowserNativeProofRequest, 'logic' | 'preferredProverFamily'>,
  ): BrowserNativeProofAdapter | undefined {
    const candidates = this.adapters.filter((candidate) => candidate.supports(request.logic));
    if (!request.preferredProverFamily) return candidates[0];
    return candidates.find(
      (candidate) => candidate.metadata.proverFamily === request.preferredProverFamily,
    );
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
