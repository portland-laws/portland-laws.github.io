import { canonicalizeJson } from '../tdfol/ipfsCacheDemo';

export type UnixfsEntryType = 'file' | 'directory';
export type UnixfsLink = { name: string; cid: string; type: UnixfsEntryType; size: number };
export type UnixfsEntry = {
  cid: string;
  path: string;
  type: UnixfsEntryType;
  size: number;
  bytes?: Uint8Array;
  links: Array<UnixfsLink>;
  metadata?: Record<string, unknown>;
  sourcePythonModule: 'logic/integrations/unixfs_integration.py';
};
export type BrowserNativeUnixfsTransport = {
  readonly mode: 'browser-native-unixfs';
  putEntry(entry: UnixfsEntry): Promise<string>;
  getEntry(cid: string): Promise<UnixfsEntry | undefined>;
};
export type UnixfsResult = {
  ok: boolean;
  source: 'browser-memory' | 'browser-native-unixfs' | 'unavailable-unixfs-adapter';
  cid?: string;
  entry?: UnixfsEntry;
  content?: Uint8Array;
  error?: string;
};

export const UNIXFS_INTEGRATION_METADATA = {
  sourcePythonModule: 'logic/integrations/unixfs_integration.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'deterministic_file_cids',
    'unix_style_path_normalization',
    'directory_link_materialization',
    'browser_uint8array_content',
    'injected_browser_unixfs_transport',
    'fail_closed_unavailable_adapter',
    'cid_verification_on_remote_reads',
  ] as Array<string>,
} as const;

export class BrowserNativeUnixfsIntegration {
  private readonly byCid = new Map<string, UnixfsEntry>();
  private readonly byPath = new Map<string, string>();

  constructor(private readonly options: { transport?: BrowserNativeUnixfsTransport } = {}) {}

  async addFile(input: {
    path: string;
    content: string | Uint8Array;
    metadata?: Record<string, unknown>;
  }): Promise<UnixfsResult> {
    try {
      const path = normalizeUnixfsPath(input.path);
      const bytes = typeof input.content === 'string' ? encodeUtf8(input.content) : input.content;
      const entry = materializeUnixfsEntry({
        path,
        type: 'file',
        size: bytes.length,
        bytes,
        links: [],
        metadata: input.metadata,
      });
      return this.store(entry);
    } catch (error) {
      return { ok: false, source: 'browser-memory', error: String(error) };
    }
  }

  async addDirectory(path: string, children: Array<UnixfsEntry>): Promise<UnixfsResult> {
    try {
      const links = children
        .map(toUnixfsLink)
        .sort((left, right) => left.name.localeCompare(right.name));
      return this.store(
        materializeUnixfsEntry({
          path: normalizeUnixfsPath(path),
          type: 'directory',
          size: links.reduce((sum, link) => sum + link.size, 0),
          links,
        }),
      );
    } catch (error) {
      return { ok: false, source: 'browser-memory', error: String(error) };
    }
  }

  async cat(cidOrPath: string): Promise<UnixfsResult> {
    const result = await this.resolve(cidOrPath);
    if (!result.ok || !result.entry) return result;
    if (result.entry.type !== 'file')
      return { ok: false, source: result.source, error: 'UnixFS entry is not a file.' };
    return { ...result, content: result.entry.bytes };
  }

  async list(cidOrPath: string): Promise<UnixfsResult> {
    const result = await this.resolve(cidOrPath);
    if (!result.ok || !result.entry || result.entry.type === 'directory') return result;
    return { ok: false, source: result.source, error: 'UnixFS entry is not a directory.' };
  }

  private async store(entry: UnixfsEntry): Promise<UnixfsResult> {
    this.byCid.set(entry.cid, entry);
    this.byPath.set(entry.path, entry.cid);
    if (!this.options.transport)
      return { ok: true, source: 'browser-memory', cid: entry.cid, entry };
    const remoteCid = await this.options.transport.putEntry(entry);
    return remoteCid === entry.cid
      ? { ok: true, source: 'browser-native-unixfs', cid: entry.cid, entry }
      : {
          ok: false,
          source: 'browser-native-unixfs',
          cid: entry.cid,
          entry,
          error: `Injected UnixFS transport returned ${remoteCid}`,
        };
  }

  private async resolve(cidOrPath: string): Promise<UnixfsResult> {
    const cid = this.byPath.get(normalizeUnixfsPath(cidOrPath, true)) ?? cidOrPath;
    const cached = this.byCid.get(cid);
    if (cached) return { ok: true, source: 'browser-memory', cid, entry: cached };
    if (!this.options.transport)
      return {
        ok: false,
        source: 'unavailable-unixfs-adapter',
        cid,
        error: 'No browser-native UnixFS transport was injected.',
      };
    const entry = await this.options.transport.getEntry(cid);
    if (!entry)
      return {
        ok: false,
        source: 'browser-native-unixfs',
        cid,
        error: 'UnixFS entry was not found.',
      };
    if (!verifyUnixfsEntry(entry, cid))
      return {
        ok: false,
        source: 'browser-native-unixfs',
        cid,
        error: 'UnixFS entry CID verification failed.',
      };
    this.byCid.set(cid, entry);
    this.byPath.set(entry.path, cid);
    return { ok: true, source: 'browser-native-unixfs', cid, entry };
  }
}

export function normalizeUnixfsPath(path: string, allowCid = false): string {
  if (allowCid && path.startsWith('bafylogicunixfs')) return path;
  const parts = path.split('/').filter((part) => part.length > 0 && part !== '.');
  if (parts.length === 0 || parts.some((part) => part === '..'))
    throw new Error('UnixFS path must stay within a relative root.');
  return parts.join('/');
}

export function verifyUnixfsEntry(entry: UnixfsEntry, expectedCid: string): boolean {
  return (
    entry.cid === expectedCid &&
    entry.sourcePythonModule === UNIXFS_INTEGRATION_METADATA.sourcePythonModule &&
    unixfsCid(entry) === expectedCid
  );
}

function materializeUnixfsEntry(
  input: Omit<UnixfsEntry, 'cid' | 'sourcePythonModule'>,
): UnixfsEntry {
  const entry = {
    ...input,
    metadata: input.metadata === undefined ? undefined : { ...input.metadata },
  };
  return {
    ...entry,
    cid: unixfsCid(entry),
    sourcePythonModule: UNIXFS_INTEGRATION_METADATA.sourcePythonModule,
  };
}

function toUnixfsLink(entry: UnixfsEntry): UnixfsLink {
  return {
    name: entry.path.split('/').pop() ?? entry.path,
    cid: entry.cid,
    type: entry.type,
    size: entry.size,
  };
}

function unixfsCid(entry: Omit<UnixfsEntry, 'cid' | 'sourcePythonModule'>): string {
  const body = {
    path: entry.path,
    type: entry.type,
    size: entry.size,
    bytes: entry.bytes === undefined ? undefined : hashBytes(entry.bytes),
    links: entry.links,
    metadata: entry.metadata,
  };
  return `bafylogicunixfs${hashString(canonicalizeJson(body))}`;
}

function encodeUtf8(value: string): Uint8Array {
  if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(value);
  return new Uint8Array(Array.from(value, (char) => char.charCodeAt(0) & 0xff));
}

function hashString(value: string): string {
  return hashBytes(encodeUtf8(value));
}

function hashBytes(bytes: Uint8Array): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < bytes.length; index += 1)
    hash = Math.imul(hash ^ bytes[index], 16777619) >>> 0;
  return hash.toString(16).padStart(8, '0');
}
