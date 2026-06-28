import type { ProofResult, ProofStatus } from '../types';
import { ZKPProver, ZKPVerifier } from '../zkp/facade';
import type { ZKPProof } from '../zkp/simulatedBackend';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import { TdfolProver, type TdfolProverOptions } from './prover';

export const HAVE_TDFOL_ZKP = true;
export type TdfolZkpBackend = 'simulated' | 'groth16';
export type TdfolProvingMethod = 'tdfol_standard' | 'tdfol_zkp';
export interface TdfolZkpStatistics {
  zkp_enabled: boolean;
  zkp_attempts: number;
  zkp_successes: number;
  zkp_success_rate: number;
  standard_proofs: number;
}

export interface TdfolZkpProofSearchQueueItem {
  id: string;
  goal: TdfolFormula;
  axioms?: TdfolFormula[];
  proverOptions?: TdfolProverOptions;
  preferZkp?: boolean;
  privateAxioms?: boolean;
}

export interface TdfolZkpProofSearchMetadata {
  queue_id: string;
  queue_index: number;
  search_order: number;
  requested_parallelism: number;
  effective_parallelism: number;
  worker_safe: true;
  backend: TdfolZkpBackend;
  deterministic_fallback: 'standard-local-prover';
  fallback_used: boolean;
}

export type TdfolZkpProofSearchResult = {
  id: string;
  proof: UnifiedTdfolProof;
  metadata: TdfolZkpProofSearchMetadata;
};

export interface TdfolZkpProofSearchSchedulerOptions {
  queueId?: string;
  parallelism?: number;
  zkpBackend?: TdfolZkpBackend;
  zkpFallback?: 'standard' | 'error';
  securityLevel?: number;
  proverOptions?: TdfolProverOptions;
}

export class UnifiedTdfolProof {
  readonly timestamp = Date.now() / 1000;

  constructor(
    readonly isProved: boolean,
    readonly formula: TdfolFormula,
    readonly axioms: TdfolFormula[],
    readonly method: TdfolProvingMethod,
    readonly proofTime: number,
    readonly baseResult: ProofStatus,
    readonly isPrivate: boolean,
    readonly proofSteps?: number,
    readonly inferenceRules?: string[],
    readonly errorMessage?: string,
    readonly zkpProof?: ZKPProof,
    readonly zkpBackend?: string,
  ) {}

  static fromStandardProof(
    formula: TdfolFormula,
    axioms: TdfolFormula[],
    proof: ProofResult,
    proofTime: number,
  ): UnifiedTdfolProof {
    const rules = proof.steps
      .map((step) => step.rule)
      .filter((rule): rule is string => typeof rule === 'string' && rule.length > 0);
    return new UnifiedTdfolProof(
      proof.status === 'proved',
      formula,
      axioms,
      'tdfol_standard',
      proofTime,
      proof.status,
      false,
      proof.steps.length,
      [...new Set<string>(rules)],
      proof.error,
    );
  }

  static fromZkpProof(
    formula: TdfolFormula,
    axioms: TdfolFormula[],
    proof: ProofResult,
    zkpProof: ZKPProof,
    proofTime: number,
    zkpBackend: string,
    isPrivate: boolean,
  ): UnifiedTdfolProof {
    return new UnifiedTdfolProof(
      proof.status === 'proved',
      formula,
      isPrivate ? [] : axioms,
      'tdfol_zkp',
      proofTime,
      proof.status,
      isPrivate,
      undefined,
      undefined,
      proof.error,
      zkpProof,
      zkpBackend,
    );
  }

  toDict(): Record<string, unknown> {
    return {
      is_proved: this.isProved,
      formula: formatTdfolFormula(this.formula),
      axioms: this.isPrivate ? ['<private>'] : this.axioms.map(formatTdfolFormula),
      method: this.method,
      proof_time: this.proofTime,
      base_result: this.baseResult,
      proof_steps: this.proofSteps,
      inference_rules: this.inferenceRules,
      error_message: this.errorMessage,
      is_private: this.isPrivate,
      zkp_backend: this.zkpBackend,
      zkp_security_note: this.zkpProof ? tdfolZkpSecurityNote(this.zkpProof) : undefined,
      timestamp: this.timestamp,
    };
  }
}

