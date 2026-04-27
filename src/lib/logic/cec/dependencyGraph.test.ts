import type { ProofResult } from '../types';
import { CecFormulaDependencyGraph, buildCecDependencyGraph } from './dependencyGraph';

const proof: ProofResult = {
  status: 'proved',
  theorem: '(comply_with agent code)',
  method: 'cec-forward-chaining',
  steps: [
    {
      id: 'cec-step-1',
      rule: 'CecModusPonens',
      premises: ['(subject_to agent code)', '(implies (subject_to agent code) (comply_with agent code))'],
      conclusion: '(comply_with agent code)',
      explanation: 'Applied CecModusPonens',
    },
  ],
};

describe('CecFormulaDependencyGraph', () => {
  it('builds graph JSON and DOT from CEC proof results', () => {
    const graph = buildCecDependencyGraph(proof);
    const json = graph.toJson();

    expect(json.nodes.map((node) => node.formula)).toContain('(comply_with agent code)');
    expect(json.edges).toHaveLength(2);
    expect(graph.toDot()).toContain('digraph CECProof');
    expect(graph.toDot()).toContain('CecModusPonens');
  });

  it('finds paths and topological order', () => {
    const graph = buildCecDependencyGraph(proof);

    expect(graph.findPath('(subject_to agent code)', '(comply_with agent code)'))
      .toEqual(['(subject_to agent code)', '(comply_with agent code)']);
    expect(graph.topologicalOrder()).toContain('(comply_with agent code)');
  });

  it('tracks unused CEC axioms', () => {
    const graph = new CecFormulaDependencyGraph();
    graph.addFormula('(subject_to ada code)', 'axiom');
    graph.addFormula('(subject_to bob code)', 'axiom');
    graph.addDependency('(subject_to bob code)', '(comply_with bob code)', 'Rule');

    expect(graph.findUnusedAxioms()).toEqual(['(subject_to ada code)']);
  });

  it('rejects circular CEC dependencies', () => {
    const graph = new CecFormulaDependencyGraph();
    graph.addDependency('(a)', '(b)', 'Rule');

    expect(() => graph.addDependency('(b)', '(a)', 'Rule')).toThrow('Circular CEC dependency detected');
  });
});
