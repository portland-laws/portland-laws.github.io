import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { ModusPonensRule } from './inferenceRules';
import { parseTdfolFormula } from './parser';
import {
  ZkpTdfolProver,
  createHybridTdfolProver,
  createSimulatedTdfolZkpProof,
  scheduleTdfolZkpProofSearch,
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

  it('schedules worker-safe parallel proof-search metadata with simulated ZKP proofs', async () => {
    const results = await scheduleTdfolZkpProofSearch(
      [
        { axioms, goal, id: 'search-a', proverOptions },
        { axioms: [...axioms].reverse(), goal, id: 'search-b', proverOptions },
      ],
      { parallelism: 4, queueId: 'queue-fixture' },
    );

    expect(results.map((result) => result.id)).toEqual(['search-a', 'search-b']);
    expect(results.map((result) => result.metadata.queue_index)).toEqual([0, 1]);
    expect(results.map((result) => result.metadata.search_order)).toEqual([0, 1]);
    expect(results.every((result) => result.metadata.worker_safe)).toBe(true);
    expect(results.every((result) => !result.metadata.fallback_used)).toBe(true);
    expect(results[0].metadata).toMatchObject({
      backend: 'simulated',
      deterministic_fallback: 'standard-local-prover',
      effective_parallelism: 2,
      queue_id: 'queue-fixture',
      requested_parallelism: 4,
    });
    expect(results[0].proof.zkpProof?.metadata).toMatchObject({
      queue_id: 'queue-fixture',
      requested_parallelism: 4,
      scheduler: 'tdfol-zkp-proof-search',
      worker_safe: true,
    });
    expect(results.every((result) => result.proof.method === 'tdfol_zkp')).toBe(true);
  });

  it('uses deterministic local prover fallback when browser ZKP backend is unavailable', async () => {
    const results = await scheduleTdfolZkpProofSearch(
      [{ axioms, goal, id: 'fallback-search', proverOptions }],
      { parallelism: 2, zkpBackend: 'groth16' },
    );

    expect(results).toHaveLength(1);
    expect(results[0].proof.method).toBe('tdfol_standard');
    expect(results[0].proof.isProved).toBe(true);
    expect(results[0].metadata).toMatchObject({
      backend: 'groth16',
      deterministic_fallback: 'standard-local-prover',
      effective_parallelism: 1,
      fallback_used: true,
      requested_parallelism: 2,
      worker_safe: true,
    });
  });
});
