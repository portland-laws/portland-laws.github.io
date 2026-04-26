export type KnowledgeDeonticModality = 'O' | 'P' | 'F' | 'OPT';
export type KnowledgeTemporalOperator = 'before' | 'after' | 'coincident' | 'during' | 'overlaps' | 'starts' | 'finishes' | 'equals';
export type KnowledgeLogicalOperator = 'and' | 'or' | 'not' | 'implies' | 'iff' | 'forall' | 'exists';

export interface TimeInterval {
  start?: Date;
  end?: Date;
  durationDays?: number;
}

export interface Party {
  name: string;
  role: string;
  entityId: string;
}

export interface Action {
  verb: string;
  objectNoun: string;
  actionId: string;
}

export interface Proposition {
  kind: 'predicate' | 'and' | 'or' | 'not' | 'implies';
  evaluate(model: Record<string, unknown>): boolean;
  toString(): string;
}

export interface DeonticStatement {
  modality: KnowledgeDeonticModality;
  actor: Party;
  action: Action;
  recipient?: Party;
  timeInterval?: TimeInterval;
  condition?: Proposition;
}

export function resolvedEnd(interval: TimeInterval): Date | undefined {
  if (interval.end) return interval.end;
  if (interval.start && interval.durationDays !== undefined) {
    return new Date(interval.start.getTime() + interval.durationDays * 24 * 60 * 60 * 1000);
  }
  return undefined;
}

export function intervalContains(interval: TimeInterval, atTime: Date): boolean {
  const end = resolvedEnd(interval);
  if (interval.start && atTime < interval.start) return false;
  if (end && atTime > end) return false;
  return true;
}

export function partyToString(party: Party): string {
  return `${party.name} (${party.role})`;
}

export function actionToString(action: Action): string {
  return `${action.verb} ${action.objectNoun}`.trim();
}

export function predicate(name: string, args: unknown[] = []): Proposition {
  return {
    kind: 'predicate',
    evaluate(model) {
      return Boolean(model[`${name}(${args.map(String).join(', ')})`]);
    },
    toString() {
      return `${name}(${args.map(String).join(', ')})`;
    },
  };
}

export function conjunction(left: Proposition, right: Proposition): Proposition {
  return {
    kind: 'and',
    evaluate(model) {
      return left.evaluate(model) && right.evaluate(model);
    },
    toString() {
      return `(${left} and ${right})`;
    },
  };
}

export function disjunction(left: Proposition, right: Proposition): Proposition {
  return {
    kind: 'or',
    evaluate(model) {
      return left.evaluate(model) || right.evaluate(model);
    },
    toString() {
      return `(${left} or ${right})`;
    },
  };
}

export function negation(prop: Proposition): Proposition {
  return {
    kind: 'not',
    evaluate(model) {
      return !prop.evaluate(model);
    },
    toString() {
      return `not (${prop})`;
    },
  };
}

export function implication(antecedent: Proposition, consequent: Proposition): Proposition {
  return {
    kind: 'implies',
    evaluate(model) {
      return !antecedent.evaluate(model) || consequent.evaluate(model);
    },
    toString() {
      return `(${antecedent} -> ${consequent})`;
    },
  };
}

export class DeonticKnowledgeBase {
  readonly statements = new Map<string, DeonticStatement>();
  readonly rules: Array<{ condition: Proposition; statement: DeonticStatement }> = [];
  readonly facts: Record<string, boolean> = {};
  readonly derivedStatements = new Map<string, DeonticStatement>();

  addStatement(statement: DeonticStatement): void {
    this.statements.set(statementKey(statement), statement);
  }

  addRule(condition: Proposition, statement: DeonticStatement): void {
    this.rules.push({ condition, statement });
  }

  addFact(factName: string, value = true): void {
    this.facts[factName] = value;
  }

  inferStatements(): DeonticStatement[] {
    const derived = new Map(this.statements);
    let changed = true;
    while (changed) {
      changed = false;
      for (const rule of this.rules) {
        const key = statementKey(rule.statement);
        if (rule.condition.evaluate(this.facts) && !derived.has(key)) {
          derived.set(key, rule.statement);
          changed = true;
        }
      }
    }
    this.derivedStatements.clear();
    for (const [key, statement] of derived.entries()) {
      this.derivedStatements.set(key, statement);
    }
    return [...derived.values()];
  }

  checkCompliance(actor: Party, action: Action, atTime: Date): { compliant: boolean; message: string } {
    const statements = this.derivedStatements.size > 0 ? [...this.derivedStatements.values()] : [...this.statements.values()];
    const matching = statements.filter((statement) => sameParty(statement.actor, actor) && sameAction(statement.action, action));
    for (const statement of matching) {
      if (statement.modality === 'F') {
        return { compliant: false, message: `${partyToString(actor)} violates prohibition against ${actionToString(action)}` };
      }
      if (statement.modality === 'O') {
        if (statement.timeInterval && !intervalContains(statement.timeInterval, atTime)) {
          return { compliant: false, message: `${partyToString(actor)} is outside the obligation window for ${actionToString(action)}` };
        }
        return { compliant: true, message: `${partyToString(actor)} complies with obligation to ${actionToString(action)}` };
      }
    }
    return { compliant: true, message: `No active contrary deontic rule found for ${partyToString(actor)} and ${actionToString(action)}` };
  }
}

function statementKey(statement: DeonticStatement): string {
  return [statement.modality, statement.actor.entityId, statement.action.actionId, statement.recipient?.entityId ?? '', statement.condition?.toString() ?? ''].join('|');
}

function sameParty(left: Party, right: Party): boolean {
  return left.entityId === right.entityId;
}

function sameAction(left: Action, right: Action): boolean {
  return left.actionId === right.actionId;
}
