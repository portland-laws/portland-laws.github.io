import { ProofCache } from '../proofCache';
import type { ProofResult } from '../types';
import { ModusPonensRule } from './inferenceRules';
import { parseTdfolFormula } from './parser';
import { TdfolForwardChainingStrategy } from './strategies';
import {
  createTdfolOptimizedProver,
  TdfolIndexedKnowledgeBase,
  TdfolOptimizationStats,
  TdfolOptimizedProver,
} from './optimization';

describe('TDFOL optimization', () => {
  it('indexes formulas by type, operator, complexity, and predicate', () => {
    const temporal = parseTdfolFormula('always(Permit(x))');
    const deontic = parseTdfolFormula('O(Comply(x))');
    const propositional = parseTdfolFormula('Person(x) -> Resident(x)');
    const indexed = new TdfolIndexedKnowledgeBase({ axioms: [temporal, deontic, propositional] });

    expect(indexed.size()).toBe(3);
    expect(indexed.getByType('temporal')).toEqual([temporal]);
    expect(indexed.getByType('deontic')).toEqual([deontic]);
    expect(indexed.getByType('propositional')).toEqual([propositional]);
    expect(indexed.getByOperator('ALWAYS')).toEqual([temporal]);
    expect(indexed.getByOperator('OBLIGATION')).toEqual([deontic]);
    expect(indexed.getByPredicate('Resident')).toEqual([propositional]);
    expect(indexed.getByComplexity(indexed.getComplexity(propositional))).toContain(propositional);
  });

  it('selects strategies with Python optimization heuristics', () => {
    const modal = createTdfolOptimizedProver({ axioms: [] });
    expect(modal.selectStrategy(parseTdfolFormula('O(Comply(x))'))).toBe('modal_tableaux');

    const largeKb = new TdfolOptimizedProver({
      axioms: Array.from({ length: 101 }, (_value, index) => parseTdfolFormula(`Fact${index}(x)`)),
    });
    expect(largeKb.selectStrategy(parseTdfolFormula('Goal(x)'))).toBe('forward');

    const smallKb = createTdfolOptimizedProver({ axioms: [parseTdfolFormula('Fact(x)')] });
    expect(smallKb.selectStrategy(parseTdfolFormula('not (Fact(x) and Other(x))'))).toBe('backward');
  });

  it('proves through the cache-aware optimized prover and records stats', () => {
    const cache = new ProofCache<ProofResult>({ now: () => 1000 });
    const prover = new TdfolOptimizedProver({
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    }, {
      cache,
      strategies: [new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] })],
      strategy: 'forward',
    });

    const first = prover.prove(parseTdfolFormula('Goal(x)'));
    const second = prover.prove(parseTdfolFormula('Goal(x)'));

    expect(first).toMatchObject({ status: 'proved', method: 'forward' });
    expect(second).toMatchObject({ status: 'proved', method: 'forward:cache-hit' });
    expect(prover.getStats()).toMatchObject({
      cacheHits: 1,
      cacheMisses: 1,
      indexedLookups: 1,
      totalProofs: 2,
    });
  });

  it('tracks auto strategy switches, worker accounting, and disabled cache', () => {
    const prover = createTdfolOptimizedProver({
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    }, {
      enableCache: false,
      workers: 2,
      strategies: [new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] })],
    });

    expect(prover.prove(parseTdfolFormula('Goal(x)'))).toMatchObject({ status: 'proved', method: 'bidirectional' });
    expect(prover.getStats()).toMatchObject({
      cacheHits: 0,
      cacheMisses: 0,
      indexedLookups: 1,
      parallelSearches: 1,
      strategySwitches: 1,
      totalProofs: 1,
    });

    prover.resetStats();
    expect(prover.getStats()).toMatchObject({ totalProofs: 0, indexedLookups: 0, parallelSearches: 0 });
  });

  it('serializes optimization statistics in a Python-compatible summary string', () => {
    const stats = new TdfolOptimizationStats();
    stats.cacheHits = 1;
    stats.cacheMisses = 3;
    stats.indexedLookups = 2;
    stats.strategySwitches = 1;
    stats.recordProof(8);

    expect(stats.snapshot()).toMatchObject({
      cacheHitRate: 0.25,
      avgProofTimeMs: 8,
    });
    expect(stats.toString()).toContain('cache_hits=1');
    expect(stats.toString()).toContain('hit_rate=25.0%');
  });
});
