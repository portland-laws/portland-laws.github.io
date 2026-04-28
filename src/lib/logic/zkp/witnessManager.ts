import {
  axiomsCommitmentHex as computeAxiomsCommitmentHex,
  canonicalizeAxioms,
  tdfolV1AxiomsCommitmentHexV2,
  theoremHashHex,
} from './canonicalization';
import { MVPCircuit, TDFOLv1DerivationCircuit } from './circuits';
import { deriveTdfolV1Trace } from './legalTheoremSemantics';
import type { ZkpProofStatement, ZkpStatement, ZkpWitness } from './statement';

export class WitnessManager {
  private readonly witnessCache = new Map<string, ZkpWitness>();

  async generateWitness(options: {
    axioms: string[];
    theorem: string;
    intermediateSteps?: string[];
    circuitVersion?: number;
    rulesetId?: string;
  }): Promise<ZkpWitness> {
    const { axioms, theorem } = options;
    const circuitVersion = options.circuitVersion ?? 1;
    const rulesetId = options.rulesetId ?? 'TDFOL_v1';

    if (axioms.length === 0) {
      throw new Error('Cannot generate witness: axioms cannot be empty');
    }

    const canonicalAxioms = canonicalizeAxioms(axioms);
    const axiomsCommitmentHex =
      circuitVersion >= 2 && rulesetId === 'TDFOL_v1'
        ? await tdfolV1AxiomsCommitmentHexV2(canonicalAxioms)
        : await computeAxiomsCommitmentHex(canonicalAxioms);

    let intermediateSteps = options.intermediateSteps;
    if (circuitVersion >= 2 && rulesetId === 'TDFOL_v1' && intermediateSteps === undefined) {
      intermediateSteps = deriveTdfolV1Trace(canonicalAxioms, theorem) ?? [];
    }

    const witness: ZkpWitness = {
      axioms: canonicalAxioms,
      axiomsCommitmentHex,
      circuitVersion,
      intermediateSteps: intermediateSteps ?? [],
      rulesetId,
      theorem,
    };

    this.witnessCache.set(axiomsCommitmentHex, witness);
    return witness;
  }

  generate_witness(
    axioms: string[],
    theorem: string,
    intermediateSteps?: string[],
    circuitVersion = 1,
    rulesetId = 'TDFOL_v1',
  ): Promise<ZkpWitness> {
    return this.generateWitness({
      axioms,
      circuitVersion,
      intermediateSteps,
      rulesetId,
      theorem,
    });
  }

  async validateWitness(
    witness: ZkpWitness,
    expectedAxiomCount?: number,
    expectedAxioms?: string[],
  ): Promise<boolean> {
    try {
      if (!Array.isArray(witness.axioms) || witness.axioms.length === 0) return false;
      if (!witness.axiomsCommitmentHex) return false;
      if (expectedAxiomCount !== undefined && witness.axioms.length !== expectedAxiomCount) return false;
      if (expectedAxioms !== undefined) {
        if (!sameStringList(canonicalizeAxioms(expectedAxioms), canonicalizeAxioms(witness.axioms))) return false;
      }

      const expected =
        (witness.circuitVersion ?? 1) >= 2 && (witness.rulesetId ?? 'TDFOL_v1') === 'TDFOL_v1'
          ? await tdfolV1AxiomsCommitmentHexV2(witness.axioms)
          : await computeAxiomsCommitmentHex(witness.axioms);
      return expected === witness.axiomsCommitmentHex;
    } catch {
      return false;
    }
  }

  validate_witness(
    witness: ZkpWitness,
    expectedAxiomCount?: number,
    expectedAxioms?: string[],
  ): Promise<boolean> {
    return this.validateWitness(witness, expectedAxiomCount, expectedAxioms);
  }

  async createProofStatement(
    witness: ZkpWitness,
    theorem: string,
    circuitId = 'knowledge_of_axioms',
  ): Promise<ZkpProofStatement> {
    const statement: ZkpStatement = {
      axiomsCommitment: witness.axiomsCommitmentHex ?? '',
      circuitVersion: witness.circuitVersion ?? 1,
      rulesetId: witness.rulesetId ?? 'TDFOL_v1',
      theoremHash: await theoremHashHex(theorem),
    };
    return {
      circuitId,
      proofType: 'simulated',
      statement,
      witnessCount: witness.axioms.length,
    };
  }

  create_proof_statement(
    witness: ZkpWitness,
    theorem: string,
    circuitId = 'knowledge_of_axioms',
  ): Promise<ZkpProofStatement> {
    return this.createProofStatement(witness, theorem, circuitId);
  }

  async verifyWitnessConsistency(witness: ZkpWitness, statement: ZkpStatement): Promise<boolean> {
    try {
      if ((statement.circuitVersion >= 2 || (witness.circuitVersion ?? 1) >= 2) && statement.rulesetId === 'TDFOL_v1') {
        return new TDFOLv1DerivationCircuit(statement.circuitVersion).verifyConstraints(witness, statement);
      }
      return new MVPCircuit(statement.circuitVersion).verifyConstraints(witness, statement);
    } catch {
      return false;
    }
  }

  verify_witness_consistency(witness: ZkpWitness, statement: ZkpStatement): Promise<boolean> {
    return this.verifyWitnessConsistency(witness, statement);
  }

  clearCache(): void {
    this.witnessCache.clear();
  }

  clear_cache(): void {
    this.clearCache();
  }

  getCachedWitness(commitmentHex: string): ZkpWitness | undefined {
    const witness = this.witnessCache.get(commitmentHex);
    return witness ? { ...witness, axioms: [...witness.axioms], intermediateSteps: [...(witness.intermediateSteps ?? [])] } : undefined;
  }

  get_cached_witness(commitmentHex: string): ZkpWitness | undefined {
    return this.getCachedWitness(commitmentHex);
  }
}

function sameStringList(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}
