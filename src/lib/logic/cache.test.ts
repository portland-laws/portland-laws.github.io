import { BoundedCache } from './cache';
import {
  BrowserTdfolIpfsCacheDemo,
  canonicalizeJson,
  createBrowserLocalCid,
  demonstrateTdfolIpfsCache,
} from './tdfol/ipfsCacheDemo';
import {
  BrowserTdfolIpfsProofStorage,
  TDFOL_IPFS_PROOF_STORAGE_STATUS,
  type TdfolIpfsProofTransport,
  type TdfolStoredProof,
} from './tdfol/ipfsProofStorage';

describe('BoundedCache', () => {
  it('returns cached values and records hit/miss stats', () => {
    const cache = new BoundedCache<string>({ maxSize: 2, ttlMs: 1000 });

    expect(cache.get('missing')).toBeUndefined();
    cache.set('a', 'alpha');

    expect(cache.get('a')).toBe('alpha');
    expect(cache.getStats()).toMatchObject({
      hits: 1,
      misses: 1,
      hitRate: 0.5,
      totalRequests: 2,
    });
  });

  it('evicts the least recently used entry when max size is reached', () => {
    const cache = new BoundedCache<string>({ maxSize: 2, ttlMs: 1000 });

    cache.set('a', 'alpha');
    cache.set('b', 'bravo');
    expect(cache.get('a')).toBe('alpha');
    cache.set('c', 'charlie');

    expect(cache.get('b')).toBeUndefined();
    expect(cache.get('a')).toBe('alpha');
    expect(cache.get('c')).toBe('charlie');
    expect(cache.getStats().evictions).toBe(1);
  });

  it('expires entries after the ttl', () => {
    let now = 1000;
    const cache = new BoundedCache<string>({ maxSize: 10, ttlMs: 50, now: () => now });

    cache.set('a', 'alpha');
    now = 1049;
    expect(cache.get('a')).toBe('alpha');

    now = 1101;
    expect(cache.get('a')).toBeUndefined();
    expect(cache.getStats().expirations).toBe(1);
  });

  it('can clean up expired entries proactively', () => {
    let now = 1000;
    const cache = new BoundedCache<string>({ maxSize: 10, ttlMs: 50, now: () => now });

    cache.set('a', 'alpha');
    cache.set('b', 'bravo');
    now = 1100;

    expect(cache.cleanupExpired()).toBe(2);
    expect(cache.size).toBe(0);
  });

  it('supports explicit removal and clearing stats', () => {
    const cache = new BoundedCache<string>({ maxSize: 10, ttlMs: 1000 });

    cache.set('a', 'alpha');
    expect(cache.remove('a')).toBe(true);
    expect(cache.remove('a')).toBe(false);

    cache.set('b', 'bravo');
    expect(cache.get('b')).toBe('bravo');
    cache.clear();

    expect(cache.size).toBe(0);
    expect(cache.getStats()).toMatchObject({
      hits: 0,
      misses: 0,
      totalRequests: 0,
    });
  });
});

