import {
  CecKProver,
  CecShadowProver,
  CecShadowProverWrapper,
  CecS4Prover,
  CecS5Prover,
  createCecCognitiveProver,
  createCecShadowProver,
  createCecShadowProverWrapper,
  proveCecShadowBatch,
  prove_cec_shadow_theorem,
  readCecShadowProblemObject,
} from './shadowProver';
import { parseCecExpression } from './parser';

describe('CEC ShadowProver', () => {
  it('proves direct assumptions and records cacheable statistics', () => {
    const prover = new CecKProver();
    const goal = parseCecExpression('(permit tenant action)');

    const first = prover.prove(goal, [goal]);
    const second = prover.prove(goal, [goal]);

    expect(first).toMatchObject({ status: 'success', logic: 'K' });
    expect(first.isSuccessful()).toBe(true);
    expect(first.getDepth()).toBe(0);
    expect(second).toBe(first);
    expect(prover.getStatistics()).toMatchObject({ proofsAttempted: 2, proofsSucceeded: 1 });
  });

  it('uses the browser-native CEC forward prover before modal tableaux', () => {
    const prover = new CecShadowProver('K');
    const goal = parseCecExpression('(comply_with agent code)');
    const proof = prover.prove(goal, [
      parseCecExpression('(subject_to agent code)'),
      parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
    ]);

    expect(proof.status).toBe('success');
    expect(proof.metadata.method).toBe('cec-forward-chaining');
    expect(proof.steps).toHaveLength(1);
  });

  it('delegates modal validity to K/T/D/S4/S5 tableaux locally', () => {
    const formula = parseCecExpression(
      '(implies (always (comply_with agent code)) (comply_with agent code))',
    );

    expect(new CecShadowProver('K').prove(formula).status).toBe('failure');
    expect(new CecShadowProver('T').prove(formula).status).toBe('success');
    expect(new CecS4Prover().prove(formula).metadata).toMatchObject({ method: 'tableau' });
    expect(new CecS5Prover().prove(formula).logic).toBe('S5');
  });

  it('proves every goal in a problem object with the requested logic', () => {
    const problem = readCecShadowProblemObject({
      name: 'modal-reflexivity',
      logic: 'T',
      goals: ['(implies (always p) p)', '(implies p p)'],
    });
    const results = new CecKProver().proveProblem(problem);

    expect(results.map((result) => result.status)).toEqual(['success', 'success']);
    expect(results.every((result) => result.logic === 'T')).toBe(true);
  });

  it('applies the cognitive calculus rule subset without Python or Java ShadowProver calls', () => {
    const prover = createCecCognitiveProver();

    expect(prover.applyCognitiveRules(['K(alpha)'])).toEqual(['alpha', 'B(alpha)', 'K(K(alpha))']);
    expect(prover.prove('B(alpha)', ['K(alpha)'])).toMatchObject({
      status: 'success',
      metadata: { method: 'cognitive_calculus' },
    });
  });

  it('creates supported modal provers and rejects unsupported LP variants', () => {
    expect(createCecShadowProver('K')).toBeInstanceOf(CecKProver);
    expect(createCecShadowProver('S4')).toBeInstanceOf(CecS4Prover);
    expect(createCecShadowProver('S5')).toBeInstanceOf(CecS5Prover);
    expect(() => createCecShadowProver('LP')).toThrow('Unsupported modal logic');
  });

  it('exposes Python-native theorem helpers as local TypeScript proof entry points', () => {
    const theorem = parseCecExpression('(comply_with agent code)');
    const proof = prove_cec_shadow_theorem(theorem, [theorem]);

    expect(proof).toMatchObject({
      status: 'success',
      logic: 'K',
      metadata: { method: 'direct-assumption' },
    });
  });

  it('proves mixed-logic batches without server, Python, or subprocess fallbacks', () => {
    const batch = proveCecShadowBatch([
      {
        theorem: '(comply_with agent code)',
        axioms: [
          '(subject_to agent code)',
          '(implies (subject_to agent code) (comply_with agent code))',
        ],
      },
      {
        theorem: '(implies (always (comply_with agent code)) (comply_with agent code))',
        logic: 'T',
        metadata: { source: 'native-shadow-prover-parity' },
      },
    ]);

    expect(batch.results.map((result) => result.status)).toEqual(['success', 'success']);
    expect(batch.results.map((result) => result.logic)).toEqual(['K', 'T']);
    expect(batch.results[1].metadata.requestMetadata).toEqual({
      source: 'native-shadow-prover-parity',
    });
    expect(batch.statistics).toMatchObject({
      proofsAttempted: 2,
      proofsSucceeded: 2,
      proofsFailed: 0,
    });
    expect(batch.metadata).toEqual({
      browserNative: true,
      dependencyMode: 'local-typescript',
      pythonRuntime: false,
    });
  });

  it('loads and proves Python wrapper-style problem content in browser-native TypeScript', () => {
    const wrapper = new CecShadowProverWrapper();
    const results = wrapper.prove_problem({
      name: 'wrapper-custom-problem',
      formatHint: 'custom',
      content: `
        LOGIC: T
        GOALS:
        (implies (always (comply_with agent code)) (comply_with agent code))
      `,
    });

    expect(results).toHaveLength(1);
    expect(results[0]).toMatchObject({
      status: 'success',
      logic: 'T',
      metadata: { method: 'tableau' },
    });
    expect(wrapper.get_runtime_contract()).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      subprocessAccess: false,
    });
  });

  it('fails closed for unsupported wrapper logics instead of delegating to Python', () => {
    const wrapper = createCecShadowProverWrapper();
    const proof = wrapper.prove_theorem('(lp_claim)', [], 'LP1');

    expect(proof).toMatchObject({
      status: 'unknown',
      logic: 'LP1',
      metadata: {
        method: 'shadow-prover-wrapper',
        failClosed: true,
        runtime: { browserNative: true, pythonRuntime: false },
      },
    });
  });
});
