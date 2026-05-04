import {
  CecParallelProofSearch,
  CecProofNode,
  CecProofOptimizer,
  CecProofTreePruner,
  CecRedundancyEliminator,
  createCecProofNode,
} from './proofOptimization';
import {
  CecFormulaCache,
  canonicalizeCecFormulaSource,
  createCecFormulaCache,
} from './formulaCache';

describe('CEC proof optimization parity helpers', () => {
  it('caches parsed CEC formulas by canonical source with Python metadata', () => {
    const cache = createCecFormulaCache({ maxSize: 4 });

    const first = cache.getFormula('  (and p   q) ');
    const second = cache.get_formula('(and p q)');

    expect(first).toBe(second);
    expect(first).toMatchObject({
      ok: true,
      canonical: '(and p q)',
      dependencies: ['p', 'q'],
      metadata: {
        sourcePythonModule: 'logic/CEC/optimization/formula_cache.py',
        browserNative: true,
        pythonRuntime: false,
        serverRuntime: false,
      },
    });
    expect(cache.getStats()).toMatchObject({
      hits: 1,
      misses: 1,
      parseAttempts: 1,
      parseFailures: 0,
    });
    expect(canonicalizeCecFormulaSource('\n(and   p\tq)  ')).toBe('(and p q)');
  });

  it('caches fail-closed errors and bounds entries deterministically', () => {
    const errors = new CecFormulaCache({
      parser: () => {
        throw new Error('bad formula');
      },
    });

    const first = errors.getFormula('not-valid');
    const second = errors.getFormula(' not-valid ');

    expect(first).toBe(second);
    expect(first.ok).toBe(false);
    expect(first.error).toBe('bad formula');
    expect(errors.get_stats()).toMatchObject({
      hits: 1,
      misses: 1,
      parseAttempts: 1,
      parseFailures: 1,
    });
    let now = 0;
    const cache = createCecFormulaCache({ maxSize: 2, ttlMs: 10, now: () => now });

    cache.getFormula('p');
    cache.getFormula('q');
    expect(cache.hasFormula('p')).toBe(true);
    cache.getFormula('r');

    expect(cache.has_formula('q')).toBe(false);
    now = 11;
    expect(cache.getFormula('p').ok).toBe(true);
    expect(cache.getStats().expirations).toBe(1);
  });

  it('models proof nodes with parent links, equality, and clone support', () => {
    const root = createCecProofNode('p', 0);
    const child = createCecProofNode('q', 1);
    root.addChild(child);

    const clone = root.cloneWithoutParent();

    expect(root.equals(createCecProofNode('p', 9))).toBe(true);
    expect(root.equals(child)).toBe(false);
    expect(child.parent).toBe(root);
    expect(clone).not.toBe(root);
    expect(clone.children[0].parent).toBe(clone);
  });

  it('prunes proof trees by depth and duplicate formulas', () => {
    const root = new CecProofNode({
      formula: 'root',
      depth: 0,
      children: [
        new CecProofNode({ formula: 'a', depth: 1 }),
        new CecProofNode({ formula: 'a', depth: 2 }),
        new CecProofNode({ formula: 'too-deep', depth: 3 }),
      ],
    });
    const pruner = new CecProofTreePruner(2);

    const [pruned, metrics] = pruner.pruneTree(root);

    expect(pruned.children.map((child) => child.formula)).toEqual(['a']);
    expect(metrics.toDict()).toMatchObject({
      nodes_explored: 2,
      nodes_pruned: 2,
      duplicates_eliminated: 1,
    });
    expect(metrics.pruningRatio()).toBe(0.5);
  });

  it('terminates a branch once a goal node is reached', () => {
    const root = new CecProofNode({
      formula: 'root',
      depth: 0,
      children: [
        new CecProofNode({
          formula: 'goal',
          depth: 1,
          isGoal: true,
          children: [new CecProofNode({ formula: 'unneeded-step', depth: 2 })],
        }),
      ],
    });
    const pruner = new CecProofTreePruner(10, true);

    const [pruned, metrics] = pruner.pruneTree(root);

    expect(pruned.children[0].formula).toBe('goal');
    expect(pruned.children[0].children).toEqual([]);
    expect(metrics.nodesExplored).toBe(2);
    expect(metrics.nodesPruned).toBe(1);
  });

  it('eliminates duplicate and syntactically subsumed formulas', () => {
    const eliminator = new CecRedundancyEliminator();

    const formulas = eliminator.eliminateRedundancy(['p', 'p', 'p(x)', 'q']);

    expect(formulas).toEqual(['p', 'q']);
    expect(eliminator.subsumes('p', 'p(x)')).toBe(true);
    expect(eliminator.getMetrics().toDict()).toMatchObject({
      duplicates_eliminated: 1,
      subsumptions_found: 1,
      nodes_explored: 2,
    });
  });

  it('resets redundancy metrics and subsumption cache between formula batches', () => {
    const eliminator = new CecRedundancyEliminator();

    expect(eliminator.eliminateRedundancy(['p', 'p(x)'])).toEqual(['p']);
    expect(eliminator.subsumptionCache.size).toBeGreaterThan(0);
    expect(eliminator.eliminateRedundancy(['q', 'r'])).toEqual(['q', 'r']);

    expect(eliminator.subsumptionCache.size).toBeGreaterThan(0);
    expect(eliminator.getMetrics().toDict()).toMatchObject({
      duplicates_eliminated: 0,
      subsumptions_found: 0,
      nodes_explored: 2,
    });
  });

  it('searches browser-native async batches without worker dependencies', async () => {
    const search = new CecParallelProofSearch(2);

    const result = await search.searchParallel(
      async (space: number) => (space === 3 ? `found-${space}` : undefined),
      [1, 2, 3, 4],
    );

    expect(result).toBe('found-3');
    expect(search.getMetrics().nodesExplored).toBe(4);
    expect(search.getMetrics().parallelSpeedup).toBeGreaterThanOrEqual(1);
  });

  it('returns undefined from async search when no result is found', async () => {
    const search = new CecParallelProofSearch(3);

    await expect(search.searchParallel(() => undefined, ['a', 'b'])).resolves.toBeUndefined();
    expect(search.getMetrics().nodesExplored).toBe(2);
  });

  it('coordinates pruning and redundancy elimination metrics', () => {
    const root = new CecProofNode({
      formula: 'root',
      depth: 0,
      children: [
        new CecProofNode({ formula: 'p', depth: 1 }),
        new CecProofNode({ formula: 'p', depth: 2 }),
        new CecProofNode({ formula: 'p(x)', depth: 1 }),
      ],
    });
    const optimizer = new CecProofOptimizer({ maxDepth: 2 });

    const [optimized, metrics] = optimizer.optimizeProofTree(root);

    expect(optimizer.collectFormulas(optimized)).toEqual(['root', 'p', 'p(x)']);
    expect(metrics.nodesPruned).toBe(1);
    expect(metrics.duplicatesEliminated).toBe(1);
    expect(metrics.subsumptionsFound).toBeGreaterThanOrEqual(1);
    expect(optimizer.getCombinedMetrics()).toBe(metrics);
  });

  it('optimizes formula batches without mutating the input list', () => {
    const optimizer = new CecProofOptimizer();
    const formulas = ['p', 'p', 'p(x)', 'q'];

    const [optimized, metrics] = optimizer.optimizeFormulas(formulas);

    expect(optimized).toEqual(['p', 'q']);
    expect(formulas).toEqual(['p', 'p', 'p(x)', 'q']);
    expect(metrics.toDict()).toMatchObject({
      duplicates_eliminated: 1,
      subsumptions_found: 1,
      nodes_explored: 2,
    });
    expect(optimizer.getCombinedMetrics()).toBe(metrics);
  });
});
