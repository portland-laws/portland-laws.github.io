import type { ProofResult } from '../types';
import { visualizeCecProofTree } from './proofTree';

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

describe('CecProofTreeVisualizer', () => {
  it('renders ASCII, JSON, DOT, and HTML proof tree views', () => {
    const visualizer = visualizeCecProofTree(proof, 'detailed');

    expect(visualizer.root).toMatchObject({
      formula: '(comply_with agent code)',
      nodeType: 'theorem',
      ruleName: 'CecModusPonens',
    });
    expect(visualizer.renderAscii()).toContain('(comply_with agent code) [CecModusPonens]');
    expect(visualizer.renderJson()).toMatchObject({
      theorem: '(comply_with agent code)',
      status: 'proved',
      method: 'cec-forward-chaining',
    });
    expect(visualizer.renderDot()).toContain('CecModusPonens');
    expect(visualizer.renderHtml()).toContain('cec-proof-tree');
  });

  it('supports minimal labels for compact browser displays', () => {
    const visualizer = visualizeCecProofTree(proof, 'minimal');

    expect(visualizer.renderAscii()).toContain('(comply_with agent code)');
    expect(visualizer.renderAscii()).not.toContain('[CecModusPonens]');
  });
});