export class ZkpTdfolProver {
  readonly enableZkp: boolean;
  readonly zkpBackend: TdfolZkpBackend;
  private zkpAttempts = 0;
  private zkpSuccesses = 0;
  private standardProofs = 0;

  constructor(
    readonly options: {
      enableZkp?: boolean;
      zkpBackend?: TdfolZkpBackend;
      zkpFallback?: 'standard' | 'error';
      securityLevel?: number;
      proverOptions?: TdfolProverOptions;
    } = {},
  ) {
    this.enableZkp = options.enableZkp ?? true;
    this.zkpBackend = options.zkpBackend ?? 'simulated';
  }

  initialize(): void {}

  async proveTheorem(
    goal: TdfolFormula,
    axioms: TdfolFormula[] = [],
    options: TdfolProverOptions & {
      preferZkp?: boolean;
      privateAxioms?: boolean;
      forceStandard?: boolean;
      zkpProofMetadata?: Record<string, unknown>;
    } = {},
  ): Promise<UnifiedTdfolProof> {
    const start = performanceNow();
    const proverOptions = { ...(this.options.proverOptions ?? {}), ...options };
    if (!options.forceStandard && this.enableZkp && (options.preferZkp ?? false)) {
      try {
        this.zkpAttempts += 1;
        const proof = new TdfolProver(proverOptions).prove(goal, { axioms });
        const zkpProof = await createSimulatedTdfolZkpProof(
          goal,
          axioms,
          proof.status === 'proved',
          { ...this.options, proofMetadata: options.zkpProofMetadata },
        );
        if (proof.status === 'proved') this.zkpSuccesses += 1;
        return UnifiedTdfolProof.fromZkpProof(
          goal,
          axioms,
          proof,
          zkpProof,
          (performanceNow() - start) / 1000,
          this.zkpBackend,
          options.privateAxioms ?? true,
        );
      } catch (error) {
        if (this.options.zkpFallback === 'error') throw error;
      }
    }
    this.standardProofs += 1;
    const proof = new TdfolProver(proverOptions).prove(goal, { axioms });
    return UnifiedTdfolProof.fromStandardProof(
      goal,
      axioms,
      proof,
      (performanceNow() - start) / 1000,
    );
  }

  getStatistics(): TdfolZkpStatistics {
    return {
      zkp_enabled: this.enableZkp,
      zkp_attempts: this.zkpAttempts,
      zkp_successes: this.zkpSuccesses,
      zkp_success_rate: this.zkpAttempts === 0 ? 0 : this.zkpSuccesses / this.zkpAttempts,
      standard_proofs: this.standardProofs,
    };
  }

  clearStatistics(): void {
    this.zkpAttempts = 0;
    this.zkpSuccesses = 0;
    this.standardProofs = 0;
  }
}

export async function createSimulatedTdfolZkpProof(
  goal: TdfolFormula,
  axioms: TdfolFormula[],
  isProved = true,
  options: {
    backend?: TdfolZkpBackend;
    zkpBackend?: TdfolZkpBackend;
    securityLevel?: number;
    proofMetadata?: Record<string, unknown>;
  } = {},
): Promise<ZKPProof> {
  const backend = options.backend ?? options.zkpBackend ?? 'simulated';
  if (backend !== 'simulated')
    throw new Error(
      'Only the simulated TDFOL ZKP backend is available in the browser-native port.',
    );
  const proof = await new ZKPProver({
    backend,
    enableCaching: false,
    securityLevel: options.securityLevel,
  }).generateProof(formatTdfolFormula(goal), axioms.map(formatTdfolFormula), {
    circuit_version: 2,
    is_proved: isProved,
    ...(options.proofMetadata ?? {}),
    ruleset_id: 'TDFOL_v1',
  });
  const verified = await new ZKPVerifier({
    backend,
    securityLevel: options.securityLevel,
  }).verifyProof(proof);
  if (!verified) throw new Error('Generated TDFOL ZKP proof failed local verification.');
  return proof;
}

