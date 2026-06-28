import type { ProofResult, ProofStatus } from '../types';
import { axiomsCommitmentHex, canonicalizeAxioms, theoremHashHex } from '../zkp/canonicalization';
import { formatCircuitRef } from '../zkp/statement';
import type { ZkpStatement, ZkpWitness } from '../zkp/statement';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import { CecProofCache } from './proofCache';
import { CecProver, type CecKnowledgeBase, type CecProverOptions } from './prover';

export const HAVE_CEC_ZKP = true;
export const HAVE_CEC_CACHE = true;

export type CecProvingMethod = 'cec_standard' | 'cec_zkp' | 'cec_hybrid' | 'cec_cached';

export interface CecZkpProof {
  backend: 'simulated' | 'groth16';
  statement: ZkpStatement & {
    goal: string;
    axiomsHash: string;
  };
  publicInputs: CecZkpPublicInputs;
  witnessCommitment: string;
  proofDigest: string;
  simulated: boolean;
  securityNote: string;
}

export interface CecZkpPublicInputs {
  circuit_id: 'cec_theorem_v1';
  circuit_ref: string;
  circuit_version: number;
  ruleset_id: 'CEC_v1';
  theorem: string;
  theorem_hash: string;
  axioms_commitment: string;
  axioms_hash: string;
  witness_commitment: string;
  witness_count: number;
  is_proved: boolean;
}

export interface CecZkpCircuitInputs {
  publicInputs: CecZkpPublicInputs;
  witness: ZkpWitness & {
    goal: string;
    isProved: boolean;
  };
}

export interface UnsupportedCecZkpBackend {
  backend: string;
  supportedBackends: string[];
  reason: string;
}

export interface UnifiedCecProofResult {
  isProved: boolean;
  formula: CecExpression;
  axioms: CecExpression[];
  method: CecProvingMethod;
  proofTime: number;
  baseResult: ProofStatus;
  proofSteps?: number;
  inferenceRules?: string[];
  errorMessage?: string;
  zkpProof?: CecZkpProof;
  unsupportedBackend?: UnsupportedCecZkpBackend;
  isPrivate: boolean;
  zkpBackend?: string;
  fromCache: boolean;
  cacheHitTime?: number;
  timestamp: number;
  toDict(): Record<string, unknown>;
}

export interface ZkpCecProverOptions {
  enableZkp?: boolean;
  enableCaching?: boolean;
  zkpBackend?: 'simulated' | 'groth16';
  zkpFallback?: 'standard' | 'error' | 'simulated';
  cacheSize?: number;
  cacheTtl?: number;
  useGlobalCache?: boolean;
  proverOptions?: CecProverOptions;
}

export interface ProveCecTheoremOptions extends CecProverOptions {
  timeout?: number;
  preferZkp?: boolean;
  privateAxioms?: boolean;
  useCache?: boolean;
  forceStandard?: boolean;
}

export interface ZkpCecStatistics {
  zkp_enabled: boolean;
  zkp_attempts: number;
  zkp_successes: number;
  zkp_success_rate: number;
  standard_proofs: number;
  cache_hits_zkp: number;
  cache_entries?: number;
  cache_hits?: number;
  cache_misses?: number;
}

export class UnifiedCecProof implements UnifiedCecProofResult {
  readonly isProved: boolean;
  readonly formula: CecExpression;
  readonly axioms: CecExpression[];
  readonly method: CecProvingMethod;
  readonly proofTime: number;
  readonly baseResult: ProofStatus;
  readonly proofSteps?: number;
  readonly inferenceRules?: string[];
  readonly errorMessage?: string;
  readonly zkpProof?: CecZkpProof;
  readonly unsupportedBackend?: UnsupportedCecZkpBackend;
  readonly isPrivate: boolean;
  readonly zkpBackend?: string;
  readonly fromCache: boolean;
  readonly cacheHitTime?: number;
  readonly timestamp: number;

