import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import {
  UnifiedCecProof,
  ZkpCecProver,
  createHybridCecProver,
  createCecZkpCircuitInputs,
  createSimulatedCecZkpProof,
} from './cecZkpIntegration';
import { parseCecExpression } from './parser';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('CEC ZKP integration parity helpers', () => {
  it('creates deterministic simulated CEC ZKP proof metadata', async () => {
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const first = await createSimulatedCecZkpProof(goal, axioms, true);
    const second = await createSimulatedCecZkpProof(goal, [...axioms].reverse(), true);

    expect(first.backend).toBe('simulated');
    expect(first.simulated).toBe(true);
    expect(first.statement.goal).toBe('q');
    expect(first.statement.rulesetId).toBe('CEC_v1');
    expect(first.statement.axiomsCommitment).toBe(second.statement.axiomsCommitment);
    expect(first.publicInputs).toMatchObject({
      circuit_id: 'cec_theorem_v1',
      circuit_ref: 'cec_theorem_v1@v1',
      ruleset_id: 'CEC_v1',
      theorem: 'q',
      witness_count: 2,
      is_proved: true,
    });
    expect(first.publicInputs.axioms_commitment).toBe(first.statement.axiomsCommitment);
    expect(first.publicInputs.witness_commitment).toBe(first.witnessCommitment);
    expect(first.proofDigest).toHaveLength(64);
  });

  it('builds deterministic CEC circuit public inputs without exposing private witness data', async () => {
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('(implies p q)'), parseCecExpression('p')];

    const first = await createCecZkpCircuitInputs(goal, axioms, true);
    const second = await createCecZkpCircuitInputs(goal, [...axioms].reverse(), true);

    expect(first.publicInputs).toEqual(second.publicInputs);
    expect(first.publicInputs.theorem_hash).toMatch(/^[0-9a-f]{64}$/);
    expect(first.publicInputs.axioms_hash).toBe(first.publicInputs.axioms_commitment);
    expect(first.publicInputs.witness_commitment).toMatch(/^[0-9a-f]{64}$/);
    expect(first.witness).toMatchObject({
      axioms: ['(implies p q)', 'p'],
      theorem: 'q',
      goal: 'q',
      rulesetId: 'CEC_v1',
      circuitVersion: 1,
      isProved: true,
    });
  });

  it('returns private simulated ZKP proofs when preferred', async () => {
    const prover = createHybridCecProver({ enableZkp: true, enableCaching: false });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const result = await prover.proveTheorem(goal, axioms, {
      preferZkp: true,
      privateAxioms: true,
    });

    expect(result.isProved).toBe(true);
    expect(result.method).toBe('cec_zkp');
    expect(result.isPrivate).toBe(true);
    expect(result.axioms).toEqual([]);
    expect(result.zkpProof?.securityNote).toContain('not cryptographically secure');
    expect(result.toDict()).toMatchObject({
      is_proved: true,
      axioms: ['<private>'],
      method: 'cec_zkp',
      zkp_backend: 'simulated',
      zkp_public_inputs: {
        circuit_ref: 'cec_theorem_v1@v1',
        theorem: 'q',
        witness_count: 2,
      },
    });
  });

  it('falls back to standard local CEC proving when ZKP is disabled or forced off', async () => {
    const prover = new ZkpCecProver({ enableZkp: false, enableCaching: false });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const disabled = await prover.proveTheorem(goal, axioms, { preferZkp: true });
    const forced = await prover.proveTheorem(goal, axioms, {
      forceStandard: true,
      preferZkp: true,
    });

    expect(disabled.method).toBe('cec_standard');
    expect(disabled.isProved).toBe(true);
    expect(disabled.proofSteps).toBe(1);
    expect(disabled.inferenceRules).toEqual(['CecModusPonens']);
    expect(forced.method).toBe('cec_standard');
  });

  it('fails closed with structured metadata for unsupported local ZKP backends', async () => {
    const prover = new ZkpCecProver({
      enableZkp: true,
      enableCaching: false,
      zkpBackend: 'groth16',
    });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const result = await prover.proveTheorem(goal, axioms, {
      preferZkp: true,
      privateAxioms: true,
    });

    expect(result.isProved).toBe(false);
    expect(result.method).toBe('cec_zkp');
    expect(result.baseResult).toBe('error');
    expect(result.isPrivate).toBe(true);
    expect(result.axioms).toEqual([]);
    expect(result.zkpProof).toBeUndefined();
    expect(result.unsupportedBackend).toEqual({
      backend: 'groth16',
      supportedBackends: ['simulated'],
      reason: "CEC ZKP backend 'groth16' is not available in the browser-native port.",
    });
    expect(result.toDict()).toMatchObject({
      is_proved: false,
      axioms: ['<private>'],
      method: 'cec_zkp',
      base_result: 'error',
      zkp_backend: 'groth16',
      unsupported_backend: {
        backend: 'groth16',
        supportedBackends: ['simulated'],
      },
    });
    expect(prover.getStatistics()).toMatchObject({
      zkp_attempts: 1,
      zkp_successes: 0,
      standard_proofs: 0,
    });
  });

  it('serves cached standard proofs before hybrid work', async () => {
    const prover = new ZkpCecProver({ enableZkp: true, enableCaching: true });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const first = await prover.proveTheorem(goal, axioms, { preferZkp: false });
    const second = await prover.proveTheorem(goal, axioms, {
      preferZkp: true,
      privateAxioms: true,
    });

    expect(first.method).toBe('cec_standard');
    expect(second.method).toBe('cec_cached');
    expect(second.fromCache).toBe(true);
    expect(second.isPrivate).toBe(false);
    expect(prover.getStatistics()).toMatchObject({
      cache_hits_zkp: 1,
      standard_proofs: 1,
      zkp_attempts: 0,
    });
  });

  it('summarizes standard proofs through the unified result wrapper', () => {
    const goal = parseCecExpression('q');
    const result = UnifiedCecProof.fromStandardProof(goal, [parseCecExpression('p')], {
      status: 'unknown',
      theorem: 'q',
      steps: [],
      method: 'cec-forward-chaining',
      error: 'No proof found',
    });

    expect(result.isProved).toBe(false);
    expect(result.method).toBe('cec_standard');
    expect(result.toDict()).toMatchObject({
      formula: 'q',
      base_result: 'unknown',
      from_cache: false,
    });
  });

  it('clears statistics independently of the proof cache', async () => {
    const prover = new ZkpCecProver({ enableZkp: true, enableCaching: true });
    await prover.proveTheorem(parseCecExpression('q'), [parseCecExpression('q')], {
      preferZkp: true,
    });

    expect(prover.getStatistics().zkp_attempts).toBe(1);
    prover.clearStatistics();
    expect(prover.getStatistics()).toMatchObject({
      zkp_attempts: 0,
      zkp_successes: 0,
      standard_proofs: 0,
      cache_hits_zkp: 0,
    });
  });
});
