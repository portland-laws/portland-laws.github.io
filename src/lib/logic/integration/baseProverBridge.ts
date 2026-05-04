import { LogicBridgeError } from '../errors';
import type { ProofResult } from '../types';
import type {
  BrowserNativeProofAdapter,
  BrowserNativeProofAdapterMetadata,
  BrowserNativeProofLogic,
  BrowserNativeProofRequest,
} from './proverAdapters';

export type BaseProverBridgePythonModule =
  | 'logic/integration/base_prover_bridge.py'
  | 'logic/integration/bridges/base_prover_bridge.py';

export interface BaseProverBridgeMetadata {
  sourcePythonModule: BaseProverBridgePythonModule;
  runtime: 'typescript-wasm-browser';
  serverCallsAllowed: false;
  pythonRuntime: false;
  subprocessAllowed: false;
  rpcAllowed: false;
  externalProverAllowed: false;
  failClosed: true;
  supportedLogics: Array<BrowserNativeProofLogic>;
  name: string;
}

export interface BaseProverBridgeInfo {
  name: string;
  available: boolean;
  runtime: 'typescript-wasm-browser';
  supportedLogics: Array<BrowserNativeProofLogic>;
  requiresExternalProver: false;
  sourcePythonModule: BaseProverBridgePythonModule;
}

export interface BaseProverBridgeValidation {
  valid: boolean;
  errors: Array<string>;
  normalizedRequest?: BrowserNativeProofRequest;
}

export interface BaseProverBridgeOptions {
  name?: string;
  supportedLogics?: Array<BrowserNativeProofLogic>;
  sourcePythonModule?: BaseProverBridgePythonModule;
}

const DEFAULT_SUPPORTED_LOGICS: Array<BrowserNativeProofLogic> = ['tdfol', 'cec', 'dcec'];

export abstract class BrowserNativeBaseProverBridge {
  readonly name: string;
  readonly supportedLogics: Array<BrowserNativeProofLogic>;
  readonly sourcePythonModule: BaseProverBridgePythonModule;

  protected constructor(options: BaseProverBridgeOptions = {}) {
    this.name = options.name ?? 'browser-native-base-prover-bridge';
    this.supportedLogics = [...(options.supportedLogics ?? DEFAULT_SUPPORTED_LOGICS)];
    this.sourcePythonModule =
      options.sourcePythonModule ?? 'logic/integration/base_prover_bridge.py';
  }

  getMetadata(): BaseProverBridgeMetadata {
    return {
      sourcePythonModule: this.sourcePythonModule,
      runtime: 'typescript-wasm-browser',
      serverCallsAllowed: false,
      pythonRuntime: false,
      subprocessAllowed: false,
      rpcAllowed: false,
      externalProverAllowed: false,
      failClosed: true,
      supportedLogics: [...this.supportedLogics],
      name: this.name,
    };
  }

  getProverInfo(): BaseProverBridgeInfo {
    return {
      name: this.name,
      available: this.checkProverAvailability(),
      runtime: 'typescript-wasm-browser',
      supportedLogics: [...this.supportedLogics],
      requiresExternalProver: false,
      sourcePythonModule: this.sourcePythonModule,
    };
  }

  checkProverAvailability(): boolean {
    return true;
  }

  supports(logic: BrowserNativeProofLogic): boolean {
    return this.supportedLogics.includes(logic);
  }

  validateRequest(request: Partial<BrowserNativeProofRequest>): BaseProverBridgeValidation {
    const errors: Array<string> = [];
    if (!request.logic) errors.push('logic is required');
    if (!request.theorem || request.theorem.trim().length === 0) errors.push('theorem is required');
    if (!Array.isArray(request.axioms)) errors.push('axioms must be an array');
    if (request.logic && !this.supports(request.logic)) {
      errors.push(`unsupported logic: ${request.logic}`);
    }
    if (request.maxSteps !== undefined && request.maxSteps <= 0) {
      errors.push('maxSteps must be positive');
    }
    if (request.maxDerivedFormulas !== undefined && request.maxDerivedFormulas <= 0) {
      errors.push('maxDerivedFormulas must be positive');
    }

    if (errors.length > 0 || !request.logic || !request.theorem || !Array.isArray(request.axioms)) {
      return { valid: false, errors };
    }

    return {
      valid: true,
      errors: [],
      normalizedRequest: {
        logic: request.logic,
        theorem: request.theorem.trim(),
        axioms: request.axioms.map((axiom) => axiom.trim()).filter((axiom) => axiom.length > 0),
        theorems: request.theorems
          ?.map((theorem) => theorem.trim())
          .filter((theorem) => theorem.length > 0),
        maxSteps: request.maxSteps,
        maxDerivedFormulas: request.maxDerivedFormulas,
        preferredProverFamily: request.preferredProverFamily,
      },
    };
  }

  prove(request: Partial<BrowserNativeProofRequest>): ProofResult {
    const validation = this.validateRequest(request);
    if (!validation.valid || !validation.normalizedRequest) {
      throw new LogicBridgeError(
        `Invalid browser-native proof request: ${validation.errors.join(', ')}`,
      );
    }
    return this.proveValidated(validation.normalizedRequest);
  }

  protected abstract proveValidated(request: BrowserNativeProofRequest): ProofResult;
}

export class BrowserNativeAdapterBaseProverBridge extends BrowserNativeBaseProverBridge {
  private readonly adapter: BrowserNativeProofAdapter;
  private readonly methodPrefix: string;

  constructor(
    adapter: BrowserNativeProofAdapter,
    options: Pick<BaseProverBridgeOptions, 'sourcePythonModule'> & { methodPrefix?: string } = {},
  ) {
    super({
      name: adapter.metadata.name,
      supportedLogics: [adapter.metadata.logic],
      sourcePythonModule: options.sourcePythonModule,
    });
    this.adapter = adapter;
    this.methodPrefix = options.methodPrefix ?? 'base-prover-bridge';
  }

  getAdapterMetadata(): BrowserNativeProofAdapterMetadata {
    return { ...this.adapter.metadata };
  }

  protected proveValidated(request: BrowserNativeProofRequest): ProofResult {
    if (!this.adapter.supports(request.logic)) {
      throw new LogicBridgeError(`Unsupported browser-native adapter logic: ${request.logic}`);
    }
    const result = this.adapter.prove(request);
    return {
      ...result,
      method: `${this.methodPrefix}:${this.adapter.metadata.name}:${result.method ?? request.logic}`,
    };
  }
}

export class BrowserNativeIntegrationBridgesBaseProverBridge extends BrowserNativeAdapterBaseProverBridge {
  constructor(adapter: BrowserNativeProofAdapter) {
    super(adapter, {
      sourcePythonModule: 'logic/integration/bridges/base_prover_bridge.py',
      methodPrefix: 'integration-bridges-base-prover-bridge',
    });
  }
}

export function createBrowserNativeBaseProverBridge(
  adapter: BrowserNativeProofAdapter,
): BrowserNativeAdapterBaseProverBridge {
  return new BrowserNativeAdapterBaseProverBridge(adapter);
}

export function createBrowserNativeIntegrationBridgesBaseProverBridge(
  adapter: BrowserNativeProofAdapter,
): BrowserNativeIntegrationBridgesBaseProverBridge {
  return new BrowserNativeIntegrationBridgesBaseProverBridge(adapter);
}

export const create_browser_native_base_prover_bridge = createBrowserNativeBaseProverBridge;
export const create_browser_native_integration_bridges_base_prover_bridge =
  createBrowserNativeIntegrationBridgesBaseProverBridge;
