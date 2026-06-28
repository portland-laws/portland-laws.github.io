export type KnowledgeDeonticModality = 'O' | 'P' | 'F' | 'OPT';
export type KnowledgeTemporalOperator =
  | 'before'
  | 'after'
  | 'coincident'
  | 'during'
  | 'overlaps'
  | 'starts'
  | 'finishes'
  | 'equals';
export type KnowledgeLogicalOperator =
  | 'and'
  | 'or'
  | 'not'
  | 'implies'
  | 'iff'
  | 'forall'
  | 'exists';

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

export interface DeonticStatementQuery {
  modality?: KnowledgeDeonticModality;
  actor?: Party | string;
  action?: Action | string;
  recipient?: Party | string;
  atTime?: Date;
  includeDerived?: boolean;
}

export interface ComplianceResult {
  compliant: boolean;
  message: string;
  matchedStatements: Array<DeonticStatement>;
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

export function predicate(name: string, args: Array<unknown> = []): Proposition {
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
  private readonly statementOrder: Array<string> = [];
  private readonly actorIndex = new Map<string, Set<string>>();
  private readonly actionIndex = new Map<string, Set<string>>();
  private readonly modalityIndex = new Map<KnowledgeDeonticModality, Set<string>>();

  addStatement(statement: DeonticStatement): void {
    const key = statementKey(statement);
    if (!this.statements.has(key)) {
      this.statementOrder.push(key);
    }
    this.statements.set(key, statement);
    this.indexStatement(key, statement);
  }

  addRule(condition: Proposition, statement: DeonticStatement): void {
    this.rules.push({ condition, statement });
  }

  addFact(factName: string, value = true): void {
    this.facts[factName] = value;
  }

  inferStatements(): DeonticStatement[] {
    const derived = new Map<string, DeonticStatement>(this.statements);
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
      if (!this.statements.has(key)) {
        this.derivedStatements.set(key, statement);
      }
    }
    return [...derived.values()];
  }

  getStatements(query: DeonticStatementQuery = {}): Array<DeonticStatement> {
    const baseKeys = this.candidateKeys(query);
    const baseStatements = baseKeys.map((key) => this.statements.get(key)).filter(isStatement);
    const includeDerived = query.includeDerived !== false;
    const derivedStatements = includeDerived ? [...this.derivedStatements.values()] : [];
    return [...baseStatements, ...derivedStatements].filter((statement) =>
      statementMatchesQuery(statement, query),
    );
  }

  findActiveStatements(
    actor: Party | string,
    action: Action | string,
    atTime: Date,
  ): Array<DeonticStatement> {
    return this.getStatements({ actor, action, atTime, includeDerived: true });
  }

  hasFact(factName: string): boolean {
    return this.facts[factName] === true;
  }

  snapshot(): {
    statements: Array<DeonticStatement>;
    facts: Record<string, boolean>;
    rules: number;
  } {
    return {
      statements: this.getStatements({ includeDerived: true }),
      facts: { ...this.facts },
      rules: this.rules.length,
    };
  }

  checkCompliance(actor: Party, action: Action, atTime: Date): ComplianceResult {
    const matching = this.findActiveStatements(actor, action, atTime);
    for (const statement of matching) {
      if (statement.modality === 'F') {
        return {
          compliant: false,
          message: `${partyToString(actor)} violates prohibition against ${actionToString(action)}`,
          matchedStatements: matching,
        };
      }
      if (statement.modality === 'O') {
        return {
          compliant: true,
          message: `${partyToString(actor)} complies with obligation to ${actionToString(action)}`,
          matchedStatements: matching,
        };
      }
    }
    const inactiveObligation = this.getStatements({
      actor,
      action,
      modality: 'O',
      includeDerived: true,
    }).find((statement) => {
      return (
        statement.timeInterval !== undefined && !intervalContains(statement.timeInterval, atTime)
      );
    });
    if (inactiveObligation) {
      return {
        compliant: false,
        message: `${partyToString(actor)} is outside the obligation window for ${actionToString(action)}`,
        matchedStatements: [inactiveObligation],
      };
    }
    return {
      compliant: true,
      message: `No active contrary deontic rule found for ${partyToString(actor)} and ${actionToString(action)}`,
      matchedStatements: [],
    };
  }

  private candidateKeys(query: DeonticStatementQuery): Array<string> {
    const sets: Array<Set<string>> = [];
    const actorId = typeof query.actor === 'string' ? query.actor : query.actor?.entityId;
    const actionId = typeof query.action === 'string' ? query.action : query.action?.actionId;
    if (actorId !== undefined) sets.push(this.actorIndex.get(actorId) ?? new Set<string>());
    if (actionId !== undefined) sets.push(this.actionIndex.get(actionId) ?? new Set<string>());
    if (query.modality !== undefined)
      sets.push(this.modalityIndex.get(query.modality) ?? new Set<string>());
    if (sets.length === 0) return [...this.statementOrder];
    const [first, ...rest] = sets.sort((left, right) => left.size - right.size);
    return [...first].filter((key) => rest.every((set) => set.has(key)));
  }

  private indexStatement(key: string, statement: DeonticStatement): void {
    addToIndex(this.actorIndex, statement.actor.entityId, key);
    addToIndex(this.actionIndex, statement.action.actionId, key);
    addToIndex(this.modalityIndex, statement.modality, key);
  }
}

function statementKey(statement: DeonticStatement): string {
  return [
    statement.modality,
    statement.actor.entityId,
    statement.action.actionId,
    statement.recipient?.entityId ?? '',
    statement.condition?.toString() ?? '',
  ].join('|');
}

function sameParty(left: Party, right: Party): boolean {
  return left.entityId === right.entityId;
}

function sameAction(left: Action, right: Action): boolean {
  return left.actionId === right.actionId;
}

function addToIndex<Key>(
  index: Map<Key, Set<string>>,
  indexKey: Key,
  statementKeyValue: string,
): void {
  const existing = index.get(indexKey);
  if (existing) {
    existing.add(statementKeyValue);
    return;
  }
  index.set(indexKey, new Set<string>([statementKeyValue]));
}

function isStatement(statement: DeonticStatement | undefined): statement is DeonticStatement {
  return statement !== undefined;
}

function statementMatchesQuery(statement: DeonticStatement, query: DeonticStatementQuery): boolean {
  const actorId = typeof query.actor === 'string' ? query.actor : query.actor?.entityId;
  const actionId = typeof query.action === 'string' ? query.action : query.action?.actionId;
  const recipientId =
    typeof query.recipient === 'string' ? query.recipient : query.recipient?.entityId;
  if (query.modality !== undefined && statement.modality !== query.modality) return false;
  if (actorId !== undefined && statement.actor.entityId !== actorId) return false;
  if (actionId !== undefined && statement.action.actionId !== actionId) return false;
  if (recipientId !== undefined && statement.recipient?.entityId !== recipientId) return false;
  if (
    query.atTime !== undefined &&
    statement.timeInterval !== undefined &&
    !intervalContains(statement.timeInterval, query.atTime)
  )
    return false;
  return true;
}