  constructor(
    options: Omit<UnifiedCecProofResult, 'toDict' | 'timestamp'> & { timestamp?: number },
  ) {
    this.isProved = options.isProved;
    this.formula = options.formula;
    this.axioms = [...options.axioms];
    this.method = options.method;
    this.proofTime = options.proofTime;
    this.baseResult = options.baseResult;
    this.proofSteps = options.proofSteps;
    this.inferenceRules = options.inferenceRules ? [...options.inferenceRules] : undefined;
    this.errorMessage = options.errorMessage;
    this.zkpProof = options.zkpProof;
    this.unsupportedBackend = options.unsupportedBackend;
    this.isPrivate = options.isPrivate;
    this.zkpBackend = options.zkpBackend;
    this.fromCache = options.fromCache;
    this.cacheHitTime = options.cacheHitTime;
    this.timestamp = options.timestamp ?? Date.now() / 1000;
  }

  static fromStandardProof(
    formula: CecExpression,
    axioms: CecExpression[],
    proof: ProofResult,
    options: { fromCache?: boolean; cacheHitTime?: number; proofTime?: number } = {},
  ): UnifiedCecProof {
    return new UnifiedCecProof({
      isProved: proof.status === 'proved',
      formula,
      axioms,
      method: options.fromCache ? 'cec_cached' : 'cec_standard',
      proofTime: options.proofTime ?? (proof.timeMs ?? 0) / 1000,
      baseResult: proof.status,
      proofSteps: proof.steps.length,
      inferenceRules: uniqueRuleNames(proof.steps.map((step) => step.rule)),
      errorMessage: proof.error,
      isPrivate: false,
      fromCache: options.fromCache ?? false,
      cacheHitTime: options.cacheHitTime,
    });
  }

  static fromZkpProof(
    formula: CecExpression,
    axioms: CecExpression[],
    zkpProof: CecZkpProof,
    isProved: boolean,
    proofTime: number,
    zkpBackend: string,
    isPrivate = true,
  ): UnifiedCecProof {
    return new UnifiedCecProof({
      isProved,
      formula,
      axioms: isPrivate ? [] : axioms,
      method: 'cec_zkp',
      proofTime,
      baseResult: isProved ? 'proved' : 'unknown',
      zkpProof,
      isPrivate,
      zkpBackend,
      fromCache: false,
    });
  }

  static unsupportedZkpBackend(
    formula: CecExpression,
    axioms: CecExpression[],
    backend: string,
    proofTime: number,
    isPrivate: boolean,
  ): UnifiedCecProof {
    const supportedBackends = ['simulated'];
    const reason = `CEC ZKP backend '${backend}' is not available in the browser-native port.`;
    return new UnifiedCecProof({
      isProved: false,
      formula,
      axioms: isPrivate ? [] : axioms,
      method: 'cec_zkp',
      proofTime,
      baseResult: 'error',
      errorMessage: `${reason} Supported local backend: simulated.`,
      isPrivate,
      zkpBackend: backend,
      unsupportedBackend: {
        backend,
        supportedBackends,
        reason,
      },
      fromCache: false,
    });
  }

  toDict(): Record<string, unknown> {
    return {
      is_proved: this.isProved,
      formula: formatCecExpression(this.formula),
      axioms: this.isPrivate ? ['<private>'] : this.axioms.map(formatCecExpression),
      method: this.method,
      proof_time: this.proofTime,
      base_result: this.baseResult,
      proof_steps: this.proofSteps,
      inference_rules: this.inferenceRules,
      error_message: this.errorMessage,
      zkp_public_inputs: this.zkpProof?.publicInputs,
      unsupported_backend: this.unsupportedBackend,
      is_private: this.isPrivate,
      zkp_backend: this.zkpBackend,
      from_cache: this.fromCache,
      cache_hit_time: this.cacheHitTime,
      timestamp: this.timestamp,
    };
  }
}

export class ZkpCecProver {
  readonly enableZkp: boolean;
  readonly enableCaching: boolean;
  readonly zkpBackend: 'simulated' | 'groth16';
  readonly zkpFallback: 'standard' | 'error' | 'simulated';
  readonly cache: CecProofCache;
  readonly proverOptions: CecProverOptions;
  private zkpAttempts = 0;
  private zkpSuccesses = 0;
  private standardProofs = 0;
  private cacheHits = 0;

