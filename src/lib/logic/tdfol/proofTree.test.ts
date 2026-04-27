import type { ProofResult } from '../types';
import { visualizeTdfolProofTree } from './proofTree';

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

describe('TdfolProofTreeVisualizer', () => {
  it('renders ASCII, JSON, DOT, and HTML proof tree views', () => {
    const visualizer = visualizeTdfolProofTree(proof, 'detailed');

    expect(visualizer.root).toMatchObject({
      formula: 'Goal(x)',
      nodeType: 'theorem',
      ruleName: 'ModusPonens',
    });
    expect(visualizer.renderAscii()).toContain('Goal(x) [ModusPonens]');
    expect(visualizer.renderJson()).toMatchObject({
      theorem: 'Goal(x)',
      status: 'proved',
    });
    expect(visualizer.renderDot()).toContain('ModusPonens');
    expect(visualizer.renderHtml()).toContain('tdfol-proof-tree');
  });

  it('supports minimal labels for compact displays', () => {
    const visualizer = visualizeTdfolProofTree(proof, 'minimal');

    expect(visualizer.renderAscii()).toContain('Goal(x)');
    expect(visualizer.renderAscii()).not.toContain('[ModusPonens]');
  });
});
