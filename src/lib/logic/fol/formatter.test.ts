import {
  convertToDefeasibleFormat,
  convertToPrologFormat,
  convertToTptpFormat,
  extractDeonticMetadata,
  extractFolMetadata,
  formatDeontic,
  formatFol,
  formatOutput,
  formatXmlOutput,
  parseDeonticToJson,
  parseFolToJson,
} from './formatter';

describe('FOL/deontic formatter utilities', () => {
  it('formats FOL into Prolog, TPTP, and JSON structures', () => {
    const formula = '∀x (Tenant(x) → Resident(x))';

    expect(convertToPrologFormat(formula)).toBe('resident(X) :- tenant(X).');
    expect(convertToTptpFormat(formula)).toBe(
      'fof(formula, axiom, ![x]: (Tenant(x)  =>  Resident(x))).',
    );
    expect(formatFol(formula, 'json')).toMatchObject({
      fol_formula: formula,
      structured_form: {
        quantifiers: [{ type: 'universal', variable: 'x', symbol: '∀' }],
        predicates: [
          { name: 'Tenant', arity: 1, arguments: ['x'] },
          { name: 'Resident', arity: 1, arguments: ['x'] },
        ],
      },
      metadata: {
        quantifier_count: 1,
        predicate_count: 2,
      },
    });
  });

  it('formats remaining Python logic formatter outputs for XML and multi-argument Prolog', () => {
    const binaryFormula = '∀x (Tenant(x, UnitA) → Resident(x, UnitA))';
    const xmlFormula = 'Tenant(A & B)';

    expect(convertToPrologFormat(binaryFormula)).toBe('resident(X, UNITA) :- tenant(X, UNITA).');
    expect(convertToPrologFormat('∃x (Tenant(x, UnitA))')).toBe('tenant(a, UNITA).');
    expect(formatFol(xmlFormula, 'xml', false)).toMatchObject({
      fol_formula: xmlFormula,
      format: 'xml',
      xml_form: expect.stringContaining('<fol_formula>'),
    });
    expect(formatFol(xmlFormula, 'xml', false).xml_form).toContain('&amp;');
    expect(formatDeontic('P(Visit(TenantA))', 'permission', 'xml', false).xml_form).toContain(
      '<norm_type>permission</norm_type>',
    );
  });

  it('formats deontic logic and extracts structure', () => {
    const formula = 'O(∀x (Tenant(x) → PayRent(x)))';

    expect(convertToDefeasibleFormat(formula, 'obligation')).toBe(
      `obligatory(${formula}) unless defeated.`,
    );
    expect(formatDeontic(formula, 'obligation', 'json')).toMatchObject({
      deontic_formula: formula,
      norm_type: 'obligation',
      structured_form: {
        deontic_operators: [{ type: 'obligation', symbol: 'O' }],
      },
    });
    expect(parseDeonticToJson(formula)).toHaveProperty('logical_structure');
  });

  it('extracts metadata and formats aggregate output', () => {
    expect(extractFolMetadata('∃x (Tenant(x) ∧ Resident(x))')).toMatchObject({
      quantifier_count: 1,
      predicate_count: 2,
      operator_count: 1,
    });
    expect(extractDeonticMetadata('F(Act(x))', 'prohibition')).toMatchObject({
      norm_type: 'prohibition',
      deontic_operator: 'P',
    });
    expect(
      formatOutput(
        [{ original_text: 'All tenants are residents', fol_formula: 'P(x)' }],
        { conversion_rate: 1 },
        'text',
      ),
    ).toContain('Total formulas: 1');
    expect(
      formatXmlOutput([{ original_text: 'A & B', fol_formula: 'P(x)' }], { conversion_rate: 1 }),
    ).toContain('A &amp; B');
    expect(
      formatOutput(
        [{ original_text: 'A & B', fol_formula: 'P(x)' }],
        { conversion_rate: 1 },
        'xml',
      ),
    ).toContain('<logic_conversion_results>');
  });

  it('parses FOL formula JSON directly', () => {
    expect(parseFolToJson('∃x (Tenant(x) ∧ Resident(x))')).toMatchObject({
      quantifiers: [{ type: 'existential', variable: 'x', symbol: '∃' }],
      operators: [{ type: 'conjunction', symbol: '∧' }],
    });
    expect(parseFolToJson('Tenant(x) ↔ Resident(x)')).toMatchObject({
      operators: [{ type: 'biconditional', symbol: '↔' }],
    });
  });
});
