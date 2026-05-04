import { LogicBridgeError } from '../errors';
import type { ProofResult } from '../types';
import type {
  BrowserNativeProofAdapter,
  BrowserNativeProofAdapterMetadata,
  BrowserNativeProofLogic,
  BrowserNativeProofRequest,
} from './proverAdapters';

export interface BaseProverBridgeMetadata {
  sourcePythonModule: 'logic/integration/base_prover_bridge.py';
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
  sourcePythonModule: 'logic/integration/base_prover_bridge.py';
}

export interface BaseProverBridgeValidation {
  valid: boolean;
  errors: Array<string>;
  normalizedRequest?: BrowserNativeProofRequest;
}

export interface BaseProverBridgeOptions {
  name?: string;
  supportedLogics?: Array<BrowserNativeProofLogic>;
}

const DEFAULT_SUPPORTED_LOGICS: Array<BrowserNativeProofLogic> = ['tdfol', 'cec', 'dcec'];

export abstract class BrowserNativeBaseProverBridge {
  readonly name: string;
  readonly supportedLogics: Array<BrowserNativeProofLogic>;

  protected constructor(options: BaseProverBridgeOptions = {}) {
    this.name = options.name ?? 'browser-native-base-prover-bridge';
    this.supportedLogics = [...(options.supportedLogics ?? DEFAULT_SUPPORTED_LOGICS)];
  }

  getMetadata(): BaseProverBridgeMetadata {
    return {
      sourcePythonModule: 'logic/integration/base_prover_bridge.py',
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
      sourcePythonModule: 'logic/integration/base_prover_bridge.py',
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

  constructor(adapter: BrowserNativeProofAdapter) {
    super({ name: adapter.metadata.name, supportedLogics: [adapter.metadata.logic] });
    this.adapter = adapter;
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
      method: `base-prover-bridge:${this.adapter.metadata.name}:${result.method ?? request.logic}`,
    };
  }
}

export function createBrowserNativeBaseProverBridge(
  adapter: BrowserNativeProofAdapter,
): BrowserNativeAdapterBaseProverBridge {
  return new BrowserNativeAdapterBaseProverBridge(adapter);
}

export const create_browser_native_base_prover_bridge = createBrowserNativeBaseProverBridge;
