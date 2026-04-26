import fixtures from './python-parity-fixtures.json';
import { analyzeNormativeSentence, buildDeonticFormula } from '../deontic';
import { parseFolText } from '../fol';
import { formatTdfolFormula, parseTdfolFormula } from '../tdfol';

type FolFixture = {
  id: string;
  kind: 'fol';
  input: string;
  python_regex_formula: string;
};

type DeonticFixture = {
  id: string;
  kind: 'deontic';
  input: string;
  python_norm_type: string;
  python_deontic_operator: string;
  python_formula_prefix: string;
};

type TdfolFixture = {
  id: string;
  kind: 'tdfol';
  input: string;
  python_parseable: boolean;
  python_contains: string[];
};

type Fixture = FolFixture | DeonticFixture | TdfolFixture;

describe('Python parity fixtures', () => {
  it.each(fixtures as Fixture[])('matches fixture $id', (fixture) => {
    if (fixture.kind === 'fol') {
      const result = parseFolText(fixture.input);
      expect(result.formula).toBe(fixture.python_regex_formula);
      expect(result.validation.valid).toBe(true);
      return;
    }

    if (fixture.kind === 'deontic') {
      const element = analyzeNormativeSentence(fixture.input);
      expect(element).toMatchObject({
        normType: fixture.python_norm_type,
        deonticOperator: fixture.python_deontic_operator,
      });
      expect(buildDeonticFormula(element!)).toContain(fixture.python_formula_prefix);
      return;
    }

    if (fixture.kind === 'tdfol') {
      const formula = parseTdfolFormula(fixture.input);
      const formatted = formatTdfolFormula(formula);
      for (const expected of fixture.python_contains) {
        expect(formatted).toContain(expected);
      }
    }
  });
});
