import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import {
  BrowserNativeZkpIpfsIntegration,
  type BrowserNativeZkpIpfsTransport,
  type ZkpIpfsPackage,
  ZKP_IPFS_INTEGRATION_METADATA,
  verifyZkpIpfsPackage,
} from './ipfsIntegration';

Object.defineProperty(globalThis, 'crypto', { value: webcrypto, configurable: true });
Object.defineProperty(globalThis, 'TextEncoder', { value: TextEncoder, configurable: true });

describe('browser-native ZKP IPFS integration', () => {
  it('creates deterministic private proof packages and fails closed without IPFS', async () => {
    const metadata = { circuit_version: 2, seed: 'fixture' };
    const first = await new BrowserNativeZkpIpfsIntegration({ now: () => 1000 }).proveAndStore(
      'Q',
      ['P -> Q', 'P'],
      { metadata },
    );
    const second = await new BrowserNativeZkpIpfsIntegration({ now: () => 2000 }).proveAndStore(
      'Q',
      ['P', 'P -> Q'],
      { metadata },
    );
    const localOnly = new BrowserNativeZkpIpfsIntegration();

    expect(first.cid).toBe(second.cid);
    expect(first.source).toBe('browser-memory');
    expect(first.package?.axioms).toEqual(['<private>']);
    expect(first.package?.sourcePythonModule).toBe(
      ZKP_IPFS_INTEGRATION_METADATA.sourcePythonModule,
    );
    expect(verifyZkpIpfsPackage(first.package as ZkpIpfsPackage, first.cid)).toBe(true);
    await expect(localOnly.loadAndVerify('bafylogicmissing')).resolves.toMatchObject({
      ok: false,
      source: 'unavailable-ipfs-adapter',
    });
  });

  it('uses injected browser IPFS transport and rejects CID tampering', async () => {
    const blocks = new Map<string, ZkpIpfsPackage>();
    const transport: BrowserNativeZkpIpfsTransport = {
      mode: 'browser-native-ipfs',
      async putPackage(item) {
        blocks.set(item.cid, item);
        return item.cid;
      },
      async getPackage(cid) {
        return blocks.get(cid);
      },
    };
    const stored = await new BrowserNativeZkpIpfsIntegration({ transport }).proveAndStore(
      'Q',
      ['P'],
      {
        privateAxioms: false,
      },
    );
    const reader = new BrowserNativeZkpIpfsIntegration({ transport });

    await expect(reader.loadAndVerify(stored.cid)).resolves.toMatchObject({
      ok: true,
      source: 'browser-native-ipfs',
      verified: true,
    });

    blocks.set('bafylogictampered', {
      ...(stored.package as ZkpIpfsPackage),
      cid: 'bafylogictampered',
      theorem: 'R',
    });
    await expect(reader.loadAndVerify('bafylogictampered')).resolves.toMatchObject({
      ok: false,
      error: 'ZKP proof package CID verification failed.',
    });
  });
});
