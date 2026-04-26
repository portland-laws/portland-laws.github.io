import { BoundedCache } from './cache';

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