  constructor(options: ZkpCecProverOptions = {}) {
    this.enableZkp = options.enableZkp ?? true;
    this.enableCaching = options.enableCaching ?? true;
    this.zkpBackend = options.zkpBackend ?? 'simulated';
    this.zkpFallback = options.zkpFallback ?? 'standard';
    this.proverOptions = options.proverOptions ?? {};
    this.cache = new CecProofCache({
      maxSize: options.cacheSize,
      ttlMs: options.cacheTtl === undefined ? undefined : options.cacheTtl * 1000,
      proverName: 'cec-zkp-hybrid',
    });
  }

  initialize(): void {
    // Kept for Python API compatibility; browser-native components initialize eagerly.
  }

  async proveTheorem(
    goal: CecExpression,
    axioms: CecExpression[] = [],
    options: ProveCecTheoremOptions = {},
  ): Promise<UnifiedCecProof> {
    const start = performanceNow();
    const kb: CecKnowledgeBase = { axioms };
    const proverOptions = mergeProverOptions(this.proverOptions, options);
    const useCache = (options.useCache ?? true) && this.enableCaching && !options.forceStandard;
    const preferZkp = options.forceStandard ? false : (options.preferZkp ?? false);
    const privateAxioms = options.forceStandard ? false : (options.privateAxioms ?? false);

    if (useCache) {
      const cacheStart = performanceNow();
      const cached = this.cache.get(goal, kb, proverOptions);
      if (cached) {
        this.cacheHits += 1;
        return UnifiedCecProof.fromStandardProof(goal, axioms, cached, {
          fromCache: true,
          cacheHitTime: (performanceNow() - cacheStart) / 1000,
        });
      }
    }

    if (preferZkp && this.enableZkp) {
      try {
        this.zkpAttempts += 1;
        const zkpResult = await this.proveWithZkp(
          goal,
          axioms,
          privateAxioms,
          proverOptions,
          start,
        );
        if (zkpResult.isProved) {
          this.zkpSuccesses += 1;
          if (useCache) this.cache.set(goal, kb, zkpResultToProofResult(zkpResult), proverOptions);
          return zkpResult;
        }
        if (zkpResult.baseResult === 'error') {
          return zkpResult;
        }
      } catch (error) {
        if (this.zkpFallback === 'error') throw error;
      }
    }

    this.standardProofs += 1;
    const result = new CecProver(proverOptions).prove(goal, kb);
    if (useCache) this.cache.set(goal, kb, result, proverOptions);
    return UnifiedCecProof.fromStandardProof(goal, axioms, result, {
      proofTime: (performanceNow() - start) / 1000,
    });
  }

  getStatistics(): ZkpCecStatistics {
    const cacheStats = this.cache.getStats();
    return {
      zkp_enabled: this.enableZkp,
      zkp_attempts: this.zkpAttempts,
      zkp_successes: this.zkpSuccesses,
      zkp_success_rate: this.zkpAttempts === 0 ? 0 : this.zkpSuccesses / this.zkpAttempts,
      standard_proofs: this.standardProofs,
      cache_hits_zkp: this.cacheHits,
      cache_entries: cacheStats.cacheSize,
      cache_hits: cacheStats.hits,
      cache_misses: cacheStats.misses,
    };
  }

  clearCache(): void {
    this.cache.clear();
  }

  clearStatistics(): void {
    this.zkpAttempts = 0;
    this.zkpSuccesses = 0;
    this.standardProofs = 0;
    this.cacheHits = 0;
  }

