import {
  BrowserNativeSymbolicContracts,
  analyze_symbolic_contract,
  create_symbolic_contracts,
} from './symbolicContracts';

describe('symbolic contracts browser-native parity', () => {
  const contract =
    'Vendor offers to deliver equipment for a payment of $5000. Buyer accepts the offer and shall inspect the goods. If vendor fails to deliver, buyer may seek damages and terminate the agreement.';

  it('extracts contract clauses and validates formation without Python or server fallback', () => {
    const result = new BrowserNativeSymbolicContracts().analyze(contract);

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      formationComplete: true,
      missingFormationElements: [],
      issues: [],
      metadata: {
        sourcePythonModule: 'logic/integration/domain/symbolic_contracts.py',
        runtimeDependencies: [],
      },
    });
    expect(result.clauses.map((clause) => clause.clauseType)).toEqual(
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
    expect(result.clauses.find((clause) => clause.clauseType === 'offer')?.formula).toContain(
      'Offer(',
    );
  });

  it('supports Python-style aliases and fails closed for incomplete local analysis', () => {
    const alias = analyze_symbolic_contract(
      'Supplier proposes a license and customer accepts for a monthly fee.',
    );
    const empty = create_symbolic_contracts().analyze('');
    const incomplete = create_symbolic_contracts().analyze('The contractor shall clean the site.');

    expect(alias).toMatchObject({ accepted: true, formationComplete: true });
    expect(empty).toMatchObject({
      accepted: false,
      issues: ['source text is required'],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(incomplete).toMatchObject({
      accepted: false,
      formationComplete: false,
      missingFormationElements: ['offer', 'acceptance', 'consideration'],
      issues: ['missing formation elements: offer, acceptance, consideration'],
    });
  });
});
