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
          this.options,
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
  options: { backend?: TdfolZkpBackend; zkpBackend?: TdfolZkpBackend; securityLevel?: number } = {},
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
