import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import {
  UnifiedCecProof,
  ZkpCecProver,
  createHybridCecProver,
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
    expect(first.proofDigest).toHaveLength(64);
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
    });
  });

  it('falls back to standard local CEC proving when ZKP is disabled or forced off', async () => {
    const prover = new ZkpCecProver({ enableZkp: false, enableCaching: false });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const disabled = await prover.proveTheorem(goal, axioms, { preferZkp: true });
    const forced = await prover.proveTheorem(goal, axioms, { forceStandard: true, preferZkp: true });

    expect(disabled.method).toBe('cec_standard');
    expect(disabled.isProved).toBe(true);
    expect(disabled.proofSteps).toBe(1);
    expect(disabled.inferenceRules).toEqual(['CecModusPonens']);
    expect(forced.method).toBe('cec_standard');
  });

  it('serves cached standard proofs before hybrid work', async () => {
    const prover = new ZkpCecProver({ enableZkp: true, enableCaching: true });
    const goal = parseCecExpression('q');
    const axioms = [parseCecExpression('p'), parseCecExpression('(implies p q)')];

    const first = await prover.proveTheorem(goal, axioms, { preferZkp: false });
    const second = await prover.proveTheorem(goal, axioms, { preferZkp: true, privateAxioms: true });

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
    await prover.proveTheorem(parseCecExpression('q'), [parseCecExpression('q')], { preferZkp: true });

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
