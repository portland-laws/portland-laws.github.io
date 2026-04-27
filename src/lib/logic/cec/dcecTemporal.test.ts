import { LogicValidationError } from '../errors';
import { dcecAtom, dcecNegation } from './dcecCore';
import {
  DcecTemporalEvaluationFormula,
  DcecTemporalEvaluationOperator,
  DcecTemporalState,
  dcecAlways,
  dcecEventually,
  dcecNext,
  dcecSince,
  dcecUntil,
  dcecYesterday,
} from './dcecTemporal';

const p = dcecAtom('p');
const q = dcecAtom('q');

describe('DCEC temporal evaluation parity helpers', () => {
  it('evaluates state valuations with false for missing propositions', () => {
    const state = new DcecTemporalState(0, { p: true }, { source: 'fixture' });

    expect(state.evaluate('p')).toBe(true);
    expect(state.evaluate('q')).toBe(false);
    expect(state.metadata).toEqual({ source: 'fixture' });
    expect(state.toString()).toContain('State(t=0');
  });

  it('evaluates always and eventually over finite future traces', () => {
    const allP = [
      new DcecTemporalState(0, { p: true }),
      new DcecTemporalState(1, { p: true }),
      new DcecTemporalState(2, { p: true, q: true }),
    ];

    expect(dcecAlways(p).evaluate(allP, 0)).toBe(true);
    expect(dcecEventually(q).evaluate(allP, 0)).toBe(true);
    expect(dcecAlways(q).evaluate(allP, 0)).toBe(false);
    expect(dcecEventually(q).evaluate(allP, 2)).toBe(true);
  });

  it('evaluates next and yesterday at trace boundaries', () => {
    const trace = [
      new DcecTemporalState(0, { p: true, q: false }),
      new DcecTemporalState(1, { p: false, q: true }),
    ];

    expect(dcecNext(q).evaluate(trace, 0)).toBe(true);
    expect(dcecNext(q).evaluate(trace, 1)).toBe(false);
    expect(dcecYesterday(p).evaluate(trace, 1)).toBe(true);
    expect(dcecYesterday(p).evaluate(trace, 0)).toBe(false);
  });

  it('evaluates until with Python-compatible finite trace semantics', () => {
    const trace = [
      new DcecTemporalState(0, { p: true, q: false }),
      new DcecTemporalState(1, { p: true, q: false }),
      new DcecTemporalState(2, { p: false, q: true }),
    ];
    const brokenTrace = [
      new DcecTemporalState(0, { p: true, q: false }),
      new DcecTemporalState(1, { p: false, q: false }),
      new DcecTemporalState(2, { p: true, q: true }),
    ];

    expect(dcecUntil(p, q).evaluate(trace, 0)).toBe(true);
    expect(dcecUntil(p, q).evaluate(brokenTrace, 0)).toBe(false);
  });

  it('evaluates since with Python-compatible finite trace semantics', () => {
    const trace = [
      new DcecTemporalState(0, { p: false, q: true }),
      new DcecTemporalState(1, { p: true, q: false }),
      new DcecTemporalState(2, { p: true, q: false }),
    ];
    const brokenTrace = [
      new DcecTemporalState(0, { p: false, q: true }),
      new DcecTemporalState(1, { p: false, q: false }),
      new DcecTemporalState(2, { p: true, q: false }),
    ];

    expect(dcecSince(p, q).evaluate(trace, 2)).toBe(true);
    expect(dcecSince(p, q).evaluate(brokenTrace, 2)).toBe(false);
  });

  it('evaluates negated atomic DCEC formulas through state valuations', () => {
    const trace = [
      new DcecTemporalState(0, { q: false }),
      new DcecTemporalState(1, { q: false }),
    ];

    expect(dcecAlways(dcecNegation(q)).evaluate(trace, 0)).toBe(true);
    expect(dcecEventually(dcecNegation(q)).evaluate(trace, 0)).toBe(true);
  });

  it('renders unary and binary temporal formulas using native operator symbols', () => {
    expect(dcecYesterday(p).toString()).toBe('Y(p())');
    expect(dcecUntil(p, q).toString()).toBe('(p() U q())');
  });

  it('validates operator arity and evaluation bounds', () => {
    expect(() => new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.UNTIL, p)).toThrow(LogicValidationError);
    expect(() => new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.ALWAYS, p, q)).toThrow(LogicValidationError);
    expect(() => dcecAlways(p).evaluate([])).toThrow(LogicValidationError);
    expect(() => dcecAlways(p).evaluate([new DcecTemporalState(0, { p: true })], 1)).toThrow(LogicValidationError);
  });
});
