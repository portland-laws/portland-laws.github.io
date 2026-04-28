import {
  buildRegisterVkCalldata,
  buildRegisterVkPayload,
  build_register_vk_payload,
  circuitIdTextToBytes32,
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

  it('fails closed for keccak and calldata helpers until browser crypto/ABI parity lands', () => {
    expect(() => circuitIdTextToBytes32('tdfol_v1')).toThrow('browser-native keccak');
    expect(() =>
      buildRegisterVkCalldata({
        payload: { circuitIdBytes32: `0x${circuitId}`, version: 1, vkHashBytes32: vkHash },
      }),
    ).toThrow('ABI calldata encoding');
    expect(() =>
      buildRegisterVkCalldata({
        overwrite: 'yes' as never,
        payload: { circuitIdBytes32: `0x${circuitId}`, version: 1, vkHashBytes32: vkHash },
      }),
    ).toThrow('overwrite must be bool');
  });

  it('validates malformed payload values', () => {
    expect(() => normalizeBytes32Hex('abc')).toThrow('32 bytes');
    expect(() => normalizeBytes32Hex('zz'.repeat(32))).toThrow('hex');
    expect(() => buildRegisterVkPayload({ circuitIdBytes32: circuitId, version: -1, vkHashHex: vkHash })).toThrow(
      'uint64',
    );
  });
});
