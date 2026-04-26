import {
  DeonticKnowledgeBase,
  actionToString,
  conjunction,
  implication,
  intervalContains,
  partyToString,
  predicate,
  resolvedEnd,
  type Action,
  type Party,
} from './knowledgeBase';

describe('DeonticKnowledgeBase', () => {
  const tenant: Party = { name: 'Tenant', role: 'resident', entityId: 'tenant' };
  const payRent: Action = { verb: 'pay', objectNoun: 'rent', actionId: 'pay_rent' };

  it('models parties, actions, intervals, and propositions', () => {
    const start = new Date('2026-01-01T00:00:00Z');
    const interval = { start, durationDays: 10 };

    expect(partyToString(tenant)).toBe('Tenant (resident)');
    expect(actionToString(payRent)).toBe('pay rent');
    expect(resolvedEnd(interval)?.toISOString()).toBe('2026-01-11T00:00:00.000Z');
    expect(intervalContains(interval, new Date('2026-01-05T00:00:00Z'))).toBe(true);
    expect(conjunction(predicate('A'), predicate('B')).evaluate({ 'A()': true, 'B()': false })).toBe(false);
    expect(implication(predicate('A'), predicate('B')).evaluate({ 'A()': true, 'B()': false })).toBe(false);
  });

  it('stores statements and checks compliance', () => {
    const kb = new DeonticKnowledgeBase();
    kb.addStatement({
      modality: 'O',
      actor: tenant,
      action: payRent,
      timeInterval: { start: new Date('2026-01-01T00:00:00Z'), durationDays: 5 },
    });

    expect(kb.checkCompliance(tenant, payRent, new Date('2026-01-03T00:00:00Z'))).toMatchObject({
      compliant: true,
      message: expect.stringContaining('complies with obligation'),
    });
    expect(kb.checkCompliance(tenant, payRent, new Date('2026-01-10T00:00:00Z'))).toMatchObject({
      compliant: false,
      message: expect.stringContaining('outside the obligation window'),
    });
  });

  it('infers rule-backed statements from facts and prioritizes prohibitions', () => {
    const kb = new DeonticKnowledgeBase();
    kb.addRule(predicate('PermitDenied'), { modality: 'F', actor: tenant, action: payRent });
    kb.addFact('PermitDenied()', true);

    expect(kb.inferStatements()).toHaveLength(1);
    expect(kb.checkCompliance(tenant, payRent, new Date())).toMatchObject({
      compliant: false,
      message: expect.stringContaining('violates prohibition'),
    });
  });
});
