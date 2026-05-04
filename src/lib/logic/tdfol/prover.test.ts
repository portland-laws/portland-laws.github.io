import { parseTdfolFormula } from './parser';
import { proveTdfol, proveTdfolPythonStyle, TDFOL_PROVER_METADATA, TdfolProver } from './prover';
import { ModusPonensRule, TemporalKAxiomRule, TemporalTAxiomRule } from './inferenceRules';
import {
  clearGlobalTdfolProofCache,
  getGlobalTdfolProofCache,
  proveTdfolWithCache,
  TDFOL_PROOF_CACHE_METADATA,
  TdfolProofCache,
} from './proofCache';

describe('TdfolProver', () => {
  it('proves direct axioms immediately', () => {
    const theorem = parseTdfolFormula('Pred(x)');
    const result = proveTdfol(theorem, { axioms: [theorem] });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Pred(x)',
      steps: [],
    });
  });

  it('proves via bounded forward chaining', () => {
    const p = parseTdfolFormula('Pred(x)');
    const implication = parseTdfolFormula('Pred(x) -> Goal(x)');
    const q = parseTdfolFormula('Goal(x)');
    const prover = new TdfolProver({ rules: [ModusPonensRule], maxSteps: 5 });

    expect(prover.prove(q, { axioms: [p, implication] })).toMatchObject({
      status: 'proved',
      steps: [{ rule: 'ModusPonens', conclusion: 'Goal(x)' }],
    });
  });

  it('chains temporal rule applications', () => {
    const temporalRule = parseTdfolFormula('always(Pred(x) -> Goal(x))');
    const temporalPremise = parseTdfolFormula('always(Pred(x))');
    const q = parseTdfolFormula('Goal(x)');
    const prover = new TdfolProver({
      rules: [TemporalKAxiomRule, TemporalTAxiomRule],
      maxSteps: 5,
    });

    expect(prover.prove(q, { axioms: [temporalRule, temporalPremise] })).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
    });
  });

  it('returns unknown when no rule can prove the theorem', () => {
    const prover = new TdfolProver({ rules: [ModusPonensRule], maxSteps: 2 });

    expect(
      prover.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] }),
    ).toMatchObject({
      status: 'unknown',
    });
  });

  it('fails closed as disproved when the local knowledge base directly contradicts the theorem', () => {
    const theorem = parseTdfolFormula('Goal(x)');
    const prover = new TdfolProver({ rules: [ModusPonensRule], maxSteps: 2 });

    expect(prover.prove(theorem, { axioms: [parseTdfolFormula('not Goal(x)')] })).toMatchObject({
      status: 'disproved',
      method: 'tdfol-direct-contradiction',
      steps: [
        {
          rule: 'DirectContradiction',
          premises: ['¬(Goal(x))'],
          conclusion: 'Goal(x)',
        },
      ],
    });
  });

  it('returns timeout when the derived formula budget is exceeded', () => {
    const prover = new TdfolProver({ maxDerivedFormulas: 1 });

    expect(
      prover.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] }),
    ).toMatchObject({
      status: 'timeout',
      error: 'Derived formula budget exceeded',
    });
  });

  it('can route proof search through browser-native strategy selection', () => {
    const theorem = parseTdfolFormula('Goal(x)');
    const result = proveTdfol(
      theorem,
      {
        axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
      },
      {
        useStrategySelection: true,
        preferLowCostStrategy: true,
        timeoutMs: 100,
      },
    );

    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
      method: expect.stringMatching(/chaining|bidirectional/),
    });
  });

  it('exposes Python-style proof reports and browser-native module metadata', () => {
    const theorem = parseTdfolFormula('Goal(x)');
    const report = proveTdfolPythonStyle(theorem, {
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    });

    expect(TDFOL_PROVER_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/tdfol_prover.py',
      browserNative: true,
      runtimeDependencies: [],
      serverCallsAllowed: false,
      pythonRuntimeRequired: false,
    });
    expect(report).toMatchObject({
      success: true,
      status: 'proved',
      theorem: 'Goal(x)',
      assumptions: ['Pred(x)', '(Pred(x)) → (Goal(x))'],
      method: 'tdfol-forward-chaining',
      stepCount: 1,
      metadata: TDFOL_PROVER_METADATA,
    });
  });

  it('caches proof results by theorem, knowledge base, and prover config', () => {
    const cache = new TdfolProofCache();
    const theorem = parseTdfolFormula('Goal(x)');
    const kb = { axioms: [parseTdfolFormula('Pred(x)')] };
    const result = { status: 'proved' as const, theorem: 'Goal(x)', steps: [], method: 'manual' };
    const options = { maxSteps: 3, rules: [ModusPonensRule] };

    const cid = cache.set(theorem, kb, result, options);

    expect(cid).toMatch(/^browsets-/);
    expect(cache.get(theorem, kb, options)).toEqual(result);
    expect(cache.get(theorem, kb, { maxSteps: 4, rules: [ModusPonensRule] })).toBeUndefined();
    expect(cache.getStats()).toMatchObject({ hits: 1, misses: 1, sets: 1 });
  });

  it('proves through the browser-native cache and exposes global helpers', () => {
    const cache = new TdfolProofCache();
    const theorem = parseTdfolFormula('Goal(x)');
    const kb = {
      axioms: [
        parseTdfolFormula('always(Pred(x) -> Goal(x))'),
        parseTdfolFormula('always(Pred(x))'),
      ],
    };
    const options = { rules: [TemporalKAxiomRule, TemporalTAxiomRule], maxSteps: 5 };

    expect(cache.prove(theorem, kb, options)).toMatchObject({
      status: 'proved',
      method: 'tdfol-forward-chaining',
    });
    expect(cache.prove(theorem, kb, options)).toMatchObject({
      status: 'proved',
      method: 'tdfol-forward-chaining:cached',
    });
    expect(cache.invalidate(theorem, kb, options)).toBe(true);
    expect(cache.clear()).toBe(0);

    clearGlobalTdfolProofCache();
    expect(proveTdfolWithCache(theorem, kb, options)).toMatchObject({ status: 'proved' });
    expect(getGlobalTdfolProofCache().get(theorem, kb, options)).toMatchObject({
      status: 'proved',
    });
    expect(TDFOL_PROOF_CACHE_METADATA.runtimeDependencies).toEqual([]);
  });
});
