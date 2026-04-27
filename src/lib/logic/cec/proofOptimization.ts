export const CecPruningStrategy = {
  DEPTH_LIMIT: 'depth_limit',
  EARLY_TERMINATION: 'early_termination',
  REDUNDANCY_CHECK: 'redundancy_check',
  COMBINED: 'combined',
} as const;

export type CecPruningStrategyValue = typeof CecPruningStrategy[keyof typeof CecPruningStrategy];

export interface CecProofNodeOptions {
  formula: string;
  depth: number;
  parent?: CecProofNode;
  children?: CecProofNode[];
  isGoal?: boolean;
  isRedundant?: boolean;
  proofStep?: string;
}

export class CecProofNode {
  formula: string;
  depth: number;
  parent?: CecProofNode;
  children: CecProofNode[];
  isGoal: boolean;
  isRedundant: boolean;
  proofStep?: string;

  constructor(options: CecProofNodeOptions) {
    this.formula = options.formula;
    this.depth = options.depth;
    this.parent = options.parent;
    this.children = [...(options.children ?? [])];
    this.isGoal = options.isGoal ?? false;
    this.isRedundant = options.isRedundant ?? false;
    this.proofStep = options.proofStep;
    for (const child of this.children) child.parent = this;
  }

  equals(other: unknown): boolean {
    return other instanceof CecProofNode && other.formula === this.formula;
  }

  addChild(child: CecProofNode): void {
    child.parent = this;
    this.children.push(child);
  }

  cloneWithoutParent(): CecProofNode {
    const clone = new CecProofNode({
      formula: this.formula,
      depth: this.depth,
      isGoal: this.isGoal,
      isRedundant: this.isRedundant,
      proofStep: this.proofStep,
    });
    clone.children = this.children.map((child) => {
      const childClone = child.cloneWithoutParent();
      childClone.parent = clone;
      return childClone;
    });
    return clone;
  }
}

export interface CecOptimizationMetricsDict {
  nodes_explored: number;
  nodes_pruned: number;
  duplicates_eliminated: number;
  subsumptions_found: number;
  total_time: number;
  parallel_speedup: number;
  pruning_ratio: number;
}

export class CecOptimizationMetrics {
  nodesExplored = 0;
  nodesPruned = 0;
  duplicatesEliminated = 0;
  subsumptionsFound = 0;
  totalTime = 0;
  parallelSpeedup = 1;

  pruningRatio(): number {
    const total = this.nodesExplored + this.nodesPruned;
    return total > 0 ? this.nodesPruned / total : 0;
  }

  add(other: CecOptimizationMetrics): void {
    this.nodesExplored += other.nodesExplored;
    this.nodesPruned += other.nodesPruned;
    this.duplicatesEliminated += other.duplicatesEliminated;
    this.subsumptionsFound += other.subsumptionsFound;
    this.totalTime += other.totalTime;
    this.parallelSpeedup = Math.max(this.parallelSpeedup, other.parallelSpeedup);
  }

  toDict(): CecOptimizationMetricsDict {
    return {
      nodes_explored: this.nodesExplored,
      nodes_pruned: this.nodesPruned,
      duplicates_eliminated: this.duplicatesEliminated,
      subsumptions_found: this.subsumptionsFound,
      total_time: this.totalTime,
      parallel_speedup: this.parallelSpeedup,
      pruning_ratio: this.pruningRatio(),
    };
  }
}

export class CecProofTreePruner {
  readonly maxDepth: number;
  readonly enableEarlyTermination: boolean;
  metrics = new CecOptimizationMetrics();

  constructor(maxDepth = 10, enableEarlyTermination = true) {
    this.maxDepth = maxDepth;
    this.enableEarlyTermination = enableEarlyTermination;
  }

  shouldPrune(node: CecProofNode, visited: Set<string>): [boolean, string] {
    if (node.depth > this.maxDepth) return [true, CecPruningStrategy.DEPTH_LIMIT];
    if (visited.has(node.formula)) return [true, 'redundancy'];
    if (this.enableEarlyTermination && node.isGoal) return [false, 'goal_reached'];
    return [false, ''];
  }

  pruneTree(root: CecProofNode): [CecProofNode, CecOptimizationMetrics] {
    const start = now();
    const visited = new Set<string>();
    this.metrics = new CecOptimizationMetrics();
    const workingRoot = root.cloneWithoutParent();

    const pruneRecursive = (node: CecProofNode): CecProofNode | undefined => {
      const [shouldPrune, reason] = this.shouldPrune(node, visited);
      if (shouldPrune) {
        this.metrics.nodesPruned += 1;
        node.isRedundant = reason === 'redundancy';
        if (reason === 'redundancy') this.metrics.duplicatesEliminated += 1;
        return undefined;
      }

      this.metrics.nodesExplored += 1;
      visited.add(node.formula);
      node.children = node.children.flatMap((child) => {
        const pruned = pruneRecursive(child);
        if (!pruned) return [];
        pruned.parent = node;
        return [pruned];
      });
      return node;
    };

    const pruned = pruneRecursive(workingRoot) ?? workingRoot;
    this.metrics.totalTime = elapsedSeconds(start);
    return [pruned, this.metrics];
  }
}

