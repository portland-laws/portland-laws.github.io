import { ProofCache } from '../proofCache';
import type { ProofResult } from '../types';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import type { TdfolKnowledgeBase } from './prover';
import {
  proveTdfolWithStrategySelection,
  TdfolForwardChainingStrategy,
  type TdfolProverStrategy,
} from './strategies';

export type TdfolProvingStrategy =
  | 'forward'
  | 'backward'
  | 'bidirectional'
  | 'modal_tableaux'
  | 'auto';
export type TdfolFormulaType = 'temporal' | 'deontic' | 'propositional' | 'modal';

export interface TdfolOptimizationStatsSnapshot {
  cacheHits: number;
  cacheMisses: number;
  zkpVerifications: number;
  indexedLookups: number;
  indexedCandidates: number;
  indexedPrunes: number;
  parallelSearches: number;
  strategySwitches: number;
  totalProofs: number;
  avgProofTimeMs: number;
  cacheHitRate: number;
}

export const TDFOL_OPTIMIZATION_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_optimization.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
  parity: [
    'indexed_knowledge_base',
    'cache_aware_proving',
    'strategy_heuristics',
    'relevance_pruning',
    'optimization_stats',
    'zkp_fail_closed_accounting',
    'parallel_search_accounting',
  ] as Array<string>,
} as const;

export class TdfolOptimizationStats {
  cacheHits = 0;
  cacheMisses = 0;
  zkpVerifications = 0;
  indexedLookups = 0;
  indexedCandidates = 0;
  indexedPrunes = 0;
  parallelSearches = 0;
  strategySwitches = 0;
  totalProofs = 0;
  avgProofTimeMs = 0;

  get cacheHitRate(): number {
    const total = this.cacheHits + this.cacheMisses;
    return total > 0 ? this.cacheHits / total : 0;
  }

  recordProof(timeMs: number): void {
    this.totalProofs += 1;
    this.avgProofTimeMs =
      (this.avgProofTimeMs * (this.totalProofs - 1) + timeMs) / this.totalProofs;
  }

  snapshot(): TdfolOptimizationStatsSnapshot {
    return {
      cacheHits: this.cacheHits,
      cacheMisses: this.cacheMisses,
      zkpVerifications: this.zkpVerifications,
      indexedLookups: this.indexedLookups,
      indexedCandidates: this.indexedCandidates,
      indexedPrunes: this.indexedPrunes,
      parallelSearches: this.parallelSearches,
      strategySwitches: this.strategySwitches,
      totalProofs: this.totalProofs,
      avgProofTimeMs: this.avgProofTimeMs,
      cacheHitRate: this.cacheHitRate,
    };
  }

  toString(): string {
    return `OptimizationStats(cache_hits=${this.cacheHits}, cache_misses=${this.cacheMisses}, hit_rate=${(this.cacheHitRate * 100).toFixed(1)}%, indexed_lookups=${this.indexedLookups}, indexed_candidates=${this.indexedCandidates}, indexed_prunes=${this.indexedPrunes}, strategy_switches=${this.strategySwitches}, total_proofs=${this.totalProofs}, avg_time=${this.avgProofTimeMs.toFixed(2)}ms)`;
  }
}

export class TdfolIndexedKnowledgeBase {
  readonly formulas = new Map<string, TdfolFormula>();
  readonly temporalFormulas = new Set<string>();
  readonly deonticFormulas = new Set<string>();
  readonly propositionalFormulas = new Set<string>();
  readonly modalFormulas = new Set<string>();
  readonly operatorIndex = new Map<string, Set<string>>();
  readonly complexityIndex = new Map<number, Set<string>>();
  readonly predicateIndex = new Map<string, Set<string>>();

  constructor(kb?: TdfolKnowledgeBase) {
    if (kb) {
      for (const formula of [...kb.axioms, ...(kb.theorems ?? [])]) {
        this.add(formula);
      }
    }
  }

  add(formula: TdfolFormula): void {
    const key = formatTdfolFormula(formula);
    this.formulas.set(key, formula);

    for (const type of this.getFormulaTypes(formula)) {
      this.typeSet(type).add(key);
    }
    for (const operator of this.extractOperators(formula)) {
      addToIndex(this.operatorIndex, operator, key);
    }
    addToIndex(this.complexityIndex, this.getComplexity(formula), key);
    for (const predicate of this.extractPredicates(formula)) {
      addToIndex(this.predicateIndex, predicate, key);
    }
  }

  getByType(type: TdfolFormulaType): TdfolFormula[] {
    return this.fromKeys(this.typeSet(type));
  }

  getByOperator(operator: string): TdfolFormula[] {
    return this.fromKeys(this.operatorIndex.get(operator) ?? new Set());
  }

  getByComplexity(complexity: number): TdfolFormula[] {
    return this.fromKeys(this.complexityIndex.get(complexity) ?? new Set());
  }

  getByPredicate(predicate: string): TdfolFormula[] {
    return this.fromKeys(this.predicateIndex.get(predicate) ?? new Set());
  }

