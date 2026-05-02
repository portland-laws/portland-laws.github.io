import { extractBrowserNativeFolNlp } from './browserNativeNlp';
import { FOLConverter, convertFolFormulaToProlog, convertFolFormulaToTptp } from './converter';

describe('FOLConverter', () => {
  it('converts text through the Python-style converter facade', () => {
    const converter = new FOLConverter({ useNlp: true, useMl: true });
    const result = converter.convert('All tenants are residents');

    expect(result).toMatchObject({
      status: 'partial',
      success: true,
      confidence: expect.any(Number),
    });
    expect(result.confidence).toBeGreaterThan(0.5);
    expect(result.output).toMatchObject({
      formulaString: '∀x (Tenants(x) → Residents(x))',
      predicates: [
        { name: 'Tenants', arity: 1 },
        { name: 'Residents', arity: 1 },
      ],
    });
    expect(result.warnings).toEqual([
      'Browser-native NLP extraction is not yet complete; regex extraction was used.',
    ]);
    expect(result.metadata).toMatchObject({
      ipfs_enabled: false,
      predicates_count: 2,
      quantifiers_count: 1,
      extracted_predicates: expect.any(Object),
      extracted_relations: [{ type: 'universal', subject: 'tenants', predicate: 'residents' }],
      browser_native_ml_confidence: true,
    });
  });

  it('classifies FOL NLP tokens without spaCy, Python, or server fallbacks', () => {
    const extraction = extractBrowserNativeFolNlp(
      'All tenants are not evicted and some occupants appeal.',
    );

    expect(extraction).toMatchObject({
      provider: 'deterministic-token-classifier',
      backend: 'typescript-token-classifier',
      candidateBackends: ['transformers.js-token-classification', 'onnx-webgpu', 'wasm-nlp'],
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonSpacy: false,
      fallback: 'none',
      metadata: {
        quantifierCount: 2,
        operatorCount: 1,
        negationCount: 1,
      },
    });
    expect(extraction.predicateCandidates).toEqual(['tenants', 'evicted', 'occupants', 'appeal']);
    expect(extraction.tokens.map((token) => token.role)).toEqual(
      expect.arrayContaining(['quantifier', 'negation', 'operator', 'predicate_candidate']),
    );
  });

  it('supports cache, batch, async, and convenience conversion APIs', async () => {
    const converter = new FOLConverter();

    expect(converter.toFol('If tenant then resident')).toBe('∀x (Tenant(x) → Resident(x))');
    expect(converter.convert('Some tenants are residents').status).toBe('partial');
    expect(converter.convert('Some tenants are residents').status).toBe('cached');
    expect(
      converter.convertBatch(['All humans are mortal', 'If tenant then resident']),
    ).toHaveLength(2);
    await expect(converter.convertAsync('All humans are mortal')).resolves.toMatchObject({
      success: true,
    });
  });

  it('renders lightweight Prolog and TPTP formats', () => {
    const formula = '∀x (Tenant(x) → Resident(x))';

    expect(convertFolFormulaToProlog(formula)).toBe('resident(X) :- tenant(X).');
    expect(convertFolFormulaToTptp(formula)).toBe(
      'fof(formula_1, axiom, ![x]: (Tenant(x)  =>  Resident(x))).',
    );
  });

  it('reports validation failures before conversion', () => {
    expect(new FOLConverter().convert('')).toMatchObject({
      status: 'validation_failed',
      success: false,
    });
  });
});
