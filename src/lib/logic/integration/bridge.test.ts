import { BrowserNativeLogicBridge, createBrowserNativeLogicBridge } from './bridge';
import {
  createBrowserNativeLeanProverBridge,
  type BrowserNativeLeanProofResult,
} from './leanProverBridge';
import {
  BrowserNativeProverRouter,
  createBrowserNativeEProverAdapter,
  createBrowserNativeProverRouter,
  type BrowserNativeProofAdapter,
  type EProverCompatibilityResult,
} from './proverAdapters';

describe('BrowserNativeLogicBridge', () => {
  it('reports local browser-native metadata and supported routes', () => {
    const bridge = createBrowserNativeLogicBridge();

    expect(bridge.metadata.requiresExternalProver).toBe(false);
    expect(bridge.metadata.toDict()).toMatchObject({
      target_system: 'typescript-wasm-browser',
      requires_external_prover: false,
    });
    expect(bridge.supportsConversion('legal_text', 'deontic')).toBe(true);
    expect(bridge.supportsConversion('tdfol', 'cec')).toBe(true);
    expect(bridge.listRoutes().length).toBeGreaterThan(10);
  });

  it('routes legal text to FOL and deontic converters without server calls', () => {
    const bridge = new BrowserNativeLogicBridge({
      fol: { useNlp: true, useMl: true },
      deontic: { useMl: true },
    });

    const fol = bridge.convert({
      source: 'All tenants are residents',
      sourceFormat: 'legal_text',
      targetFormat: 'fol',
    });
    const deontic = bridge.convert('Tenants must maintain exits.', 'legal_text', 'deontic');

    expect(fol.status).toBe('partial');
    expect(fol.targetFormula).toBe('∀x (Tenants(x) → Residents(x))');
    expect(fol.metadata).toMatchObject({
      routed_to: 'FOLConverter',
      server_calls_allowed: false,
      browser_native_ml_confidence: true,
    });
    expect(deontic.status).toBe('success');
    expect(deontic.targetFormula).toContain('O(');
    expect(deontic.metadata).toMatchObject({
      routed_to: 'DeonticConverter',
      server_calls_allowed: false,
    });
  });

  it('routes TDFOL and CEC conversions through local parser/formatter cores', () => {
    const bridge = createBrowserNativeLogicBridge();

    const tdfolToCec = bridge.convert('forall x. O(Comply(x))', 'tdfol', 'cec');
    const cecToJson = bridge.convert('(O (Comply ada))', 'cec', 'json');

    expect(tdfolToCec).toMatchObject({
      status: 'success',
      targetFormula: '(forall x (O (Comply x)))',
      sourceFormat: 'tdfol',
      targetFormat: 'cec',
    });
    expect(tdfolToCec.metadata).toMatchObject({
      routed_to: 'convertTdfolFormula',
      server_calls_allowed: false,
    });
    expect(JSON.parse(cecToJson.targetFormula)).toMatchObject({
      kind: 'unary',
      operator: 'O',
    });
  });

  it('proves TDFOL and CEC requests using local proof engines', () => {
    const bridge = createBrowserNativeLogicBridge();

    const tdfol = bridge.prove({
      logic: 'tdfol',
      theorem: 'Resident(Ada)',
      axioms: ['Resident(Ada)'],
    });
    const cec = bridge.prove({
      logic: 'cec',
      theorem: '(subject_to ada code)',
      axioms: ['(subject_to ada code)'],
    });

    expect(tdfol).toMatchObject({
      status: 'proved',
      theorem: 'Resident(Ada)',
      method: 'bridge:tdfol-forward-chaining',
    });
    expect(cec).toMatchObject({
      status: 'proved',
      theorem: '(subject_to ada code)',
      method: 'bridge:cec-forward-chaining',
    });
    expect(tdfol.timeMs).toEqual(expect.any(Number));
    expect(cec.timeMs).toEqual(expect.any(Number));
  });

  it('exposes browser-local prover adapter contracts for TDFOL, CEC, and DCEC', () => {
    const router = createBrowserNativeProverRouter();
    const adapters = router.listAdapters();

    expect(adapters.map((adapter) => adapter.logic)).toEqual(['tdfol', 'cec', 'dcec']);
    expect(adapters.every((adapter) => adapter.runtime === 'typescript-wasm-browser')).toBe(true);
    expect(adapters.every((adapter) => adapter.requiresExternalProver === false)).toBe(true);
    expect(router.supports('tdfol')).toBe(true);
    expect(router.supports('dcec')).toBe(true);
  });

  it('routes proof requests through local browser adapters without external prover delegation', () => {
    const router = createBrowserNativeProverRouter();

    const tdfol = router.prove({
      logic: 'tdfol',
      theorem: 'Resident(Ada)',
      axioms: ['Resident(Ada)'],
    });
    const dcec = router.prove({
      logic: 'dcec',
      theorem: '(P (always (comply_with ada code)))',
      axioms: ['(P (always (comply_with ada code)))'],
    });

    expect(tdfol).toMatchObject({
      status: 'proved',
      theorem: 'Resident(Ada)',
      method: 'adapter:local-tdfol-forward-prover:tdfol-forward-chaining',
    });
    expect(dcec).toMatchObject({
      status: 'proved',
      theorem: '(P (always (comply_with ada code)))',
      method: 'adapter:local-dcec-forward-prover:cec-forward-chaining',
    });
    expect(tdfol.timeMs).toEqual(expect.any(Number));
    expect(dcec.timeMs).toEqual(expect.any(Number));
  });

  it('ports the E prover adapter as a browser-native fail-closed TDFOL compatibility adapter', () => {
    const adapter = createBrowserNativeEProverAdapter();
    const result = adapter.prove({
      logic: 'tdfol',
      theorem: 'Resident(Ada)',
      axioms: ['Resident(Ada)'],
    }) as EProverCompatibilityResult;

    expect(adapter.metadata).toMatchObject({
      logic: 'tdfol',
      name: 'browser-native-e-prover-adapter',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
      proverFamily: 'e-prover',
    });
    expect(adapter.supports('cec')).toBe(false);
    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Resident(Ada)',
      method: 'e-prover-compatible:tdfol-forward-chaining',
    });
    expect(result.eProver).toMatchObject({
      adapter: 'browser-native-e-prover-adapter',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      command: null,
      statusMapping: 'Theorem',
    });
    expect(result.eProver.tptpProblem).toContain('fof(tdfol_formula, axiom, resident(ada)).');
    expect(result.eProver.tptpProblem).toContain(
      'fof(tdfol_conjecture, conjecture, resident(ada)).',
    );
  });

  it('can expose the E prover compatibility adapter through the local router without server calls', () => {
    const router = createBrowserNativeProverRouter({ includeEProverCompatibilityAdapter: true });
    const adapters = router.listAdapters();

    expect(adapters.map((adapter) => adapter.name)).toContain('browser-native-e-prover-adapter');
    expect(adapters.every((adapter) => adapter.requiresExternalProver === false)).toBe(true);
  });

  it('ports the Lean prover bridge as a browser-native TDFOL compatibility adapter', () => {
    const adapter = createBrowserNativeLeanProverBridge();
    const result = adapter.prove({
      logic: 'tdfol',
      theorem: 'Resident(Ada)',
      axioms: ['Resident(Ada)'],
    }) as BrowserNativeLeanProofResult;

    expect(adapter.metadata).toMatchObject({
      logic: 'tdfol',
      name: 'browser-native-lean-prover-bridge',
      runtime: 'typescript-wasm-browser',
      requiresExternalProver: false,
    });
    expect(adapter.supports('cec')).toBe(false);
    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Resident(Ada)',
      method: 'lean-compatible:tdfol-forward-chaining',
    });
    expect(result.lean).toMatchObject({
      adapter: 'browser-native-lean-prover-bridge',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntime: false,
      command: null,
      leanVersion: null,
      statusMapping: 'proved',
    });
    expect(result.lean.theoremDeclaration).toContain('axiom h1 : (Resident Ada)');
    expect(result.lean.theoremDeclaration).toContain('theorem target : (Resident Ada)');
  });

  it('accepts injectable browser-native prover adapters for bridge contract tests', () => {
    const adapter: BrowserNativeProofAdapter = {
      metadata: {
        logic: 'tdfol',
        name: 'test-local-adapter',
        runtime: 'typescript-wasm-browser',
        requiresExternalProver: false,
      },
      supports: (logic) => logic === 'tdfol',
      prove: (request) => ({
        status: 'proved',
        theorem: request.theorem,
        steps: [],
        method: 'injected-local-proof',
      }),
    };
    const router = new BrowserNativeProverRouter([adapter]);

    const result = router.prove({ logic: 'tdfol', theorem: 'opaque theorem', axioms: [] });

    expect(router.listAdapters()).toEqual([adapter.metadata]);
    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'opaque theorem',
      method: 'adapter:test-local-adapter:injected-local-proof',
    });
  });

  it('returns explicit unsupported conversion results for missing local routes', () => {
    const bridge = createBrowserNativeLogicBridge();
    const result = bridge.convert('Resident(Ada)', 'fol', 'cec');

    expect(result).toMatchObject({
      status: 'unsupported',
      targetFormula: '',
      warnings: ['Unsupported browser-native conversion route: fol -> cec'],
    });
    expect(result.metadata).toMatchObject({ server_calls_allowed: false });
  });
});
