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

export interface ExternalProverIdentity {
  name: string;
  version?: string;
  logic?: string;
  backend?: 'browser-native' | 'wasm' | 'local-adapter' | 'simulated';
}

export interface ExternalProverProofCacheQuery {
  formula: unknown;
  axioms?: Array<unknown>;
  prover: ExternalProverIdentity;
  options?: Record<string, unknown>;
}

export interface ExternalProverProofArtifact {
  status: 'proved' | 'disproved' | 'unknown' | 'error';
  proofText?: string;
  modelText?: string;
  stdout?: string;
  stderr?: string;
  metadata?: Record<string, unknown>;
}

export interface ExternalProverCachedProof extends ExternalProverProofArtifact {
  replayValidated: boolean;
}

export interface ExternalProverProofCacheOptions extends ProofCacheOptions {
  requireReplayValidation?: boolean;
  replayValidator?: (
    query: ExternalProverProofCacheQuery,
    artifact: ExternalProverProofArtifact,
  ) => boolean;
}

export interface IpfsProofCacheQuery {
  formula: unknown;
  axioms?: Array<unknown>;
  proverName?: string;
  proverConfig?: Record<string, unknown>;
}

export interface IpfsProofCacheEntry<Result = unknown> {
  cid: string;
  result: Result;
  query: {
    formula: string;
    axioms: Array<string>;
    proverName: string;
    proverConfig: Record<string, unknown>;
  };
  canonicalJson: string;
  storedAt: number;
  sourcePythonModule: 'logic/integration/caching/ipfs_proof_cache.py';
}

export interface BrowserNativeIpfsProofTransport<Result = unknown> {
  readonly mode: 'browser-native-ipfs';
  addProof(entry: IpfsProofCacheEntry<Result>): Promise<string>;
  getProof(cid: string): Promise<IpfsProofCacheEntry<Result> | undefined>;
}

export interface IpfsProofCacheResult<Result = unknown> {
  ok: boolean;
  cid: string;
  source: 'browser-cache' | 'browser-native-ipfs' | 'unavailable-ipfs-adapter';
  entry?: IpfsProofCacheEntry<Result>;
  error?: string;
}

export interface IpfsProofCacheOptions<Result = unknown> extends ProofCacheOptions {
  transport?: BrowserNativeIpfsProofTransport<Result>;
}

export interface IntegrationCachingProofCacheQuery {
  logic: string;
  formula: unknown;
  axioms?: Array<unknown>;
  bridgeName?: string;
  cacheNamespace?: string;
  proverConfig?: Record<string, unknown>;
  context?: Record<string, unknown>;
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

export const EXTERNAL_PROVER_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/external_provers/proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'external_prover_identity_keys',
    'version_and_logic_sensitive_lookup',
    'option_sensitive_lookup',
    'fail_closed_replay_validation',
    'ttl_lru_statistics',
    'local_snapshot_introspection',
  ] as Array<string>,
} as const;

export const IPFS_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/integration/caching/ipfs_proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'deterministic_content_addressed_entries',
    'order_insensitive_axiom_keys',
    'prover_config_sensitive_lookup',
    'browser_cache_first_reads',
    'injected_browser_ipfs_transport',
    'fail_closed_unavailable_adapter',
    'cid_verification_on_remote_reads',
    'ttl_lru_statistics',
  ] as Array<string>,
} as const;

export const INTEGRATION_CACHING_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/integration/caching/proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'logic_and_bridge_scoped_keys',
    'namespace_sensitive_lookup',
    'order_insensitive_axiom_keys',
    'prover_config_sensitive_lookup',
    'context_sensitive_lookup',
    'ttl_lru_statistics',
    'invalidation_and_snapshot_introspection',
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

export class ExternalProverProofCache {
  private readonly cache: ProofCache<ExternalProverCachedProof>;
  private readonly requireReplayValidation: boolean;
  private readonly replayValidator?: ExternalProverProofCacheOptions['replayValidator'];

  constructor(options: ExternalProverProofCacheOptions = {}) {
    this.cache = new ProofCache<ExternalProverCachedProof>(options);
    this.requireReplayValidation = options.requireReplayValidation ?? false;
    this.replayValidator = options.replayValidator;
  }

