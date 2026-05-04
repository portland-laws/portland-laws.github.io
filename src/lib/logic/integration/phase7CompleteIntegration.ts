import { BrowserNativeLogicBridge, type BrowserNativeLogicBridgeOptions } from './bridge';
import { routeLogicIntegrationToCore } from './coreBridge';

export const PHASE7_COMPLETE_INTEGRATION_METADATA = {
  sourcePythonModule: 'logic/integrations/phase7_complete_integration.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: ['local_bridge_orchestration', 'local_core_routing', 'fail_closed_wasm_policy'],
} as const;

export type Phase7CompleteIntegrationRequest = {
  readonly text?: string;
  readonly tdfolFormula?: string;
  readonly cecExpression?: string;
  readonly preferWasmForZkp?: boolean;
  readonly wasmZkpAvailable?: boolean;
  readonly requireWasmZkp?: boolean;
};
export type Phase7CompleteIntegrationStage = {
  readonly name: 'deontic' | 'fol' | 'tdfol_cec' | 'cec_json' | 'zkp_route';
  readonly status: 'success' | 'partial' | 'failed';
  readonly output: string;
  readonly confidence: number;
  readonly warnings: readonly string[];
  readonly coreId?: string;
};
export type Phase7CompleteIntegrationResult = {
  readonly status: 'success' | 'partial' | 'validation_failed';
  readonly success: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly confidence: number;
  readonly stages: readonly Phase7CompleteIntegrationStage[];
  readonly issues: readonly string[];
  readonly metadata: typeof PHASE7_COMPLETE_INTEGRATION_METADATA;
};

export class BrowserNativePhase7CompleteIntegration {
  private readonly bridge: BrowserNativeLogicBridge;

  constructor(options: BrowserNativeLogicBridgeOptions = {}) {
    this.bridge = new BrowserNativeLogicBridge(options);
  }

  integrate(input: Phase7CompleteIntegrationRequest | string): Phase7CompleteIntegrationResult {
    const request = typeof input === 'string' ? { text: input } : input;
    const text = request.text?.trim() ?? '';
    const tdfolFormula = request.tdfolFormula?.trim() ?? '';
    const cecExpression = request.cecExpression?.trim() ?? '';
    const stages: Phase7CompleteIntegrationStage[] = [];
    if (text.length === 0 && tdfolFormula.length === 0 && cecExpression.length === 0) {
      return buildPhase7Result(
        'validation_failed',
        [],
        ['phase7 integration requires text or a logic expression'],
      );
    }
    if (text.length > 0) {
      stages.push(this.convertStage('deontic', text, 'legal_text', 'deontic'));
      stages.push(this.convertStage('fol', text, 'legal_text', 'fol'));
    }
    if (tdfolFormula.length > 0)
      stages.push(this.convertStage('tdfol_cec', tdfolFormula, 'tdfol', 'cec'));
    if (cecExpression.length > 0)
      stages.push(this.convertStage('cec_json', cecExpression, 'cec', 'json'));
    const zkpRoute = routeLogicIntegrationToCore({
      logic: 'zkp',
      operation: 'verify_phase7_artifacts',
      preferWasm: request.preferWasmForZkp ?? true,
      wasmAvailable: request.wasmZkpAvailable ?? false,
      allowTypeScriptFallback: !(request.requireWasmZkp ?? false),
    });
    stages.push({
      name: 'zkp_route',
      status: zkpRoute.ok ? 'success' : 'failed',
      output: zkpRoute.coreKind ?? '',
      confidence: zkpRoute.ok ? 1 : 0,
      warnings: zkpRoute.reason ? [zkpRoute.reason] : [],
      coreId: zkpRoute.coreId,
    });
    const failedCount = stages.filter((stage) => stage.status === 'failed').length;
    const issues = stages.flatMap((stage) => stage.warnings);
    if (!zkpRoute.ok && (request.requireWasmZkp ?? false)) {
      issues.unshift(
        'requested WASM ZKP verification failed closed without TypeScript or external fallback',
      );
    }
    return buildPhase7Result(
      failedCount === 0
        ? 'success'
        : failedCount === stages.length
          ? 'validation_failed'
          : 'partial',
      stages,
      issues,
    );
  }

  private convertStage(
    name: Phase7CompleteIntegrationStage['name'],
    source: string,
    sourceFormat: 'legal_text' | 'tdfol' | 'cec',
    targetFormat: 'deontic' | 'fol' | 'cec' | 'json',
  ): Phase7CompleteIntegrationStage {
    const converted = this.bridge.convert({ source, sourceFormat, targetFormat });
    return {
      name,
      status:
        converted.status === 'success'
          ? 'success'
          : converted.status === 'partial'
            ? 'partial'
            : 'failed',
      output: converted.targetFormula,
      confidence: converted.confidence,
      warnings: converted.warnings,
      coreId:
        typeof converted.metadata.routed_to === 'string' ? converted.metadata.routed_to : undefined,
    };
  }
}

function buildPhase7Result(
  status: Phase7CompleteIntegrationResult['status'],
  stages: readonly Phase7CompleteIntegrationStage[],
  issues: readonly string[],
): Phase7CompleteIntegrationResult {
  const confidence =
    stages.length === 0
      ? 0
      : stages.reduce((total, stage) => total + stage.confidence, 0) / stages.length;
  return {
    status,
    success: status !== 'validation_failed',
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    confidence,
    stages,
    issues,
    metadata: PHASE7_COMPLETE_INTEGRATION_METADATA,
  };
}

export function createBrowserNativePhase7CompleteIntegration(
  options: BrowserNativeLogicBridgeOptions = {},
): BrowserNativePhase7CompleteIntegration {
  return new BrowserNativePhase7CompleteIntegration(options);
}

export function phase7_complete_integration(
  request: Phase7CompleteIntegrationRequest | string,
): Phase7CompleteIntegrationResult {
  return createBrowserNativePhase7CompleteIntegration().integrate(request);
}
