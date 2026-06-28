import { ProofCache, type ProofCacheOptions, type ProofCacheStats } from '../proofCache';
import type { ProofResult } from '../types';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import type { TdfolInferenceRule } from './inferenceRules';
import { TdfolProver, type TdfolKnowledgeBase, type TdfolProverOptions } from './prover';

export interface TdfolProofCacheOptions extends ProofCacheOptions {
  proverName?: string;
}

export const TDFOL_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'normalized_theorem_axiom_keys',
    'prover_config_sensitive_lookup',
    'ttl_lru_statistics',
    'cached_forward_prover_facade',
    'global_cache_helpers',
  ] as Array<string>,
} as const;

export class TdfolProofCache {
  private readonly cache: ProofCache<ProofResult>;
  private readonly proverName: string;

  constructor(options: TdfolProofCacheOptions = {}) {
    this.cache = new ProofCache<ProofResult>(options);
    this.proverName = options.proverName ?? 'tdfol-forward-chaining';
  }

  get(
    theorem: TdfolFormula,
    kb: TdfolKnowledgeBase,
    options: TdfolProverOptions = {},
  ): ProofResult | undefined {
    return this.cache.get(
      formatTdfolFormula(theorem),
      normalizeTdfolAxioms(kb),
      this.proverName,
      normalizeTdfolProverConfig(options),
    );
  }

  set(
    theorem: TdfolFormula,
    kb: TdfolKnowledgeBase,
    result: ProofResult,
    options: TdfolProverOptions = {},
  ): string {
    return this.cache.set(
      formatTdfolFormula(theorem),
      result,
      normalizeTdfolAxioms(kb),
      this.proverName,
      normalizeTdfolProverConfig(options),
    );
  }

  invalidate(
    theorem: TdfolFormula,
    kb: TdfolKnowledgeBase,
    options: TdfolProverOptions = {},
  ): boolean {
    return this.cache.invalidate(
      formatTdfolFormula(theorem),
      normalizeTdfolAxioms(kb),
      this.proverName,
      normalizeTdfolProverConfig(options),
    );
  }

  clear(): number {
    return this.cache.clear();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
  }

  prove(
    theorem: TdfolFormula,
    kb: TdfolKnowledgeBase,
    options: TdfolProverOptions = {},
  ): ProofResult {
    const cached = this.get(theorem, kb, options);
    if (cached) {
      return {
        ...cached,
        method: `${cached.method ?? this.proverName}:cached`,
      };
    }
    const result = new TdfolProver(options).prove(theorem, kb);
    this.set(theorem, kb, result, options);
    return result;
  }
}

let globalTdfolProofCache: TdfolProofCache | undefined;

export function getGlobalTdfolProofCache(): TdfolProofCache {
  globalTdfolProofCache ??= new TdfolProofCache();
  return globalTdfolProofCache;
}

export function clearGlobalTdfolProofCache(): void {
  globalTdfolProofCache?.clear();
}

export function proveTdfolWithCache(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
  options: TdfolProverOptions = {},
  cache = getGlobalTdfolProofCache(),
): ProofResult {
  return cache.prove(theorem, kb, options);
}

function normalizeTdfolAxioms(kb: TdfolKnowledgeBase): string[] {
  return [...kb.axioms, ...(kb.theorems ?? [])].map(formatTdfolFormula);
}

function normalizeTdfolProverConfig(options: TdfolProverOptions): Record<string, unknown> {
  return {
    maxSteps: options.maxSteps,
    maxDerivedFormulas: options.maxDerivedFormulas,
    rules: options.rules?.map(ruleName),
  };
}

function ruleName(rule: TdfolInferenceRule): string {
  return rule.name;
}
