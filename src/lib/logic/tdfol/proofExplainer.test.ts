import type { ProofResult } from '../types';
import {
  explainTdfolProof,
  explainTdfolProofSteps,
  explainTdfolZkpProof,
  TdfolProofExplainer,
} from './proofExplainer';

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
      justification: 'Given p -> q and p, we conclude q.',
    });
    expect(explanation.text).toContain('Proof of: Goal(x)');
  });

  it('supports brief explanations and generic rule descriptions', () => {
    const explainer = new TdfolProofExplainer('brief');

    expect(explainer.explainRule('CustomWeakeningRule')).toContain('weaker conclusion');
    expect(explainer.explainProof(proof).steps[0].naturalLanguage).toBe('Step 1: derived Goal(x).');
  });

  it('summarizes unknown and timeout proof states', () => {
    expect(explainTdfolProof({ ...proof, status: 'unknown', steps: [] }).summary).toContain(
      'No proof',
    );
    expect(explainTdfolProof({ ...proof, status: 'timeout', steps: [] }).summary).toContain(
      'budget was exhausted',
    );
  });

  it('ports Python proof-step explanation by proof type', () => {
    const forward = explainTdfolProofSteps('Goal(x)', [
      { rule: 'DeonticDetachment', premises: ['O(P -> Q)', 'P'], conclusion: 'O(Q)' },
    ]);

    expect(forward.steps[0].justification).toBe(
      'Given obligation(P -> Q) and P, conclude obligation(Q).',
    );
    expect(
      explainTdfolProofSteps('Goal(x)', ['resolve subgoal'], 'backward_chaining').steps[0],
    ).toMatchObject({ ruleName: 'BackwardChaining', justification: 'Goal-directed search' });
    expect(
      explainTdfolProofSteps('□P', ['closed branch from ¬P'], 'modal_tableaux').steps[0],
    ).toMatchObject({ ruleName: 'TableauxExpansion', justification: 'Tableaux expansion' });
  });

  it('renders inference-rule details at Python-compatible levels', () => {
    expect(
      new TdfolProofExplainer('brief').explainInferenceRule('ModusPonens', ['P -> Q', 'P'], 'Q'),
    ).toBe('ModusPonens: P -> Q, P |- Q');
    expect(
      new TdfolProofExplainer('detailed').explainInferenceRule(
        'TemporalInduction',
        ['P'],
        'always(P)',
      ),
    ).toContain('Inference Rule: TemporalInduction');
  });

  it('explains ZKP proofs and compares them with standard proofs without external calls', () => {
    const explainer = new TdfolProofExplainer();
    const standard = explainTdfolProof(proof);
    const zkp = explainTdfolZkpProof('Goal(x)', {}, { backend: 'simulated', securityLevel: 96 });

    expect(zkp.summary).toContain('96-bit security');
    expect(zkp.statistics).toMatchObject({ backend: 'simulated', privacy: 'Axioms hidden' });
    expect(explainer.explainSecurityProperties('simulated', 96)).toContain(
      'not cryptographically secure',
    );
    expect(explainer.compareProofs(standard, zkp)).toContain('Standard: Transparent reasoning');
  });
});
