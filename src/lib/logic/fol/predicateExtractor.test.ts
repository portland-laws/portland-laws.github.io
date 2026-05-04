import {
  BROWSER_NATIVE_NLP_PREDICATE_EXTRACTOR,
  buildFolFormulaFromParts,
  extractLogicalRelations,
  extractNlpPredicates,
  extractPredicates,
  extractVariables,
  normalizePredicate,
  parseSimpleRelationPredicate,
} from './predicateExtractor';

describe('FOL predicate extractor', () => {
  it('extracts nouns, verbs, and adjectives with Python-style normalization', () => {
    expect(extractPredicates('Portland is Safe and tenants must comply.')).toEqual({
      nouns: ['Portland', 'Safe'],
      verbs: ['Safe', 'Comply'],
      adjectives: ['Safe'],
      relations: [],
    });
    expect(normalizePredicate('the city of portland')).toBe('CityPortland');
  });

  it('extracts implication, universal, and existential relations', () => {
    expect(extractLogicalRelations('If tenant applies then auditor responds.')).toEqual([
      { type: 'implication', premise: 'tenant applies', conclusion: 'auditor responds' },
    ]);
    expect(extractLogicalRelations('All tenants are residents. Some permits are active.')).toEqual([
      { type: 'universal', subject: 'tenants', predicate: 'residents' },
      { type: 'existential', subject: 'permits', predicate: 'active' },
    ]);
  });

  it('builds FOL formulas from extracted parts', () => {
    expect(
      buildFolFormulaFromParts(
        [],
        extractPredicates('All tenants are residents.'),
        [],
        extractLogicalRelations('All tenants are residents.'),
      ),
    ).toBe('∀x (Tenants(x) → Residents(x))');
    expect(parseSimpleRelationPredicate('tenant applies')).toBe('Applies(x)');
  });

  it('allocates standard variables by unique predicate count', () => {
    expect(
      extractVariables({ nouns: ['A', 'B'], verbs: ['C'], adjectives: [], relations: [] }),
    ).toEqual(['x', 'y', 'z']);
  });

  it('exposes a browser-native NLP predicate adapter without runtime fallbacks', () => {
    expect(BROWSER_NATIVE_NLP_PREDICATE_EXTRACTOR).toEqual({
      id: 'browser-native-deterministic-nlp-predicate-extractor',
      runtime: 'browser-native',
      pythonModule: 'logic/fol/utils/nlp_predicate_extractor.py',
      dependencies: [],
      failClosed: true,
    });
  });

  it('extracts deterministic spaCy-style tokens and local syntactic relations', () => {
    const result = extractNlpPredicates(
      'Tenant submits application to auditor. If tenant applies then auditor responds.',
    );

    expect(result.adapter.runtime).toBe('browser-native');
    expect(result.predicates.nouns).toEqual(['Tenant', 'If']);
    expect(result.logicalRelations).toEqual([
      { type: 'implication', premise: 'tenant applies', conclusion: 'auditor responds' },
    ]);
    expect(
      result.tokens.filter((token) => token.pos === 'verb').map((token) => token.normalized),
    ).toEqual(['Submits', 'Applies', 'Responds']);
    expect(result.syntacticRelations).toEqual([
      { subject: 'Tenant', predicate: 'Submits', object: 'Application', confidence: 0.62 },
      { subject: 'Tenant', predicate: 'Applies', object: 'Auditor', confidence: 0.62 },
    ]);
  });
});
