import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { axiomsCommitmentHex, theoremHashHex } from './canonicalization';
import {
  formatCircuitRef,
  parseCircuitRef,
  parseCircuitRefLenient,
  statementFromDict,
  statementToDict,
  statementToFieldElements,
  type ZkpStatement,
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
});
