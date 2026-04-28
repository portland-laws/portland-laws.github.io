import { createHash, webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { VKRegistry, computeVkHash } from './vkRegistry';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('VK registry browser-native parity', () => {
  it('computes stable VK hashes for bytes, text, and structured data', async () => {
    await expect(computeVkHash(new Uint8Array([1, 2, 3]))).resolves.toBe(createHash('sha256').update(Buffer.from([1, 2, 3])).digest('hex'));
    await expect(computeVkHash('vk')).resolves.toBe(createHash('sha256').update('vk', 'utf8').digest('hex'));
    await expect(computeVkHash({ b: 2, a: [1] })).resolves.toBe(
      createHash('sha256').update('{"a":[1],"b":2}', 'utf8').digest('hex'),
    );
    await expect(computeVkHash(1 as never)).rejects.toThrow('vk must be bytes, str, dict, or list');
  });

  it('registers, looks up, serializes, and restores VK hashes', async () => {
    const hash = await computeVkHash('vk');
    const registry = new VKRegistry();

    registry.register('tdfol_v1', 1, hash.toUpperCase());
    registry.register('tdfol_v1', 1, hash);
    registry.register('tdfol_v1', 2, hash, { overwrite: true });

    expect(registry.get('tdfol_v1', 1)).toBe(hash);
    expect(registry.getByRef('tdfol_v1@v2')).toBe(hash);
    expect(registry.listVersions('tdfol_v1')).toEqual([1, 2]);
    expect(VKRegistry.fromDict(registry.toDict()).toDict()).toEqual(registry.toDict());
  });

  it('rejects invalid registry entries like the Python helper', async () => {
    const hash = await computeVkHash('vk');
    const registry = new VKRegistry();

    expect(() => registry.register('', 1, hash)).toThrow('circuit_id cannot be empty');
    expect(() => registry.register('bad@id', 1, hash)).toThrow("circuit_id must not contain '@'");
    expect(() => registry.register('tdfol_v1', -1, hash)).toThrow('uint64');
    expect(() => registry.register('tdfol_v1', 1, '00')).toThrow('64 hex');
    registry.register('tdfol_v1', 1, hash);
    expect(() => registry.register('tdfol_v1', 1, '11'.repeat(32))).toThrow('already registered');
    expect(() => VKRegistry.fromDict({ vk_registry: { x: [] } })).toThrow('vk_registry values must be dicts');
    expect(() => VKRegistry.fromDict({ vk_registry: { x: { nope: hash } } })).toThrow('version keys');
  });
});
