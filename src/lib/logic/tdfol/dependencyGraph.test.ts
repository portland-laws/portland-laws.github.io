import type { ProofResult } from '../types';
import {
  TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF,
  TdfolFormulaDependencyGraph,
  buildExampleTdfolFormulaDependencyGraph,
  buildTdfolDependencyGraph,
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
