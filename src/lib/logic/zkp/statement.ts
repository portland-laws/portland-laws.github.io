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
  rulesetId?: string;
}

export interface ZkpProofStatement {
  statement: ZkpStatement;
  circuitId: string;
  proofType: string;
  witnessCount: number;
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

export function witnessToDict(witness: ZkpWitness): Record<string, string | number | string[] | null> {
  return {
    axioms: [...witness.axioms],
    theorem: witness.theorem ?? null,
    intermediate_steps: [...(witness.intermediateSteps ?? [])],
    axioms_commitment_hex: witness.axiomsCommitmentHex ?? null,
    circuit_version: witness.circuitVersion ?? 1,
    ruleset_id: witness.rulesetId ?? 'TDFOL_v1',
  };
}

export function witnessFromDict(data: Record<string, unknown>): ZkpWitness {
  const axioms = data.axioms;
  if (!Array.isArray(axioms)) {
    throw new Error('axioms must be an array');
  }

  const intermediateSteps = data.intermediate_steps;
  if (intermediateSteps !== undefined && !Array.isArray(intermediateSteps)) {
    throw new Error('intermediate_steps must be an array when present');
  }

  return {
    axioms: axioms.map(String),
    theorem: data.theorem === undefined || data.theorem === null ? undefined : String(data.theorem),
    intermediateSteps: intermediateSteps === undefined ? [] : intermediateSteps.map(String),
    axiomsCommitmentHex:
      data.axioms_commitment_hex === undefined || data.axioms_commitment_hex === null
        ? undefined
        : String(data.axioms_commitment_hex),
    circuitVersion: data.circuit_version === undefined ? 1 : Number(data.circuit_version),
    rulesetId: data.ruleset_id === undefined ? 'TDFOL_v1' : String(data.ruleset_id),
  };
}

export function proofStatementToDict(
  proofStatement: ZkpProofStatement,
): Record<string, string | number | Record<string, string | number>> {
  return {
    statement: statementToDict(proofStatement.statement),
    circuit_id: proofStatement.circuitId,
    circuit_ref: formatCircuitRef(proofStatement.circuitId, proofStatement.statement.circuitVersion),
    proof_type: proofStatement.proofType,
    witness_count: proofStatement.witnessCount,
  };
}

export function proofStatementFromDict(data: Record<string, unknown>): ZkpProofStatement {
  if (!data.statement || typeof data.statement !== 'object' || Array.isArray(data.statement)) {
    throw new Error('statement must be an object');
  }
  return {
    statement: statementFromDict(data.statement as Record<string, unknown>),
    circuitId: String(data.circuit_id || ''),
    proofType: data.proof_type === undefined ? 'simulated' : String(data.proof_type),
    witnessCount: data.witness_count === undefined ? 0 : Number(data.witness_count),
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
