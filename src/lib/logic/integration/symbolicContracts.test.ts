import {
  BrowserNativeIntegrationSymbolicContracts,
  INTEGRATION_SYMBOLIC_CONTRACTS_METADATA,
  analyze_symbolic_contract,
  create_symbolic_contracts,
} from './symbolicContracts';

describe('top-level symbolic contracts browser-native parity', () => {
  const contract =
    'Acme offers to license the dataset for a fee of $500. Beta accepts the offer and must preserve attribution. If Beta fails to pay, Acme may seek damages and terminate access.';

  it('extracts symbolic contract elements without Python or server fallback', () => {
    const result = new BrowserNativeIntegrationSymbolicContracts().analyze(contract);

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      requiredElementsPresent: true,
      missingRequiredElements: [],
      issues: [],
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic_contracts.py',
        runtimeDependencies: [],
      },
    });
    expect(result.clauses.map((clause) => clause.element)).toEqual(
      expect.arrayContaining([
        'offer',
        'acceptance',
        'consideration',
        'obligation',
        'condition',
        'breach',
        'remedy',
        'termination',
      ]),
    );
    expect(result.clauses[0].symbolicFormula).toContain('(');
    expect(INTEGRATION_SYMBOLIC_CONTRACTS_METADATA.parity).toContain(
      'top_level_symbolic_contract_adapter',
    );
  });

  it('keeps Python-style aliases local and fails closed on incomplete formation', () => {
    const complete = analyze_symbolic_contract(
      'Seller proposes a delivery agreement, buyer accepts, and buyer pays consideration.',
    );
    const analyzer = create_symbolic_contracts();
    const incomplete = analyzer.analyze('The vendor shall provide weekly support.');

    expect(complete.accepted).toBe(true);
    expect(analyzer.extract_contract_elements(contract).length).toBeGreaterThan(0);
    expect(analyzer.validate_contract_formation(contract)).toBe(true);
    expect(incomplete).toMatchObject({
      accepted: false,
      requiredElementsPresent: false,
      missingRequiredElements: ['offer', 'acceptance', 'consideration'],
      issues: ['missing required elements: offer, acceptance, consideration'],
    });
    expect(analyzer.analyze('')).toMatchObject({
      accepted: false,
      issues: ['source text is required'],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
  });
});
