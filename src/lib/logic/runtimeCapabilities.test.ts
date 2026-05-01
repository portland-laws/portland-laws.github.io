import {
  getLocalWasmProverEvaluations,
  getLogicRuntimeCapabilities,
  getRecommendedLocalWasmProvers,
} from './runtimeCapabilities';
import { convertLegalTextToDeontic } from './deontic';
import { parseFolText } from './fol';

describe('logic runtime capabilities', () => {
  it('declares browser-native mode with no server calls', () => {
    expect(getLogicRuntimeCapabilities()).toMatchObject({
      mode: 'browser_native',
      target: 'full_python_logic_parity_typescript_wasm',
      serverCallsAllowed: false,
      fol: {
        regexParser: true,
        nlpStatus: 'incomplete',
        nlpUnavailable: true,
        mlStatus: 'complete',
        mlUnavailable: false,
      },
      deontic: {
        ruleExtractor: true,
        mlStatus: 'complete',
        mlUnavailable: false,
      },
      proving: {
        lightweightReasoning: true,
        wasmProverStatus: 'incomplete',
        externalProverUnavailable: true,
        browserWasmProver: true,
        recommendedLocalProvers: ['z3', 'cvc5', 'tau-prolog'],
      },
    });
  });

  it('evaluates local WASM prover routes without server or Python wrappers', () => {
    const evaluations = getLocalWasmProverEvaluations();

    expect(evaluations.map((prover) => prover.id)).toEqual([
      'z3',
      'cvc5',
      'tau-prolog',
      'lean',
      'coq',
    ]);
    expect(evaluations.every((prover) => prover.serverCallsAllowed === false)).toBe(true);
    expect(
      evaluations.filter((prover) => prover.status !== 'blocked').map((prover) => prover.id),
    ).toEqual(['z3', 'cvc5', 'tau-prolog']);
    expect(
      evaluations.filter((prover) => prover.status === 'blocked').map((prover) => prover.id),
    ).toEqual(['lean', 'coq']);
  });

  it('selects deterministic browser-native prover candidates by workflow', () => {
    expect(getRecommendedLocalWasmProvers('smt').map((prover) => prover.id)).toEqual([
      'z3',
      'cvc5',
    ]);
    expect(getRecommendedLocalWasmProvers('logic-programming').map((prover) => prover.id)).toEqual([
      'tau-prolog',
    ]);
    expect(getRecommendedLocalWasmProvers('proof-checking')).toEqual([]);
  });

  it('surfaces temporary incomplete-port ML/NLP capabilities in converter outputs', () => {
    expect(parseFolText('All humans are mortal').capabilities).toEqual({
      nlpUnavailable: true,
      mlUnavailable: false,
      serverCallsAllowed: false,
    });

    expect(convertLegalTextToDeontic('The tenant must pay rent.').capabilities).toEqual({
      mlUnavailable: false,
      serverCallsAllowed: false,
    });
  });
});
