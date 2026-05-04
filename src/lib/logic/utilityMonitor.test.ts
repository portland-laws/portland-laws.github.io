import {
  UtilityMonitor,
  clearGlobalCache,
  getGlobalCacheStats,
  getGlobalStats,
  resetGlobalStats,
  trackPerformance,
  withCaching,
} from './utilityMonitor';

describe('UtilityMonitor', () => {
  it('tracks calls, time, and errors for wrapped utilities', () => {
    const monitor = new UtilityMonitor();
    const upper = monitor.trackPerformance('upper', (value: string) => value.toUpperCase());
    const fail = monitor.trackPerformance('fail', () => {
      throw new Error('boom');
    });

    expect(upper('ok')).toBe('OK');
    expect(() => fail()).toThrow('boom');
    expect(monitor.getStats('upper')).toMatchObject({ calls: 1, errors: 0 });
    expect(monitor.getStats('fail')).toMatchObject({ calls: 0, errors: 1 });
  });

  it('adds deterministic argument caching', () => {
    const monitor = new UtilityMonitor();
    let calls = 0;
    const cached = monitor.withCaching('double', (value: number) => {
      calls += 1;
      return value * 2;
    });

    expect(cached(4)).toBe(8);
    expect(cached(4)).toBe(8);
    expect(calls).toBe(1);
    expect(monitor.getStats('double')).toMatchObject({ cacheHits: 1, cacheMisses: 1 });
    expect(monitor.getCacheStats()).toMatchObject({ entries: 1, hits: 1, misses: 1 });
  });

  it('supports TTL and bounded browser-native cache entries', () => {
    const monitor = new UtilityMonitor({ cache: { maxEntries: 1 } });
    let calls = 0;
    const ttlCached = monitor.withCaching(
      'ttl',
      (value: number) => {
        calls += 1;
        return value + calls;
      },
      undefined,
      { ttlMs: 0 },
    );
    const bounded = monitor.withCaching('bounded', (value: string) => value.toUpperCase());

    expect(ttlCached(1)).toBe(2);
    expect(ttlCached(1)).toBe(3);
    expect(calls).toBe(2);

    expect(bounded('a')).toBe('A');
    expect(bounded('b')).toBe('B');
    expect(monitor.getCacheStats().entries).toBe(1);
  });

  it('provides global helper functions', () => {
    resetGlobalStats();
    clearGlobalCache();
    const tracked = trackPerformance('global_upper', (value: string) => value.toUpperCase());
    const cached = withCaching('global_cached', (value: string) => value.repeat(2));

    expect(tracked('x')).toBe('X');
    expect(cached('a')).toBe('aa');
    expect(cached('a')).toBe('aa');
    expect(getGlobalStats()).toHaveProperty('global_upper');
    expect(getGlobalCacheStats()).toMatchObject({ entries: 1, hits: 1, misses: 1 });
  });
});
