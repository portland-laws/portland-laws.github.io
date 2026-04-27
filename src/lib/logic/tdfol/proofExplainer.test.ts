import type { ProofResult } from '../types';
import { explainTdfolProof, TdfolProofExplainer } from './proofExplainer';

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

describe('TdfolProofExplainer', () => {
  it('explains proof results with summary, chain, and statistics', () => {
    const explanation = explainTdfolProof(proof);

    expect(explanation).toMatchObject({
      formula: 'Goal(x)',
      isProved: true,
      proofType: 'forward_chaining',
      summary: 'Proved Goal(x) using forward_chaining in 1 step.',
      statistics: {
        status: 'proved',
        step_count: 1,
        method: 'tdfol-forward-chaining',
      },
    });
    expect(explanation.steps[0]).toMatchObject({
      ruleName: 'ModusPonens',
      justification: 'Given phi -> psi and phi, conclude psi.',
    });
    expect(explanation.text).toContain('Proof of: Goal(x)');
  });

  it('supports brief explanations and generic rule descriptions', () => {
    const explainer = new TdfolProofExplainer('brief');

    expect(explainer.explainRule('CustomWeakeningRule')).toContain('weaker conclusion');
    expect(explainer.explainProof(proof).steps[0].naturalLanguage).toBe('Step 1: derived Goal(x).');
  });

  it('summarizes unknown and timeout proof states', () => {
    expect(explainTdfolProof({ ...proof, status: 'unknown', steps: [] }).summary).toContain('No proof');
    expect(explainTdfolProof({ ...proof, status: 'timeout', steps: [] }).summary).toContain('budget was exhausted');
  });
});
