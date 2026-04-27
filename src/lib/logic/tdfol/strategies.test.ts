import type { ProofResult } from '../types';
import { ModusPonensRule, TemporalKAxiomRule, TemporalTAxiomRule, type TdfolInferenceRule } from './inferenceRules';
import { parseTdfolFormula } from './parser';
import {
  proveTdfolWithStrategySelection,
  TdfolForwardChainingStrategy,
  TdfolStrategySelector,
  type TdfolProverStrategy,
} from './strategies';

describe('TDFOL proving strategies', () => {
  it('proves direct knowledge-base formulas with forward chaining', () => {
    const theorem = parseTdfolFormula('Pred(x)');
    const strategy = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] });

    expect(strategy.prove(theorem, { axioms: [theorem] })).toMatchObject({
      status: 'proved',
      theorem: 'Pred(x)',
      steps: [],
      method: 'forward_chaining',
    });
  });

  it('derives formulas through bounded forward chaining', () => {
    const strategy = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule], maxIterations: 5 });
    const result = strategy.prove(parseTdfolFormula('Goal(x)'), {
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    });

    expect(result).toMatchObject({
      status: 'proved',
      steps: [{ rule: 'ModusPonens', conclusion: 'Goal(x)' }],
    });
    expect(result.timeMs).toBeGreaterThanOrEqual(0);
  });

  it('chains temporal and propositional rules using the strategy facade', () => {
    const result = proveTdfolWithStrategySelection(parseTdfolFormula('Goal(x)'), {
      axioms: [parseTdfolFormula('always(Pred(x) -> Goal(x))'), parseTdfolFormula('always(Pred(x))')],
    }, {
      strategies: [new TdfolForwardChainingStrategy({ rules: [TemporalKAxiomRule, TemporalTAxiomRule] })],
    });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
      method: 'forward_chaining',
    });
  });

  it('returns unknown when the selected strategy cannot progress', () => {
    const strategy = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule], maxIterations: 2 });

    expect(strategy.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] })).toMatchObject({
      status: 'unknown',
    });
  });

  it('respects the derived formula budget', () => {
    const expandingRule: TdfolInferenceRule = {
      name: 'Expand',
      description: 'Wraps any formula in eventually',
      arity: 1,
      canApply: () => true,
      apply: (formula) => ({ kind: 'temporal', operator: 'EVENTUALLY', formula }),
    };
    const strategy = new TdfolForwardChainingStrategy({ rules: [expandingRule], maxDerivedFormulas: 2 });

    expect(strategy.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] })).toMatchObject({
      status: 'timeout',
      error: 'Derived formula budget exceeded',
    });
  });

  it('selects the highest-priority applicable strategy by default', () => {
    const highPriority = fakeStrategy('High', 90, 10, false);
    const fallback = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] });
    const selector = new TdfolStrategySelector({ strategies: [fallback, highPriority] });

    expect(selector.selectStrategy(parseTdfolFormula('Goal(x)'), { axioms: [] }).name).toBe('High');
  });

  it('can prefer the lowest estimated cost among applicable strategies', () => {
    const expensive = fakeStrategy('Expensive', 100, 200, false);
    const cheap = fakeStrategy('Cheap', 10, 1, false);
    const selector = new TdfolStrategySelector({ strategies: [expensive, cheap] });

    expect(selector.selectStrategy(parseTdfolFormula('Goal(x)'), { axioms: [] }, true).name).toBe('Cheap');
  });

  it('reports strategy metadata and ordered fallback lists', () => {
    const selector = new TdfolStrategySelector({
      strategies: [fakeStrategy('Low', 5, 1, false), fakeStrategy('High', 50, 2, false)],
    });

    expect(selector.getStrategyInfo(parseTdfolFormula('Goal(x)'), { axioms: [] })).toEqual([
      { name: 'High', type: 'forward_chaining', priority: 50, cost: 2 },
      { name: 'Low', type: 'forward_chaining', priority: 5, cost: 1 },
    ]);
    expect(selector.selectMultiple(parseTdfolFormula('Goal(x)'), { axioms: [] }, 1).map((s) => s.name)).toEqual(['High']);
  });
});

function fakeStrategy(name: string, priority: number, cost: number, proved: boolean): TdfolProverStrategy {
  return {
    name,
    strategyType: 'forward_chaining',
    canHandle: () => true,
    prove: (formula): ProofResult => ({
      status: proved ? 'proved' : 'unknown',
      theorem: String(formula),
      steps: [],
      method: name,
    }),
    getPriority: () => priority,
    estimateCost: () => cost,
  };
}
