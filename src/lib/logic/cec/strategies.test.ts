import type { ProofResult } from '../types';
import { CecModusPonensRule, CecTemporalTRule } from './inferenceRules';
import { parseCecExpression } from './parser';
import {
  CecCachedForwardStrategy,
  CecBackwardChainingStrategy,
  CecBidirectionalStrategy,
  CecForwardChainingStrategy,
  CecHybridStrategy,
  CecStrategySelector,
  getCecStrategy,
  proveCecWithStrategySelection,
  type CecProverStrategy,
} from './strategies';

describe('CEC proving strategies', () => {
  it('selects cached forward chaining by default and proves through it', () => {
    const theorem = parseCecExpression('(comply_with agent code)');
    const kb = {
      axioms: [
        parseCecExpression('(subject_to agent code)'),
        parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
      ],
    };
    const selector = new CecStrategySelector();

    expect(selector.selectStrategy(theorem, kb).strategyType).toBe('cached_forward');
    expect(selector.proveWithSelectedStrategy(theorem, kb, { rules: [CecModusPonensRule] })).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining',
    });
  });

  it('can prefer the lowest-cost CEC strategy', () => {
    const expensive = fakeCecStrategy('Expensive', 100, 50);
    const cheap = fakeCecStrategy('Cheap', 10, 1);
    const selector = new CecStrategySelector({ strategies: [expensive, cheap] });

    expect(selector.selectStrategy(parseCecExpression('(goal)'), { axioms: [] }, true).name).toBe('Cheap');
  });

  it('reports strategy metadata and cache stats', () => {
    const cached = new CecCachedForwardStrategy();
    const selector = new CecStrategySelector({ strategies: [new CecForwardChainingStrategy(), cached] });
    const theorem = parseCecExpression('(active code)');
    const kb = { axioms: [theorem] };

    expect(selector.getStrategyInfo(theorem, kb).map((info) => info.type)).toEqual(['cached_forward', 'forward_chaining']);
    cached.prove(theorem, kb);
    cached.prove(theorem, kb);
    expect(cached.getCacheStats()).toMatchObject({ hits: 1, sets: 1 });
  });

  it('exposes a browser-native strategy selection convenience facade', () => {
    const result = proveCecWithStrategySelection(parseCecExpression('(comply_with agent code)'), {
      axioms: [
        parseCecExpression('(always (subject_to agent code))'),
        parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
      ],
    }, {
      rules: [CecTemporalTRule, CecModusPonensRule],
      preferLowCost: true,
    });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(comply_with agent code)',
    });
  });

  it('proves implication goals with backward chaining', () => {
    const strategy = new CecBackwardChainingStrategy();
    const result = strategy.prove(parseCecExpression('(q)'), {
      axioms: [
        parseCecExpression('(p)'),
        parseCecExpression('(implies (p) (q))'),
      ],
    });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'cec-backward-chaining',
      theorem: '(q)',
    });
    expect(result.steps[0]).toMatchObject({
      rule: 'CecBackwardImplication',
      conclusion: '(q)',
    });
  });

  it('uses bidirectional search as backward-first with forward fallback', () => {
    const theorem = parseCecExpression('(q)');
    const kb = {
      axioms: [
        parseCecExpression('(p)'),
        parseCecExpression('(implies (p) (q))'),
      ],
    };

    expect(new CecBidirectionalStrategy().prove(theorem, kb).method).toBe('cec-bidirectional-search');
    expect(new CecBidirectionalStrategy().prove(theorem, kb).status).toBe('proved');
  });

  it('selects adaptive hybrid strategies using Python-compatible axiom-count heuristics', () => {
    const hybrid = new CecHybridStrategy();

    expect(hybrid.selectAdaptiveStrategy({ axioms: [parseCecExpression('(p)')] }).strategyType).toBe('forward_chaining');
    expect(hybrid.selectAdaptiveStrategy({
      axioms: Array.from({ length: 6 }, (_, index) => parseCecExpression(`(p${index})`)),
    }).strategyType).toBe('bidirectional');
    expect(hybrid.selectAdaptiveStrategy({
      axioms: Array.from({ length: 10 }, (_, index) => parseCecExpression(`(p${index})`)),
    }).strategyType).toBe('backward_chaining');
  });

  it('creates strategies by Python-style strategy type', () => {
    expect(getCecStrategy('forward_chaining')).toBeInstanceOf(CecForwardChainingStrategy);
    expect(getCecStrategy('backward_chaining')).toBeInstanceOf(CecBackwardChainingStrategy);
    expect(getCecStrategy('bidirectional')).toBeInstanceOf(CecBidirectionalStrategy);
    expect(getCecStrategy('hybrid')).toBeInstanceOf(CecHybridStrategy);
    expect(getCecStrategy('auto')).toBeInstanceOf(CecHybridStrategy);
  });
});

function fakeCecStrategy(name: string, priority: number, cost: number): CecProverStrategy {
  return {
    name,
    strategyType: 'forward_chaining',
    canHandle: () => true,
    prove: (theorem): ProofResult => ({
      status: 'unknown',
      theorem: String(theorem),
      steps: [],
      method: name,
    }),
    getPriority: () => priority,
    estimateCost: () => cost,
  };
}
