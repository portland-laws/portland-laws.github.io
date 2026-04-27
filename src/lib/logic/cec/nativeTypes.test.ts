import {
  CecProofStatistics,
  createCecErrorResult,
  createCecResult,
  isCecConverterProtocol,
  isCecExpression,
  isCecFormulaProtocol,
  isCecKnowledgeBaseProtocol,
  isCecProverProtocol,
  type CecCacheEntry,
  type CecConversionResultDict,
  type CecFormulaDict,
  type CecNativeGrammarConfig,
  type CecNamespaceExport,
  type CecPatternMatch,
  type CecProofResultDict,
  type CecProverConfig,
  type CecResult,
  type CecStatistics,
} from './nativeTypes';

describe('CEC native type parity helpers', () => {
  it('models Python-style dictionary aliases with TypeScript interfaces', () => {
    const formula: CecFormulaDict = {
      type: 'deontic',
      operator: 'O',
      arguments: ['agent', 'act'],
      variables: ['x'],
      metadata: { source: 'fixture' },
    };
    const proof: CecProofResultDict = {
      is_valid: true,
      steps: [{ rule: 'Modus Ponens' }],
      time_taken: 0.25,
      rules_used: ['Modus Ponens'],
      cached: false,
    };
    const conversion: CecConversionResultDict = {
      formula,
      confidence: 0.9,
      patterns_matched: ['obligation'],
      text: 'tenant must pay rent',
      language: 'en',
    };
    const namespaceExport: CecNamespaceExport = {
      sorts: { Agent: {} },
      variables: { x: {} },
      functions: {},
      predicates: { Pays: {} },
      constants: { tenant: {} },
    };
    const grammar: CecNativeGrammarConfig = { language: 'en', enable_caching: true, max_cache_size: 25 };
    const prover: CecProverConfig = { max_depth: 4, timeout: 1, strategy: 'forward', parallel: false };
    const pattern: CecPatternMatch = ['must', 0.8];

    expect(formula.metadata).toEqual({ source: 'fixture' });
    expect(proof.rules_used).toEqual(['Modus Ponens']);
    expect(conversion.confidence).toBe(0.9);
    expect(namespaceExport.predicates).toHaveProperty('Pays');
    expect(grammar.max_cache_size).toBe(25);
    expect(prover.strategy).toBe('forward');
    expect(pattern).toEqual(['must', 0.8]);
  });

  it('guards formula, expression, prover, converter, and knowledge-base protocol shapes', () => {
    const formulaLike = { toString: () => 'p' };
    const expression = { kind: 'atom', name: 'p' };
    const prover = { prove: () => ({ status: 'proved' }) };
    const converter = { convert: (text: string) => ({ text }) };
    const kb = {
      add: () => 'f1',
      query: () => [],
      remove: () => true,
    };

    expect(isCecFormulaProtocol(formulaLike)).toBe(true);
    expect(isCecFormulaProtocol(null)).toBe(false);
    expect(isCecExpression(expression)).toBe(true);
    expect(isCecExpression({ name: 'p' })).toBe(false);
    expect(isCecProverProtocol(prover)).toBe(true);
    expect(isCecConverterProtocol(converter)).toBe(true);
    expect(isCecKnowledgeBaseProtocol(kb)).toBe(true);
    expect(isCecKnowledgeBaseProtocol({ add: () => 'f1' })).toBe(false);
  });

  it('creates generic operation results and cache/stat records', () => {
    const ok: CecResult<number> = createCecResult(7, { source: 'unit' });
    const err = createCecErrorResult('failed', { operation: 'parse' });
    const cacheEntry: CecCacheEntry<string> = {
      value: 'formula',
      timestamp: 123,
      hits: 2,
      size: 7,
    };
    const stats: CecStatistics = {
      total_operations: 3,
      successful: 2,
      failed: 1,
      average_time: 0.5,
      cache_hits: 1,
      cache_misses: 2,
    };

    expect(ok).toEqual({ success: true, value: 7, metadata: { source: 'unit' } });
    expect(err).toEqual({ success: false, error: 'failed', metadata: { operation: 'parse' } });
    expect(cacheEntry.hits).toBe(2);
    expect(stats.average_time).toBe(0.5);
  });

  it('tracks proof statistics with Python-compatible incremental averages', () => {
    const stats = new CecProofStatistics();

    expect(stats.getSuccessRate()).toBe(0);

    stats.recordSuccess(5, 0.1);
    stats.recordFailure(0.3);
    stats.recordRule('Modus Ponens');
    stats.recordRule('Modus Ponens');
    stats.recordRule('Temporal T');
    stats.recordCacheHit();

    expect(stats.getSuccessRate()).toBe(50);
    expect(stats.getStatsDict()).toEqual({
      total_attempts: 2,
      succeeded: 1,
      failed: 1,
      steps_taken: 5,
      average_time: 0.2,
      cache_hits: 1,
      rules_applied: {
        'Modus Ponens': 2,
        'Temporal T': 1,
      },
      success_rate: 50,
    });

    stats.reset();
    expect(stats.getStatsDict()).toEqual({
      total_attempts: 0,
      succeeded: 0,
      failed: 0,
      steps_taken: 0,
      average_time: 0,
      cache_hits: 0,
      rules_applied: {},
      success_rate: 0,
    });
  });
});
