import {
  COMMON_PROOF_CACHE_METADATA,
  ProofCache,
  cidForObject,
  clearGlobalProofCache,
  getGlobalProofCache,
} from './proofCache';

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

  it('declares the browser-native common proof_cache.py parity contract', () => {
    expect(COMMON_PROOF_CACHE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/common/proof_cache.py',
      browserNative: true,
      runtimeDependencies: [],
    });
    expect(COMMON_PROOF_CACHE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'deterministic_content_ids',
        'order_insensitive_axiom_keys',
        'ttl_lru_eviction',
        'local_snapshot_introspection',
      ]),
    );
  });

  it('normalizes axiom order for content IDs and lookup keys', () => {
    const cache = new ProofCache<string>();
    const leftCid = cache.set('R', 'proved', ['B', 'A'], 'common', { mode: 'strict' });
    const rightCid = cache.computeCid({
      formula: 'R',
      axioms: ['A', 'B'],
      proverName: 'common',
      proverConfig: { mode: 'strict' },
    });

    expect(leftCid).toBe(rightCid);
    expect(cache.get('R', ['A', 'B'], 'common', { mode: 'strict' })).toBe('proved');
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

  it('provides browser-local snapshots and expired-entry cleanup without exposing mutable internals', () => {
    let now = 100;
    const cache = new ProofCache<{ status: string }>({ ttlMs: 5, now: () => now });
    cache.set('P', { status: 'proved' }, ['B', 'A'], 'common', { depth: 2 });
    cache.get('P', ['A', 'B'], 'common', { depth: 2 });

    const snapshot = cache.snapshot();
    expect(snapshot).toHaveLength(1);
    expect(snapshot[0]).toMatchObject({
      formulaString: 'P',
      axiomStrings: ['A', 'B'],
      proverName: 'common',
      proverConfig: { depth: 2 },
      hitCount: 1,
      ageMs: 0,
      expired: false,
    });

    snapshot[0].axiomStrings.push('mutated');
    expect(cache.snapshot()[0].axiomStrings).toEqual(['A', 'B']);

    now = 110;
    expect(cache.snapshot()[0]).toMatchObject({ ageMs: 10, expired: true });
    expect(cache.deleteExpired()).toBe(1);
    expect(cache.getStats().cacheSize).toBe(0);
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
