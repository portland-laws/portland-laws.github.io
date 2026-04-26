export interface UtilityStats {
  calls: number;
  totalTime: number;
  errors: number;
  avgTime?: number;
}

export type UtilityFunction<Args extends unknown[], Result> = (...args: Args) => Result;

export class UtilityMonitor {
  private readonly stats = new Map<string, UtilityStats>();
  private readonly cache = new Map<string, unknown>();

  trackPerformance<Args extends unknown[], Result>(
    name: string,
    fn: UtilityFunction<Args, Result>,
  ): UtilityFunction<Args, Result> {
    this.ensureStats(name);
    return (...args: Args): Result => {
      const startedAt = performance.now();
      try {
        const result = fn(...args);
        const elapsed = performance.now() - startedAt;
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

  withCaching<Args extends unknown[], Result>(
    name: string,
    fn: UtilityFunction<Args, Result>,
    cacheKeyFn?: (...args: Args) => string,
  ): UtilityFunction<Args, Result> {
    return (...args: Args): Result => {
      const key = cacheKeyFn ? cacheKeyFn(...args) : defaultCacheKey(name, args);
      if (this.cache.has(key)) {
        return this.cache.get(key) as Result;
      }
      const result = fn(...args);
      this.cache.set(key, result);
      return result;
    };
  }

  getStats(name?: string): Record<string, UtilityStats> | UtilityStats {
    if (name) {
      return withAverage(this.stats.get(name) ?? { calls: 0, totalTime: 0, errors: 0 });
    }
    return Object.fromEntries([...this.stats.entries()].map(([key, value]) => [key, withAverage(value)]));
  }

  clearCache(): void {
    this.cache.clear();
  }

  resetStats(): void {
    this.stats.clear();
  }

  private ensureStats(name: string): UtilityStats {
    if (!this.stats.has(name)) {
      this.stats.set(name, { calls: 0, totalTime: 0, errors: 0 });
    }
    return this.stats.get(name)!;
  }
}

const globalMonitor = new UtilityMonitor();

export function trackPerformance<Args extends unknown[], Result>(
  name: string,
  fn: UtilityFunction<Args, Result>,
): UtilityFunction<Args, Result> {
  return globalMonitor.trackPerformance(name, fn);
}

export function withCaching<Args extends unknown[], Result>(
  name: string,
  fn: UtilityFunction<Args, Result>,
  cacheKeyFn?: (...args: Args) => string,
): UtilityFunction<Args, Result> {
  return globalMonitor.withCaching(name, fn, cacheKeyFn);
}

export function getGlobalStats(): Record<string, UtilityStats> | UtilityStats {
  return globalMonitor.getStats();
}

export function clearGlobalCache(): void {
  globalMonitor.clearCache();
}

export function resetGlobalStats(): void {
  globalMonitor.resetStats();
}

function withAverage(stats: UtilityStats): UtilityStats {
  return {
    ...stats,
    ...(stats.calls > 0 ? { avgTime: stats.totalTime / stats.calls } : {}),
  };
}

function defaultCacheKey(name: string, args: unknown[]): string {
  return stableStringify({ name, args });
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => `${JSON.stringify(key)}:${stableStringify(entry)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}
