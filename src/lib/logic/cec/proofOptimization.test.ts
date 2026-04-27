import {
  CecParallelProofSearch,
  CecProofNode,
  CecProofOptimizer,
  CecProofTreePruner,
  CecRedundancyEliminator,
  createCecProofNode,
} from './proofOptimization';

describe('CEC proof optimization parity helpers', () => {
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

  it('searches browser-native async batches without worker dependencies', async () => {
    const search = new CecParallelProofSearch(2);

    const result = await search.searchParallel(async (space: number) => (
      space === 3 ? `found-${space}` : undefined
    ), [1, 2, 3, 4]);

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
});
