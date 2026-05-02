export type BrowserNativeCoreKind = 'typescript' | 'wasm';

export interface LogicCoreRouteRequest {
  logic: string;
  operation: string;
  preferWasm?: boolean;
  wasmAvailable?: boolean;
  allowTypeScriptFallback?: boolean;
  payload?: unknown;
}

export interface LogicCoreRouteResult {
  ok: boolean;
  logic: string;
  operation: string;
  coreKind?: BrowserNativeCoreKind;
  coreId?: string;
  fallbackUsed: boolean;
  reason?: string;
  payload?: unknown;
}

export interface BrowserNativeLogicCore {
  id: string;
  kind: BrowserNativeCoreKind;
  supports: (request: LogicCoreRouteRequest) => boolean;
  execute: (request: LogicCoreRouteRequest) => LogicCoreRouteResult;
}

const TYPESCRIPT_LOGIC_CORES = new Set(['cec', 'dcec', 'deontic', 'flogic', 'fol', 'tdfol', 'zkp']);

const WASM_ACCELERATED_CORES = new Set(['groth16', 'zkp']);

function normalizeToken(value: string): string {
  return value.trim().toLowerCase();
}

function normalizeRequest(request: LogicCoreRouteRequest): LogicCoreRouteRequest {
  return {
    ...request,
    logic: normalizeToken(request.logic),
    operation: normalizeToken(request.operation),
  };
}

function invalidRequestReason(request: LogicCoreRouteRequest): string | undefined {
  if (normalizeToken(request.logic).length === 0) {
    return 'logic core name is required';
  }
  if (normalizeToken(request.operation).length === 0) {
    return 'logic operation name is required';
  }
  return undefined;
}

function orderCoresForRequest(
  request: LogicCoreRouteRequest,
  cores: readonly BrowserNativeLogicCore[],
): readonly BrowserNativeLogicCore[] {
  if (request.preferWasm) {
    return cores;
  }

  return [...cores].sort((left, right) => {
    if (left.kind === right.kind) {
      return 0;
    }
    return left.kind === 'typescript' ? -1 : 1;
  });
}

export const typescriptLogicCore: BrowserNativeLogicCore = {
  id: 'browser-native-typescript-logic-core',
  kind: 'typescript',
  supports(request) {
    return TYPESCRIPT_LOGIC_CORES.has(normalizeToken(request.logic));
  },
  execute(request) {
    const normalized = normalizeRequest(request);
    return {
      ok: true,
      logic: normalized.logic,
      operation: normalized.operation,
      coreKind: 'typescript',
      coreId: this.id,
      fallbackUsed: false,
      payload: normalized.payload,
    };
  },
};

export const wasmLogicCore: BrowserNativeLogicCore = {
  id: 'browser-native-wasm-logic-core',
  kind: 'wasm',
  supports(request) {
    return (
      Boolean(request.wasmAvailable) && WASM_ACCELERATED_CORES.has(normalizeToken(request.logic))
    );
  },
  execute(request) {
    const normalized = normalizeRequest(request);
    return {
      ok: true,
      logic: normalized.logic,
      operation: normalized.operation,
      coreKind: 'wasm',
      coreId: this.id,
      fallbackUsed: false,
      payload: normalized.payload,
    };
  },
};

export const browserNativeLogicCores: readonly BrowserNativeLogicCore[] = [
  wasmLogicCore,
  typescriptLogicCore,
];

export function routeLogicIntegrationToCore(
  request: LogicCoreRouteRequest,
  cores: readonly BrowserNativeLogicCore[] = browserNativeLogicCores,
): LogicCoreRouteResult {
  const invalidReason = invalidRequestReason(request);
  const normalized = normalizeRequest(request);

  if (invalidReason) {
    return {
      ok: false,
      logic: normalized.logic,
      operation: normalized.operation,
      fallbackUsed: false,
      reason: invalidReason,
    };
  }

  const orderedCores = orderCoresForRequest(normalized, cores);
  const wasmCore = orderedCores.find((core) => core.kind === 'wasm' && core.supports(normalized));
  if (wasmCore) {
    return wasmCore.execute(normalized);
  }

  if (normalized.preferWasm && normalized.allowTypeScriptFallback === false) {
    return {
      ok: false,
      logic: normalized.logic,
      operation: normalized.operation,
      fallbackUsed: false,
      reason: 'requested WASM logic core is unavailable in this browser runtime',
    };
  }

  const selectedCore = orderedCores.find(
    (core) => core.kind === 'typescript' && core.supports(normalized),
  );
  if (selectedCore) {
    const result = selectedCore.execute(normalized);
    return {
      ...result,
      fallbackUsed: Boolean(normalized.preferWasm) && result.coreKind === 'typescript',
    };
  }

  return {
    ok: false,
    logic: normalized.logic,
    operation: normalized.operation,
    fallbackUsed: false,
    reason: 'no browser-native TypeScript or WASM logic core supports this request',
  };
}
