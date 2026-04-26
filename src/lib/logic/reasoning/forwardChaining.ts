import { addFact, makeFact, makeFactId } from './knowledgeBase';
import type {
  ForwardChainingOptions,
  ForwardChainingResult,
  LogicFact,
  LogicImplication,
  LogicKnowledgeBase,
  LogicProofTraceStep,
} from './types';

export function runForwardChaining(
  kb: LogicKnowledgeBase,
  options: ForwardChainingOptions = {},
): ForwardChainingResult {
  const maxSteps = options.maxSteps ?? 100;
  const maxMs = options.maxMs ?? 25;
  const startedAt = Date.now();
  const inferredFacts: LogicFact[] = [];
  const trace: LogicProofTraceStep[] = [];
  let stoppedBy: ForwardChainingResult['stoppedBy'] = 'fixed_point';

  for (let step = 0; step < maxSteps; step += 1) {
    if (Date.now() - startedAt > maxMs) {
      stoppedBy = 'time_budget';
      break;
    }

    const next = findNextInference(kb, inferredFacts);
    if (!next) {
      break;
    }

    addFact(kb, next.fact);
    inferredFacts.push(next.fact);
    trace.push(next.trace);

    if (step === maxSteps - 1) {
      stoppedBy = 'max_steps';
    }
  }

  return {
    facts: [...kb.factsById.values()],
    inferredFacts,
    trace,
    exhausted: stoppedBy === 'fixed_point',
    stoppedBy,
  };
}

function findNextInference(
  kb: LogicKnowledgeBase,
  inferredFacts: LogicFact[],
): { fact: LogicFact; trace: LogicProofTraceStep } | null {
  for (const implication of kb.implications) {
    const premise = findMatchingFact(kb, implication);
    if (!premise) {
      continue;
    }

    const fact = instantiateConclusion(implication, premise);
    if (kb.factsById.has(fact.id) || inferredFacts.some((candidate) => candidate.id === fact.id)) {
      continue;
    }

    return {
      fact,
      trace: {
        id: `trace:${implication.id}:${fact.id}`,
        rule: implication.id,
        premises: [premise.id],
        conclusion: fact.id,
        sourceIds: [...new Set([...premise.sourceIds, ...implication.sourceIds])],
      },
    };
  }
  return null;
}

function findMatchingFact(kb: LogicKnowledgeBase, implication: LogicImplication): LogicFact | null {
  for (const fact of kb.factsById.values()) {
    if (fact.predicate === implication.when.predicate && sameArgs(fact.args, implication.when.args)) {
      return fact;
    }
  }
  return null;
}

function instantiateConclusion(implication: LogicImplication, premise: LogicFact): LogicFact {
  const args = implication.then.args.map((arg) => {
    if (arg.startsWith('$')) {
      const index = Number(arg.slice(1));
      return premise.args[index] || arg;
    }
    return arg;
  });
  return makeFact(implication.then.predicate, args, [...new Set([...premise.sourceIds, ...implication.sourceIds])]);
}

function sameArgs(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => right[index] === value || right[index] === `$${index}`);
}

export function createImplication(
  id: string,
  whenPredicate: string,
  whenArgs: string[],
  thenPredicate: string,
  thenArgs: string[],
  sourceIds: string[],
): LogicImplication {
  return {
    id,
    when: {
      id: makeFactId(whenPredicate, whenArgs),
      predicate: whenPredicate,
      args: whenArgs,
      sourceIds,
    },
    then: {
      predicate: thenPredicate,
      args: thenArgs,
    },
    sourceIds,
  };
}