describe('BrowserTdfolIpfsCacheDemo', () => {
  const proofPayload = {
    theorem: 'Goal(a)',
    formula: 'P(a) -> Goal(a)',
    proof: {
      status: 'proved' as const,
      theorem: 'Goal(a)',
      method: 'tdfol-forward-chaining',
      steps: [
        {
          id: 'tdfol-step-1',
          rule: 'ModusPonens',
          premises: ['P(a)', 'P(a) -> Goal(a)'],
          conclusion: 'Goal(a)',
        },
      ],
    },
    metadata: { module: 'logic/TDFOL/nl/demonstrate_ipfs_cache.py' },
  };

  it('stores proof payloads by deterministic browser-local CID', () => {
    const canonical = canonicalizeJson({ b: 2, a: 1 });

    expect(canonical).toBe('{"a":1,"b":2}');
    expect(createBrowserLocalCid(canonical)).toBe(createBrowserLocalCid(canonical));

    const result = demonstrateTdfolIpfsCache(proofPayload);

    expect(result.cid).toMatch(/^bafylogic[0-9a-f]{16}$/);
    expect(result.firstLookup).toMatchObject({ hit: true, source: 'browser-cache' });
    expect(result.secondLookup).toMatchObject({ hit: true, source: 'browser-cache' });
    expect(result.stats).toMatchObject({ hits: 2, misses: 0, totalRequests: 2 });
    expect(result.transport).toMatchObject({ available: false, mode: 'fail-closed-local-only' });
  });

  it('expires locally cached proof payloads without remote IPFS fallback', () => {
    let now = 10;
    const demo = new BrowserTdfolIpfsCacheDemo({ ttlMs: 5, now: () => now });
    const entry = demo.putProof(proofPayload);

    expect(demo.getProof(entry.cid).hit).toBe(true);
    now = 20;

    expect(demo.getProof(entry.cid)).toMatchObject({
      cid: entry.cid,
      hit: false,
      source: 'unavailable-ipfs-adapter',
    });
    expect(demo.getStats()).toMatchObject({ hits: 1, misses: 1, expirations: 1 });
  });
});

describe('BrowserTdfolIpfsProofStorage', () => {
  const proofPayload = {
    theorem: 'Goal(a)',
    formula: 'P(a) -> Goal(a)',
    axioms: ['P(a) -> Goal(a)', 'P(a)'],
    proof: {
      status: 'proved' as const,
      theorem: 'Goal(a)',
      method: 'tdfol-forward-chaining',
      steps: [{ id: 's1', rule: 'ModusPonens', premises: ['P(a)'], conclusion: 'Goal(a)' }],
    },
  };

  it('stores TDFOL proof payloads by deterministic browser-local CID and fails closed without transport', async () => {
    let now = 100;
    const storage = new BrowserTdfolIpfsProofStorage({ ttlMs: 5, now: () => now });
    const stored = await storage.storeProof(proofPayload);

    expect(stored).toMatchObject({ ok: true, source: 'browser-cache' });
    expect(stored.cid).toMatch(/^bafylogic[0-9a-f]{16}$/);
    expect(TDFOL_IPFS_PROOF_STORAGE_STATUS).toMatchObject({
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });

    now = 102;
    const repeated = await storage.storeProof({
      ...proofPayload,
      axioms: [...proofPayload.axioms].reverse(),
    });
    expect(repeated.cid).toBe(stored.cid);
    expect((await storage.retrieveProof(stored.cid)).entry?.payload.axioms).toEqual([
      'P(a)',
      'P(a) -> Goal(a)',
    ]);
    expect(storage.getStats()).toMatchObject({
      hits: 1,
      transportAvailable: false,
      storedProofs: 1,
    });

    now = 200;
    await expect(storage.retrieveProof(stored.cid)).resolves.toMatchObject({
      ok: false,
      source: 'unavailable-ipfs-adapter',
    });
  });

  it('accepts an injected browser-native transport and verifies returned CIDs', async () => {
    const remote = new Map<string, TdfolStoredProof>();
    const transport: TdfolIpfsProofTransport = {
      mode: 'browser-native-ipfs',
      async addProof(entry) {
        remote.set(entry.cid, entry);
        return entry.cid;
      },
      async getProof(cid) {
        return remote.get(cid);
      },
    };
    const storage = new BrowserTdfolIpfsProofStorage({ maxEntries: 1, transport });
    const stored = await storage.storeProof(proofPayload);
    const other = await storage.storeProof({ ...proofPayload, theorem: 'Other(a)' });

    expect(stored).toMatchObject({ ok: true, source: 'browser-native-ipfs' });
    expect(await storage.retrieveProof(stored.cid)).toMatchObject({
      ok: true,
      source: 'browser-native-ipfs',
    });
    expect(other.cid).not.toBe(stored.cid);
  });
});
