import type { ProofResult } from '../types';
import type { CecBinaryExpression, CecExpression } from './ast';
import { analyzeCecExpression } from './analyzer';
import { formatCecExpression } from './formatter';
import { cecExpressionEquals } from './inferenceRules';
import { CecProofCache, type CecProofCacheOptions } from './proofCache';
import { CecProver, type CecKnowledgeBase, type CecProverOptions } from './prover';

export type CecStrategyType =
  | 'forward_chaining'
  | 'cached_forward'
  | 'backward_chaining'
  | 'bidirectional'
  | 'hybrid'
  | 'auto';

export type CecProofStrategyAlias =
  | CecStrategyType
  | 'forward'
  | 'cached'
  | 'backward'
  | 'bi'
  | 'adaptive';

export interface CecStrategyInfo {
  name: string;
  type: CecStrategyType;
  priority: number;
  cost?: number;
}

export interface CecProofStrategyCandidate extends CecStrategyInfo {
  canHandle: boolean;
  selected: boolean;
  reason: string;
}

export interface CecProofStrategyPlan {
  selectedType: CecStrategyType;
  selectedName: string;
  preferLowCost: boolean;
  candidates: CecProofStrategyCandidate[];
}

export interface CecProofStrategyRunResult extends ProofResult {
  strategyPlan: CecProofStrategyPlan;
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

export class CecBackwardChainingStrategy implements CecProverStrategy {
  readonly name = 'CEC Backward Chaining';
  readonly strategyType = 'backward_chaining' satisfies CecStrategyType;

  canHandle(): boolean {
    return true;
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    const maxSteps = options.maxSteps ?? 50;
    const allKnown = [...kb.axioms, ...(kb.theorems ?? [])];
    const proof = proveBackwardGoal(theorem, allKnown, maxSteps, new Set());

    return proof
      ? {
          status: 'proved',
          theorem: formatCec(theorem),
          steps: proof,
          method: 'cec-backward-chaining',
        }
      : {
          status: 'unknown',
          theorem: formatCec(theorem),
          steps: [],
          method: 'cec-backward-chaining',
        };
  }

  getPriority(): number {
    return 55;
  }

  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number {
    const analysis = analyzeCecExpression(theorem);
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, analysis.maxDepth + Math.log2(kbSize + 2));
  }
}

export class CecBidirectionalStrategy implements CecProverStrategy {
  readonly name = 'CEC Bidirectional Search';
  readonly strategyType = 'bidirectional' satisfies CecStrategyType;

  canHandle(): boolean {
    return true;
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    const backward = new CecBackwardChainingStrategy().prove(theorem, kb, options);
    if (backward.status === 'proved') {
      return { ...backward, method: 'cec-bidirectional-search' };
    }
    const forward = new CecForwardChainingStrategy().prove(theorem, kb, options);
    return { ...forward, method: 'cec-bidirectional-search' };
  }

  getPriority(): number {
    return 58;
  }

  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number {
    const forward = new CecForwardChainingStrategy().estimateCost(theorem, kb);
    const backward = new CecBackwardChainingStrategy().estimateCost(theorem, kb);
    return Math.max(1, (forward + backward) / 2);
  }
}

export class CecHybridStrategy implements CecProverStrategy {
  readonly name = 'CEC Hybrid Adaptive';
  readonly strategyType = 'hybrid' satisfies CecStrategyType;

  canHandle(): boolean {
    return true;
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    const strategy = this.selectAdaptiveStrategy(kb);
    const result = strategy.prove(theorem, kb, options);
    return {
      ...result,
      method: `cec-hybrid:${strategy.strategyType}`,
    };
  }

  getPriority(): number {
    return 65;
  }

  estimateCost(theorem: CecExpression, kb: CecKnowledgeBase): number {
    return this.selectAdaptiveStrategy(kb).estimateCost(theorem, kb);
  }

