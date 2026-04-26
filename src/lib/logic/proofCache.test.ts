import { ProofCache, cidForObject, clearGlobalProofCache, getGlobalProofCache } from './proofCache';

describe('ProofCache', () => {
  it('computes deterministic CIDs independent of object key order', () => {
    expect(cidForObject({ b: 2, a: 1 })).toBe(cidForObject({ a: 1, b: 2 }));
  });

  it('stores and retrieves proof results by formula, axioms, prover, and config', () => {
    const cache = new ProofCache<{ status: string }>();
    const cid = cache.set('P -> Q', { status: 'proved' }, ['P'], 'tdfol', { depth: 3 });

    expect(cid).toMatch(/^browsets-/);
    expect(cache.get('P -> Q', ['P'], 'tdfol', { depth: 3 })).toEqual({ status: 'proved' });
    expect(cache.getStats()).toMatchObject({
      hits: 1,
      misses: 0,
      sets: 1,
      hitRate: 1,
    });
  });

  it('supports prover-name compat lookup style', () => {
    const cache = new ProofCache<string>();
    cache.set('P', 'proved', [], 'z3');

    expect(cache.get('P', 'z3')).toBe('proved');
  });

  it('expires and evicts entries deterministically', () => {
    let now = 0;
    const cache = new ProofCache<string>({ maxSize: 1, ttlMs: 10, now: () => now });
    cache.set('P', 'first');
    cache.set('Q', 'second');

    expect(cache.get('P')).toBeUndefined();
    expect(cache.getStats().evictions).toBe(1);
    expect(cache.get('Q')).toBe('second');
    now = 20;
    expect(cache.get('Q')).toBeUndefined();
  });

  it('invalidates, clears, and exposes a global cache', () => {
    const cache = new ProofCache<string>();
    cache.set('P', 'proved');

    expect(cache.invalidate('P')).toBe(true);
    expect(cache.clear()).toBe(0);

    clearGlobalProofCache();
    getGlobalProofCache().set('A', 'proved');
    expect(getGlobalProofCache().get('A')).toBe('proved');
  });
});
