export interface UtilityStats {
  calls: number;
  totalTime: number;
  errors: number;
  cacheHits: number;
  cacheMisses: number;
  avgTime?: number;
}

export interface UtilityCacheOptions {
  ttlMs?: number;
  maxEntries?: number;
}

export interface UtilityCacheStats {
  entries: number;
  hits: number;
  misses: number;
}

export interface UtilityMonitorOptions {
  cache?: UtilityCacheOptions;
}

export type UtilityFunction<Args extends Array<unknown>, Result> = (...args: Args) => Result;

interface CacheEntry {
  value: unknown;
  expiresAt?: number;
  lastAccessed: number;
}

export class UtilityMonitor {
  private readonly stats = new Map<string, UtilityStats>();
  private readonly cache = new Map<string, CacheEntry>();
  private readonly cacheOptions: UtilityCacheOptions;
  private cacheHits = 0;
  private cacheMisses = 0;

  constructor(options: UtilityMonitorOptions = {}) {
    this.cacheOptions = options.cache ?? {};
  }

  trackPerformance<Args extends Array<unknown>, Result>(
    name: string,
    fn: UtilityFunction<Args, Result>,
  ): UtilityFunction<Args, Result> {
    this.ensureStats(name);
    return (...args: Args): Result => {
      const startedAt = now();
      try {
        const result = fn(...args);
        const elapsed = now() - startedAt;
        const stats = this.ensureStats(name);
        stats.calls += 1;
        stats.totalTime += elapsed;
        return result;
      } catch (error) {
        this.ensureStats(name).errors += 1;
        throw error;
      }
    };
  }

  withCaching<Args extends Array<unknown>, Result>(
    name: string,
    fn: UtilityFunction<Args, Result>,
    cacheKeyFn?: (...args: Args) => string,
    options: UtilityCacheOptions = {},
  ): UtilityFunction<Args, Result> {
    return (...args: Args): Result => {
      const key = cacheKeyFn ? cacheKeyFn(...args) : defaultCacheKey(name, args);
      const cached = this.cache.get(key);
      const stats = this.ensureStats(name);
      if (cached && !isExpired(cached)) {
        cached.lastAccessed = now();
        stats.cacheHits += 1;
        this.cacheHits += 1;
        return cached.value as Result;
      }
      if (cached) {
        this.cache.delete(key);
      }
      stats.cacheMisses += 1;
      this.cacheMisses += 1;
      const result = fn(...args);
      this.setCacheEntry(key, result, options);
      return result;
    };
  }

  getStats(name?: string): Record<string, UtilityStats> | UtilityStats {
    if (name) {
      return withAverage(this.stats.get(name) ?? createStats());
    }
    return Object.fromEntries(
      [...this.stats.entries()].map(([key, value]) => [key, withAverage(value)]),
    );
  }

  getCacheStats(): UtilityCacheStats {
    this.evictExpired();
    return { entries: this.cache.size, hits: this.cacheHits, misses: this.cacheMisses };
  }

  clearCache(): void {
    this.cache.clear();
  }

  resetStats(): void {
    this.stats.clear();
    this.cacheHits = 0;
    this.cacheMisses = 0;
  }

  private ensureStats(name: string): UtilityStats {
    if (!this.stats.has(name)) {
      this.stats.set(name, createStats());
    }
    return this.stats.get(name)!;
  }

  private setCacheEntry(key: string, value: unknown, options: UtilityCacheOptions): void {
    this.evictExpired();
    const ttlMs = options.ttlMs ?? this.cacheOptions.ttlMs;
    const timestamp = now();
    this.cache.set(key, {
      value,
      ...(ttlMs !== undefined ? { expiresAt: timestamp + ttlMs } : {}),
      lastAccessed: timestamp,
    });
    this.evictOverflow(options.maxEntries ?? this.cacheOptions.maxEntries);
  }

  private evictExpired(): void {
    for (const [key, entry] of this.cache.entries()) {
      if (isExpired(entry)) {
        this.cache.delete(key);
      }
    }
  }

  private evictOverflow(maxEntries?: number): void {
    if (maxEntries === undefined || maxEntries < 1) {
      return;
    }
    while (this.cache.size > maxEntries) {
      const oldest = [...this.cache.entries()].sort(
        ([, left], [, right]) => left.lastAccessed - right.lastAccessed,
      )[0];
      if (!oldest) {
        return;
      }
      this.cache.delete(oldest[0]);
    }
  }
}

const globalMonitor = new UtilityMonitor();

export function trackPerformance<Args extends Array<unknown>, Result>(
  name: string,
  fn: UtilityFunction<Args, Result>,
): UtilityFunction<Args, Result> {
  return globalMonitor.trackPerformance(name, fn);
}

export function withCaching<Args extends Array<unknown>, Result>(
  name: string,
  fn: UtilityFunction<Args, Result>,
  cacheKeyFn?: (...args: Args) => string,
  options: UtilityCacheOptions = {},
): UtilityFunction<Args, Result> {
  return globalMonitor.withCaching(name, fn, cacheKeyFn, options);
}

export function getGlobalStats(): Record<string, UtilityStats> | UtilityStats {
  return globalMonitor.getStats();
}

export function getGlobalCacheStats(): UtilityCacheStats {
  return globalMonitor.getCacheStats();
}

export function clearGlobalCache(): void {
  globalMonitor.clearCache();
}

export function resetGlobalStats(): void {
  globalMonitor.resetStats();
}

export const track_performance = trackPerformance;
export const with_caching = withCaching;
export const get_global_stats = getGlobalStats;
export const get_global_cache_stats = getGlobalCacheStats;
export const clear_global_cache = clearGlobalCache;
export const reset_global_stats = resetGlobalStats;

function createStats(): UtilityStats {
  return { calls: 0, totalTime: 0, errors: 0, cacheHits: 0, cacheMisses: 0 };
}

function withAverage(stats: UtilityStats): UtilityStats {
  return {
    ...stats,
    ...(stats.calls > 0 ? { avgTime: stats.totalTime / stats.calls } : {}),
  };
}

function defaultCacheKey(name: string, args: Array<unknown>): string {
  return stableStringify({ name, args });
}

function now(): number {
  return typeof performance !== 'undefined' ? performance.now() : Date.now();
}

function isExpired(entry: CacheEntry): boolean {
  return entry.expiresAt !== undefined && entry.expiresAt <= now();
}

function stableStringify(value: unknown, seen = new WeakSet<object>()): string {
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry, seen)).join(',')}]`;
  }
  if (value === undefined) {
    return '"__undefined__"';
  }
  if (typeof value === 'bigint') {
    return `"${value.toString()}n"`;
  }
  if (value && typeof value === 'object') {
    if (seen.has(value)) {
      return '"__circular__"';
    }
    seen.add(value);
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => `${JSON.stringify(key)}:${stableStringify(entry, seen)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
