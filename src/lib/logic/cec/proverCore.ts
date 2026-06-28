import type { CecExpression } from './ast';
import {
  CecProver,
  type CecKnowledgeBase,
  type CecProofResult,
  type CecProverOptions,
} from './prover';

export const CEC_PROVER_CORE_RUNTIME = {
  module: 'logic/CEC/native/prover_core.py',
  runtime: 'browser-native-typescript',
  pythonRuntime: false,
  serverDelegation: false,
} as const;

export interface CecProverCoreSearchLimits {
  maxDepth: number;
  maxNodes: number;
  maxRuleApplications: number;
}

export interface CecProverCoreSearchLimitOverrides {
  maxDepth?: number;
  maxNodes?: number;
  maxRuleApplications?: number;
}

export interface CecProverCoreOptions extends CecProverOptions {
  searchLimits?: CecProverCoreSearchLimitOverrides;
}

export interface CecProverCoreDependencies {
  proverFactory?: (options: CecProverOptions) => {
    prove: (theorem: CecExpression, kb: CecKnowledgeBase) => CecProofResult;
  };
  now?: () => number;
}

export interface CecProverCoreResult {
  proof: CecProofResult | null;
  summary: {
    outcome: 'proved' | 'not_proved' | 'invalid_input';
    success: boolean;
    elapsedMs: number;
    diagnostics: Array<unknown>;
    limits: CecProverCoreSearchLimits;
    metadata: Record<string, unknown>;
  };
}

const DEFAULT_LIMITS: CecProverCoreSearchLimits = {
  maxDepth: 12,
  maxNodes: 256,
  maxRuleApplications: 512,
};

export function normalizeCecProverCoreSearchLimits(
  limits: CecProverCoreSearchLimitOverrides = {},
): CecProverCoreSearchLimits {
  return {
    maxDepth: asPositiveInt(limits.maxDepth, DEFAULT_LIMITS.maxDepth),
    maxNodes: asPositiveInt(limits.maxNodes, DEFAULT_LIMITS.maxNodes),
    maxRuleApplications: asPositiveInt(
      limits.maxRuleApplications,
      DEFAULT_LIMITS.maxRuleApplications,
    ),
  };
}

export class BrowserNativeCecProverCore {
  constructor(
    private readonly options: CecProverCoreOptions = {},
    private readonly dependencies: CecProverCoreDependencies = {},
  ) {}

  prove(theorem: CecExpression, kb: CecKnowledgeBase): CecProverCoreResult {
    const limits = normalizeCecProverCoreSearchLimits(this.options.searchLimits);
    if (theorem === null || theorem === undefined) {
      return invalid('Theorem must be provided as a CEC expression.', limits);
    }
    if (kb === null || kb === undefined) {
      return invalid('Knowledge base must be provided for proof search.', limits);
    }

    const now = this.dependencies.now ?? Date.now;
    const started = now();
    try {
      const merged: Record<string, unknown> = { ...(this.options as Record<string, unknown>) };
      delete merged.searchLimits;
      merged.maxDepth = limits.maxDepth;
      merged.maxNodes = limits.maxNodes;
      merged.maxRuleApplications = limits.maxRuleApplications;
      const proverFactory =
        this.dependencies.proverFactory ?? ((options: CecProverOptions) => new CecProver(options));
      const proof = proverFactory(merged as CecProverOptions).prove(theorem, kb);
      return summary(proof, inferSuccess(proof), now() - started, limits, []);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown prover error.';
      return summary(null, false, now() - started, limits, [message]);
    }
  }
}

export const CecProverCore = BrowserNativeCecProverCore;

export function createBrowserNativeCecProverCore(options: CecProverCoreOptions = {}) {
  return new BrowserNativeCecProverCore(options);
}

export const create_cec_prover_core = createBrowserNativeCecProverCore;

export function proveCecCore(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverCoreOptions = {},
  dependencies: CecProverCoreDependencies = {},
): CecProverCoreResult {
  return new BrowserNativeCecProverCore(options, dependencies).prove(theorem, kb);
}

export const prove_cec_core = proveCecCore;

function summary(
  proof: CecProofResult | null,
  success: boolean,
  elapsedMs: number,
  limits: CecProverCoreSearchLimits,
  diagnostics: Array<unknown>,
): CecProverCoreResult {
  return {
    proof,
    summary: {
      outcome: diagnostics.length > 0 ? 'not_proved' : success ? 'proved' : 'not_proved',
      success,
      elapsedMs: elapsedMs > 0 ? Math.floor(elapsedMs) : 0,
      diagnostics,
      limits,
      metadata: CEC_PROVER_CORE_RUNTIME,
    },
  };
}

function invalid(message: string, limits: CecProverCoreSearchLimits): CecProverCoreResult {
  return {
    proof: null,
    summary: {
      outcome: 'invalid_input',
      success: false,
      elapsedMs: 0,
      diagnostics: [message],
      limits,
      metadata: CEC_PROVER_CORE_RUNTIME,
    },
  };
}

function inferSuccess(proof: CecProofResult): boolean {
  if (typeof proof === 'object' && proof !== null) {
    const flags = proof as { success?: unknown; proved?: unknown };
    if (typeof flags.success === 'boolean') return flags.success;
    if (typeof flags.proved === 'boolean') return flags.proved;
  }
  return true;
}

function asPositiveInt(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  const normalized = Math.floor(value);
  return normalized >= 1 ? normalized : fallback;
}
