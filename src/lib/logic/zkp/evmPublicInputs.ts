import { BN254_FIELD_MODULUS } from './canonicalization';

export const BN254_FR_MODULUS = BN254_FIELD_MODULUS;

export interface EvmPublicInputTuple {
  theoremHashHex: string;
  axiomsCommitmentHex: string;
  circuitVersion: number | bigint;
  rulesetId: string;
}

export function strip0x(hexString: string): string {
  const value = String(hexString).trim().toLowerCase();
  return value.startsWith('0x') ? value.slice(2) : value;
}

export function intTo0x32(value: number | bigint): string {
  if (typeof value !== 'number' && typeof value !== 'bigint') {
    throw new TypeError('value must be int');
  }
  const intValue = BigInt(value);
  if (intValue < BigInt(0)) {
    throw new Error('value must be non-negative');
  }
  const reduced = intValue % BN254_FR_MODULUS;
  return `0x${reduced.toString(16).padStart(64, '0')}`;
}

export function bytes32HexToIntModFr(bytes32Hex: string): bigint {
  const value = strip0x(bytes32Hex);
  if (value.length !== 64) {
    throw new Error('expected 32-byte hex string');
  }
  if (!/^[0-9a-f]+$/.test(value)) {
    throw new Error('invalid hex');
  }
  return BigInt(`0x${value}`) % BN254_FR_MODULUS;
}

export async function hashTextToFieldSha256(text: string): Promise<string> {
  if (typeof text !== 'string') {
    throw new TypeError('text must be str');
  }
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return intTo0x32(BigInt(`0x${bytesToHex(new Uint8Array(digest))}`));
}

export async function packPublicInputsForEvm(input: EvmPublicInputTuple): Promise<string[]> {
  if (typeof input.circuitVersion !== 'number' && typeof input.circuitVersion !== 'bigint') {
    throw new TypeError('circuit_version must be int');
  }
  const circuitVersion = BigInt(input.circuitVersion);
  if (circuitVersion < BigInt(0)) {
    throw new Error('circuit_version must be non-negative');
  }
  if (circuitVersion >= BN254_FR_MODULUS) {
    throw new Error('circuit_version must be < BN254_FR_MODULUS');
  }

  return [
    intTo0x32(bytes32HexToIntModFr(input.theoremHashHex)),
    intTo0x32(bytes32HexToIntModFr(input.axiomsCommitmentHex)),
    intTo0x32(circuitVersion),
    await hashTextToFieldSha256(input.rulesetId),
  ];
}

export function pack_public_inputs_for_evm(options: {
  theorem_hash_hex: string;
  axioms_commitment_hex: string;
  circuit_version: number | bigint;
  ruleset_id: string;
}): Promise<string[]> {
  return packPublicInputsForEvm({
    axiomsCommitmentHex: options.axioms_commitment_hex,
    circuitVersion: options.circuit_version,
    rulesetId: options.ruleset_id,
    theoremHashHex: options.theorem_hash_hex,
  });
}

export async function packManyPublicInputsForEvm(inputs: Iterable<EvmPublicInputTuple>): Promise<string[][]> {
  const packed: string[][] = [];
  for (const input of inputs) {
    packed.push(await packPublicInputsForEvm(input));
  }
  return packed;
}

export function pack_many_public_inputs_for_evm(
  inputs: Iterable<[string, string, number | bigint, string]>,
): Promise<string[][]> {
  return packManyPublicInputsForEvm(
    [...inputs].map(([theoremHashHex, axiomsCommitmentHex, circuitVersion, rulesetId]) => ({
      axiomsCommitmentHex,
      circuitVersion,
      rulesetId,
      theoremHashHex,
    })),
  );
}

function bytesToHex(bytes: Uint8Array): string {
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}
