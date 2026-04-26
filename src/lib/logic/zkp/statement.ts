import { sha256FieldInt } from './canonicalization';

const U64_MAX = (BigInt(1) << BigInt(64)) - BigInt(1);

export interface ZkpStatement {
  theoremHash: string;
  axiomsCommitment: string;
  circuitVersion: number;
  rulesetId: string;
}

export interface ZkpWitness {
  axioms: string[];
  theorem?: string;
  intermediateSteps?: string[];
  axiomsCommitmentHex?: string;
  circuitVersion?: number;
}

export function parseCircuitRef(circuitRef: string): { circuitId: string; version: bigint } {
  if (typeof circuitRef !== 'string') {
    throw new TypeError('circuitRef must be a string');
  }
  if (!circuitRef) {
    throw new Error('circuitRef cannot be empty');
  }

  const [circuitId, versionPart, ...rest] = circuitRef.split('@v');
  if (!versionPart || rest.length > 0) {
    throw new Error('circuitRef must be of the form circuit_id@v<uint64>');
  }
  if (!circuitId || circuitId.includes('@')) {
    throw new Error('circuit_id is invalid');
  }
  if (!/^[0-9]+$/.test(versionPart)) {
    throw new Error('circuitRef version must be an unsigned base-10 integer');
  }

  const version = BigInt(versionPart);
  if (version > U64_MAX) {
    throw new Error('circuitRef version must be in uint64 range');
  }

  return { circuitId, version };
}

export function parseCircuitRefLenient(
  circuitRef: string,
  legacyDefaultVersion = BigInt(1),
): { circuitId: string; version: bigint } {
  if (circuitRef.includes('@v')) {
    return parseCircuitRef(circuitRef);
  }
  if (!circuitRef || circuitRef.includes('@')) {
    throw new Error('legacy circuit_id is invalid');
  }
  if (legacyDefaultVersion < BigInt(0) || legacyDefaultVersion > U64_MAX) {
    throw new Error('legacyDefaultVersion must be in uint64 range');
  }
  return { circuitId: circuitRef, version: legacyDefaultVersion };
}

export function formatCircuitRef(circuitId: string, version: bigint | number): string {
  if (!circuitId || circuitId.includes('@')) {
    throw new Error('circuit_id is invalid');
  }
  const normalizedVersion = BigInt(version);
  if (normalizedVersion < BigInt(0) || normalizedVersion > U64_MAX) {
    throw new Error('version must be in uint64 range');
  }
  return `${circuitId}@v${normalizedVersion.toString()}`;
}

export function statementToDict(statement: ZkpStatement): Record<string, string | number> {
  return {
    theorem_hash: statement.theoremHash,
    axioms_commitment: statement.axiomsCommitment,
    circuit_version: statement.circuitVersion,
    ruleset_id: statement.rulesetId,
  };
}

export function statementFromDict(data: Record<string, unknown>): ZkpStatement {
  return {
    theoremHash: String(data.theorem_hash || ''),
    axiomsCommitment: String(data.axioms_commitment || ''),
    circuitVersion: Number(data.circuit_version || 0),
    rulesetId: String(data.ruleset_id || ''),
  };
}

export async function statementToFieldElements(statement: ZkpStatement): Promise<bigint[]> {
  return [
    BigInt(`0x${statement.theoremHash}`) % (await fieldModulus()),
    BigInt(`0x${statement.axiomsCommitment}`) % (await fieldModulus()),
    BigInt(statement.circuitVersion),
    await sha256FieldInt(statement.rulesetId),
  ];
}

async function fieldModulus(): Promise<bigint> {
  const { BN254_FIELD_MODULUS } = await import('./canonicalization');
  return BN254_FIELD_MODULUS;
}
