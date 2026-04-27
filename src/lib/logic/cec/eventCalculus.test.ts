import {
  CecEventCalculus,
  CecTimePoint,
  createCecEventTerm,
  createCecFluentTerm,
} from './eventCalculus';
import { parseCecExpression } from './parser';

describe('CEC event calculus', () => {
  it('records event occurrences and evaluates initiation/termination rules', () => {
    const ec = new CecEventCalculus();
    const turnOn = createCecEventTerm('turn_on_light');
    const turnOff = createCecEventTerm('turn_off_light');
    const lightOn = createCecFluentTerm('light_on');

    ec.addInitiationRule(turnOn, lightOn);
    ec.addTerminationRule(turnOff, lightOn);
    ec.recordEvent(turnOn, 2);
    ec.recordEvent(turnOff, 5);

    expect(ec.happens(turnOn, 2)).toBe(true);
    expect(ec.happens(turnOn, 3)).toBe(false);
    expect(ec.initiates(turnOn, lightOn, 2)).toBe(true);
    expect(ec.terminates(turnOff, lightOn, 5)).toBe(true);
  });

  it('implements Python-compatible discrete HoldsAt and Clipped semantics', () => {
    const ec = new CecEventCalculus();
    ec.addInitiationRule('turn_on', 'light_on');
    ec.addTerminationRule('turn_off', 'light_on');
    ec.recordEvent('turn_on', 2);
    ec.recordEvent('turn_off', 5);

    expect(ec.holdsAt('light_on', 1)).toBe(false);
    expect(ec.holdsAt('light_on', 2)).toBe(false);
    expect(ec.holdsAt('light_on', 3)).toBe(true);
    expect(ec.holdsAt('light_on', 5)).toBe(true);
    expect(ec.holdsAt('light_on', 6)).toBe(false);
    expect(ec.clipped(3, 'light_on', 7)).toBe(true);
  });

  it('supports initially true fluents, all-fluent queries, and change timelines', () => {
    const ec = new CecEventCalculus();
    ec.setInitiallyTrue('door_closed');
    ec.addTerminationRule('open_door', 'door_closed');
    ec.recordEvent('open_door', 3);

    expect(ec.holdsAt('door_closed', 0)).toBe(true);
    expect(ec.holdsAt('door_closed', 4)).toBe(false);
    expect(ec.getAllFluentsAt(2)).toEqual([createCecFluentTerm('door_closed')]);
    expect(ec.getTimeline('door_closed', 5)).toEqual([
      { time: 0, holds: true },
      { time: 4, holds: false },
    ]);
  });

  it('supports release rules as explicit inertia breaks', () => {
    const ec = new CecEventCalculus();
    ec.setInitiallyTrue('permit_active');
    ec.addReleaseRule('suspend_permit', 'permit_active');
    ec.addInitiationRule('reinstate_permit', 'permit_active');
    ec.recordEvent('suspend_permit', 2);

    expect(ec.releases('suspend_permit', 'permit_active', 2)).toBe(true);
    expect(ec.releasedAt('permit_active', 3)).toBe(true);
    expect(ec.holdsAt('permit_active', 3)).toBe(false);

    ec.recordEvent('reinstate_permit', 5);
    expect(ec.releasedAt('permit_active', 6)).toBe(false);
    expect(ec.holdsAt('permit_active', 6)).toBe(true);
  });

  it('loads and evaluates CEC event-calculus predicates from parsed expressions', () => {
    const ec = new CecEventCalculus();
    [
      '(Initiates (turn_on light) (on light))',
      '(Terminates (turn_off light) (on light))',
      '(Happens (turn_on light) 2)',
      '(Happens (turn_off light) 5)',
    ].forEach((source) => expect(ec.loadFact(parseCecExpression(source))).toBe(true));

    expect(ec.evaluatePredicate(parseCecExpression('(HoldsAt (on light) 3)'))).toBe(true);
    expect(ec.evaluatePredicate(parseCecExpression('(Clipped 3 (on light) 7)'))).toBe(true);
    expect(ec.evaluatePredicate(parseCecExpression('(Happens (turn_on light) t2)'))).toBe(true);
    expect(ec.evaluatePredicate(parseCecExpression('(not (HoldsAt (on light) 3))'))).toBeUndefined();
  });

  it('reports statistics, clears state, and validates time values', () => {
    const ec = new CecEventCalculus();
    ec.addInitiationRule('turn_on', 'light_on');
    ec.recordEvent('turn_on', 1);
    ec.holdsAt('light_on', 2);

    expect(ec.getStatistics()).toMatchObject({
      eventOccurrences: 1,
      initiationRules: 1,
      cachedHoldsAtQueries: 1,
    });

    expect(new CecTimePoint(3).toString()).toBe('t3');
    expect(() => ec.recordEvent('bad_time', -1)).toThrow('non-negative integer');
    expect(() => new CecTimePoint(1.5)).toThrow('non-negative integer');

    ec.clear();
    expect(ec.getStatistics()).toMatchObject({
      eventOccurrences: 0,
      initiationRules: 0,
      cachedHoldsAtQueries: 0,
    });
  });
});
