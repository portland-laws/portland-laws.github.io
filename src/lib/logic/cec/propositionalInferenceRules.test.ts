import {
  applyPropositionalRule,
  propositionalAnd,
  propositionalAtom,
  propositionalIff,
  propositionalImplies,
  propositionalNot,
  propositionalOr,
} from './propositionalInferenceRules';

describe('propositionalInferenceRules', () => {
  const p = propositionalAtom('P');
  const q = propositionalAtom('Q');
  const r = propositionalAtom('R');

  it('applies core Python CEC propositional rules deterministically', () => {
    expect(
      applyPropositionalRule({ rule: 'modus_ponens', premises: [p, propositionalImplies(p, q)] }),
    ).toEqual({
      ok: true,
      rule: 'modus_ponens',
      conclusion: q,
    });
    expect(
      applyPropositionalRule({
        rule: 'hypothetical_syllogism',
        premises: [propositionalImplies(p, q), propositionalImplies(q, r)],
      }).conclusion,
    ).toEqual(propositionalImplies(p, r));
    expect(
      applyPropositionalRule({
        rule: 'disjunctive_syllogism',
        premises: [propositionalOr(p, q), propositionalNot(p)],
      }).conclusion,
    ).toEqual(q);
    expect(
      applyPropositionalRule({
        rule: 'double_negation_elimination',
        premises: [propositionalNot(propositionalNot(p))],
      }).conclusion,
    ).toEqual(p);
  });

  it('supports conjunction and biconditional elimination contracts', () => {
    expect(
      applyPropositionalRule({ rule: 'conjunction_introduction', premises: [p, q] }).conclusion,
    ).toEqual(propositionalAnd(p, q));
    expect(
      applyPropositionalRule({
        rule: 'conjunction_elimination_left',
        premises: [propositionalAnd(p, q)],
      }).conclusion,
    ).toEqual(p);
    expect(
      applyPropositionalRule({
        rule: 'conjunction_elimination_right',
        premises: [propositionalAnd(p, q)],
      }).conclusion,
    ).toEqual(q);
    expect(
      applyPropositionalRule({
        rule: 'biconditional_elimination_left',
        premises: [propositionalIff(p, q)],
      }).conclusion,
    ).toEqual(propositionalImplies(p, q));
  });

  it('validates targets and fails closed for malformed browser inputs', () => {
    expect(
      applyPropositionalRule({
        rule: 'modus_ponens',
        premises: [p, propositionalImplies(p, q)],
        target: q,
      }).ok,
    ).toBe(true);
    expect(
      applyPropositionalRule({
        rule: 'modus_ponens',
        premises: [p, propositionalImplies(p, q)],
        target: r,
      }).ok,
    ).toBe(false);
    expect(
      applyPropositionalRule({
        rule: 'modus_ponens',
        premises: [{ kind: 'atom', args: [] }, propositionalImplies(p, q)],
      }).ok,
    ).toBe(false);
    expect(applyPropositionalRule({ rule: 'conjunction_elimination_left', premises: [p] }).ok).toBe(
      false,
    );
  });
});
