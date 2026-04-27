export type CecFluentType = 'boolean' | 'numerical' | 'categorical' | 'relational';
export type CecPersistenceRule = 'inertial' | 'transient' | 'decaying' | 'conditional';

export interface CecFluentOptions {
  persistenceRule?: CecPersistenceRule;
  defaultValue?: unknown;
  metadata?: Record<string, unknown>;
}

export interface CecEvent {
  name: string;
  metadata?: Record<string, unknown>;
}

export type CecPersistenceCondition = (fluent: CecFluent, fromTime: number, toTime: number) => boolean;
export type CecConflictResolver = (fluent: CecFluent, previousValue: unknown, nextValue: unknown) => unknown;
export type CecFluentEffects = Map<CecFluent | string, unknown> | Record<string, unknown>;

export class CecFluent {
  readonly name: string;
  readonly fluentType: CecFluentType;
  readonly persistenceRule: CecPersistenceRule;
  readonly defaultValue: unknown;
  readonly metadata: Record<string, unknown>;

  constructor(name: string, fluentType: CecFluentType, options: CecFluentOptions = {}) {
    if (!name.trim()) throw new Error('CEC fluent name cannot be empty');
    this.name = name;
    this.fluentType = fluentType;
    this.persistenceRule = options.persistenceRule ?? 'inertial';
    this.defaultValue = options.defaultValue ?? defaultValueForType(fluentType);
    this.metadata = options.metadata ?? {};
  }

  persists(fromTime: number, toTime: number, context: { persistenceCondition?: CecPersistenceCondition } = {}): boolean {
    if (fromTime >= toTime) return false;
    if (this.persistenceRule === 'inertial') return true;
    if (this.persistenceRule === 'transient') return false;
    if (this.persistenceRule === 'decaying') return true;
    if (this.persistenceRule === 'conditional') {
      return context.persistenceCondition?.(this, fromTime, toTime) ?? false;
    }
    return false;
  }

  equals(other: CecFluent): boolean {
    return this.name === other.name;
  }

  toString(): string {
    return `CecFluent(${this.name}, ${this.fluentType})`;
  }
}

export class CecFluentManager {
  readonly fluents = new Map<string, CecFluent>();
  readonly states = new Map<number, Map<string, unknown>>();
  readonly eventEffects = new Map<string, Map<string, unknown>>();
  conflictResolver?: CecConflictResolver;
  persistenceCondition?: CecPersistenceCondition;

  addFluent(fluent: CecFluent): void {
    if (this.fluents.has(fluent.name)) throw new Error(`CEC fluent '${fluent.name}' already registered`);
    this.fluents.set(fluent.name, fluent);
  }

  removeFluent(fluent: CecFluent | string): void {
    const name = this.fluentName(fluent);
    this.fluents.delete(name);
    for (const state of this.states.values()) state.delete(name);
  }

  setFluentValue(fluent: CecFluent | string, value: unknown, time: number): void {
    const registered = this.requireFluent(fluent);
    this.assertTime(time);
    const state = this.states.get(time) ?? new Map<string, unknown>();
    if (state.has(registered.name) && this.conflictResolver) {
      state.set(registered.name, this.conflictResolver(registered, state.get(registered.name), value));
    } else {
      state.set(registered.name, value);
    }
    this.states.set(time, state);
  }

  getFluentValue(fluent: CecFluent | string, time: number): unknown {
    const registered = this.requireFluent(fluent);
    this.assertTime(time);
    const explicit = this.states.get(time)?.get(registered.name);
    if (this.states.get(time)?.has(registered.name)) return explicit;

    if (registered.persistenceRule === 'inertial' || registered.persistenceRule === 'decaying' || registered.persistenceRule === 'conditional') {
      for (let previousTime = time - 1; previousTime >= 0; previousTime -= 1) {
        const previousState = this.states.get(previousTime);
        if (!previousState?.has(registered.name)) continue;
        if (registered.persists(previousTime, time, { persistenceCondition: this.persistenceCondition })) {
          return previousState.get(registered.name);
        }
        break;
      }
    }

    return registered.defaultValue;
  }

  getState(time: number): Map<CecFluent, unknown> {
    this.assertTime(time);
    const state = new Map<CecFluent, unknown>();
    for (const fluent of [...this.fluents.values()].sort((left, right) => left.name.localeCompare(right.name))) {
      state.set(fluent, this.getFluentValue(fluent, time));
    }
    return state;
  }

  applyTransition(event: CecEvent | string, time: number, effects: CecFluentEffects): void {
    this.assertTime(time);
    const normalized = this.normalizeEffects(effects);
    this.eventEffects.set(eventName(event), normalized);
    for (const [fluentName, value] of normalized.entries()) {
      if (!this.fluents.has(fluentName)) continue;
      this.setFluentValue(fluentName, value, time);
    }
  }

  setConflictResolver(resolver: CecConflictResolver): void {
    this.conflictResolver = resolver;
  }

  setPersistenceCondition(condition: CecPersistenceCondition): void {
    this.persistenceCondition = condition;
  }

  getTimeline(fluent: CecFluent | string, maxTime: number): Array<{ time: number; value: unknown }> {
    const registered = this.requireFluent(fluent);
    this.assertTime(maxTime);
    const timeline: Array<{ time: number; value: unknown }> = [];
    let previousValue: unknown = Symbol('initial');

    for (let time = 0; time <= maxTime; time += 1) {
      const value = this.getFluentValue(registered, time);
      if (!Object.is(value, previousValue)) {
        timeline.push({ time, value });
        previousValue = value;
      }
    }

    return timeline;
  }

  clearHistory(): void {
    this.states.clear();
    this.eventEffects.clear();
  }

  getStatistics(): Record<string, unknown> {
    return {
      total_fluents: this.fluents.size,
      time_points_recorded: this.states.size,
      total_state_entries: [...this.states.values()].reduce((total, state) => total + state.size, 0),
      event_effects_recorded: this.eventEffects.size,
      has_conflict_resolver: Boolean(this.conflictResolver),
      has_persistence_condition: Boolean(this.persistenceCondition),
    };
  }

  private normalizeEffects(effects: CecFluentEffects): Map<string, unknown> {
    const entries = effects instanceof Map ? [...effects.entries()] : Object.entries(effects);
    return new Map(entries.map(([fluent, value]) => [this.fluentName(fluent), value]));
  }

  private requireFluent(fluent: CecFluent | string): CecFluent {
    const name = this.fluentName(fluent);
    const registered = this.fluents.get(name);
    if (!registered) throw new Error(`CEC fluent '${name}' is not registered`);
    return registered;
  }

  private fluentName(fluent: CecFluent | string): string {
    return typeof fluent === 'string' ? fluent : fluent.name;
  }

  private assertTime(time: number): void {
    if (!Number.isInteger(time) || time < 0) throw new Error('CEC fluent time must be a non-negative integer');
  }
}

export function createCecEvent(name: string, metadata: Record<string, unknown> = {}): CecEvent {
  if (!name.trim()) throw new Error('CEC event name cannot be empty');
  return { name, metadata };
}

function eventName(event: CecEvent | string): string {
  return typeof event === 'string' ? event : event.name;
}

function defaultValueForType(fluentType: CecFluentType): unknown {
  if (fluentType === 'boolean') return false;
  if (fluentType === 'numerical') return 0;
  if (fluentType === 'categorical') return null;
  return null;
}
