import { ZKPProver, ZKPVerifier } from '../zkp/facade';
import type { ZKPProof } from '../zkp/simulatedBackend';
import { formatFLogicOntology } from './formatter';
import type { FLogicOntology, FLogicQuery, FLogicStatus } from './types';

export const HAVE_FLOGIC_ZKP = true;
export interface FLogicZkpStatistics {
  zkp_enabled: boolean;
  zkp_attempts: number;
  zkp_successes: number;
  zkp_success_rate: number;
  standard_queries: number;
}
export interface FLogicZkpOptions {
  enableZkp?: boolean;
  zkpBackend?: 'simulated' | 'groth16';
  zkpFallback?: 'standard' | 'error';
  securityLevel?: number;
}

export class UnifiedFLogicProof {
  readonly timestamp = Date.now() / 1000;
  constructor(
    readonly query: FLogicQuery,
    readonly method: 'flogic_standard' | 'flogic_zkp',
    readonly proofTime: number,
    readonly isPrivate: boolean,
    readonly zkpProof?: ZKPProof,
    readonly zkpBackend?: string,
  ) {}
  get isProved(): boolean {
    return this.query.status === 'success';
  }
  toDict(): Record<string, unknown> {
    return {
      bindings: this.isPrivate
        ? ['<private>']
        : this.query.bindings.map((binding) => ({ ...binding })),
      error_message: this.query.errorMessage,
      goal: this.query.goal,
      is_private: this.isPrivate,
      is_proved: this.isProved,
      method: this.method,
      proof_time: this.proofTime,
      status: this.query.status,
      timestamp: this.timestamp,
      zkp_backend: this.zkpBackend,
      zkp_security_note: this.zkpProof ? flogicZkpSecurityNote(this.zkpProof) : undefined,
    };
  }
}

export class ZkpFLogicProver {
  readonly enableZkp: boolean;
  readonly zkpBackend: 'simulated' | 'groth16';
  private zkpAttempts = 0;
  private zkpSuccesses = 0;
  private standardQueries = 0;
  constructor(readonly options: FLogicZkpOptions = {}) {
    this.enableZkp = options.enableZkp ?? true;
    this.zkpBackend = options.zkpBackend ?? 'simulated';
  }
  initialize(): void {}
  async proveTheorem(
    goal: string,
    ontology: FLogicOntology,
    options: { preferZkp?: boolean; privateOntology?: boolean; forceStandard?: boolean } = {},
  ): Promise<UnifiedFLogicProof> {
    const start = performanceNow();
    const query = evaluateFLogicGoal(goal, ontology);
    if (!options.forceStandard && this.enableZkp && (options.preferZkp ?? false)) {
      try {
        this.zkpAttempts += 1;
        const proof = await createSimulatedFLogicZkpProof(
          goal,
          ontology,
          query.status === 'success',
          this.options,
        );
        if (query.status === 'success') this.zkpSuccesses += 1;
        return new UnifiedFLogicProof(
          query,
          'flogic_zkp',
          elapsedSeconds(start),
          options.privateOntology ?? true,
          proof,
          this.zkpBackend,
        );
      } catch (error) {
        if (this.options.zkpFallback === 'error') throw error;
      }
    }
    this.standardQueries += 1;
    return new UnifiedFLogicProof(query, 'flogic_standard', elapsedSeconds(start), false);
  }
  getStatistics(): FLogicZkpStatistics {
    return {
      standard_queries: this.standardQueries,
      zkp_attempts: this.zkpAttempts,
      zkp_enabled: this.enableZkp,
      zkp_success_rate: this.zkpAttempts === 0 ? 0 : this.zkpSuccesses / this.zkpAttempts,
      zkp_successes: this.zkpSuccesses,
    };
  }
  clearStatistics(): void {
    this.zkpAttempts = 0;
    this.zkpSuccesses = 0;
    this.standardQueries = 0;
  }
}

