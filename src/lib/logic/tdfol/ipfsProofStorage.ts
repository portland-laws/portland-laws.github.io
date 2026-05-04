import { BoundedCache } from '../cache';
import type { ProofResult } from '../types';
import { canonicalizeJson, createBrowserLocalCid } from './ipfsCacheDemo';

export interface TdfolProofStoragePayload {
  theorem: string;
  proof: ProofResult;
  formula?: string;
  axioms?: string[];
  metadata?: Record<string, unknown>;
}

export type TdfolStoredProof = {
  cid: string;
  payload: TdfolProofStoragePayload;
  canonicalJson: string;
  storedAt: number;
  sourcePythonModule: 'logic/TDFOL/p2p/ipfs_proof_storage.py';
};
export type TdfolIpfsProofTransport = {
  readonly mode: 'browser-native-ipfs';
  addProof?(entry: TdfolStoredProof): Promise<string>;
  getProof?(cid: string): Promise<TdfolStoredProof | undefined>;
};
export type TdfolProofStorageResult = {
  ok: boolean;
  cid: string;
  source: 'browser-cache' | 'browser-native-ipfs' | 'unavailable-ipfs-adapter';
  entry?: TdfolStoredProof;
  error?: string;
};

export const TDFOL_IPFS_PROOF_STORAGE_STATUS = {
  sourcePythonModule: 'logic/TDFOL/p2p/ipfs_proof_storage.py',
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  defaultMode: 'browser-cache-fail-closed',
} as const;

export class BrowserTdfolIpfsProofStorage {
  private readonly cache: BoundedCache<TdfolStoredProof>;
  private readonly now: () => number;
  private readonly transport?: TdfolIpfsProofTransport;

  constructor(
    options: {
      maxEntries?: number;
      ttlMs?: number;
      now?: () => number;
      transport?: TdfolIpfsProofTransport;
    } = {},
  ) {
    this.now = options.now ?? (() => Date.now());
    this.transport = options.transport;
    this.cache = new BoundedCache<TdfolStoredProof>({
      maxSize: options.maxEntries ?? 256,
      ttlMs: options.ttlMs ?? 60 * 60 * 1000,
      now: this.now,
    });
  }

  async storeProof(payload: TdfolProofStoragePayload): Promise<TdfolProofStorageResult> {
    const normalized = normalizeProofStoragePayload(payload);
    const canonicalJson = canonicalizeJson(normalized);
    const cid = createBrowserLocalCid(canonicalJson);
    const entry = {
      cid,
      payload: normalized,
      canonicalJson,
      storedAt: this.now(),
      sourcePythonModule: TDFOL_IPFS_PROOF_STORAGE_STATUS.sourcePythonModule,
    };
    this.cache.set(cid, entry);
    if (!this.transport?.addProof) return { ok: true, cid, source: 'browser-cache', entry };
    try {
      const remoteCid = await this.transport.addProof(entry);
      if (remoteCid === cid) return { ok: true, cid, source: 'browser-native-ipfs', entry };
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

  async retrieveProof(cid: string): Promise<TdfolProofStorageResult> {
    const cached = this.cache.get(cid);
    if (cached) return { ok: true, cid, source: 'browser-cache', entry: cached };
    if (!this.transport?.getProof)
      return {
        ok: false,
        cid,
        source: 'unavailable-ipfs-adapter',
        error: 'No browser-native IPFS proof transport was injected.',
      };
    const entry = await this.transport.getProof(cid);
    if (!entry)
      return { ok: false, cid, source: 'browser-native-ipfs', error: 'Proof CID was not found.' };
    if (entry.cid !== cid || createBrowserLocalCid(entry.canonicalJson) !== cid) {
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

  getStats(): ReturnType<BoundedCache<TdfolStoredProof>['getStats']> & {
    transportAvailable: boolean;
    storedProofs: number;
  } {
    return {
      ...this.cache.getStats(),
      transportAvailable: this.transport !== undefined,
      storedProofs: this.cache.size,
    };
  }
}

export function normalizeProofStoragePayload(
  payload: TdfolProofStoragePayload,
): TdfolProofStoragePayload {
  if (payload.theorem.trim().length === 0)
    throw new Error('TDFOL proof storage requires a non-empty theorem.');
  return {
    theorem: payload.theorem,
    proof: payload.proof,
    formula: payload.formula,
    axioms: payload.axioms === undefined ? undefined : [...payload.axioms].sort(),
    metadata: payload.metadata === undefined ? undefined : { ...payload.metadata },
  };
}
