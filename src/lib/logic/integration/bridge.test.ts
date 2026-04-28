import { BrowserNativeLogicBridge, createBrowserNativeLogicBridge } from './bridge';

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
