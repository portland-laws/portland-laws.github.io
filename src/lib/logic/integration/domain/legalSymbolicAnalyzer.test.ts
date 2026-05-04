import {
  BrowserNativeLegalSymbolicAnalyzer,
  analyze_legal_symbolic_text,
  create_legal_symbolic_analyzer,
} from './legalSymbolicAnalyzer';

describe('legal symbolic analyzer browser-native parity', () => {
  const text =
    'Under PCC 33.110.210, the landlord must provide notice if the tenant requests repairs. Smith v. Jones, 123 Or. 456 held the agency may inspect the parcel. Staff shall not disclose sealed testimony.';

  it('extracts symbolic legal operators, references, and domains locally', () => {
    const result = new BrowserNativeLegalSymbolicAnalyzer().analyze(text);

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: {
        sourcePythonModule: 'logic/integration/domain/legal_symbolic_analyzer.py',
        runtimeDependencies: [],
      },
    });
    expect(result.statements.map((statement) => statement.symbol)).toEqual(
      expect.arrayContaining(['O', 'P', 'F', 'IF']),
    );
    expect(result.statements[0].formula).toContain('O(');
    expect(result.references).toEqual(
      expect.arrayContaining([
        { kind: 'section', value: 'PCC 33.110.210' },
        { kind: 'citation', value: '123 Or. 456' },
        { kind: 'case', value: 'Smith v. Jones' },
      ]),
    );
    expect(result.domains).toEqual(expect.arrayContaining(['property', 'administrative']));
  });

  it('supports Python-style aliases and fails closed without remote fallback', () => {
    const alias = analyze_legal_symbolic_text('ORS 90.320 says a landlord shall maintain repairs.');
    const empty = create_legal_symbolic_analyzer().analyze('');
    const unmatched = create_legal_symbolic_analyzer().analyze('This paragraph describes context.');

    expect(alias.statements[0]).toMatchObject({ operator: 'obligation', symbol: 'O' });
    expect(empty).toMatchObject({
      accepted: false,
      issues: ['source text is required'],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(unmatched).toMatchObject({
      accepted: false,
      issues: [
        'no legal symbolic operators matched locally',
        'no legal references detected locally',
      ],
    });
  });
});
