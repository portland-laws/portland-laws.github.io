import { CecFluent, CecFluentManager, createCecEvent } from './fluents';

describe('CEC fluents', () => {
  it('creates fluents with Python-style defaults and persistence behavior', () => {
    const lightOn = new CecFluent('light_on', 'boolean');
    const temperature = new CecFluent('temperature', 'numerical', { persistenceRule: 'decaying', defaultValue: 20 });
    const buttonPress = new CecFluent('button_press', 'boolean', { persistenceRule: 'transient' });

    expect(lightOn).toMatchObject({
      name: 'light_on',
      fluentType: 'boolean',
      persistenceRule: 'inertial',
      defaultValue: false,
    });
    expect(temperature.defaultValue).toBe(20);
    expect(lightOn.persists(5, 10)).toBe(true);
    expect(buttonPress.persists(5, 6)).toBe(false);
  });

  it('applies event transitions and preserves inertial fluents across time', () => {
    const manager = new CecFluentManager();
    const lightOn = new CecFluent('light_on', 'boolean');
    const doorOpen = new CecFluent('door_open', 'boolean');
    manager.addFluent(lightOn);
    manager.addFluent(doorOpen);

    expect(manager.getFluentValue(lightOn, 0)).toBe(false);
    manager.applyTransition(createCecEvent('turn_on_light'), 2, new Map([[lightOn, true]]));
    manager.applyTransition('open_door', 5, { door_open: true });
    manager.applyTransition('turn_off_light', 8, { light_on: false });

    expect(manager.getFluentValue(lightOn, 1)).toBe(false);
    expect(manager.getFluentValue(lightOn, 3)).toBe(true);
    expect(manager.getFluentValue(doorOpen, 3)).toBe(false);
    expect(manager.getFluentValue(doorOpen, 6)).toBe(true);
    expect(manager.getFluentValue(lightOn, 10)).toBe(false);
  });

  it('handles transient fluents separately from inertial frame persistence', () => {
    const manager = new CecFluentManager();
    const buttonPress = new CecFluent('button_press', 'boolean', { persistenceRule: 'transient' });
    const alarmActive = new CecFluent('alarm_active', 'boolean');
    manager.addFluent(buttonPress);
    manager.addFluent(alarmActive);

    manager.setFluentValue(buttonPress, true, 5);
    manager.setFluentValue(alarmActive, true, 5);

    expect(manager.getFluentValue(buttonPress, 5)).toBe(true);
    expect(manager.getFluentValue(alarmActive, 5)).toBe(true);
    expect(manager.getFluentValue(buttonPress, 6)).toBe(false);
    expect(manager.getFluentValue(alarmActive, 6)).toBe(true);
  });

  it('supports custom conflict resolution for same-time writes', () => {
    const manager = new CecFluentManager();
    const counter = new CecFluent('counter', 'numerical');
    manager.addFluent(counter);
    manager.setConflictResolver((_fluent, previous, next) => Math.max(Number(previous), Number(next)));

    manager.setFluentValue(counter, 10, 5);
    manager.setFluentValue(counter, 3, 5);
    manager.setFluentValue(counter, 20, 5);

    expect(manager.getFluentValue(counter, 5)).toBe(20);
  });

  it('supports conditional persistence and complete state snapshots', () => {
    const manager = new CecFluentManager();
    const permitActive = new CecFluent('permit_active', 'boolean', { persistenceRule: 'conditional' });
    const noticeSent = new CecFluent('notice_sent', 'boolean');
    manager.addFluent(permitActive);
    manager.addFluent(noticeSent);
    manager.setPersistenceCondition((_fluent, from, to) => to - from <= 3);

    manager.setFluentValue(permitActive, true, 1);
    manager.setFluentValue(noticeSent, true, 1);

    expect(manager.getFluentValue(permitActive, 3)).toBe(true);
    expect(manager.getFluentValue(permitActive, 6)).toBe(false);
    expect(manager.getState(3).get(noticeSent)).toBe(true);
  });

  it('returns timelines, statistics, and clears history', () => {
    const manager = new CecFluentManager();
    const lightOn = new CecFluent('light_on', 'boolean');
    manager.addFluent(lightOn);
    manager.setFluentValue(lightOn, true, 2);
    manager.setFluentValue(lightOn, false, 5);

    expect(manager.getTimeline(lightOn, 7)).toEqual([
      { time: 0, value: false },
      { time: 2, value: true },
      { time: 5, value: false },
    ]);
    expect(manager.getStatistics()).toMatchObject({
      total_fluents: 1,
      time_points_recorded: 2,
      total_state_entries: 2,
    });

    manager.clearHistory();
    expect(manager.getStatistics()).toMatchObject({ time_points_recorded: 0, total_state_entries: 0 });
  });

  it('validates duplicate fluents, unknown fluents, and invalid times', () => {
    const manager = new CecFluentManager();
    const lightOn = new CecFluent('light_on', 'boolean');
    manager.addFluent(lightOn);

    expect(() => manager.addFluent(new CecFluent('light_on', 'boolean'))).toThrow("already registered");
    expect(() => manager.getFluentValue('missing', 0)).toThrow("not registered");
    expect(() => manager.setFluentValue(lightOn, true, -1)).toThrow('non-negative integer');
  });
});
