import type { LogicFact, LogicImplication, LogicKnowledgeBase } from './types';

export function createLogicKnowledgeBase(
  facts: LogicFact[] = [],
  implications: LogicImplication[] = [],
): LogicKnowledgeBase {
  const factsById = new Map<string, LogicFact>();
  const factsBySourceId = new Map<string, LogicFact[]>();

  for (const fact of facts) {
    factsById.set(fact.id, fact);
    for (const sourceId of fact.sourceIds) {
      const list = factsBySourceId.get(sourceId) || [];
      list.push(fact);
      factsBySourceId.set(sourceId, list);
    }
  }

  return {
    factsById,
    factsBySourceId,
    implications,
  };
}

export function addFact(kb: LogicKnowledgeBase, fact: LogicFact): void {
  kb.factsById.set(fact.id, fact);
  for (const sourceId of fact.sourceIds) {
    const list = kb.factsBySourceId.get(sourceId) || [];
    list.push(fact);
    kb.factsBySourceId.set(sourceId, list);
  }
}

export function makeFactId(predicate: string, args: string[]): string {
  return `${predicate}(${args.join(',')})`;
}

export function makeFact(predicate: string, args: string[], sourceIds: string[]): LogicFact {
  return {
    id: makeFactId(predicate, args),
    predicate,
    args,
    sourceIds,
  };
}

