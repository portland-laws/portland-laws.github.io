import {
  BrowserNativeUnixfsIntegration,
  UNIXFS_INTEGRATION_METADATA,
  type BrowserNativeUnixfsTransport,
  type UnixfsEntry,
} from './unixfsIntegration';

describe('BrowserNativeUnixfsIntegration', () => {
  it('declares browser-native unixfs_integration.py parity without Python or server calls', () => {
    expect(UNIXFS_INTEGRATION_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integrations/unixfs_integration.py',
      browserNative: true,
      runtimeDependencies: [],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(UNIXFS_INTEGRATION_METADATA.parity).toEqual(
      expect.arrayContaining([
        'deterministic_file_cids',
        'directory_link_materialization',
        'fail_closed_unavailable_adapter',
      ]),
    );
  });

  it('adds and reads deterministic browser-native file bytes by path or CID', async () => {
    const unixfs = new BrowserNativeUnixfsIntegration();
    const left = await unixfs.addFile({
      path: '/logic/proofs/result.json',
      content: '{"ok":true}',
    });
    const right = await unixfs.addFile({
      path: 'logic/proofs/result.json',
      content: '{"ok":true}',
    });

    expect(left).toMatchObject({ ok: true, cid: right.cid, source: 'browser-memory' });
    await expect(unixfs.cat('logic/proofs/result.json')).resolves.toMatchObject({
      ok: true,
      content: new Uint8Array([123, 34, 111, 107, 34, 58, 116, 114, 117, 101, 125]),
    });
    await expect(unixfs.cat(left.cid!)).resolves.toMatchObject({ ok: true, cid: left.cid });
    await expect(unixfs.addFile({ path: '../escape', content: 'x' })).resolves.toMatchObject({
      ok: false,
      error: 'Error: UnixFS path must stay within a relative root.',
    });
  });

  it('materializes sorted directory links and fails closed without injected transport', async () => {
    const unixfs = new BrowserNativeUnixfsIntegration();
    const beta = await unixfs.addFile({ path: 'proofs/b.txt', content: 'B' });
    const alpha = await unixfs.addFile({ path: 'proofs/a.txt', content: 'A' });
    const directory = await unixfs.addDirectory('proofs', [beta.entry!, alpha.entry!]);

    expect(directory.entry?.links.map((link) => link.name)).toEqual(['a.txt', 'b.txt']);
    await expect(unixfs.list('proofs')).resolves.toMatchObject({
      ok: true,
      entry: { type: 'directory', links: [{ name: 'a.txt' }, { name: 'b.txt' }] },
    });
    await expect(new BrowserNativeUnixfsIntegration().cat(alpha.cid!)).resolves.toMatchObject({
      ok: false,
      source: 'unavailable-unixfs-adapter',
    });
  });

  it('uses injected browser UnixFS transport and verifies remote CIDs', async () => {
    const remote = new Map<string, UnixfsEntry>();
    const transport: BrowserNativeUnixfsTransport = {
      mode: 'browser-native-unixfs',
      async putEntry(entry) {
        remote.set(entry.cid, entry);
        return entry.cid;
      },
      async getEntry(cid) {
        return remote.get(cid);
      },
    };
    const stored = await new BrowserNativeUnixfsIntegration({ transport }).addFile({
      path: 'proofs/remote.txt',
      content: 'remote proof',
    });

    await expect(
      new BrowserNativeUnixfsIntegration({ transport }).cat(stored.cid!),
    ).resolves.toMatchObject({
      ok: true,
      source: 'browser-native-unixfs',
    });
    remote.set(stored.cid!, { ...remote.get(stored.cid!)!, size: 999 });
    await expect(
      new BrowserNativeUnixfsIntegration({ transport }).cat(stored.cid!),
    ).resolves.toMatchObject({
      ok: false,
      error: 'UnixFS entry CID verification failed.',
    });
  });
});
