import type { ProofResult } from '../types';
import {
  TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF,
  TdfolFormulaDependencyGraph,
  analyzeTdfolProofDependencies,
  buildExampleTdfolFormulaDependencyGraph,
  buildTdfolDependencyGraph,
  findTdfolProofChain,
} from './dependencyGraph';

const proof: ProofResult = {
  status: 'proved',
  theorem: 'Goal(x)',
  method: 'tdfol-forward-chaining',
  steps: [
    {
      id: 's1',
      rule: 'ModusPonens',
      premises: ['Pred(x)', '(Pred(x)) → (Goal(x))'],
      conclusion: 'Goal(x)',
    },
  ],
};

describe('TdfolFormulaDependencyGraph', () => {
  it('builds graph JSON and DOT from proof results', () => {
    const graph = buildTdfolDependencyGraph(proof);
    const json = graph.toJson();

    expect(json.nodes.map((node) => node.formula)).toContain('Goal(x)');
    expect(json.edges).toHaveLength(2);
    expect(graph.toDot()).toContain('digraph TDFOLProof');
  });

  it('finds paths and topological order', () => {
    const graph = buildTdfolDependencyGraph(proof);

    expect(graph.findPath('Pred(x)', 'Goal(x)')).toEqual(['Pred(x)', 'Goal(x)']);
    expect(graph.topologicalOrder()).toContain('Goal(x)');
  });

  it('tracks unused axioms', () => {
    const graph = new TdfolFormulaDependencyGraph();
    graph.addFormula('Axiom(x)', 'axiom');
    graph.addFormula('Used(x)', 'axiom');
    graph.addDependency('Used(x)', 'Goal(x)', 'Rule');

    expect(graph.findUnusedAxioms()).toEqual(['Axiom(x)']);
  });

  it('ports Python formula dependency queries and statistics', () => {
    const graph = new TdfolFormulaDependencyGraph();
    graph.addFormulaWithDependencies('P(a)', [], 'Axiom', '', 'axiom');
    graph.addFormulaWithDependencies('Q(a)', ['P(a)'], 'Rule1', 'from P');
    graph.addFormulaWithDependencies('R(a)', ['Q(a)'], 'Rule2', 'from Q');
    graph.addFormulaWithDependencies('R(a)', ['P(a)'], 'Rule3', 'direct shortcut');
    graph.addFormulaWithDependencies('Unused(a)', [], 'Axiom', '', 'axiom');

    expect(graph.getDependencies('R(a)')).toEqual(['P(a)', 'Q(a)']);
    expect(graph.getDependents('P(a)')).toEqual(['Q(a)', 'R(a)']);
    expect(graph.getAllDependencies('R(a)')).toEqual(['P(a)', 'Q(a)']);
    expect(graph.getAllDependents('P(a)')).toEqual(['Q(a)', 'R(a)']);
    expect(graph.detectCycles()).toEqual([]);
    expect(graph.findCriticalPath('P(a)', 'R(a)')).toEqual(['P(a)', 'R(a)']);
    expect(graph.getStatistics()).toMatchObject({
      num_nodes: 4,
      num_edges: 3,
      has_cycles: false,
      num_axioms: 2,
      num_derived: 2,
    });
    expect(graph.toJson().statistics?.edge_types.direct).toBe(3);
  });

  it('exports the Python adjacency matrix shape without filesystem dependencies', () => {
    const graph = buildTdfolDependencyGraph(proof);
    const { formulas, matrix } = graph.toAdjacencyMatrix();
    const predIndex = formulas.indexOf('Pred(x)');
    const goalIndex = formulas.indexOf('Goal(x)');

    expect(matrix[predIndex][goalIndex]).toBe(1);
    expect(matrix[goalIndex][predIndex]).toBe(0);
  });

  it('provides browser-native proof analysis convenience functions', () => {
    const graph = analyzeTdfolProofDependencies(proof);
    const chain = findTdfolProofChain('Pred(x)', 'Goal(x)', [proof]);

    expect(graph.getStatistics().num_edges).toBe(2);
    expect(chain).toEqual(['Pred(x)', 'Goal(x)']);
    expect(findTdfolProofChain('Goal(x)', 'Pred(x)', [proof])).toBeNull();
  });

  it('rejects circular dependencies', () => {
    const graph = new TdfolFormulaDependencyGraph();
    graph.addDependency('A', 'B', 'Rule');

    expect(() => graph.addDependency('B', 'A', 'Rule')).toThrow('Circular dependency detected');
  });

  it('ports the Python example formula dependency graph as a browser-native fixture', () => {
    const example = buildExampleTdfolFormulaDependencyGraph();

    expect(example.proofResult).toBe(TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF);
    expect(example.json.nodes.map((node) => node.formula)).toEqual(
      expect.arrayContaining([
        'RequestsAccess(Alice, DatasetAlpha)',
        'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
        'Permitted(Alice, DatasetAlpha)',
        'RetentionOnly(ArchiveNotice)',
      ]),
    );
    expect(example.json.edges.map((edge) => edge.rule)).toEqual(
      expect.arrayContaining(['UniversalInstantiation', 'DeonticDischarge']),
    );
    expect(example.accessDecisionPath).toEqual([
      'RequestsAccess(Alice, DatasetAlpha)',
      'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
      'Permitted(Alice, DatasetAlpha)',
    ]);
    expect(example.topologicalOrder.indexOf('RequestsAccess(Alice, DatasetAlpha)')).toBeLessThan(
      example.topologicalOrder.indexOf('Permitted(Alice, DatasetAlpha)'),
    );
    expect(example.unusedAxioms).toEqual(['RetentionOnly(ArchiveNotice)']);
    expect(example.dot).toContain('DeonticDischarge');
  });
});
