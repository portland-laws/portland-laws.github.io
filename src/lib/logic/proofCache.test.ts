import {
  COMMON_PROOF_CACHE_METADATA,
  EXTERNAL_PROVER_PROOF_CACHE_METADATA,
  IPFS_PROOF_CACHE_METADATA,
  IpfsProofCache,
  type BrowserNativeIpfsProofTransport,
  type IpfsProofCacheEntry,
  ExternalProverProofCache,
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

  it('declares the browser-native external_provers proof_cache.py parity contract', () => {
    expect(EXTERNAL_PROVER_PROOF_CACHE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/external_provers/proof_cache.py',
      browserNative: true,
      runtimeDependencies: [],
    });
    expect(EXTERNAL_PROVER_PROOF_CACHE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'external_prover_identity_keys',
        'version_and_logic_sensitive_lookup',
        'fail_closed_replay_validation',
      ]),
    );
  });

  it('caches external prover artifacts by prover identity, version, logic, and options', () => {
    const cache = new ExternalProverProofCache();
    const query = {
      formula: '(assert (=> P Q))',
      axioms: ['P'],
      prover: { name: 'z3', version: '4.13.0', logic: 'SMT-LIB' },
      options: { timeoutMs: 500, model: false },
    };
    const stored = cache.set(query, { status: 'proved', proofText: 'sat-proof' });

    expect(stored).toMatch(/^browsets-/);
    expect(cache.get(query)).toMatchObject({
      status: 'proved',
      proofText: 'sat-proof',
      replayValidated: false,
    });
    expect(
      cache.get({
        ...query,
        prover: { name: 'z3', version: '4.12.0', logic: 'SMT-LIB' },
      }),
    ).toBeUndefined();
    expect(cache.get({ ...query, options: { timeoutMs: 1000, model: false } })).toBeUndefined();
  });

  it('fails closed when external prover replay validation is required', () => {
    const cache = new ExternalProverProofCache({
      requireReplayValidation: true,
      replayValidator: (_query, artifact) => artifact.proofText === 'locally-replayed',
    });
    const query = { formula: 'P', prover: { name: 'cvc5', version: '1.2.0' } };

    expect(cache.set(query, { status: 'proved', proofText: 'opaque' })).toBeUndefined();
    expect(cache.get(query)).toBeUndefined();

    expect(cache.set(query, { status: 'proved', proofText: 'locally-replayed' })).toMatch(
      /^browsets-/,
    );
    expect(cache.get(query)).toMatchObject({ replayValidated: true });
  });

  it('declares the browser-native integration ipfs_proof_cache.py parity contract', () => {
    expect(IPFS_PROOF_CACHE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integration/caching/ipfs_proof_cache.py',
      browserNative: true,
      runtimeDependencies: [],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(IPFS_PROOF_CACHE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'deterministic_content_addressed_entries',
        'injected_browser_ipfs_transport',
        'fail_closed_unavailable_adapter',
        'cid_verification_on_remote_reads',
      ]),
    );
  });

  it('stores IPFS proof cache entries with deterministic content addressing and local reads', async () => {
    const cache = new IpfsProofCache<{ status: string }>({ now: () => 25 });
    const query = {
      formula: 'Q',
      axioms: ['B', 'A'],
      proverName: 'tdfol',
      proverConfig: { depth: 3 },
    };

    const stored = await cache.set(query, { status: 'proved' });
    const sameCid = cache.computeCid({ ...query, axioms: ['A', 'B'] }, { status: 'proved' });

    expect(stored).toMatchObject({ ok: true, cid: sameCid, source: 'browser-cache' });
    expect(stored.entry).toMatchObject({
      cid: sameCid,
      query: { formula: 'Q', axioms: ['A', 'B'], proverName: 'tdfol' },
      storedAt: 25,
      sourcePythonModule: 'logic/integration/caching/ipfs_proof_cache.py',
    });
    await expect(cache.get(stored.cid)).resolves.toMatchObject({
      ok: true,
      source: 'browser-cache',
      entry: { result: { status: 'proved' } },
    });
    expect(cache.getStats()).toMatchObject({ hits: 1, sets: 1, transportAvailable: false });
  });

  it('fails closed without an adapter and verifies injected IPFS transport CIDs', async () => {
    const remote = new Map<string, IpfsProofCacheEntry<{ status: string }>>();
    const transport: BrowserNativeIpfsProofTransport<{ status: string }> = {
      mode: 'browser-native-ipfs',
      async addProof(entry) {
        remote.set(entry.cid, entry);
        return entry.cid;
      },
      async getProof(cid) {
        return remote.get(cid);
      },
    };
    const writer = new IpfsProofCache<{ status: string }>({ transport });
    const stored = await writer.set({ formula: 'P', proverName: 'cec' }, { status: 'proved' });
    const reader = new IpfsProofCache<{ status: string }>({ transport });

    await expect(reader.get(stored.cid)).resolves.toMatchObject({
      ok: true,
      source: 'browser-native-ipfs',
      entry: { result: { status: 'proved' } },
    });

    const offline = new IpfsProofCache<{ status: string }>();
    await expect(offline.get(stored.cid)).resolves.toMatchObject({
      ok: false,
      source: 'unavailable-ipfs-adapter',
    });

    remote.set(stored.cid, { ...remote.get(stored.cid)!, canonicalJson: '{"tampered":true}' });
    const verifier = new IpfsProofCache<{ status: string }>({ transport });
    await expect(verifier.get(stored.cid)).resolves.toMatchObject({
      ok: false,
      error: 'Proof CID verification failed.',
    });
  });
});
