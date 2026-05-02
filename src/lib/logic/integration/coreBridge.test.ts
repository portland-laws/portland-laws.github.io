import {
  type BrowserNativeLogicCore,
  routeLogicIntegrationToCore,
  typescriptLogicCore,
  wasmLogicCore,
} from './coreBridge';

describe('browser-native integration core bridge', () => {
  it('routes ordinary logic operations to the TypeScript core by default', () => {
    const result = routeLogicIntegrationToCore({
      logic: 'CEC',
      operation: 'prove',
      payload: { goal: 'q' },
    });

    expect(result.ok).toBe(true);
    expect(result.logic).toBe('cec');
    expect(result.operation).toBe('prove');
    expect(result.coreKind).toBe('typescript');
    expect(result.coreId).toBe('browser-native-typescript-logic-core');
    expect(result.fallbackUsed).toBe(false);
    expect(result.payload).toEqual({ goal: 'q' });
  });

  it('routes WASM-capable requests to the WASM core when available and preferred', () => {
    const result = routeLogicIntegrationToCore({
      logic: 'zkp',
      operation: 'verify',
      preferWasm: true,
      wasmAvailable: true,
    });

    expect(result.ok).toBe(true);
    expect(result.coreKind).toBe('wasm');
    expect(result.coreId).toBe('browser-native-wasm-logic-core');
    expect(result.fallbackUsed).toBe(false);
  });

  it('falls back to the TypeScript core when WASM is preferred but unavailable', () => {
    const result = routeLogicIntegrationToCore({
      logic: 'zkp',
      operation: 'prove',
      preferWasm: true,
      wasmAvailable: false,
    });

    expect(result.ok).toBe(true);
    expect(result.coreKind).toBe('typescript');
    expect(result.fallbackUsed).toBe(true);
  });

  it('fails closed when a WASM-only request disallows TypeScript fallback', () => {
    const result = routeLogicIntegrationToCore({
      logic: 'zkp',
      operation: 'prove',
      preferWasm: true,
      wasmAvailable: false,
      allowTypeScriptFallback: false,
    });

    expect(result.ok).toBe(false);
    expect(result.coreKind).toBeUndefined();
    expect(result.fallbackUsed).toBe(false);
    expect(result.reason).toBe('requested WASM logic core is unavailable in this browser runtime');
  });

  it('never routes unsupported logic work to an external fallback', () => {
    const result = routeLogicIntegrationToCore({
      logic: 'python-service-only',
      operation: 'prove',
    });

    expect(result.ok).toBe(false);
    expect(result.coreKind).toBeUndefined();
    expect(result.coreId).toBeUndefined();
    expect(result.reason).toBe(
      'no browser-native TypeScript or WASM logic core supports this request',
    );
  });

  it('allows integration adapters to inject a narrowed browser-native core list', () => {
    const auditCore: BrowserNativeLogicCore = {
      id: 'audit-core',
      kind: 'typescript',
      supports: (request) => request.logic === 'audit' && request.operation === 'classify',
      execute: (request) => ({
        ok: true,
        logic: request.logic,
        operation: request.operation,
        coreKind: 'typescript',
        coreId: 'audit-core',
        fallbackUsed: false,
      }),
    };

    const result = routeLogicIntegrationToCore({ logic: 'audit', operation: 'classify' }, [
      auditCore,
      wasmLogicCore,
      typescriptLogicCore,
    ]);

    expect(result.ok).toBe(true);
    expect(result.coreId).toBe('audit-core');
  });
});
