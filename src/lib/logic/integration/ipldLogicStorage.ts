import { BoundedCache, type CacheStats } from '../cache';
import { canonicalizeJson, createBrowserLocalCid } from '../tdfol/ipfsCacheDemo';

export type IpldLogicStoragePayload = {
  logic: string;
  formula: string;
  axioms?: Array<string>;
  result?: unknown;
  metadata?: Record<string, unknown>;
};

export type IpldLogicStorageEntry = {
  cid: string;
  payload: IpldLogicStoragePayload;
  canonicalJson: string;
  storedAt: number;
  sourcePythonModule: 'logic/integration/caching/ipld_logic_storage.py';
};

export type BrowserNativeIpldLogicTransport = {
  readonly mode: 'browser-native-ipld';
  putBlock(entry: IpldLogicStorageEntry): Promise<string>;
  getBlock(cid: string): Promise<IpldLogicStorageEntry | undefined>;
};

export type IpldLogicStorageResult = {
  ok: boolean;
  cid: string;
  source: 'browser-cache' | 'browser-native-ipld' | 'unavailable-ipld-adapter';
  entry?: IpldLogicStorageEntry;
  error?: string;
};

export type IpldLogicStorageOptions = {
  maxEntries?: number;
  ttlMs?: number;
  now?: () => number;
  transport?: BrowserNativeIpldLogicTransport;
};

export const IPLD_LOGIC_STORAGE_METADATA = {
  sourcePythonModule: 'logic/integration/caching/ipld_logic_storage.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'deterministic_ipld_blocks',
    'canonical_json_payloads',
    'order_insensitive_axioms',
    'browser_cache_first_reads',
    'injected_browser_ipld_transport',
    'fail_closed_unavailable_adapter',
    'cid_verification_on_remote_reads',
    'ttl_lru_statistics',
  ] as Array<string>,
} as const;

export class BrowserNativeIpldLogicStorage {
  private readonly cache: BoundedCache<IpldLogicStorageEntry>;
  private readonly now: () => number;
  private readonly transport?: BrowserNativeIpldLogicTransport;

  constructor(options: IpldLogicStorageOptions = {}) {
    this.now = options.now ?? (() => Date.now());
    this.transport = options.transport;
    this.cache = new BoundedCache<IpldLogicStorageEntry>({
      maxSize: options.maxEntries ?? 256,
      ttlMs: options.ttlMs ?? 3600000,
      now: this.now,
    });
  }

  async store(payload: IpldLogicStoragePayload): Promise<IpldLogicStorageResult> {
    const normalized = normalizeIpldLogicPayload(payload);
    const canonicalJson = canonicalizeJson(normalized);
    const cid = createBrowserLocalCid(canonicalJson);
    const entry: IpldLogicStorageEntry = {
      cid,
      payload: normalized,
      canonicalJson,
      storedAt: this.now(),
      sourcePythonModule: IPLD_LOGIC_STORAGE_METADATA.sourcePythonModule,
    };
    this.cache.set(cid, entry);
    if (!this.transport) return { ok: true, cid, source: 'browser-cache', entry };
    try {
      const remoteCid = await this.transport.putBlock(entry);
      return remoteCid === cid
        ? { ok: true, cid, source: 'browser-native-ipld', entry }
        : {
            ok: false,
            cid,
            source: 'browser-native-ipld',
            entry,
            error: `Injected IPLD transport returned ${remoteCid}`,
          };
    } catch (error) {
      return { ok: false, cid, source: 'browser-native-ipld', entry, error: String(error) };
    }
  }

  async load(cid: string): Promise<IpldLogicStorageResult> {
    const cached = this.cache.get(cid);
    if (cached) return { ok: true, cid, source: 'browser-cache', entry: cached };
    if (!this.transport)
      return {
        ok: false,
        cid,
        source: 'unavailable-ipld-adapter',
        error: 'No browser-native IPLD logic storage transport was injected.',
      };
    const entry = await this.transport.getBlock(cid);
    if (!entry)
      return {
        ok: false,
        cid,
        source: 'browser-native-ipld',
        error: 'IPLD logic block was not found.',
      };
    if (!verifyIpldLogicEntry(entry, cid))
      return {
        ok: false,
        cid,
        source: 'browser-native-ipld',
        error: 'IPLD logic block CID verification failed.',
      };
    this.cache.set(cid, entry);
    return { ok: true, cid, source: 'browser-native-ipld', entry };
  }

  getStats(): CacheStats & { transportAvailable: boolean } {
    return { ...this.cache.getStats(), transportAvailable: this.transport !== undefined };
  }
}

export function normalizeIpldLogicPayload(
  payload: IpldLogicStoragePayload,
): IpldLogicStoragePayload {
  if (payload.logic.trim().length === 0)
    throw new Error('IPLD logic storage requires a non-empty logic identifier.');
  if (payload.formula.trim().length === 0)
    throw new Error('IPLD logic storage requires a non-empty formula.');
  return {
    logic: payload.logic,
    formula: payload.formula,
    axioms: payload.axioms === undefined ? undefined : [...payload.axioms].sort(),
    result: payload.result,
    metadata: payload.metadata === undefined ? undefined : { ...payload.metadata },
  };
}

export function verifyIpldLogicEntry(entry: IpldLogicStorageEntry, expectedCid: string): boolean {
  return (
    entry.cid === expectedCid &&
    entry.sourcePythonModule === IPLD_LOGIC_STORAGE_METADATA.sourcePythonModule &&
    entry.canonicalJson === canonicalizeJson(entry.payload) &&
    createBrowserLocalCid(entry.canonicalJson) === expectedCid
  );
}
