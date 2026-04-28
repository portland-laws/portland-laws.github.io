import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { axiomsCommitmentHex, theoremHashHex } from './canonicalization';
import {
  formatCircuitRef,
  parseCircuitRef,
  parseCircuitRefLenient,
  proofStatementFromDict,
  proofStatementToDict,
  statementFromDict,
  statementToDict,
  statementToFieldElements,
  witnessFromDict,
  witnessToDict,
  type ZkpProofStatement,
  type ZkpStatement,
  type ZkpWitness,
} from './statement';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('ZKP statement helpers', () => {
  it('parses and formats circuit references', () => {
    expect(parseCircuitRef('TDFOL_v1@v2')).toEqual({ circuitId: 'TDFOL_v1', version: BigInt(2) });
    expect(parseCircuitRefLenient('TDFOL_v1')).toEqual({ circuitId: 'TDFOL_v1', version: BigInt(1) });
    expect(formatCircuitRef('TDFOL_v1', BigInt(2))).toBe('TDFOL_v1@v2');
  });

  it('rejects malformed circuit references', () => {
    expect(() => parseCircuitRef('TDFOL_v1')).toThrow('circuitRef must be of the form');
    expect(() => parseCircuitRef('TDFOL_v1@vnope')).toThrow('unsigned base-10 integer');
    expect(() => formatCircuitRef('bad@id', 1)).toThrow('circuit_id is invalid');
  });

  it('serializes statements and maps them to field elements', async () => {
    const statement: ZkpStatement = {
      theoremHash: await theoremHashHex('Q'),
      axiomsCommitment: await axiomsCommitmentHex(['P', 'P -> Q']),
      circuitVersion: 2,
      rulesetId: 'TDFOL_v1',
    };

    const serialized = statementToDict(statement);
    expect(statementFromDict(serialized)).toEqual(statement);

    const fields = await statementToFieldElements(statement);
    expect(fields).toHaveLength(4);
    expect(fields[2]).toBe(BigInt(2));
  });

  it('serializes witnesses with Python-compatible defaults', () => {
    const witness: ZkpWitness = {
      axioms: ['P', 'P -> Q'],
      theorem: 'Q',
      axiomsCommitmentHex: 'abc123',
    };

    const serialized = witnessToDict(witness);

    expect(serialized).toEqual({
      axioms: ['P', 'P -> Q'],
      theorem: 'Q',
      intermediate_steps: [],
      axioms_commitment_hex: 'abc123',
      circuit_version: 1,
      ruleset_id: 'TDFOL_v1',
    });
    expect(witnessFromDict(serialized)).toEqual({
      axioms: ['P', 'P -> Q'],
      theorem: 'Q',
      intermediateSteps: [],
      axiomsCommitmentHex: 'abc123',
      circuitVersion: 1,
      rulesetId: 'TDFOL_v1',
    });
  });

  it('serializes complete proof statements with circuit references', async () => {
    const statement: ZkpStatement = {
      theoremHash: await theoremHashHex('Q'),
      axiomsCommitment: await axiomsCommitmentHex(['P', 'P -> Q']),
      circuitVersion: 3,
      rulesetId: 'TDFOL_v1',
    };
    const proofStatement: ZkpProofStatement = {
      statement,
      circuitId: 'knowledge_of_axioms',
      proofType: 'simulated',
      witnessCount: 2,
    };

    const serialized = proofStatementToDict(proofStatement);

    expect(serialized).toMatchObject({
      circuit_id: 'knowledge_of_axioms',
      circuit_ref: 'knowledge_of_axioms@v3',
      proof_type: 'simulated',
      witness_count: 2,
    });
    expect(proofStatementFromDict(serialized)).toEqual(proofStatement);
  });

  it('validates witness and proof statement dictionaries', () => {
    expect(() => witnessFromDict({ axioms: 'P' })).toThrow('axioms must be an array');
    expect(() => witnessFromDict({ axioms: [], intermediate_steps: 'P' })).toThrow(
      'intermediate_steps must be an array',
    );
    expect(() => proofStatementFromDict({ statement: null })).toThrow('statement must be an object');
  });
});
