import type { CecExpression } from './ast';
import {
  CecLemma,
  CecLemmaCache,
  CecLemmaGenerator,
  CecLemmaType,
  createCecLemmaGenerator,
  hashCecLemmaPattern,
} from './lemmaGeneration';

const atom = (name: string): CecExpression => ({ kind: 'atom', name });
const implies = (left: CecExpression, right: CecExpression): CecExpression => ({
  kind: 'binary',
  operator: 'implies',
  left,
  right,
});
const and = (left: CecExpression, right: CecExpression): CecExpression => ({
  kind: 'binary',
  operator: 'and',
  left,
  right,
});

describe('CEC lemma generation parity helpers', () => {
  it('creates deterministic lemmas with pattern matching and JSON export', () => {
    const p = atom('p');
    const q = atom('q');
    const formula = implies(p, q);
    const lemma = new CecLemma({ formula, premises: [p, implies(p, q)], rule: 'CecModusPonens' });

    expect(lemma.patternHash).toBe(hashCecLemmaPattern('(implies p q)'));
    expect(lemma.matchesPattern(implies(p, q))).toBe(true);
    expect(lemma.matchesPattern(q)).toBe(false);

    lemma.incrementUsage();
    expect(lemma.toJSON()).toMatchObject({
      formula: '(implies p q)',
      premises: ['p', '(implies p q)'],
      rule: 'CecModusPonens',
      lemma_type: CecLemmaType.DERIVED,
      usage_count: 1,
    });
  });

  it('stores lemmas in an LRU cache with exact and pattern lookup statistics', () => {
    const cache = new CecLemmaCache(2);
    const first = new CecLemma({ formula: atom('a'), rule: 'axiom' });
    const second = new CecLemma({ formula: atom('b'), rule: 'axiom' });
    const third = new CecLemma({ formula: atom('c'), rule: 'axiom' });

    cache.add(first);
    cache.add(second);

    expect(cache.get(atom('a'))).toBe(first);
    cache.add(third);

    expect(cache.get(atom('b'))).toBeUndefined();
    expect(cache.findByPattern(atom('a'))).toEqual([first]);
    expect(cache.findByPattern(atom('c'))).toEqual([third]);
    expect(cache.getStatistics()).toMatchObject({
      size: 2,
      max_size: 2,
      hits: 1,
      misses: 1,
      total_requests: 2,
    });
  });

  it('discovers lemmas from successful proof trees and marks repeated patterns reusable', () => {
    const p = atom('p');
    const q = atom('q');
    const formula = and(p, q);
    const generator = new CecLemmaGenerator(10);

    const lemmas = generator.discoverLemmas({
      result: 'proved',
      axioms: [p, q],
      steps: [
        { formula, premises: [0, 1], rule: 'CecConjunctionIntroduction' },
        { formula: and(p, q), premises: [0, 1], rule: 'CecConjunctionIntroduction' },
      ],
    });

    expect(lemmas).toHaveLength(2);
    expect(lemmas.every((lemma) => lemma.lemmaType === CecLemmaType.REUSABLE)).toBe(true);
    expect(generator.getStatistics()).toMatchObject({
      discovery_count: 2,
      cache_size: 1,
    });
  });

  it('returns applicable lemmas from exact and pattern matches without duplicates', () => {
    const p = atom('p');
    const q = atom('q');
    const generator = new CecLemmaGenerator(10);
    const lemma = new CecLemma({ formula: p, premises: [q], rule: 'fixture' });
    generator.cache.add(lemma);

    const applicable = generator.getApplicableLemmas(q, [p]);

    expect(applicable).toEqual([lemma]);
    expect(lemma.usageCount).toBe(1);
  });

  it('proves goals from cached lemmas and discovers lemmas from regular CEC proving', () => {
    const p = atom('p');
    const q = atom('q');
    const generator = createCecLemmaGenerator(10);
    generator.cache.add(new CecLemma({ formula: q, premises: [p], rule: 'fixture-lemma' }));

    const lemmaResult = generator.proveWithLemmas(q, { axioms: [p] });
    expect(lemmaResult.status).toBe('proved');
    expect(lemmaResult.method).toBe('cec-lemma-generation');
    expect(lemmaResult.steps[0].rule).toBe('Lemma: fixture-lemma');

    const discoveringGenerator = createCecLemmaGenerator(10);
    const derivedResult = discoveringGenerator.proveWithLemmas(q, { axioms: [p, implies(p, q)] });
    expect(derivedResult.status).toBe('proved');
    expect(generator.getStatistics().reuse_count).toBeGreaterThanOrEqual(1);
    expect(discoveringGenerator.getStatistics().discovery_count).toBeGreaterThanOrEqual(1);
  });

  it('clears lemma cache and generator statistics', () => {
    const generator = new CecLemmaGenerator(5);
    generator.cache.add(new CecLemma({ formula: atom('p'), rule: 'fixture' }));
    generator.cache.get(atom('p'));
    generator.clear();

    expect(generator.getStatistics()).toEqual({
      discovery_count: 0,
      reuse_count: 0,
      cache_size: 0,
      cache_hit_rate: 0,
      cache_hits: 0,
      cache_misses: 0,
    });
  });
});
