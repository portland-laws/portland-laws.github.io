import { createHash, webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { BN254_FR_MODULUS, bytes32HexToIntModFr, hashTextToFieldSha256, intTo0x32, packManyPublicInputsForEvm, packPublicInputsForEvm, strip0x } from './evmPublicInputs';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('EVM public input packing', () => {
  const theoremHashHex = '11'.repeat(32);
  const axiomsCommitmentHex = `0x${'22'.repeat(32)}`;

  it('normalizes 0x-prefixed hex and packs integers as 32-byte field elements', () => {
    expect(strip0x(' 0xAB ')).toBe('ab');
    expect(intTo0x32(2)).toBe(`0x${'0'.repeat(63)}2`);
    expect(intTo0x32(BN254_FR_MODULUS + BigInt(1))).toBe(`0x${'0'.repeat(63)}1`);
    expect(bytes32HexToIntModFr(`0x${'ff'.repeat(32)}`)).toBe(BigInt(`0x${'ff'.repeat(32)}`) % BN254_FR_MODULUS);
  });

  it('hashes text to BN254 field elements using SHA-256', async () => {
    const digest = createHash('sha256').update('TDFOL_v1', 'utf8').digest('hex');
    const expected = `0x${(BigInt(`0x${digest}`) % BN254_FR_MODULUS).toString(16).padStart(64, '0')}`;

    await expect(hashTextToFieldSha256('TDFOL_v1')).resolves.toBe(expected);
  });

  it('packs logical public inputs into four EVM-friendly field scalars', async () => {
    const packed = await packPublicInputsForEvm({
      axiomsCommitmentHex,
      circuitVersion: 2,
      rulesetId: 'TDFOL_v1',
      theoremHashHex,
    });

    expect(packed).toHaveLength(4);
    expect(packed[0]).toBe(`0x${theoremHashHex}`);
    expect(packed[1]).toBe(`0x${'22'.repeat(32)}`);
    expect(packed[2]).toBe(`0x${'0'.repeat(63)}2`);
    expect(packed[3]).toMatch(/^0x[0-9a-f]{64}$/);
  });

  it('packs many public input tuples in order', async () => {
    const packed = await packManyPublicInputsForEvm([
      { theoremHashHex, axiomsCommitmentHex, circuitVersion: 1, rulesetId: 'A' },
      { theoremHashHex: '33'.repeat(32), axiomsCommitmentHex: '44'.repeat(32), circuitVersion: BigInt(2), rulesetId: 'B' },
    ]);

    expect(packed).toHaveLength(2);
    expect(packed[0][2]).toBe(`0x${'0'.repeat(63)}1`);
    expect(packed[1][0]).toBe(`0x${(BigInt(`0x${'33'.repeat(32)}`) % BN254_FR_MODULUS).toString(16).padStart(64, '0')}`);
  });

  it('rejects malformed values like the Python helper', async () => {
    expect(() => intTo0x32(-1)).toThrow('non-negative');
    expect(() => bytes32HexToIntModFr('abc')).toThrow('expected 32-byte hex string');
    expect(() => bytes32HexToIntModFr(`${'zz'.repeat(32)}`)).toThrow('invalid hex');
    await expect(
      packPublicInputsForEvm({
        axiomsCommitmentHex,
        circuitVersion: -1,
        rulesetId: 'TDFOL_v1',
        theoremHashHex,
      }),
    ).rejects.toThrow('circuit_version must be non-negative');
    await expect(
      packPublicInputsForEvm({
        axiomsCommitmentHex,
        circuitVersion: BN254_FR_MODULUS,
        rulesetId: 'TDFOL_v1',
        theoremHashHex,
      }),
    ).rejects.toThrow('circuit_version must be < BN254_FR_MODULUS');
  });
});
