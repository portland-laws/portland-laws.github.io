export interface CacheEntry<T> {
  value: T;
  timestamp: number;
  accessCount: number;
}

export interface CacheStats {
  size: number;
  maxSize: number;
  ttlMs: number;
  hits: number;
  misses: number;
  evictions: number;
  expirations: number;
  hitRate: number;
  totalRequests: number;
}

export interface BoundedCacheOptions {
  maxSize?: number;
  ttlMs?: number;
  now?: () => number;
}

export class BoundedCache<T> {
  readonly maxSize: number;
  readonly ttlMs: number;

  private readonly now: () => number;
  private readonly cache = new Map<string, CacheEntry<T>>();
  private hits = 0;
  private misses = 0;
  private evictions = 0;
  private expirations = 0;

  constructor(options: BoundedCacheOptions = {}) {
    this.maxSize = options.maxSize ?? 1000;
    this.ttlMs = options.ttlMs ?? 60 * 60 * 1000;
    this.now = options.now ?? (() => Date.now());
  }

  get size(): number {
    return this.cache.size;
  }

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) {
      this.misses += 1;
      return undefined;
    }

    if (this.isExpired(entry)) {
      this.cache.delete(key);
      this.expirations += 1;
      this.misses += 1;
      return undefined;
    }

    entry.accessCount += 1;
    this.cache.delete(key);
    this.cache.set(key, entry);
    this.hits += 1;
    return entry.value;
  }

  set(key: string, value: T): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.maxSize > 0 && this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value as string | undefined;
      if (oldestKey !== undefined) {
        this.cache.delete(oldestKey);
        this.evictions += 1;
      }
    }

    this.cache.set(key, {
      value,
      timestamp: this.now(),
      accessCount: 0,
    });
  }

  remove(key: string): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
    this.hits = 0;
    this.misses = 0;
    this.evictions = 0;
    this.expirations = 0;
  }

  cleanupExpired(): number {
    if (this.ttlMs <= 0) {
      return 0;
    }

    let removed = 0;
    for (const [key, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        this.cache.delete(key);
        this.expirations += 1;
        removed += 1;
      }
    }
    return removed;
  }

  getStats(): CacheStats {
    const totalRequests = this.hits + this.misses;
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      ttlMs: this.ttlMs,
      hits: this.hits,
      misses: this.misses,
      evictions: this.evictions,
      expirations: this.expirations,
      hitRate: totalRequests > 0 ? this.hits / totalRequests : 0,
      totalRequests,
    };
  }

  private isExpired(entry: CacheEntry<T>): boolean {
    return this.ttlMs > 0 && this.now() - entry.timestamp > this.ttlMs;
  }
}

