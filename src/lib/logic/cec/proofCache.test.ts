import { CecModusPonensRule, CecTemporalTRule } from './inferenceRules';
import { parseCecExpression } from './parser';
import {
  CecProofCache,
  clearGlobalCecProofCache,
  getGlobalCecProofCache,
  proveCecWithCache,
} from './proofCache';

describe('CEC proof cache', () => {
  it('stores and retrieves proof results by normalized theorem, axioms, and prover config', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(comply_with agent code)');
    const kb = { axioms: [parseCecExpression('(subject_to agent code)')] };
    const result = { status: 'proved' as const, theorem: '(comply_with agent code)', steps: [], method: 'manual' };
    const options = { maxSteps: 3, rules: [CecModusPonensRule] };

    const cid = cache.set(theorem, kb, result, options);

    expect(cid).toMatch(/^browsets-/);
    expect(cache.get(theorem, kb, options)).toEqual(result);
    expect(cache.get(theorem, kb, { maxSteps: 4, rules: [CecModusPonensRule] })).toBeUndefined();
    expect(cache.getStats()).toMatchObject({ hits: 1, misses: 1, sets: 1 });
  });

  it('proves through the cache and marks cached method names', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(comply_with agent code)');
    const kb = {
      axioms: [
        parseCecExpression('(always (subject_to agent code))'),
        parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
      ],
    };
    const options = { rules: [CecTemporalTRule, CecModusPonensRule] };

    expect(cache.prove(theorem, kb, options)).toMatchObject({ status: 'proved', method: 'cec-forward-chaining' });
    expect(cache.prove(theorem, kb, options)).toMatchObject({ status: 'proved', method: 'cec-forward-chaining:cached' });
    expect(cache.getStats()).toMatchObject({ hits: 1, sets: 1 });
  });

  it('invalidates, clears, and exposes global helpers', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(active code)');
    const kb = { axioms: [theorem] };

    cache.prove(theorem, kb);
    expect(cache.invalidate(theorem, kb)).toBe(true);
    expect(cache.clear()).toBe(0);

    clearGlobalCecProofCache();
    expect(proveCecWithCache(theorem, kb)).toMatchObject({ status: 'proved' });
    expect(getGlobalCecProofCache().get(theorem, kb)).toMatchObject({ status: 'proved' });
  });
});
