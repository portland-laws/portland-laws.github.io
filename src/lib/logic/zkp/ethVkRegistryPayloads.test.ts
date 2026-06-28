import {
  buildManyRegisterVkPayloads,
  buildRegisterVkCalldata,
  buildRegisterVkCalldataFromEntry,
  buildRegisterVkPayload,
  buildRegisterVkPayloadFromEntry,
  build_register_vk_payload,
  circuitIdTextToBytes32,
  keccak256Hex,
  normalizeBytes32Hex,
  vkHashHexToBytes32,
} from './ethVkRegistryPayloads';

describe('EVM VK registry payload helpers', () => {
  const circuitId = 'aa'.repeat(32);
  const vkHash = `0x${'bb'.repeat(32)}`;

  it('normalizes bytes32 values and VK hashes', () => {
    expect(normalizeBytes32Hex(` 0x${circuitId.toUpperCase()} `)).toBe(`0x${circuitId}`);
    expect(vkHashHexToBytes32(vkHash)).toBe(vkHash);
  });

  it('builds registerVK payloads with Python-compatible field names', () => {
    expect(
      buildRegisterVkPayload({
        circuitIdBytes32: circuitId,
        version: 2,
        vkHashHex: vkHash,
      }),
    ).toEqual({
      circuitIdBytes32: `0x${circuitId}`,
      version: 2,
      vkHashBytes32: vkHash,
    });
    expect(
      build_register_vk_payload({
        circuit_id_bytes32: circuitId,
        version: BigInt(3),
        vk_hash_hex: vkHash,
      }),
    ).toEqual({
      circuit_id_bytes32: `0x${circuitId}`,
      version: BigInt(3),
      vk_hash_bytes32: vkHash,
    });
  });

  it('derives registerVK payloads from VK registry entries', () => {
    const expectedCircuitIdBytes32 = circuitIdTextToBytes32('tdfol_v1');

    expect(
      buildRegisterVkPayloadFromEntry({
        circuitId: 'tdfol_v1',
        version: BigInt(7),
        vkHashHex: vkHash,
      }),
    ).toEqual({
      circuitIdBytes32: expectedCircuitIdBytes32,
      version: BigInt(7),
      vkHashBytes32: vkHash,
    });
    expect(
      buildManyRegisterVkPayloads([
        { circuit_id: 'tdfol_v1', version: 1, vk_hash_hex: vkHash },
        { circuitId: 'tdfol_v2', version: 2, vkHashHex: 'cc'.repeat(32) },
      ]).map((payload) => payload.version),
    ).toEqual([1, 2]);
  });

  it('hashes circuit ids with browser-native Keccak-256', () => {
    expect(keccak256Hex('')).toBe(
      '0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470',
    );
    expect(keccak256Hex('hello')).toBe(
      '0x1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8',
    );
    expect(circuitIdTextToBytes32('tdfol_v1')).toMatch(/^0x[0-9a-f]{64}$/);
  });

  it('builds registerVK calldata without RPC or server dependencies', () => {
    const selector = keccak256Hex('registerVK(bytes32,uint64,bytes32,bool)').slice(2, 10);
    expect(
      buildRegisterVkCalldata({
        payload: { circuitIdBytes32: `0x${circuitId}`, version: 1, vkHashBytes32: vkHash },
      }),
    ).toBe(
      `0x${selector}${circuitId}${'1'.padStart(64, '0')}${'bb'.repeat(32)}${''.padStart(64, '0')}`,
    );
    expect(
      buildRegisterVkCalldata({
        overwrite: true,
        payload: { circuitIdBytes32: `0x${circuitId}`, version: BigInt(2), vkHashBytes32: vkHash },
      }).endsWith('1'.padStart(64, '0')),
    ).toBe(true);
    expect(() =>
      buildRegisterVkCalldata({
        overwrite: 'yes' as never,
        payload: { circuitIdBytes32: `0x${circuitId}`, version: 1, vkHashBytes32: vkHash },
      }),
    ).toThrow('overwrite must be bool');
  });

  it('builds calldata directly from registry entries for browser chain clients', () => {
    const bundle = buildRegisterVkCalldataFromEntry(
      { circuitId: 'tdfol_v1', version: 5, vkHashHex: vkHash },
      { overwrite: true },
    );

    expect(bundle.payload.circuitIdBytes32).toBe(circuitIdTextToBytes32('tdfol_v1'));
    expect(bundle.calldata).toMatch(/^0x[0-9a-f]+$/);
    expect(bundle.calldata.endsWith('1'.padStart(64, '0'))).toBe(true);
  });

  it('validates malformed payload values', () => {
    expect(() => normalizeBytes32Hex('abc')).toThrow('32 bytes');
    expect(() => normalizeBytes32Hex('zz'.repeat(32))).toThrow('hex');
    expect(() =>
      buildRegisterVkPayload({ circuitIdBytes32: circuitId, version: -1, vkHashHex: vkHash }),
    ).toThrow('uint64');
    expect(() =>
      buildRegisterVkPayloadFromEntry({ circuitId: '', version: 1, vkHashHex: vkHash }),
    ).toThrow('cannot be empty');
  });
});