  computeCid(query: ExternalProverProofCacheQuery): string {
    return this.cache.computeCid(toProofCacheQuery(query));
  }

  get(query: ExternalProverProofCacheQuery): ExternalProverCachedProof | undefined {
    return this.cache.get(
      String(query.formula),
      normalizeAxiomStrings(query.axioms),
      query.prover.name,
      externalProverConfig(query),
    );
  }

  set(
    query: ExternalProverProofCacheQuery,
    artifact: ExternalProverProofArtifact,
  ): string | undefined {
    const replayValidated = this.replayValidator?.(query, artifact) ?? false;
    if (this.requireReplayValidation && !replayValidated) {
      return undefined;
    }
    const cached: ExternalProverCachedProof = { ...artifact, replayValidated };
    return this.cache.set(
      String(query.formula),
      cached,
      normalizeAxiomStrings(query.axioms),
      query.prover.name,
      externalProverConfig(query),
    );
  }

  snapshot(): Array<ProofCacheSnapshotEntry<ExternalProverCachedProof>> {
    return this.cache.snapshot();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
  }
}

export class IpfsProofCache<Result = unknown> {
  private readonly cache: ProofCache<IpfsProofCacheEntry<Result>>;
  private readonly now: () => number;
  private readonly transport?: BrowserNativeIpfsProofTransport<Result>;

  constructor(options: IpfsProofCacheOptions<Result> = {}) {
    this.now = options.now ?? (() => Date.now());
    this.transport = options.transport;
    this.cache = new ProofCache<IpfsProofCacheEntry<Result>>({ ...options, now: this.now });
  }

  computeCid(query: IpfsProofCacheQuery, result?: Result): string {
    return cidForObject({ query: normalizeIpfsProofQuery(query), result });
  }

  async set(query: IpfsProofCacheQuery, result: Result): Promise<IpfsProofCacheResult<Result>> {
    const normalized = normalizeIpfsProofQuery(query);
    const canonicalJson = stableStringify({ query: normalized, result });
    const cid = cidForObject({ query: normalized, result });
    const entry: IpfsProofCacheEntry<Result> = {
      cid,
      result,
      query: normalized,
      canonicalJson,
      storedAt: this.now(),
      sourcePythonModule: IPFS_PROOF_CACHE_METADATA.sourcePythonModule,
    };
    this.cache.set(cid, entry);
    if (!this.transport) {
      return { ok: true, cid, source: 'browser-cache', entry };
    }
    try {
      const remoteCid = await this.transport.addProof(entry);
      if (remoteCid === cid) {
        return { ok: true, cid, source: 'browser-native-ipfs', entry };
      }
      return {
        ok: false,
        cid,
        source: 'browser-native-ipfs',
        entry,
        error: `Injected IPFS transport returned ${remoteCid}`,
      };
    } catch (error) {
      return { ok: false, cid, source: 'browser-native-ipfs', entry, error: String(error) };
    }
  }

  async get(cid: string): Promise<IpfsProofCacheResult<Result>> {
    const cached = this.cache.get(cid);
    if (cached) {
      return { ok: true, cid, source: 'browser-cache', entry: cached };
    }
    if (!this.transport) {
      return {
        ok: false,
        cid,
        source: 'unavailable-ipfs-adapter',
        error: 'No browser-native IPFS proof cache transport was injected.',
      };
    }
    const entry = await this.transport.getProof(cid);
    if (!entry) {
      return { ok: false, cid, source: 'browser-native-ipfs', error: 'Proof CID was not found.' };
    }
    if (!verifyIpfsProofEntry(entry, cid)) {
      return {
        ok: false,
        cid,
        source: 'browser-native-ipfs',
        error: 'Proof CID verification failed.',
      };
    }
    this.cache.set(cid, entry);
    return { ok: true, cid, source: 'browser-native-ipfs', entry };
  }

  snapshot(): Array<ProofCacheSnapshotEntry<IpfsProofCacheEntry<Result>>> {
    return this.cache.snapshot();
  }

  getStats(): ProofCacheStats & { transportAvailable: boolean } {
    return { ...this.cache.getStats(), transportAvailable: this.transport !== undefined };
  }
}

export class IntegrationCachingProofCache<Result = unknown> {
  private readonly cache: ProofCache<Result>;

