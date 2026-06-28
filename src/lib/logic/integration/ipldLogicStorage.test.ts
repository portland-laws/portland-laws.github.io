import {
  BrowserNativeIpldLogicStorage,
  IPLD_LOGIC_STORAGE_METADATA,
  type BrowserNativeIpldLogicTransport,
  type IpldLogicStorageEntry,
} from './ipldLogicStorage';

describe('BrowserNativeIpldLogicStorage', () => {
  it('declares browser-native ipld_logic_storage.py parity', () => {
    expect(IPLD_LOGIC_STORAGE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integration/caching/ipld_logic_storage.py',
      browserNative: true,
      runtimeDependencies: [],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(IPLD_LOGIC_STORAGE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'deterministic_ipld_blocks',
        'fail_closed_unavailable_adapter',
        'cid_verification_on_remote_reads',
      ]),
    );
  });

  it('stores canonical local blocks with order-insensitive axioms', async () => {
    const storage = new BrowserNativeIpldLogicStorage({ now: () => 42 });
    const left = await storage.store({
      logic: 'tdfol',
      formula: 'P -> Q',
      axioms: ['B', 'A'],
      result: { status: 'proved' },
    });
    const right = await storage.store({
      logic: 'tdfol',
      formula: 'P -> Q',
      axioms: ['A', 'B'],
      result: { status: 'proved' },
    });

    expect(left).toMatchObject({ ok: true, cid: right.cid, source: 'browser-cache' });
    expect(left.entry).toMatchObject({ payload: { axioms: ['A', 'B'] }, storedAt: 42 });
    await expect(storage.load(left.cid)).resolves.toMatchObject({
      ok: true,
      source: 'browser-cache',
      entry: { payload: { result: { status: 'proved' } } },
    });
    expect(storage.getStats()).toMatchObject({ hits: 1, size: 1, transportAvailable: false });
  });

  it('fails closed and verifies injected IPLD transport CIDs', async () => {
    const remote = new Map<string, IpldLogicStorageEntry>();
    const transport: BrowserNativeIpldLogicTransport = {
      mode: 'browser-native-ipld',
      async putBlock(entry) {
        remote.set(entry.cid, entry);
        return entry.cid;
      },
      async getBlock(cid) {
        return remote.get(cid);
      },
    };
    const stored = await new BrowserNativeIpldLogicStorage({ transport }).store({
      logic: 'cec',
      formula: 'O(A)',
      result: { ok: true },
    });

    await expect(
      new BrowserNativeIpldLogicStorage({ transport }).load(stored.cid),
    ).resolves.toMatchObject({ ok: true, source: 'browser-native-ipld' });
    await expect(new BrowserNativeIpldLogicStorage().load(stored.cid)).resolves.toMatchObject({
      ok: false,
      source: 'unavailable-ipld-adapter',
    });

    remote.set(stored.cid, { ...remote.get(stored.cid)!, canonicalJson: '{"tampered":true}' });
    await expect(
      new BrowserNativeIpldLogicStorage({ transport }).load(stored.cid),
    ).resolves.toMatchObject({ ok: false, error: 'IPLD logic block CID verification failed.' });
  });
});