export async function createSimulatedFLogicZkpProof(
  goal: string,
  ontology: FLogicOntology,
  isProved = true,
  options: FLogicZkpOptions = {},
): Promise<ZKPProof> {
  const backend = options.zkpBackend ?? 'simulated';
  if (backend !== 'simulated')
    throw new Error(
      'Only the simulated F-logic ZKP backend is available in the browser-native port.',
    );
  const proof = await new ZKPProver({
    backend,
    enableCaching: false,
    securityLevel: options.securityLevel,
  }).generateProof(goal, [formatFLogicOntology(ontology)], {
    circuit_version: 1,
    is_proved: isProved,
    ruleset_id: 'FLOGIC_v1',
  });
  if (
    !(await new ZKPVerifier({ backend, securityLevel: options.securityLevel }).verifyProof(proof))
  )
    throw new Error('Generated F-logic ZKP proof failed local verification.');
  return proof;
}

export function createHybridFLogicProver(options: FLogicZkpOptions = {}): ZkpFLogicProver {
  return new ZkpFLogicProver(options);
}

export function evaluateFLogicGoal(goal: string, ontology: FLogicOntology): FLogicQuery {
  const trimmed = goal.trim().replace(/\.$/, '');
  const classMatch = trimmed.match(
    /^(\?[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z_][A-Za-z0-9_]*)$/,
  );
  if (classMatch) return classQuery(goal, ontology, classMatch[1], classMatch[2]);
  const attrMatch = trimmed.match(
    /^(\?[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*)\[([A-Za-z_][A-Za-z0-9_]*)\s*->\s*(\?[A-Za-z_][A-Za-z0-9_]*|"[^"]*"|[A-Za-z_][A-Za-z0-9_]*)\]$/,
  );
  if (!attrMatch) return queryResult(goal, [], 'unsupported F-logic ZKP goal shape');
  const [, objectTerm, method, valueTerm] = attrMatch;
  const expectedValue = valueTerm.startsWith('"') ? valueTerm.slice(1, -1) : valueTerm;
  return queryResult(
    goal,
    ontology.frames.flatMap((frame) => {
      const value = frame.scalarMethods[method];
      if (
        value === undefined ||
        (!valueTerm.startsWith('?') && value !== expectedValue) ||
        (!objectTerm.startsWith('?') && objectTerm !== frame.objectId)
      )
        return [];
      return [
        {
          ...(objectTerm.startsWith('?') ? { [objectTerm]: frame.objectId } : {}),
          ...(valueTerm.startsWith('?') ? { [valueTerm]: value } : {}),
        },
      ];
    }),
  );
}

function classQuery(
  goal: string,
  ontology: FLogicOntology,
  objectTerm: string,
  classId: string,
): FLogicQuery {
  const frames = ontology.frames.filter((frame) => frameHasClass(frame.isaset, classId, ontology));
  return queryResult(
    goal,
    objectTerm.startsWith('?')
      ? frames.map((frame) => ({ [objectTerm]: frame.objectId }))
      : frames.some((frame) => frame.objectId === objectTerm)
        ? [{}]
        : [],
  );
}

function queryResult(
  goal: string,
  bindings: Array<Record<string, string>>,
  errorMessage?: string,
): FLogicQuery {
  const status: FLogicStatus = bindings.length > 0 ? 'success' : errorMessage ? 'error' : 'failure';
  return { bindings, errorMessage, goal, status };
}

function frameHasClass(
  frameClasses: Array<string>,
  classId: string,
  ontology: FLogicOntology,
): boolean {
  const pending = [...frameClasses];
  for (let index = 0; index < pending.length; index += 1) {
    if (pending[index] === classId) return true;
    const cls = ontology.classes.find((item) => item.classId === pending[index]);
    if (cls) pending.push(...cls.superclasses.filter((item) => !pending.includes(item)));
  }
  return false;
}

function flogicZkpSecurityNote(proof: ZKPProof): string {
  return String(proof.metadata.proof_system ?? '')
    .toLowerCase()
    .includes('simulated')
    ? 'Simulated educational F-logic ZKP certificate; not cryptographically secure.'
    : 'Browser-native F-logic ZKP proof.';
}

function elapsedSeconds(start: number): number {
  return (performanceNow() - start) / 1000;
}
function performanceNow(): number {
  return globalThis.performance?.now?.() ?? Date.now();
}
