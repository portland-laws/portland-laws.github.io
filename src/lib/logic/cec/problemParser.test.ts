import type { CecExpression } from './ast';
import {
  CecVampireAdapter,
  mapCecVampireStatus,
  proveCecWithVampireAdapter,
  type CecVampireProofResult,
} from './vampireAdapter';
import { CecZ3Adapter, mapCecZ3Status, proveCecWithZ3Adapter } from './z3Adapter';
import {
  CecProblemParseError,
  CecProblemParser,
  CecTptpParser,
  detectProblemFormat,
  parseCecProblemString,
} from './problemParser';
import { CecTptpConverter, cecFormulaToTptp, createCecTptpProblem } from './tptpUtils';

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
    expect(parser.formulas.map((formula) => formula.name)).toEqual([
      'ax1',
      'h1',
      'goal',
      'neg_goal',
    ]);
  });

  it('keeps nested TPTP formulas and annotations intact', () => {
    const problem = parseCecProblemString(`
      fof(nested, axiom, (![X] : (human(X) => mortal(X))), file('source.p', nested)).
      fof(goal, theorem, mortal(socrates)).
    `);

    expect(problem.assumptions).toEqual(['(![X] : (human(X) => mortal(X)))']);
    expect(problem.goals).toEqual(['mortal(socrates)']);
    expect((problem.metadata?.formulas as Array<{ annotations?: string }>)[0].annotations).toBe(
      "file('source.p', nested)",
    );
  });

  it('parses typed TPTP formulas and include selections without filesystem fallback', () => {
    const parser = new CecTptpParser();
    const problem = parser.parseString(
      `
      include('Axioms/Modal.ax', [mvalid, mbox]).
      tff(person_type, type, person: $tType).
      tff(alice_type, type, alice: person).
      tff(ax, axiom, ! [X: person] : (human(X) => mortal(X))).
      thf(goal, conjecture, (mortal @ alice)).
    `,
      'typed-tptp',
    );

    expect(detectProblemFormat('tff(person_type, type, person: $tType).')).toBe('tptp');
    expect(problem.assumptions).toEqual(['! [X: person] : (human(X) => mortal(X))']);
    expect(problem.goals).toEqual(['(mortal @ alice)']);
    expect(problem.metadata).toMatchObject({
      includes: ['Axioms/Modal.ax'],
      includeDirectives: [{ path: 'Axioms/Modal.ax', selections: ['mvalid', 'mbox'] }],
      includeResolution: 'browser-native-metadata-only',
      totalFormulas: 4,
    });
    expect(problem.metadata?.declarations as Array<{ name: string; formula: string }>).toEqual([
      { kind: 'tff', name: 'person_type', role: 'type', formula: 'person: $tType' },
      { kind: 'tff', name: 'alice_type', role: 'type', formula: 'alice: person' },
    ]);
  });

  it('parses custom ShadowProver problem format with logic sections', () => {
    const problem = parseCecProblemString(
      `
      # browser-native custom format
      LOGIC: S4

      ASSUMPTIONS:
      (always (implies (p) (q)))
      (always (p))

      GOALS:
      (always (q))
    `,
      'custom',
    );

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
    expect(() => parseCecProblemString('fof(ax, axiom, (p => q).', 'tptp')).toThrow(
      CecProblemParseError,
    );
    expect(() => parseCecProblemString('fof(ax, axiom).', 'tptp')).toThrow(
      'requires name, role, and formula',
    );
    expect(() => parseCecProblemString("include('Axioms/SET001.ax', ax).", 'tptp')).toThrow(
      'include selections must be a list',
    );
  });

  it('formats CEC expressions into browser-native TPTP utility output', () => {
    const quantifiedAxiom: CecExpression = {
      kind: 'quantified',
      quantifier: 'forall',
      variable: 'x',
      expression: {
        kind: 'binary',
        operator: 'implies',
        left: { kind: 'application', name: 'human', args: [{ kind: 'atom', name: 'x' }] },
        right: {
          kind: 'unary',
          operator: 'O',
          expression: {
            kind: 'application',
            name: 'comply-with',
            args: [{ kind: 'atom', name: 'x' }],
          },
        },
      },
    };
    expect(cecFormulaToTptp(quantifiedAxiom, 'axiom', 'Ax 1')).toBe(
      'fof(ax_1, axiom, (! [X] : (human(x) => obligated(comply_with(x))))).',
    );
    const axiom: CecExpression = {
      kind: 'application',
      name: 'permitted',
      args: [{ kind: 'atom', name: 'ada' }],
    };
    const goal: CecExpression = {
      kind: 'application',
      name: 'compliant',
      args: [{ kind: 'atom', name: 'ada' }],
    };
    const converter = new CecTptpConverter();

    expect(createCecTptpProblem(goal, [axiom], { problemName: 'policy_case' })).toBe(
      [
        '% Problem: policy_case',
        '% Generated by CEC TPTP utilities',
        '',
        'fof(ax1, axiom, permitted(ada)).',
        '',
        'fof(goal, conjecture, compliant(ada)).',
      ].join('\n'),
    );
    expect(converter.convertFormula(goal)).toMatchObject({
      role: 'conjecture',
      name: 'f1',
      tptp: 'fof(f1, conjecture, compliant(ada)).',
    });
    expect(converter.createProblem(goal, [], 'single')).toContain('% Problem: single');
  });

  it('ports the CEC Vampire adapter as browser-native TPTP compatibility metadata', () => {
    const adapter = new CecVampireAdapter({ problemName: 'policy_vampire_case' });
    const result = adapter.prove('(comply_with ada code)', [
      '(comply_with ada code)',
    ]) as CecVampireProofResult;

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(comply_with ada code)',
      method: 'vampire-compatible:cec-forward-chaining',
    });
    expect(result.vampire).toMatchObject({
      adapter: 'browser-native-cec-vampire-adapter',
      sourcePythonModule: 'logic/CEC/provers/vampire_adapter.py',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      command: null,
      statusMapping: 'Theorem',
    });
    expect(result.vampire.tptpProblem).toContain('% Problem: policy_vampire_case');
    expect(result.vampire.tptpAxioms).toEqual(['fof(vampire_ax1, axiom, comply_with(ada, code)).']);
    expect(result.vampire.tptpTheorem).toBe(
      'fof(vampire_goal, conjecture, comply_with(ada, code)).',
    );
    expect(mapCecVampireStatus('timeout')).toBe('ResourceOut');
  });

  it('fails closed for unproved Vampire-compatible CEC requests without delegation', () => {
    const result = proveCecWithVampireAdapter('(comply_with ada code)', ['(subject_to ada code)']);

    expect(result.status).toBe('unknown');
    expect(result.vampire.statusMapping).toBe('GaveUp');
    expect(result.vampire.warnings[0]).toContain('local TypeScript CEC engine');
    expect(result.vampire.command).toBeNull();
  });

  it('ports the CEC Z3 adapter as browser-native SMT-LIB compatibility metadata', () => {
    const adapter = new CecZ3Adapter({ logic: 'UF' });
    const result = adapter.prove('(comply_with ada code)', ['(comply_with ada code)']);

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(comply_with ada code)',
      method: 'z3-compatible:cec-forward-chaining',
    });
    expect(result.z3).toMatchObject({
      adapter: 'browser-native-cec-z3-adapter',
      sourcePythonModule: 'logic/CEC/provers/z3_adapter.py',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      command: null,
      checkSatStatus: 'unsat',
    });
    expect(result.z3.smtLibProblem).toContain('(set-logic UF)');
    expect(result.z3.smtLibProblem).toContain('(declare-fun comply_with (Entity Entity) Bool)');
    expect(result.z3.smtLibAxioms).toEqual(['(assert (comply_with ada code))']);
    expect(result.z3.smtLibNegatedTheorem).toBe('(assert (not (comply_with ada code)))');
    expect(mapCecZ3Status('disproved')).toBe('sat');
  });

  it('fails closed for unproved Z3-compatible CEC requests without Python or server delegation', () => {
    const result = proveCecWithZ3Adapter('(comply_with ada code)', ['(subject_to ada code)']);

    expect(result.status).toBe('unknown');
    expect(result.z3.checkSatStatus).toBe('unknown');
    expect(result.z3.warnings[0]).toContain('local TypeScript CEC engine');
    expect(result.z3.command).toBeNull();
    expect(result.z3.smtLibProblem).toContain('(check-sat)');
  });
});