  private async proveWithZkp(
    goal: CecExpression,
    axioms: CecExpression[],
    privateAxioms: boolean,
    proverOptions: CecProverOptions,
    start: number,
  ): Promise<UnifiedCecProof> {
    if (this.zkpBackend !== 'simulated') {
      return UnifiedCecProof.unsupportedZkpBackend(
        goal,
        axioms,
        this.zkpBackend,
        (performanceNow() - start) / 1000,
        privateAxioms,
      );
    }

    const proof = new CecProver(proverOptions).prove(goal, { axioms });
    const zkpProof = await createSimulatedCecZkpProof(goal, axioms, proof.status === 'proved');

    return UnifiedCecProof.fromZkpProof(
      goal,
      axioms,
      zkpProof,
      proof.status === 'proved',
      (performanceNow() - start) / 1000,
      this.zkpBackend,
      privateAxioms,
    );
  }
}

export function createHybridCecProver(options: ZkpCecProverOptions = {}): ZkpCecProver {
  return new ZkpCecProver(options);
}

export async function createSimulatedCecZkpProof(
  goal: CecExpression,
  axioms: CecExpression[],
  isProved: boolean,
): Promise<CecZkpProof> {
  const circuitInputs = await createCecZkpCircuitInputs(goal, axioms, isProved);
  const { publicInputs } = circuitInputs;
  const proofDigest = await theoremHashHex(
    `${publicInputs.theorem}#${publicInputs.axioms_commitment}#${publicInputs.witness_commitment}#${isProved}`,
  );

  return {
    backend: 'simulated',
    statement: {
      theoremHash: publicInputs.theorem_hash,
      axiomsCommitment: publicInputs.axioms_commitment,
      circuitVersion: publicInputs.circuit_version,
      rulesetId: publicInputs.ruleset_id,
      goal: publicInputs.theorem,
      axiomsHash: publicInputs.axioms_hash,
    },
    publicInputs,
    witnessCommitment: publicInputs.witness_commitment,
    proofDigest,
    simulated: true,
    securityNote: 'Simulated educational CEC ZKP certificate; not cryptographically secure.',
  };
}

export async function createCecZkpCircuitInputs(
  goal: CecExpression,
  axioms: CecExpression[],
  isProved: boolean,
): Promise<CecZkpCircuitInputs> {
  const goalText = formatCecExpression(goal);
  const axiomTexts = canonicalizeAxioms(axioms.map(formatCecExpression));
  const axiomsCommitment = await axiomsCommitmentHex(axiomTexts);
  const theoremHash = await theoremHashHex(goalText);
  const witness: ZkpWitness = {
    axioms: axiomTexts,
    theorem: goalText,
    axiomsCommitmentHex: axiomsCommitment,
    circuitVersion: 1,
    rulesetId: 'CEC_v1',
  };
  const witnessCommitment = await axiomsCommitmentHex([
    ...witness.axioms,
    witness.theorem ?? '',
    String(isProved),
    witness.rulesetId ?? 'CEC_v1',
  ]);

  return {
    publicInputs: {
      circuit_id: 'cec_theorem_v1',
      circuit_ref: formatCircuitRef('cec_theorem_v1', 1),
      circuit_version: 1,
      ruleset_id: 'CEC_v1',
      theorem: goalText,
      theorem_hash: theoremHash,
      axioms_commitment: axiomsCommitment,
      axioms_hash: axiomsCommitment,
      witness_commitment: witnessCommitment,
      witness_count: axiomTexts.length,
      is_proved: isProved,
    },
    witness: {
      ...witness,
      goal: goalText,
      isProved,
    },
  };
}

function zkpResultToProofResult(result: UnifiedCecProof): ProofResult {
  return {
    status: result.baseResult,
    theorem: formatCecExpression(result.formula),
    steps: [],
    method: result.method,
    timeMs: result.proofTime * 1000,
    error: result.errorMessage,
  };
}

function mergeProverOptions(base: CecProverOptions, overrides: CecProverOptions): CecProverOptions {
  return {
    maxSteps: overrides.maxSteps ?? base.maxSteps,
    maxDerivedExpressions: overrides.maxDerivedExpressions ?? base.maxDerivedExpressions,
    rules: overrides.rules ?? base.rules,
  };
}

function uniqueRuleNames(values: unknown[]): string[] {
  return [...new Set(values.filter(isRuleName))];
}

function isRuleName(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function performanceNow(): number {
  return globalThis.performance?.now?.() ?? Date.now();
}
