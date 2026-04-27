import {
  CecProblemParseError,
  CecProblemParser,
  CecTptpParser,
  detectProblemFormat,
  parseCecProblemString,
} from './problemParser';

describe('CEC problem parser', () => {
  it('parses TPTP fof/cnf formulas into ShadowProver problem objects', () => {
    const content = `
      % comment ignored
      include('Axioms/SET001.ax').
      fof(ax1, axiom, (p => q)).
      cnf(h1, hypothesis, p | r).
      fof(goal, conjecture, q).
      fof(neg_goal, negated_conjecture, r).
    `;

    const parser = new CecTptpParser();
    const problem = parser.parseString(content, 'sample-tptp');

    expect(problem).toMatchObject({
      name: 'sample-tptp',
      logic: 'K',
      assumptions: ['(p => q)', 'p | r'],
      goals: ['q', 'not(r)'],
      metadata: {
        format: 'tptp',
        includes: ['Axioms/SET001.ax'],
        totalFormulas: 4,
      },
    });
    expect(parser.formulas.map((formula) => formula.name)).toEqual(['ax1', 'h1', 'goal', 'neg_goal']);
  });

  it('keeps nested TPTP formulas and annotations intact', () => {
    const problem = parseCecProblemString(`
      fof(nested, axiom, (![X] : (human(X) => mortal(X))), file('source.p', nested)).
      fof(goal, theorem, mortal(socrates)).
    `);

    expect(problem.assumptions).toEqual(['(![X] : (human(X) => mortal(X)))']);
    expect(problem.goals).toEqual(['mortal(socrates)']);
    expect((problem.metadata?.formulas as Array<{ annotations?: string }>)[0].annotations)
      .toBe("file('source.p', nested)");
  });

  it('parses custom ShadowProver problem format with logic sections', () => {
    const problem = parseCecProblemString(`
      # browser-native custom format
      LOGIC: S4

      ASSUMPTIONS:
      (always (implies (p) (q)))
      (always (p))

      GOALS:
      (always (q))
    `, 'custom');

    expect(problem).toEqual({
      name: 'custom_problem',
      logic: 'S4',
      assumptions: ['(always (implies (p) (q)))', '(always (p))'],
      goals: ['(always (q))'],
      metadata: { format: 'custom' },
    });
  });

  it('auto-detects formats and maps cognitive custom logic to S5', () => {
    expect(detectProblemFormat('fof(a, axiom, p).')).toBe('tptp');
    expect(detectProblemFormat('LOGIC: K')).toBe('custom');

    const parser = new CecProblemParser();
    const problem = parser.parseString('LOGIC: Cognitive\nGOALS:\n(K alice (p))', { name: 'cog' });

    expect(problem.logic).toBe('S5');
    expect(problem.name).toBe('cog');
    expect(problem.goals).toEqual(['(K alice (p))']);
  });

  it('reports malformed TPTP formulas with parser-specific errors', () => {
    expect(() => parseCecProblemString('fof(ax, axiom, (p => q).', 'tptp')).toThrow(CecProblemParseError);
    expect(() => parseCecProblemString('fof(ax, axiom).', 'tptp')).toThrow('requires name, role, and formula');
  });
});
