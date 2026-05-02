import type { ProofResult } from '../types';
import { explainCecProof, CecProofExplainer } from './proofExplainer';

const proof: ProofResult = {
  status: 'proved',
  theorem: '(comply_with agent code)',
  method: 'cec-forward-chaining',
  steps: [
    {
      id: 'cec-step-1',
      rule: 'CecTemporalT',
      premises: ['(always (subject_to agent code))'],
      conclusion: '(subject_to agent code)',
    },
    {
      id: 'cec-step-2',
      rule: 'CecModusPonens',
      premises: [
        '(subject_to agent code)',
        '(implies (subject_to agent code) (comply_with agent code))',
      ],
      conclusion: '(comply_with agent code)',
    },
  ],
};

describe('CEC proof explainer', () => {
  it('explains CEC proof results with summary, chain, and statistics', () => {
    const explanation = explainCecProof(proof);

    expect(explanation).toMatchObject({
      expression: '(comply_with agent code)',
      isProved: true,
      proofType: 'forward_chaining',
      summary: 'Proved (comply_with agent code) using forward_chaining in 2 steps.',
      statistics: {
        status: 'proved',
        step_count: 2,
        method: 'cec-forward-chaining',
        dependency_nodes: 4,
        dependency_edges: 3,
        leaf_premise_count: 2,
      },
    });
    expect(explanation.steps[0]).toMatchObject({
      ruleName: 'CecTemporalT',
      justification: 'Use always(phi) to conclude phi in the local temporal fragment.',
    });
    expect(explanation.text).toContain('CEC proof of: (comply_with agent code)');
  });

  it('derives browser-native dependency paths and critical path metadata', () => {
    const explanation = explainCecProof(proof);

    expect(explanation.dependencyGraph).toMatchObject({
      nodes: 4,
      edges: 3,
      leafPremises: [
        '(always (subject_to agent code))',
        '(implies (subject_to agent code) (comply_with agent code))',
      ],
      criticalPath: [
        '(always (subject_to agent code))',
        '(subject_to agent code)',
        '(comply_with agent code)',
      ],
    });
    expect(explanation.dependencyGraph.topologicalOrder).toEqual([
      '(always (subject_to agent code))',
      '(implies (subject_to agent code) (comply_with agent code))',
      '(subject_to agent code)',
      '(comply_with agent code)',
    ]);
    expect(explanation.dependencyGraph.premisePaths).toContainEqual({
      premise: '(implies (subject_to agent code) (comply_with agent code))',
      path: [
        '(implies (subject_to agent code) (comply_with agent code))',
        '(comply_with agent code)',
      ],
    });
    expect(explanation.text).toContain(
      'Critical path: (always (subject_to agent code)) -> (subject_to agent code) -> (comply_with agent code)',
    );
  });

  it('supports brief explanations and fallback rule descriptions', () => {
    const explainer = new CecProofExplainer('brief');

    expect(explainer.explainRule('CustomDeonticRule')).toContain('deontic CEC');
    expect(explainer.explainRule('UnknownRule')).toBe('Applied UnknownRule CEC inference rule.');
    expect(explainer.explainProof(proof).steps[0].naturalLanguage).toBe(
      'Step 1: derived (subject_to agent code).',
    );
  });

  it('summarizes unknown and timeout proof states', () => {
    expect(explainCecProof({ ...proof, status: 'unknown', steps: [] }).summary).toContain(
      'No CEC proof',
    );
    expect(explainCecProof({ ...proof, status: 'timeout', steps: [] }).summary).toContain(
      'budget was exhausted',
    );
  });
});
