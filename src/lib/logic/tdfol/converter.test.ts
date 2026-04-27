import { parseTdfolFormula } from './parser';
import {
  convertTdfolBatch,
  convertTdfolFormula,
  tdfolToFol,
  tdfolToTptp,
} from './converter';

describe('TDFOL converter', () => {
  it('converts parsed formulas back to stable TDFOL output with metadata', () => {
    const result = convertTdfolFormula('forall x. Resident(x) -> Tenant(x)', 'tdfol');

    expect(result.output).toBe('∀x ((Resident(x)) → (Tenant(x)))');
    expect(result.metadata).toMatchObject({
      target: 'tdfol',
      quantifierCount: 1,
      predicateCount: 2,
      operatorCount: 2,
      freeVariables: [],
    });
  });

  it('projects temporal and deontic operators for FOL output with explicit warnings', () => {
    const result = convertTdfolFormula('always(O(Comply(x)))', 'fol');

    expect(result.output).toBe('Comply(x)');
    expect(result.warnings).toEqual([
      'Projected temporal operator ALWAYS away for FOL output.',
      'Projected deontic operator OBLIGATION away for FOL output.',
    ]);
    expect(result.metadata).toMatchObject({ containsTemporal: true, containsDeontic: true });
  });

  it('converts TDFOL to DCEC s-expression syntax', () => {
    const result = convertTdfolFormula('forall x. O(Comply(x))', 'dcec');

    expect(result.output).toBe('(forall x (O (Comply x)))');
  });

  it('converts TDFOL to a local TPTP-style formula string', () => {
    const formula = parseTdfolFormula('forall x. Resident(x) -> O(Comply(x))');

    expect(tdfolToTptp(formula)).toBe('![X]:((resident(X) => obligation(comply(X))))');
    expect(convertTdfolFormula(formula, 'tptp').output).toBe('fof(tdfol_formula, axiom, ![X]:((resident(X) => obligation(comply(X))))).');
  });

  it('converts formulas to JSON and supports batch conversion', () => {
    const json = convertTdfolFormula('Permit(Alice)', 'json').output as Record<string, unknown>;

    expect(json).toMatchObject({
      formatted: 'Permit(Alice)',
      freeVariables: [],
    });
    expect(tdfolToFol(parseTdfolFormula('Permit(Alice)'))).toBe('Permit(Alice)');
    expect(convertTdfolBatch(['Permit(Alice)', 'O(Comply(x))'], 'dcec').map((result) => result.output)).toEqual([
      '(Permit Alice)',
      '(O (Comply x))',
    ]);
  });
});