export class CecRedundancyEliminator {
  readonly seenFormulas = new Set<string>();
  readonly subsumptionCache = new Map<string, string[]>();
  metrics = new CecOptimizationMetrics();

  isDuplicate(formula: string): boolean {
    if (this.seenFormulas.has(formula)) {
      this.metrics.duplicatesEliminated += 1;
      return true;
    }
    this.seenFormulas.add(formula);
    return false;
  }

  subsumes(formula1: string, formula2: string): boolean {
    if (formula1 === formula2) return true;
    return formula2.includes(formula1) && formula2.length > formula1.length;
  }

  eliminateRedundancy(formulas: string[]): string[] {
    const start = now();
    this.seenFormulas.clear();
    this.metrics = new CecOptimizationMetrics();
    const result: string[] = [];

    for (const formula of formulas) {
      if (this.isDuplicate(formula)) continue;
      const isSubsumed = result.some((existing) => {
        const subsumed = this.subsumes(existing, formula);
        if (subsumed) this.metrics.subsumptionsFound += 1;
        return subsumed;
      });
      if (!isSubsumed) {
        result.push(formula);
        this.metrics.nodesExplored += 1;
      }
    }

    this.metrics.totalTime = elapsedSeconds(start);
    return result;
  }

  getMetrics(): CecOptimizationMetrics {
    return this.metrics;
  }
}

export class CecParallelProofSearch {
  readonly maxWorkers: number;
  metrics = new CecOptimizationMetrics();

  constructor(maxWorkers = 4) {
    this.maxWorkers = Math.max(1, maxWorkers);
  }

  async searchParallel<TSpace, TResult>(
    searchFn: (space: TSpace) => TResult | undefined | Promise<TResult | undefined>,
    searchSpaces: TSpace[],
  ): Promise<TResult | undefined> {
    const start = now();
    this.metrics = new CecOptimizationMetrics();
    const pending = [...searchSpaces];

    while (pending.length > 0) {
      const batch = pending.splice(0, this.maxWorkers);
      const results = await Promise.all(batch.map(async (space) => {
        try {
          return await searchFn(space);
        } catch {
          return undefined;
        }
      }));
      const found = results.find((result) => result !== undefined && result !== null);
      this.metrics.nodesExplored += batch.length;
      if (found !== undefined) {
        const elapsed = elapsedSeconds(start);
        this.metrics.totalTime = elapsed;
        this.metrics.parallelSpeedup = elapsed > 0 ? (elapsed * searchSpaces.length) / elapsed : 1;
        return found as TResult;
      }
    }

    this.metrics.totalTime = elapsedSeconds(start);
    return undefined;
  }

  getMetrics(): CecOptimizationMetrics {
    return this.metrics;
  }
}

export interface CecProofOptimizerOptions {
  maxDepth?: number;
  enablePruning?: boolean;
  enableRedundancyElimination?: boolean;
  enableParallel?: boolean;
  maxWorkers?: number;
}

export class CecProofOptimizer {
  readonly maxDepth: number;
  readonly enablePruning: boolean;
  readonly enableRedundancyElimination: boolean;
  readonly enableParallel: boolean;
  readonly pruner: CecProofTreePruner;
  readonly eliminator: CecRedundancyEliminator;
  readonly parallelSearch: CecParallelProofSearch;
  combinedMetrics = new CecOptimizationMetrics();

  constructor(options: CecProofOptimizerOptions = {}) {
    this.maxDepth = options.maxDepth ?? 10;
    this.enablePruning = options.enablePruning ?? true;
    this.enableRedundancyElimination = options.enableRedundancyElimination ?? true;
    this.enableParallel = options.enableParallel ?? false;
    this.pruner = new CecProofTreePruner(this.maxDepth);
    this.eliminator = new CecRedundancyEliminator();
    this.parallelSearch = new CecParallelProofSearch(options.maxWorkers ?? 4);
  }

  optimizeProofTree(root: CecProofNode): [CecProofNode, CecOptimizationMetrics] {
    const start = now();
    this.combinedMetrics = new CecOptimizationMetrics();
    let result = root;

    if (this.enablePruning) {
      const [pruned, pruneMetrics] = this.pruner.pruneTree(result);
      result = pruned;
      this.combinedMetrics.add(pruneMetrics);
    }

    if (this.enableRedundancyElimination) {
      this.eliminator.eliminateRedundancy(this.collectFormulas(result));
      this.combinedMetrics.add(this.eliminator.getMetrics());
    }

    this.combinedMetrics.totalTime = elapsedSeconds(start);
    return [result, this.combinedMetrics];
  }

  collectFormulas(node: CecProofNode): string[] {
    return [node.formula, ...node.children.flatMap((child) => this.collectFormulas(child))];
  }

  getCombinedMetrics(): CecOptimizationMetrics {
    return this.combinedMetrics;
  }
}

export function createCecProofNode(formula: string, depth: number, children: CecProofNode[] = []): CecProofNode {
  return new CecProofNode({ formula, depth, children });
}

function now(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}

function elapsedSeconds(start: number): number {
  return Math.max(0, (now() - start) / 1000);
}