  getRelevantFormulas(goal: TdfolFormula): TdfolFormula[] {
    return this.fromKeys(this.getRelevantFormulaKeys(goal));
  }

  size(): number {
    return this.formulas.size;
  }

  getFormulaTypes(formula: TdfolFormula): TdfolFormulaType[] {
    const types = new Set<TdfolFormulaType>();
    visitFormula(formula, (node) => {
      if (node.kind === 'temporal') {
        types.add('temporal');
        types.add('modal');
      }
      if (node.kind === 'deontic') {
        types.add('deontic');
        types.add('modal');
      }
    });
    if (types.size === 0) {
      types.add('propositional');
    }
    return [...types];
  }

  getComplexity(formula: TdfolFormula): number {
    return getFormulaDepth(formula);
  }

  extractPredicates(formula: TdfolFormula): string[] {
    const predicates = new Set<string>();
    visitFormula(formula, (node) => {
      if (node.kind === 'predicate') {
        predicates.add(node.name);
      }
    });
    return [...predicates].sort();
  }

  private extractOperators(formula: TdfolFormula): string[] {
    const operators = new Set<string>();
    visitFormula(formula, (node) => {
      if (node.kind === 'temporal') operators.add(node.operator);
      if (node.kind === 'deontic') operators.add(node.operator);
      if (node.kind === 'binary') operators.add(node.operator);
      if (node.kind === 'unary') operators.add(node.operator);
      if (node.kind === 'quantified') operators.add(node.quantifier);
    });
    return [...operators].sort();
  }

  private getRelevantFormulaKeys(goal: TdfolFormula): Set<string> {
    const keys = new Set<string>();
    const goalPredicates = new Set(this.extractPredicates(goal));
    const pendingPredicates = [...goalPredicates];

    for (const type of this.getFormulaTypes(goal)) {
      if (type === 'propositional') {
        continue;
      }
      for (const key of this.typeSet(type)) {
        keys.add(key);
      }
    }
    for (const operator of this.extractOperators(goal)) {
      for (const key of this.operatorIndex.get(operator) ?? []) {
        keys.add(key);
      }
    }

    while (pendingPredicates.length > 0) {
      const predicate = pendingPredicates.pop();
      if (!predicate) {
        continue;
      }
      for (const key of this.predicateIndex.get(predicate) ?? []) {
        if (keys.has(key)) {
          continue;
        }
        keys.add(key);
        const formula = this.formulas.get(key);
        if (formula?.kind === 'binary' && formula.operator === 'IMPLIES') {
          for (const premisePredicate of this.extractPredicates(formula.left)) {
            if (!goalPredicates.has(premisePredicate)) {
              goalPredicates.add(premisePredicate);
              pendingPredicates.push(premisePredicate);
            }
          }
        }
      }
    }
    return keys.size > 0 ? keys : new Set(this.formulas.keys());
  }

  private typeSet(type: TdfolFormulaType): Set<string> {
    switch (type) {
      case 'temporal':
        return this.temporalFormulas;
      case 'deontic':
        return this.deonticFormulas;
      case 'propositional':
        return this.propositionalFormulas;
      case 'modal':
        return this.modalFormulas;
    }
  }

  private fromKeys(keys: Set<string>): TdfolFormula[] {
    return [...keys]
      .map((key) => this.formulas.get(key))
      .filter((formula): formula is TdfolFormula => Boolean(formula));
  }
}

export interface TdfolOptimizedProverOptions {
  enableCache?: boolean;
  enableZkp?: boolean;
  cacheMaxSize?: number;
  cacheTtlMs?: number;
  workers?: number;
  strategy?: TdfolProvingStrategy;
  strategies?: TdfolProverStrategy[];
  cache?: ProofCache<ProofResult>;
}

export class TdfolOptimizedProver {
  readonly indexedKb: TdfolIndexedKnowledgeBase;
  readonly stats = new TdfolOptimizationStats();
  private readonly kb: TdfolKnowledgeBase;
  private readonly enableCache: boolean;
  private readonly enableZkp: boolean;
  private readonly workers: number;
  private readonly defaultStrategy: TdfolProvingStrategy;
  private readonly strategies: TdfolProverStrategy[];
  private readonly cache?: ProofCache<ProofResult>;

  constructor(kb: TdfolKnowledgeBase, options: TdfolOptimizedProverOptions = {}) {
    this.kb = kb;
    this.indexedKb = new TdfolIndexedKnowledgeBase(kb);
    this.enableCache = options.enableCache ?? true;
    this.enableZkp = options.enableZkp ?? false;
    this.workers = options.workers ?? 1;
    this.defaultStrategy = options.strategy ?? 'auto';
    this.strategies = options.strategies ?? [new TdfolForwardChainingStrategy()];
    this.cache = this.enableCache
      ? (options.cache ??
        new ProofCache<ProofResult>({
          maxSize: options.cacheMaxSize ?? 10000,
          ttlMs: options.cacheTtlMs ?? 60 * 60 * 1000,
        }))
      : undefined;
  }

