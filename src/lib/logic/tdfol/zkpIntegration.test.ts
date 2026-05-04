import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { ModusPonensRule } from './inferenceRules';
import { parseTdfolFormula } from './parser';
import {
  ZkpTdfolProver,
  createHybridTdfolProver,
  createSimulatedTdfolZkpProof,
} from './zkpIntegration';

Object.defineProperty(globalThis, 'crypto', { value: webcrypto, configurable: true });
Object.defineProperty(globalThis, 'TextEncoder', { value: TextEncoder, configurable: true });

describe('TDFOL ZKP integration parity helpers', () => {
  const goal = parseTdfolFormula('Goal(x)');
  const axioms = [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')];
  const proverOptions = { rules: [ModusPonensRule], maxSteps: 5 };

  it('creates browser-native simulated ZKP proofs with TDFOL public inputs', async () => {
    const proof = await createSimulatedTdfolZkpProof(goal, axioms, true);
    const reversed = await createSimulatedTdfolZkpProof(goal, [...axioms].reverse(), true);

    expect(proof.metadata.proof_system).toBe('Groth16 (simulated)');
    expect(proof.publicInputs).toMatchObject({
      theorem: 'Goal(x)',
      circuit_version: 2,
      ruleset_id: 'TDFOL_v1',
    });
    expect(proof.publicInputs.theorem_hash).toHaveLength(64);
    expect(proof.publicInputs.axioms_commitment).toBe(reversed.publicInputs.axioms_commitment);
  });

  it('returns private simulated ZKP proofs when preferred', async () => {
    const prover = createHybridTdfolProver({ enableZkp: true, proverOptions });
    const result = await prover.proveTheorem(goal, axioms, {
      preferZkp: true,
      privateAxioms: true,
    });

    expect(result.isProved).toBe(true);
    expect(result.method).toBe('tdfol_zkp');
    expect(result.axioms).toEqual([]);
    expect(result.toDict()).toMatchObject({
      axioms: ['<private>'],
      method: 'tdfol_zkp',
      zkp_backend: 'simulated',
    });
    expect(result.toDict().zkp_security_note).toContain('not cryptographically secure');
    expect(prover.getStatistics()).toMatchObject({ zkp_attempts: 1, zkp_successes: 1 });
  });

  it('falls back to standard local proving and fails closed for Groth16', async () => {
    const prover = new ZkpTdfolProver({ enableZkp: false, proverOptions });
    const disabled = await prover.proveTheorem(goal, axioms, { preferZkp: true });
    const forced = await prover.proveTheorem(goal, axioms, {
      forceStandard: true,
      preferZkp: true,
    });

    expect(disabled).toMatchObject({ method: 'tdfol_standard', isProved: true, proofSteps: 1 });
    expect(disabled.inferenceRules).toEqual(['ModusPonens']);
    expect(forced.method).toBe('tdfol_standard');
    expect(prover.getStatistics()).toMatchObject({ standard_proofs: 2, zkp_attempts: 0 });
    await expect(
      createSimulatedTdfolZkpProof(goal, axioms, true, { backend: 'groth16' }),
    ).rejects.toThrow('Only the simulated TDFOL ZKP backend is available');
  });
});
