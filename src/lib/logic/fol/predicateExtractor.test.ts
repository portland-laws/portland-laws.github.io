import {
  buildFolFormulaFromParts,
  extractLogicalRelations,
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
      buildFolFormulaFromParts([], extractPredicates('All tenants are residents.'), [], extractLogicalRelations('All tenants are residents.')),
    ).toBe('∀x (Tenants(x) → Residents(x))');
    expect(parseSimpleRelationPredicate('tenant applies')).toBe('Applies(x)');
  });

  it('allocates standard variables by unique predicate count', () => {
    expect(extractVariables({ nouns: ['A', 'B'], verbs: ['C'], adjectives: [], relations: [] })).toEqual(['x', 'y', 'z']);
  });
});
