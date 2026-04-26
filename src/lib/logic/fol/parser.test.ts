import {
  buildFolFormula,
  parseFolOperators,
  parseFolQuantifiers,
  parseFolText,
  parseSimplePredicate,
  validateFolSyntax,
} from './parser';

describe('FOL parser utilities', () => {
  it('extracts quantifiers and logical operators from text', () => {
    expect(parseFolQuantifiers('All tenants are residents')).toMatchObject([
      { type: 'universal', symbol: '∀', text: 'All tenants' },
    ]);
    expect(parseFolOperators('If a tenant applies then the auditor may respond')).toMatchObject([
      { type: 'implication', symbol: '→' },
    ]);
  });

  it('builds simple first-order formulas', () => {
    expect(buildFolFormula('All tenants are residents')).toBe('∀x (Tenants(x) → Residents(x))');
    expect(buildFolFormula('If tenant then resident')).toBe('∀x (Tenant(x) → Resident(x))');
    expect(parseSimplePredicate('pay rent')).toBe('Rent(x)');
  });

  it('returns parse result with validation', () => {
    const result = parseFolText('All humans are mortal');

    expect(result.formula).toBe('∀x (Humans(x) → Mortal(x))');
    expect(result.validation.valid).toBe(true);
  });

  it('validates common syntax failures', () => {
    expect(validateFolSyntax('∀ (Broken(x)').valid).toBe(false);
    expect(validateFolSyntax('⊤').valid).toBe(true);
  });
});