  constructor(options: ProofCacheOptions = {}) {
    this.cache = new ProofCache<Result>(options);
  }

  computeCid(query: IntegrationCachingProofCacheQuery): string {
    return this.cache.computeCid(
      toIntegrationProofCacheQuery(normalizeIntegrationProofQuery(query)),
    );
  }

  set(query: IntegrationCachingProofCacheQuery, result: Result): string {
    const normalized = normalizeIntegrationProofQuery(query);
    return this.cache.set(
      normalized.formula,
      result,
      normalized.axioms,
      integrationProofProverName(normalized),
      integrationProofConfig(normalized),
    );
  }

  get(query: IntegrationCachingProofCacheQuery): Result | undefined {
    const normalized = normalizeIntegrationProofQuery(query);
    return this.cache.get(
      normalized.formula,
      normalized.axioms,
      integrationProofProverName(normalized),
      integrationProofConfig(normalized),
    );
  }

  invalidate(query: IntegrationCachingProofCacheQuery): boolean {
    const normalized = normalizeIntegrationProofQuery(query);
    return this.cache.invalidate(
      normalized.formula,
      normalized.axioms,
      integrationProofProverName(normalized),
      integrationProofConfig(normalized),
    );
  }

  snapshot(): Array<ProofCacheSnapshotEntry<Result>> {
    return this.cache.snapshot();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
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

function toProofCacheQuery(query: ExternalProverProofCacheQuery): ProofCacheQuery {
  return {
    formula: String(query.formula),
    axioms: normalizeAxiomStrings(query.axioms),
    proverName: query.prover.name,
    proverConfig: externalProverConfig(query),
  };
}

function externalProverConfig(query: ExternalProverProofCacheQuery): Record<string, unknown> {
  return {
    backend: query.prover.backend,
    logic: query.prover.logic,
    options: query.options ?? {},
    version: query.prover.version,
  };
}

function normalizeIpfsProofQuery(
  query: IpfsProofCacheQuery,
): IpfsProofCacheEntry<unknown>['query'] {
  return {
    formula: String(query.formula),
    axioms: normalizeAxiomStrings(query.axioms),
    proverName: query.proverName ?? 'unknown',
    proverConfig: query.proverConfig ?? {},
  };
}

function verifyIpfsProofEntry(entry: IpfsProofCacheEntry<unknown>, expectedCid: string): boolean {
  return (
    entry.cid === expectedCid &&
    entry.sourcePythonModule === IPFS_PROOF_CACHE_METADATA.sourcePythonModule &&
    entry.canonicalJson === stableStringify({ query: entry.query, result: entry.result }) &&
    cidForObject({ query: entry.query, result: entry.result }) === expectedCid
  );
}

function normalizeIntegrationProofQuery(
  query: IntegrationCachingProofCacheQuery,
): Required<IntegrationCachingProofCacheQuery> & { formula: string; axioms: Array<string> } {
  const logic = query.logic.trim();
  const formula = String(query.formula).trim();
  if (logic.length === 0)
    throw new Error('Integration proof cache requires a non-empty logic identifier.');
  if (formula.length === 0)
    throw new Error('Integration proof cache requires a non-empty formula.');
  return {
    logic,
    formula,
    axioms: normalizeAxiomStrings(query.axioms),
    bridgeName: query.bridgeName ?? 'unknown',
    cacheNamespace: query.cacheNamespace ?? 'default',
    proverConfig: query.proverConfig ?? {},
    context: query.context ?? {},
  };
}

function toIntegrationProofCacheQuery(
  query: Required<IntegrationCachingProofCacheQuery> & { formula: string; axioms: Array<string> },
): ProofCacheQuery {
  return {
    formula: query.formula,
    axioms: query.axioms,
    proverName: integrationProofProverName(query),
    proverConfig: integrationProofConfig(query),
  };
}

function integrationProofProverName(
  query: Required<IntegrationCachingProofCacheQuery> & { formula: string; axioms: Array<string> },
): string {
  return `${query.logic}:${query.bridgeName}:${query.cacheNamespace}`;
}

function integrationProofConfig(
  query: Required<IntegrationCachingProofCacheQuery> & { formula: string; axioms: Array<string> },
): Record<string, unknown> {
  return {
    context: query.context,
    proverConfig: query.proverConfig,
  };
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
