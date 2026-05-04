import {
  buildFolFormula,
  parseFolOperators,
  parseFolQuantifiers,
  parseFolText,
  parseSimplePredicate,
  textToFol,
  text_to_fol,
  validateFolSyntax,
} from './index';

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

  it('ports text_to_fol.py as a browser-native deterministic adapter', () => {
    const result = textToFol('Every tenant pays rent. Alice is a tenant.');

    expect(result).toMatchObject({
      ok: true,
      formula: '(∀x (Tenant(x) → PaysRent(x))) ∧ (Tenant(alice))',
      metadata: {
        sourcePythonModule: 'logic/fol/text_to_fol.py',
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
      },
    });
    expect(result.nlp).toMatchObject({
      provider: 'deterministic-token-classifier',
      serverCallsAllowed: false,
      pythonSpacy: false,
    });
    expect(result.clauses.map((clause) => clause.formula)).toEqual([
      '∀x (Tenant(x) → PaysRent(x))',
      'Tenant(alice)',
    ]);
  });

  it('handles negative and existential text_to_fol clauses without runtime fallbacks', () => {
    expect(text_to_fol('No tenant is exempt').formula).toBe('∀x (Tenant(x) → ¬Exempt(x))');
    expect(textToFol('Some tenant files appeal').formula).toBe('∃x (Tenant(x) ∧ FilesAppeal(x))');
  });
});
