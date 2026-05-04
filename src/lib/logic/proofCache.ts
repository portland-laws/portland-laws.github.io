export interface CachedProofResult<Result = unknown> {
  result: Result;
  cid: string;
  proverName: string;
  formulaString: string;
  axiomStrings: Array<string>;
  proverConfig: Record<string, unknown>;
  timestamp: number;
  hitCount: number;
}

export interface ProofCacheStats {
  hits: number;
  misses: number;
  sets: number;
  evictions: number;
  totalRequests: number;
  hitRate: number;
  cacheSize: number;
  maxSize: number;
  ttlMs: number;
}

export interface ProofCacheOptions {
  maxSize?: number;
  ttlMs?: number;
  now?: () => number;
}

export interface ProofCacheQuery {
  formula: unknown;
  axioms?: unknown[];
  proverName?: string;
  proverConfig?: Record<string, unknown>;
}

export interface ProofCacheSnapshotEntry<Result = unknown> extends CachedProofResult<Result> {
  ageMs: number;
  expired: boolean;
}

export const COMMON_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/common/proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'deterministic_content_ids',
    'order_insensitive_axiom_keys',
    'prover_config_sensitive_lookup',
    'ttl_lru_eviction',
    'invalidation_and_clear',
    'cache_statistics',
    'global_cache_helpers',
    'local_snapshot_introspection',
  ] as Array<string>,
} as const;

export class ProofCache<Result = unknown> {
  readonly maxSize: number;
  readonly ttlMs: number;

  private readonly now: () => number;
  private readonly cache = new Map<string, CachedProofResult<Result>>();
  private hits = 0;
  private misses = 0;
  private sets = 0;
  private evictions = 0;

  constructor(options: ProofCacheOptions = {}) {
    this.maxSize = options.maxSize ?? 1000;
    this.ttlMs = options.ttlMs ?? 60 * 60 * 1000;
    this.now = options.now ?? (() => Date.now());
  }

  computeCid(query: ProofCacheQuery): string {
    return cidForObject({
      formula: String(query.formula),
      axioms: normalizeAxiomStrings(query.axioms),
      prover: query.proverName ?? 'unknown',
      config: query.proverConfig ?? {},
    });
  }

  get(
    formula: unknown,
    axioms?: unknown[] | string,
    proverName = 'unknown',
    proverConfig?: Record<string, unknown>,
  ): Result | undefined {
    const normalized = normalizeProofCacheArgs(formula, axioms, proverName, proverConfig);
    const cid = this.computeCid(normalized);
    const cached = this.cache.get(cid);
    if (!cached) {
      this.misses += 1;
      return undefined;
    }
    if (this.isExpired(cached)) {
      this.cache.delete(cid);
      this.misses += 1;
      return undefined;
    }
    cached.hitCount += 1;
    this.cache.delete(cid);
    this.cache.set(cid, cached);
    this.hits += 1;
    return cached.result;
  }

  set(
    formula: unknown,
    result: Result,
    axioms: unknown[] = [],
    proverName = 'unknown',
    proverConfig?: Record<string, unknown>,
  ): string {
    const normalizedAxioms = normalizeAxiomStrings(axioms);
    const normalizedConfig = proverConfig ?? {};
    const cid = this.computeCid({
      formula,
      axioms: normalizedAxioms,
      proverName,
      proverConfig: normalizedConfig,
    });
    if (this.cache.has(cid)) {
      this.cache.delete(cid);
    } else if (this.maxSize > 0 && this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value as string | undefined;
      if (oldestKey !== undefined) {
        this.cache.delete(oldestKey);
        this.evictions += 1;
      }
    }
    this.cache.set(cid, {
      result,
      cid,
      proverName,
      formulaString: String(formula),
      axiomStrings: normalizedAxioms,
      proverConfig: normalizedConfig,
      timestamp: this.now(),
      hitCount: 0,
    });
    this.sets += 1;
    return cid;
  }

  invalidate(
    formula: unknown,
    axioms: unknown[] = [],
    proverName = 'unknown',
    proverConfig?: Record<string, unknown>,
  ): boolean {
    return this.cache.delete(this.computeCid({ formula, axioms, proverName, proverConfig }));
  }

  clear(): number {
    const count = this.cache.size;
    this.cache.clear();
    return count;
  }

  deleteExpired(): number {
    let deleted = 0;
    for (const [cid, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        this.cache.delete(cid);
        deleted += 1;
      }
    }
    return deleted;
  }

  snapshot(): Array<ProofCacheSnapshotEntry<Result>> {
    return Array.from(this.cache.values(), (entry) => this.snapshotEntry(entry));
  }

  getStats(): ProofCacheStats {
    const totalRequests = this.hits + this.misses;
    return {
      hits: this.hits,
      misses: this.misses,
      sets: this.sets,
      evictions: this.evictions,
      totalRequests,
      hitRate: totalRequests > 0 ? this.hits / totalRequests : 0,
      cacheSize: this.cache.size,
      maxSize: this.maxSize,
      ttlMs: this.ttlMs,
    };
  }

  private isExpired(entry: CachedProofResult<Result>): boolean {
    return this.ttlMs > 0 && this.now() - entry.timestamp > this.ttlMs;
  }

  private snapshotEntry(entry: CachedProofResult<Result>): ProofCacheSnapshotEntry<Result> {
    const ageMs = this.now() - entry.timestamp;
    return {
      ...entry,
      axiomStrings: [...entry.axiomStrings],
      proverConfig: { ...entry.proverConfig },
      ageMs,
      expired: this.ttlMs > 0 && ageMs > this.ttlMs,
    };
  }
}

let globalProofCache: ProofCache | undefined;

export function getGlobalProofCache(): ProofCache {
  globalProofCache ??= new ProofCache();
  return globalProofCache;
}

export function clearGlobalProofCache(): void {
  globalProofCache?.clear();
}

export function cidForObject(value: unknown): string {
  return `browsets-${hashString(stableStringify(value))}`;
}

function normalizeProofCacheArgs(
  formula: unknown,
  axiomsOrProver?: unknown[] | string,
  proverName = 'unknown',
  proverConfig?: Record<string, unknown>,
): ProofCacheQuery {
  if (typeof axiomsOrProver === 'string') {
    return { formula, axioms: [], proverName: axiomsOrProver, proverConfig };
  }
  return { formula, axioms: axiomsOrProver ?? [], proverName, proverConfig };
}

function normalizeAxiomStrings(axioms: unknown[] | undefined): Array<string> {
  return (axioms ?? []).map(String).sort((left, right) => left.localeCompare(right));
}

function hashString(value: string): string {
  let hashA = 0xdeadbeef;
  let hashB = 0x41c6ce57;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    hashA = Math.imul(hashA ^ code, 2654435761);
    hashB = Math.imul(hashB ^ code, 1597334677);
  }
  hashA =
    Math.imul(hashA ^ (hashA >>> 16), 2246822507) ^ Math.imul(hashB ^ (hashB >>> 13), 3266489909);
  hashB =
    Math.imul(hashB ^ (hashB >>> 16), 2246822507) ^ Math.imul(hashA ^ (hashA >>> 13), 3266489909);
  return `${(hashB >>> 0).toString(16).padStart(8, '0')}${(hashA >>> 0).toString(16).padStart(8, '0')}`;
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
