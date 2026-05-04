import { BoundedCache, type CacheStats } from '../cache';
import type { ProofResult } from '../types';

export interface TdfolIpfsProofPayload {
  theorem: string;
  proof: ProofResult;
  formula?: string;
  metadata?: Record<string, unknown>;
}

export interface TdfolIpfsCacheDemoOptions {
  maxEntries?: number;
  ttlMs?: number;
  now?: () => number;
}

export interface TdfolIpfsCacheEntry {
  cid: string;
  payload: TdfolIpfsProofPayload;
  canonicalJson: string;
  cachedAt: number;
}

export interface TdfolIpfsCacheLookup {
  cid: string;
  hit: boolean;
  source: 'browser-cache' | 'unavailable-ipfs-adapter';
  entry?: TdfolIpfsCacheEntry;
  error?: string;
}

export interface TdfolIpfsCacheDemoResult {
  cid: string;
  firstLookup: TdfolIpfsCacheLookup;
  secondLookup: TdfolIpfsCacheLookup;
  stats: CacheStats;
  transport: typeof IPFS_TRANSPORT_STATUS;
}

export class BrowserTdfolIpfsCacheDemo {
  private readonly cache: BoundedCache<TdfolIpfsCacheEntry>;
  private readonly now: () => number;

  constructor(options: TdfolIpfsCacheDemoOptions = {}) {
    this.now = options.now ?? (() => Date.now());
    this.cache = new BoundedCache<TdfolIpfsCacheEntry>({
      maxSize: options.maxEntries ?? 32,
      ttlMs: options.ttlMs ?? 5 * 60 * 1000,
      now: this.now,
    });
  }

  putProof(payload: TdfolIpfsProofPayload): TdfolIpfsCacheEntry {
    const canonicalJson = canonicalizeJson(payload);
    const cid = createBrowserLocalCid(canonicalJson);
    const entry: TdfolIpfsCacheEntry = { cid, payload, canonicalJson, cachedAt: this.now() };
    this.cache.set(cid, entry);
    return entry;
  }

  getProof(cid: string): TdfolIpfsCacheLookup {
    const entry = this.cache.get(cid);
    if (entry) {
      return { cid, hit: true, source: 'browser-cache', entry };
    }
    return {
      cid,
      hit: false,
      source: 'unavailable-ipfs-adapter',
      error: IPFS_TRANSPORT_STATUS.reason,
    };
  }

  getStats(): CacheStats {
    return this.cache.getStats();
  }

  run(payload: TdfolIpfsProofPayload): TdfolIpfsCacheDemoResult {
    const entry = this.putProof(payload);
    const firstLookup = this.getProof(entry.cid);
    const secondLookup = this.getProof(entry.cid);
    return {
      cid: entry.cid,
      firstLookup,
      secondLookup,
      stats: this.getStats(),
      transport: IPFS_TRANSPORT_STATUS,
    };
  }
}

export const IPFS_TRANSPORT_STATUS = {
  available: false,
  mode: 'fail-closed-local-only',
  reason:
    'Browser TDFOL demo cache does not contact IPFS without an injected browser-native transport.',
} as const;

export function demonstrateTdfolIpfsCache(
  payload: TdfolIpfsProofPayload,
): TdfolIpfsCacheDemoResult {
  return new BrowserTdfolIpfsCacheDemo().run(payload);
}

export function createBrowserLocalCid(canonicalJson: string): string {
  return `bafylogic${fnv1a64Hex(canonicalJson)}`;
}

export function canonicalizeJson(value: unknown): string {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalizeJson(item)).join(',')}]`;
  }

  const record = value as Record<string, unknown>;
  const keys = Object.keys(record)
    .filter((key) => record[key] !== undefined)
    .sort();
  const pairs = keys.map((key) => `${JSON.stringify(key)}:${canonicalizeJson(record[key])}`);
  return `{${pairs.join(',')}}`;
}

function fnv1a64Hex(input: string): string {
  let high = fnv1a32(`high:${input}`);
  let low = fnv1a32(`low:${input}`);
  for (let index = 0; index < input.length; index += 1) {
    const code = input.charCodeAt(index);
    high = Math.imul(high ^ code, 16777619) >>> 0;
    low = Math.imul(low ^ (code + index), 16777619) >>> 0;
  }

  return `${high.toString(16).padStart(8, '0')}${low.toString(16).padStart(8, '0')}`;
}

function fnv1a32(input: string): number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < input.length; index += 1) {
    hash = Math.imul(hash ^ input.charCodeAt(index), 16777619) >>> 0;
  }
  return hash;
}
