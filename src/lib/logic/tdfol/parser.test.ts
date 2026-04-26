import { LogicParseError } from '../errors';
import { formatTdfolFormula } from './formatter';
import { lexTdfol } from './lexer';
import { parseTdfolFormula } from './parser';
import { getFreeVariables, substituteFormula } from './ast';

const portlandFormula =
  '∀a:Agent (SubjectTo(a,portland_city_code_1_01_010) → P(□(ComplyWith(a,portland_city_code_1_01_010))))';

describe('TDFOL lexer', () => {
  it('tokenizes Portland generated formulas', () => {
    const tokens = lexTdfol(portlandFormula);

    expect(tokens.map((token) => token.type).slice(0, 8)).toEqual([
      'FORALL',
      'IDENTIFIER',
      'COLON',
      'IDENTIFIER',
      'LPAREN',
      'IDENTIFIER',
      'LPAREN',
      'IDENTIFIER',
    ]);
    expect(tokens.some((token) => token.type === 'IMPLIES')).toBe(true);
    expect(tokens.some((token) => token.type === 'PERMISSION')).toBe(true);
    expect(tokens.some((token) => token.type === 'ALWAYS')).toBe(true);
  });
});

describe('TDFOL parser', () => {
  it('parses generated Portland deontic temporal formulas', () => {
    const formula = parseTdfolFormula(portlandFormula);

    expect(formula).toMatchObject({
      kind: 'quantified',
      quantifier: 'FORALL',
      variable: { kind: 'variable', name: 'a', sort: 'Agent' },
      formula: {
        kind: 'binary',
        operator: 'IMPLIES',
      },
    });

    if (formula.kind !== 'quantified' || formula.formula.kind !== 'binary') {
      throw new Error('Unexpected formula shape');
    }

    expect(formula.formula.left).toMatchObject({
      kind: 'predicate',
      name: 'SubjectTo',
    });
    expect(formula.formula.right).toMatchObject({
      kind: 'deontic',
      operator: 'PERMISSION',
      formula: {
        kind: 'temporal',
        operator: 'ALWAYS',
      },
    });
    expect([...getFreeVariables(formula)]).toEqual([]);
  });

  it('supports ASCII aliases and right-associative implication', () => {
    const formula = parseTdfolFormula('forall x. Person(x) -> O([]ComplyWith(x, code_section))');

    expect(formatTdfolFormula(formula)).toBe(
      '∀x ((Person(x)) → (O(□(ComplyWith(x, code_section)))))',
    );
  });

  it('parses prohibitions distinctly from eventuality', () => {
    const prohibition = parseTdfolFormula('F(ComplyWith(a, section))');
    const eventuality = parseTdfolFormula('<>ComplyWith(a, section)');

    expect(prohibition).toMatchObject({ kind: 'deontic', operator: 'PROHIBITION' });
    expect(eventuality).toMatchObject({ kind: 'temporal', operator: 'EVENTUALLY' });
  });

  it('throws positional parse errors for invalid formulas', () => {
    expect(() => parseTdfolFormula('forall x. Person(')).toThrow(LogicParseError);
    try {
      parseTdfolFormula('forall x. Person(');
    } catch (error) {
      expect(error).toBeInstanceOf(LogicParseError);
      expect((error as LogicParseError).context).toMatchObject({
        source: 'forall x. Person(',
      });
    }
  });

  it('substitutes free variables without rewriting bound variables', () => {
    const free = parseTdfolFormula('ComplyWith(x, section)');
    const substitutedFree = substituteFormula(free, 'x', { kind: 'constant', name: 'auditor' });

    expect(formatTdfolFormula(substitutedFree)).toBe('ComplyWith(auditor, section)');

    const bound = parseTdfolFormula('forall x. ComplyWith(x, section)');
    const substitutedBound = substituteFormula(bound, 'x', { kind: 'constant', name: 'auditor' });

    expect(formatTdfolFormula(substitutedBound)).toBe('∀x (ComplyWith(x, section))');
  });
});