  prove(
    formula: TdfolFormula,
    options: { timeoutMs?: number; strategy?: TdfolProvingStrategy; preferZkp?: boolean } = {},
  ): ProofResult {
    const start = nowMs();
    const strategy = options.strategy ?? this.defaultStrategy;
    const cacheKeyStrategy = strategy === 'auto' ? this.selectStrategy(formula) : strategy;

    if (this.cache) {
      const cached = this.cache.get(
        formatTdfolFormula(formula),
        this.kbFormulaStrings(),
        cacheKeyStrategy,
      );
      if (cached) {
        this.stats.cacheHits += 1;
        this.stats.recordProof(nowMs() - start);
        return { ...cached, method: `${cached.method ?? cacheKeyStrategy}:cache-hit` };
      }
      this.stats.cacheMisses += 1;
    }

    if (this.enableZkp && options.preferZkp) {
      this.stats.zkpVerifications += 1;
    }

    const selectedStrategy = strategy === 'auto' ? cacheKeyStrategy : strategy;
    if (strategy === 'auto') {
      this.stats.strategySwitches += 1;
    }

    const result = this.proveIndexed(formula, selectedStrategy, options.timeoutMs);
    const elapsed = nowMs() - start;
    this.stats.recordProof(elapsed);

    const normalizedResult = {
      ...result,
      method: selectedStrategy,
      timeMs: result.timeMs ?? elapsed,
    };

    this.cache?.set(
      formatTdfolFormula(formula),
      normalizedResult,
      this.kbFormulaStrings(),
      selectedStrategy,
    );
    return normalizedResult;
  }

  selectStrategy(formula: TdfolFormula): TdfolProvingStrategy {
    const types = this.indexedKb.getFormulaTypes(formula);
    const kbSize = this.indexedKb.size();
    const complexity = this.indexedKb.getComplexity(formula);

    if (types.includes('modal') || types.includes('temporal') || types.includes('deontic')) {
      return 'modal_tableaux';
    }
    if (kbSize > 100 && complexity < 3) {
      return 'forward';
    }
    if (kbSize < 50 && complexity >= 3) {
      return 'backward';
    }
    return 'bidirectional';
  }

  getStats(): TdfolOptimizationStatsSnapshot {
    return this.stats.snapshot();
  }

  resetStats(): void {
    this.stats.cacheHits = 0;
    this.stats.cacheMisses = 0;
    this.stats.zkpVerifications = 0;
    this.stats.indexedLookups = 0;
    this.stats.indexedCandidates = 0;
    this.stats.indexedPrunes = 0;
    this.stats.parallelSearches = 0;
    this.stats.strategySwitches = 0;
    this.stats.totalProofs = 0;
    this.stats.avgProofTimeMs = 0;
  }

  private proveIndexed(
    formula: TdfolFormula,
    strategy: TdfolProvingStrategy,
    timeoutMs?: number,
  ): ProofResult {
    this.stats.indexedLookups += 1;
    if (this.workers > 1) {
      this.stats.parallelSearches += 1;
    }

    const candidateAxioms = this.indexedKb.getRelevantFormulas(formula);
    this.stats.indexedCandidates += candidateAxioms.length;
    if (candidateAxioms.length > 0 && candidateAxioms.length < this.indexedKb.size()) {
      this.stats.indexedPrunes += this.indexedKb.size() - candidateAxioms.length;
    }

    return proveTdfolWithStrategySelection(
      formula,
      {
        axioms: candidateAxioms.length > 0 ? candidateAxioms : this.kb.axioms,
        theorems: this.kb.theorems,
      },
      {
        strategies: this.strategies,
        preferLowCost: strategy === 'backward' || strategy === 'bidirectional',
        timeoutMs,
      },
    );
  }

  private kbFormulaStrings(): string[] {
    return [...this.kb.axioms, ...(this.kb.theorems ?? [])].map(formatTdfolFormula);
  }
}

export function createTdfolOptimizedProver(
  kb: TdfolKnowledgeBase,
  options: TdfolOptimizedProverOptions = {},
): TdfolOptimizedProver {
  return new TdfolOptimizedProver(kb, options);
}

function visitFormula(formula: TdfolFormula, visitor: (formula: TdfolFormula) => void): void {
  visitor(formula);
  switch (formula.kind) {
    case 'predicate':
      return;
    case 'unary':
    case 'temporal':
    case 'deontic':
    case 'quantified':
      visitFormula(formula.formula, visitor);
      return;
    case 'binary':
      visitFormula(formula.left, visitor);
      visitFormula(formula.right, visitor);
      return;
  }
}

function getFormulaDepth(formula: TdfolFormula): number {
  switch (formula.kind) {
    case 'predicate':
      return 1;
    case 'unary':
    case 'temporal':
    case 'deontic':
    case 'quantified':
      return 1 + getFormulaDepth(formula.formula);
    case 'binary':
      return 1 + Math.max(getFormulaDepth(formula.left), getFormulaDepth(formula.right));
  }
}

function addToIndex<Key>(index: Map<Key, Set<string>>, key: Key, formulaKey: string): void {
  const formulas = index.get(key) ?? new Set<string>();
  formulas.add(formulaKey);
  index.set(key, formulas);
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}
