import type { ProofResult } from '../types';
import type { CecExpression } from './ast';
import { analyzeCecExpression } from './analyzer';
import { CecProofCache, type CecProofCacheOptions } from './proofCache';
import { CecProver, type CecKnowledgeBase, type CecProverOptions } from './prover';

export type CecStrategyType = 'forward_chaining' | 'cached_forward' | 'auto';

export interface CecStrategyInfo {
  name: string;
  type: CecStrategyType;
  priority: number;
  cost?: number;
}

export interface CecProverStrategy {
  readonly name: string;
  readonly strategyType: CecStrategyType;
  canHandle(theorem: CecExpression, kb: CecKnowledgeBase): boolean;
  prove(theorem: CecExpression, kb: CecKnowledgeBase, options?: CecProverOptions): ProofResult;
  getPriority(): number;
  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number;
}

export class CecForwardChainingStrategy implements CecProverStrategy {
  readonly name = 'CEC Forward Chaining';
  readonly strategyType = 'forward_chaining' satisfies CecStrategyType;

  canHandle(): boolean {
    return true;
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    return new CecProver(options).prove(theorem, kb);
  }

  getPriority(): number {
    return 60;
  }

  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number {
    const analysis = analyzeCecExpression(theorem);
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, analysis.nodeCount * Math.log2(kbSize + 2));
  }
}

export interface CecCachedForwardStrategyOptions extends CecProofCacheOptions {
  cache?: CecProofCache;
}

export class CecCachedForwardStrategy implements CecProverStrategy {
  readonly name = 'CEC Cached Forward Chaining';
  readonly strategyType = 'cached_forward' satisfies CecStrategyType;
  private readonly cache: CecProofCache;

  constructor(options: CecCachedForwardStrategyOptions = {}) {
    this.cache = options.cache ?? new CecProofCache(options);
  }

  canHandle(): boolean {
    return true;
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    return this.cache.prove(theorem, kb, options);
  }

  getPriority(): number {
    return 70;
  }

  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number {
    const analysis = analyzeCecExpression(theorem);
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, (analysis.maxDepth + kbSize) / 2);
  }

  getCacheStats() {
    return this.cache.getStats();
  }
}

export interface CecStrategySelectorOptions {
  strategies?: CecProverStrategy[];
}

export class CecStrategySelector {
  private readonly strategies: CecProverStrategy[];

  constructor(options: CecStrategySelectorOptions = {}) {
    this.strategies = [...(options.strategies ?? createDefaultCecStrategies())].sort(
      (left, right) => right.getPriority() - left.getPriority(),
    );
  }

  selectStrategy(theorem: CecExpression, kb: CecKnowledgeBase, preferLowCost = false): CecProverStrategy {
    if (this.strategies.length === 0) {
      throw new Error('No CEC strategies available for selection');
    }
    const applicable = this.strategies.filter((strategy) => strategy.canHandle(theorem, kb));
    const candidates = applicable.length > 0 ? applicable : this.strategies;
    if (preferLowCost) {
      return candidates.reduce((best, candidate) =>
        candidate.estimateCost(theorem, kb) < best.estimateCost(theorem, kb) ? candidate : best,
      );
    }
    return candidates[0];
  }

  getStrategyInfo(theorem?: CecExpression, kb?: CecKnowledgeBase): CecStrategyInfo[] {
    return this.strategies.map((strategy) => ({
      name: strategy.name,
      type: strategy.strategyType,
      priority: strategy.getPriority(),
      cost: theorem && kb ? strategy.estimateCost(theorem, kb) : undefined,
    }));
  }

  proveWithSelectedStrategy(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    options: CecProverOptions & { preferLowCost?: boolean } = {},
  ): ProofResult {
    const strategy = this.selectStrategy(theorem, kb, options.preferLowCost);
    return strategy.prove(theorem, kb, options);
  }
}

export function createDefaultCecStrategies(): CecProverStrategy[] {
  return [new CecCachedForwardStrategy(), new CecForwardChainingStrategy()];
}

export function proveCecWithStrategySelection(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions & { strategies?: CecProverStrategy[]; preferLowCost?: boolean } = {},
): ProofResult {
  return new CecStrategySelector({ strategies: options.strategies }).proveWithSelectedStrategy(theorem, kb, options);
}
