import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { WitnessManager } from './witnessManager';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('ZKP WitnessManager browser-native parity', () => {
  it('generates canonical v1 witnesses and caches them by commitment', async () => {
    const manager = new WitnessManager();
    const witness = await manager.generateWitness({
      axioms: ['P -> Q', 'P'],
      theorem: 'Q',
    });

    expect(witness).toMatchObject({
      axioms: ['P', 'P -> Q'],
      circuitVersion: 1,
      intermediateSteps: [],
      rulesetId: 'TDFOL_v1',
      theorem: 'Q',
    });
    expect(witness.axiomsCommitmentHex).toMatch(/^[0-9a-f]{64}$/);
    await expect(manager.validateWitness(witness, 2, ['P', 'P -> Q'])).resolves.toBe(true);
    expect(manager.getCachedWitness(witness.axiomsCommitmentHex!)).toEqual(witness);
  });

  it('generates v2 TDFOL witnesses with derived Horn traces', async () => {
    const manager = new WitnessManager();
    const witness = await manager.generateWitness({
      axioms: ['P -> Q', 'Q -> R', 'P'],
      circuitVersion: 2,
      theorem: 'R',
    });
    const proofStatement = await manager.createProofStatement(witness, 'R', 'tdfol_v1_horn_derivation');

    expect(witness.intermediateSteps).toEqual(['P', 'Q', 'R']);
    expect(proofStatement).toMatchObject({
      circuitId: 'tdfol_v1_horn_derivation',
      proofType: 'simulated',
      witnessCount: 3,
      statement: {
        circuitVersion: 2,
        rulesetId: 'TDFOL_v1',
      },
    });
    await expect(manager.verifyWitnessConsistency(witness, proofStatement.statement)).resolves.toBe(true);
  });

  it('validates expected axioms and rejects inconsistent commitments', async () => {
    const manager = new WitnessManager();
    const witness = await manager.generateWitness({ axioms: ['P'], theorem: 'P' });

    await expect(manager.validateWitness(witness, 2)).resolves.toBe(false);
    await expect(manager.validateWitness(witness, 1, ['Q'])).resolves.toBe(false);
    await expect(manager.validateWitness({ ...witness, axiomsCommitmentHex: '00' })).resolves.toBe(false);
    await expect(manager.generateWitness({ axioms: [], theorem: 'Q' })).rejects.toThrow('axioms cannot be empty');
  });

  it('supports Python-style aliases and cache clearing', async () => {
    const manager = new WitnessManager();
    const witness = await manager.generate_witness(['P'], 'P');

    expect(manager.get_cached_witness(witness.axiomsCommitmentHex!)).toEqual(witness);
    manager.clear_cache();
    expect(manager.get_cached_witness(witness.axiomsCommitmentHex!)).toBeUndefined();
  });
});