export function createHybridTdfolProver(
  options: ConstructorParameters<typeof ZkpTdfolProver>[0] = {},
): ZkpTdfolProver {
  return new ZkpTdfolProver(options);
}

export async function scheduleTdfolZkpProofSearch(
  items: Array<TdfolZkpProofSearchQueueItem>,
  options: TdfolZkpProofSearchSchedulerOptions = {},
): Promise<Array<TdfolZkpProofSearchResult>> {
  const queue = normalizeTdfolZkpProofSearchQueue(items);
  const requestedParallelism = Math.max(1, Math.floor(options.parallelism ?? 1));
  const effectiveParallelism = Math.min(requestedParallelism, Math.max(1, queue.length));
  const queueId = options.queueId ?? 'tdfol-zkp-queue';
  const results: Array<TdfolZkpProofSearchResult | undefined> = new Array(queue.length);
  let cursor = 0;

  async function runNext(): Promise<void> {
    const index = cursor;
    cursor += 1;
    if (index >= queue.length) return;

    const item = queue[index];
    const backend = options.zkpBackend ?? 'simulated';
    const baseMetadata: Omit<TdfolZkpProofSearchMetadata, 'fallback_used'> = {
      backend,
      deterministic_fallback: 'standard-local-prover',
      effective_parallelism: effectiveParallelism,
      queue_id: queueId,
      queue_index: index,
      requested_parallelism: requestedParallelism,
      search_order: index,
      worker_safe: true,
    };
    const prover = new ZkpTdfolProver({
      enableZkp: true,
      proverOptions: { ...(options.proverOptions ?? {}), ...(item.proverOptions ?? {}) },
      securityLevel: options.securityLevel,
      zkpBackend: backend,
      zkpFallback: options.zkpFallback ?? 'standard',
    });
    const proof = await prover.proveTheorem(item.goal, item.axioms ?? [], {
      preferZkp: item.preferZkp ?? true,
      privateAxioms: item.privateAxioms ?? true,
      zkpProofMetadata: {
        ...baseMetadata,
        fallback_used: false,
        scheduler: 'tdfol-zkp-proof-search',
      },
    });
    const metadata: TdfolZkpProofSearchMetadata = {
      ...baseMetadata,
      fallback_used: proof.method !== 'tdfol_zkp',
    };
    results[index] = { id: item.id, metadata, proof };
    await runNext();
  }

  await Promise.all(Array.from({ length: effectiveParallelism }, () => runNext()));
  return results.filter((result): result is TdfolZkpProofSearchResult => result !== undefined);
}

function normalizeTdfolZkpProofSearchQueue(
  items: Array<TdfolZkpProofSearchQueueItem>,
): Array<TdfolZkpProofSearchQueueItem> {
  return items.map((item, index) => ({
    ...item,
    axioms: (item.axioms ?? []).map(cloneTdfolFormula),
    goal: cloneTdfolFormula(item.goal),
    id: item.id || `tdfol-zkp-search-${index + 1}`,
  }));
}

function cloneTdfolFormula(formula: TdfolFormula): TdfolFormula {
  return JSON.parse(JSON.stringify(formula)) as TdfolFormula;
}

function tdfolZkpSecurityNote(proof: ZKPProof): string {
  return String(proof.metadata.proof_system ?? '')
    .toLowerCase()
    .includes('simulated')
    ? 'Simulated educational TDFOL ZKP certificate; not cryptographically secure.'
    : 'Browser-native TDFOL ZKP proof.';
}

function performanceNow(): number {
  return globalThis.performance?.now?.() ?? Date.now();
}