  selectAdaptiveStrategy(kb: CecKnowledgeBase): CecProverStrategy {
    const count = kb.axioms.length + (kb.theorems?.length ?? 0);
    if (count < 5) return new CecForwardChainingStrategy();
    if (count >= 10) return new CecBackwardChainingStrategy();
    return new CecBidirectionalStrategy();
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

  selectStrategy(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    preferLowCost = false,
  ): CecProverStrategy {
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

export function buildCecProofStrategyPlan(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecStrategySelectorOptions & { preferLowCost?: boolean } = {},
): CecProofStrategyPlan {
  const strategies = [...(options.strategies ?? createDefaultCecStrategies())].sort(
    (left, right) => right.getPriority() - left.getPriority(),
  );
  if (strategies.length === 0) {
    throw new Error('No CEC strategies available for planning');
  }

  const candidates = strategies.map((strategy) => {
    const canHandle = strategy.canHandle(theorem, kb);
    return {
      name: strategy.name,
      type: strategy.strategyType,
      priority: strategy.getPriority(),
      cost: strategy.estimateCost(theorem, kb),
      canHandle,
      selected: false,
      reason: canHandle
        ? 'strategy accepted theorem and knowledge base'
        : 'strategy declined theorem or knowledge base',
    };
  });
  const applicable = candidates.filter((candidate) => candidate.canHandle);
  const ranked = applicable.length > 0 ? applicable : candidates;
  const selected = options.preferLowCost
    ? ranked.reduce((best, candidate) => (candidate.cost < best.cost ? candidate : best))
    : ranked[0];

  return {
    selectedType: selected.type,
    selectedName: selected.name,
    preferLowCost: options.preferLowCost ?? false,
    candidates: candidates.map((candidate) => ({
      ...candidate,
      selected: candidate.name === selected.name && candidate.type === selected.type,
      reason:
        candidate.name === selected.name && candidate.type === selected.type
          ? selectionReason(candidate, options.preferLowCost ?? false)
          : candidate.reason,
    })),
  };
}

export function createDefaultCecStrategies(): CecProverStrategy[] {
  return [
    new CecCachedForwardStrategy(),
    new CecHybridStrategy(),
    new CecBidirectionalStrategy(),
    new CecBackwardChainingStrategy(),
    new CecForwardChainingStrategy(),
  ];
}

export function getCecStrategy(
  strategyType: CecProofStrategyAlias,
  options: CecCachedForwardStrategyOptions = {},
): CecProverStrategy {
  const normalized = normalizeCecProofStrategyType(strategyType);
  if (normalized === 'forward_chaining') return new CecForwardChainingStrategy();
  if (normalized === 'cached_forward') return new CecCachedForwardStrategy(options);
  if (normalized === 'backward_chaining') return new CecBackwardChainingStrategy();
  if (normalized === 'bidirectional') return new CecBidirectionalStrategy();
  if (normalized === 'hybrid' || normalized === 'auto') return new CecHybridStrategy();
  throw new Error(`Unknown CEC strategy type: ${strategyType}`);
}

export function normalizeCecProofStrategyType(
  strategyType: CecProofStrategyAlias,
): CecStrategyType {
  if (strategyType === 'forward') return 'forward_chaining';
  if (strategyType === 'cached') return 'cached_forward';
  if (strategyType === 'backward') return 'backward_chaining';
  if (strategyType === 'bi') return 'bidirectional';
  if (strategyType === 'adaptive') return 'hybrid';
  if (
    strategyType === 'forward_chaining' ||
    strategyType === 'cached_forward' ||
    strategyType === 'backward_chaining' ||
    strategyType === 'bidirectional' ||
    strategyType === 'hybrid' ||
    strategyType === 'auto'
  ) {
    return strategyType;
  }
  throw new Error(`Unsupported CEC proof strategy: ${strategyType}`);
}

export function proveCecWithStrategySelection(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions & { strategies?: CecProverStrategy[]; preferLowCost?: boolean } = {},
): ProofResult {
  return new CecStrategySelector({ strategies: options.strategies }).proveWithSelectedStrategy(
    theorem,
    kb,
    options,
  );
}

export function runCecProofStrategy(
  strategyType: CecProofStrategyAlias,
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions & CecCachedForwardStrategyOptions = {},
): CecProofStrategyRunResult {
  const strategy = getCecStrategy(strategyType, options);
  const plan = buildCecProofStrategyPlan(theorem, kb, { strategies: [strategy] });
  const result = strategy.prove(theorem, kb, options);
  return { ...result, strategyPlan: plan };
}

function selectionReason(candidate: CecProofStrategyCandidate, preferLowCost: boolean): string {
  if (!candidate.canHandle) return 'fallback selected after all strategies declined';
  return preferLowCost
    ? 'selected lowest estimated browser-native proof cost'
    : 'selected highest-priority browser-native proof strategy';
}

function proveBackwardGoal(
  goal: CecExpression,
  known: CecExpression[],
  maxSteps: number,
  visited: Set<string>,
): ProofResult['steps'] | undefined {
  const key = formatCec(goal);
  if (visited.has(key) || visited.size >= maxSteps) return undefined;
  visited.add(key);

  if (known.some((candidate) => cecExpressionEquals(candidate, goal))) return [];

  if (isBinary(goal, 'and')) {
    const leftSteps = proveBackwardGoal(goal.left, known, maxSteps, visited);
    const rightSteps = proveBackwardGoal(goal.right, known, maxSteps, visited);
    if (leftSteps && rightSteps) {
      return [
        ...leftSteps,
        ...rightSteps,
        {
          id: `cec-backward-${visited.size}`,
          rule: 'CecBackwardConjunctionGoal',
          premises: [formatCec(goal.left), formatCec(goal.right)],
          conclusion: formatCec(goal),
          explanation: 'Solved both conjunctive subgoals.',
        },
      ];
    }
  }

  for (const implication of known.filter((candidate): candidate is CecBinaryExpression =>
    isBinary(candidate, 'implies'),
  )) {
    if (!cecExpressionEquals(implication.right, goal)) continue;
    const substeps = proveBackwardGoal(implication.left, known, maxSteps, visited);
    if (!substeps) continue;
    return [
      ...substeps,
      {
        id: `cec-backward-${visited.size}`,
        rule: 'CecBackwardImplication',
        premises: [formatCec(implication.left), formatCec(implication)],
        conclusion: formatCec(goal),
        explanation: 'Reduced the goal to an implication antecedent.',
      },
    ];
  }

  return undefined;
}

function isBinary(
  expression: CecExpression,
  operator: CecBinaryExpression['operator'],
): expression is CecBinaryExpression {
  return expression.kind === 'binary' && expression.operator === operator;
}

function formatCec(expression: CecExpression): string {
  return expressionToStringCache.get(expression) ?? cacheFormattedExpression(expression);
}

const expressionToStringCache = new WeakMap<CecExpression, string>();

function cacheFormattedExpression(expression: CecExpression): string {
  const formatted = formatCecExpression(expression);
  expressionToStringCache.set(expression, formatted);
  return formatted;
}
