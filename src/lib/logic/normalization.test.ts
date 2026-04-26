import {
  normalizePortlandIdentifier,
  normalizePredicateName,
  normalizeWhitespace,
  objectIdToPortlandIdentifier,
  portlandIdentifierToObjectId,
} from './normalization';

describe('logic normalization helpers', () => {
  it('normalizes whitespace', () => {
    expect(normalizeWhitespace('  Portland   City\nCode  ')).toBe('Portland City Code');
  });

  it('normalizes predicate names for generated formulas', () => {
    expect(normalizePredicateName('ComplyWith')).toBe('comply_with');
    expect(normalizePredicateName('  has review-authority  ')).toBe('has_review_authority');
    expect(normalizePredicateName('1.01.010')).toBe('p_1_01_010');
    expect(normalizePredicateName(' *** ')).toBe('unknown');
  });

  it('normalizes Portland identifiers and aliases', () => {
    expect(normalizePortlandIdentifier('pcc 1.01.010')).toBe('Portland City Code 1.01.010');
    expect(normalizePortlandIdentifier('Portland Code 9.01.050')).toBe('Portland City Code 9.01.050');
    expect(normalizePortlandIdentifier('Some Other Citation')).toBe('Some Other Citation');
  });

  it('converts Portland identifiers to generated object IDs and back', () => {
    expect(portlandIdentifierToObjectId('Portland City Code 1.01.010')).toBe(
      'portland_city_code_1_01_010',
    );
    expect(objectIdToPortlandIdentifier('portland_city_code_9_01_050')).toBe(
      'Portland City Code 9.01.050',
    );
    expect(objectIdToPortlandIdentifier('not_a_portland_section')).toBeNull();
  });
});

