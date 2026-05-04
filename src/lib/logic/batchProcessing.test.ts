import {
  BatchProcessor,
  BatchResult,
  ChunkedBatchProcessor,
  FOLBatchProcessor,
  ProofBatchProcessor,
  exportBatchResult,
  normalizeProofLogic,
} from './batchProcessing';

describe('logic batch processing browser-native parity helpers', () => {
  it('models Python BatchResult statistics and dictionary output', () => {
    const result = new BatchResult({
      totalItems: 4,
      successful: 3,
      failed: 1,
      totalTime: 2,
      itemsPerSecond: 2,
      results: ['a', 'b', 'c'],
      errors: [{ index: 3, error: 'bad item' }],
    });

    expect(result.successRate()).toBe(75);
    expect(result.toDict()).toEqual({
      total_items: 4,
      successful: 3,
      failed: 1,
      total_time: 2,
      items_per_second: 2,
      success_rate: 75,
      results_count: 3,
      errors_count: 1,
    });
  });

  it('exports BatchResult summaries as browser-native JSON and CSV without filesystem access', () => {
    const result = new BatchResult({
      totalItems: 2,
      successful: 1,
      failed: 1,
      totalTime: 0.5,
      itemsPerSecond: 4,
      results: ['ok'],
      errors: [{ index: 1, error: 'bad, "quoted" item' }],
    });

    expect(JSON.parse(result.toJson(0))).toEqual(result.toDict());
    expect(exportBatchResult(result, 'dict')).toEqual(result.toDict());
    expect(exportBatchResult(result, 'json', { jsonIndent: 0 })).toBe(result.toJson(0));
    expect(result.toCsv()).toBe(
      [
        'metric,value',
        'total_items,2',
        'successful,1',
        'failed,1',
        'total_time,0.5',
        'items_per_second,4',
        'success_rate,50',
        'results_count,1',
        'errors_count,1',
      ].join('\n'),
    );
  });

  it('processes async batches with bounded local concurrency and per-item errors', async () => {
    let now = 0;
    let active = 0;
    let maxActive = 0;
    const progress: string[] = [];
    const processor = new BatchProcessor({
      maxConcurrency: 2,
      now: () => now,
      onProgress: (event) => progress.push(`${event.phase}:${event.index}`),
    });

    const result = await processor.processBatchAsync([1, 2, 3, 4], async (item) => {
      active += 1;
      maxActive = Math.max(maxActive, active);
      await Promise.resolve();
      active -= 1;
      now += 0.5;
      if (item === 3) throw new Error('three failed');
      return item * 2;
    });

    expect(maxActive).toBeLessThanOrEqual(2);
    expect(result).toMatchObject({ totalItems: 4, successful: 3, failed: 1 });
    expect(result.results).toEqual([2, 4, 8]);
    expect(result.errors).toEqual([{ index: 2, error: 'three failed' }]);
    expect(progress).toContain('complete:4');
  });

  it('runs FOL conversion batches through the local converter', async () => {
    const processor = new FOLBatchProcessor(2, { useMl: true });
    const result = await processor.convertBatch(
      ['All tenants are residents', 'If tenant then resident'],
      {
        useNlp: true,
      },
    );

    expect(result).toMatchObject({ totalItems: 2, successful: 2, failed: 0 });
    expect(result.results.map((item) => item.output?.formulaString)).toEqual([
      '∀x (Tenants(x) → Residents(x))',
      '∀x (Tenant(x) → Resident(x))',
    ]);
    expect(
      result.results.every((item) => item.metadata.browser_native_ml_confidence === true),
    ).toBe(true);
  });

  it('runs proof batches through the browser-native bridge', async () => {
    const processor = new ProofBatchProcessor(2);
    const result = await processor.proveBatch([
      { logic: 'tdfol', theorem: 'Resident(Ada)', axioms: ['Resident(Ada)'] },
      { logic: 'cec', theorem: '(subject_to ada code)', axioms: ['(subject_to ada code)'] },
    ]);

    expect(result).toMatchObject({ totalItems: 2, successful: 2, failed: 0 });
    expect(result.results.map((item) => item.status)).toEqual(['proved', 'proved']);
    expect(result.results.map((item) => item.method)).toEqual([
      'bridge:tdfol-forward-chaining:cache-eligible',
      'bridge:cec-forward-chaining:cache-eligible',
    ]);
  });

  it('processes large batches in chunks and remaps error indexes globally', async () => {
    const chunks: string[] = [];
    let now = 0;
    const processor = new ChunkedBatchProcessor({
      chunkSize: 2,
      maxConcurrency: 1,
      now: () => now,
      onChunkStart: (index, total) => chunks.push(`${index}/${total}`),
    });

    const result = await processor.processLargeBatch(
      ['a', 'b', 'c', 'd', 'e'],
      async (item, index) => {
        now += 1;
        if (item === 'd') throw new Error('bad chunk item');
        return `${index}:${item}`;
      },
    );

    expect(chunks).toEqual(['1/3', '2/3', '3/3']);
    expect(result).toMatchObject({ totalItems: 5, successful: 4, failed: 1 });
    expect(result.results).toEqual(['0:a', '1:b', '2:c', '4:e']);
    expect(result.errors).toEqual([{ index: 3, error: 'bad chunk item' }]);
  });

  it('normalizes non-local prover names to the default TDFOL bridge path', () => {
    expect(normalizeProofLogic('cec')).toBe('cec');
    expect(normalizeProofLogic('dcec')).toBe('dcec');
    expect(normalizeProofLogic('z3')).toBe('tdfol');
  });
});
