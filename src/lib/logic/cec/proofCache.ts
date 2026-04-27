import { ProofCache, type ProofCacheOptions, type ProofCacheStats } from '../proofCache';
import type { ProofResult } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import type { CecInferenceRule } from './inferenceRules';
import { CecProver, type CecKnowledgeBase, type CecProverOptions } from './prover';

export interface CecProofCacheOptions extends ProofCacheOptions {
  proverName?: string;
}

export class CecProofCache {
  private readonly cache: ProofCache<ProofResult>;
  private readonly proverName: string;

  constructor(options: CecProofCacheOptions = {}) {
    this.cache = new ProofCache<ProofResult>(options);
    this.proverName = options.proverName ?? 'cec-forward-chaining';
  }

  get(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult | undefined {
    return this.cache.get(
      formatCecExpression(theorem),
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
  }

  set(theorem: CecExpression, kb: CecKnowledgeBase, result: ProofResult, options: CecProverOptions = {}): string {
    return this.cache.set(
      formatCecExpression(theorem),
      result,
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
  }

  invalidate(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): boolean {
    return this.cache.invalidate(
      formatCecExpression(theorem),
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
  }

  clear(): number {
    return this.cache.clear();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    const cached = this.get(theorem, kb, options);
    if (cached) {
      return {
        ...cached,
        method: `${cached.method ?? this.proverName}:cached`,
      };
    }
    const result = new CecProver(options).prove(theorem, kb);
    this.set(theorem, kb, result, options);
    return result;
  }
}

let globalCecProofCache: CecProofCache | undefined;

export function getGlobalCecProofCache(): CecProofCache {
  globalCecProofCache ??= new CecProofCache();
  return globalCecProofCache;
}

export function clearGlobalCecProofCache(): void {
  globalCecProofCache?.clear();
}

export function proveCecWithCache(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions = {},
  cache = getGlobalCecProofCache(),
): ProofResult {
  return cache.prove(theorem, kb, options);
}

function normalizeCecAxioms(kb: CecKnowledgeBase): string[] {
  return [...kb.axioms, ...(kb.theorems ?? [])].map(formatCecExpression);
}

function normalizeCecProverConfig(options: CecProverOptions): Record<string, unknown> {
  return {
    maxSteps: options.maxSteps,
    maxDerivedExpressions: options.maxDerivedExpressions,
    rules: options.rules?.map(ruleName),
  };
}

function ruleName(rule: CecInferenceRule): string {
  return rule.name;
}
