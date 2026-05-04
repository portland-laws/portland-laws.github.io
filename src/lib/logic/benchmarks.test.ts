import {
  BenchmarkResult,
  CacheBenchmarks,
  FOLBenchmarks,
  Phase7_4Benchmarks,
  Phase7_4PerformanceMetric,
  PerformanceBenchmark,
  runComprehensiveBenchmarks,
  runPhase7_4Benchmarks,
} from './benchmarks';

describe('logic benchmarks browser-native parity helpers', () => {
  it('serializes and summarizes benchmark results with Python-compatible fields', () => {
    const result = new BenchmarkResult({
      name: 'demo',
      description: 'Demo benchmark',
      iterations: 4,
      totalTime: 0.2,
      meanTime: 0.05,
      medianTime: 0.04,
      stdDev: 0.01,
      minTime: 0.03,
      maxTime: 0.07,
      throughput: 20,
      metadata: { browser_native: true },
    });

    expect(result.toDict()).toEqual({
      name: 'demo',
      description: 'Demo benchmark',
      iterations: 4,
      total_time: 0.2,
      mean_time: 0.05,
      median_time: 0.04,
      std_dev: 0.01,
      min_time: 0.03,
      max_time: 0.07,
      throughput: 20,
      metadata: { browser_native: true },
    });
    expect(result.summary()).toBe('demo: 50.00ms avg, 20.0 ops/sec, σ=10.00ms');
  });

  it('benchmarks sync and async functions with warmups, comparisons, and summaries', async () => {
    let clock = 0;
    const benchmark = new PerformanceBenchmark({
      warmupIterations: 1,
      now: () => {
        clock += 0.01;
        return clock;
      },
    });
    let syncCalls = 0;
    let asyncCalls = 0;

    const sync = benchmark.benchmark(
      'sync',
      () => {
        syncCalls += 1;
      },
      3,
      'sync function',
    );
    const asyncResult = await benchmark.benchmarkAsync(
      'async',
      async () => {
        asyncCalls += 1;
      },
      2,
      'async function',
    );

    expect(syncCalls).toBe(4);
    expect(asyncCalls).toBe(3);
    expect(sync.iterations).toBe(3);
    expect(sync.totalTime).toBeCloseTo(0.03);
    expect(sync.meanTime).toBeCloseTo(0.01);
    expect(asyncResult.iterations).toBe(2);
    expect(benchmark.compare(sync, asyncResult)).toMatchObject({
      baseline: 'sync',
      comparison: 'async',
    });
    expect(['sync', 'async']).toContain(benchmark.compare(sync, asyncResult).faster);
    const summary = benchmark.getSummary();
    expect(summary).toMatchObject({ total_benchmarks: 2 });
    expect(['sync', 'async']).toContain(summary.fastest);
    expect(['sync', 'async']).toContain(summary.slowest);
    expect(benchmark.printSummary()).toContain('BENCHMARK SUMMARY');
  });

  it('returns an empty summary before any benchmark runs', () => {
    expect(new PerformanceBenchmark({ warmupIterations: 0 }).getSummary()).toEqual({
      error: 'No benchmark results',
    });
  });

  it('runs local FOL benchmark suites without Python services', async () => {
    let clock = 0;
    const benchmark = new PerformanceBenchmark({
      warmupIterations: 0,
      now: () => {
        clock += 0.001;
        return clock;
      },
    });

    const simple = await FOLBenchmarks.benchmarkSimpleConversion(benchmark, false);
    const batch = await FOLBenchmarks.benchmarkBatchConversion(benchmark, 5);

    expect(simple.name).toBe('FOL Simple Conversion (Regex)');
    expect(simple.metadata).toMatchObject({ use_nlp: false, browser_native: true });
    expect(batch.name).toBe('FOL Batch Conversion (5 items)');
    expect(batch.metadata).toMatchObject({ batch_size: 5, browser_native: true });
  });

  it('runs local proof-cache benchmark suites', () => {
    let clock = 0;
    const benchmark = new PerformanceBenchmark({
      warmupIterations: 0,
      now: () => {
        clock += 0.0001;
        return clock;
      },
    });

    const hit = CacheBenchmarks.benchmarkCacheHit(benchmark);
    const miss = CacheBenchmarks.benchmarkCacheMiss(benchmark);

    expect(hit).toMatchObject({ name: 'Cache Hit', iterations: 10000 });
    expect(miss).toMatchObject({ name: 'Cache Miss', iterations: 10000 });
    expect(benchmark.results).toHaveLength(2);
  });

  it('runs the comprehensive browser-native suite', async () => {
    let clock = 0;
    const summary = await runComprehensiveBenchmarks({
      warmupIterations: 0,
      now: () => {
        clock += 0.001;
        return clock;
      },
    });

    expect(summary).toMatchObject({
      total_benchmarks: 6,
    });
    expect(summary.results).toHaveLength(6);
  });

  it('ports phase7_4_benchmarks.py performance metrics without Python services', () => {
    const metric = new Phase7_4PerformanceMetric({
      name: 'Cache Hit Rate',
      target: '>60%',
      measured: '100.0%',
      passed: true,
      details: { hit_rate: 1 },
    });

    expect(metric.summary()).toBe('PASS Cache Hit Rate: 100.0% (target: >60%)');
    expect(metric.toDict()).toEqual({
      name: 'Cache Hit Rate',
      target: '>60%',
      measured: '100.0%',
      passed: true,
      details: { hit_rate: 1 },
    });
  });

  it('runs Phase 7.4 browser-native validation suite with Python-compatible results', async () => {
    let clock = 0;
    const summary = await runPhase7_4Benchmarks({
      iterations: 2,
      now: () => {
        clock += 0.0001;
        return clock;
      },
    });

    expect(summary).toMatchObject({
      phase: '7.4',
      name: 'Performance Benchmarking',
      source_python_module: 'logic/phase7_4_benchmarks.py',
      browser_native: true,
      server_calls_allowed: false,
      python_runtime_allowed: false,
      passed: true,
      total_benchmarks: 9,
      passed_benchmarks: 9,
    });
    expect(summary.metrics).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'Cache Hit Rate', passed: true }),
        expect.objectContaining({ name: 'ML Confidence Overhead', passed: true }),
        expect.objectContaining({ name: 'ZKP Verification', passed: true }),
        expect.objectContaining({ name: 'Deontic Converter', passed: true }),
      ]),
    );
    expect(summary.detailed_results).toMatchObject({
      batch: { batch_size: 40 },
      cache: { total_queries: 3 },
      nlp: { adapter: 'browser-native-deterministic', available: true },
    });
  });

  it('supports Python-style Phase7_4Benchmarks orchestration and summaries', async () => {
    let clock = 0;
    const benchmarks = new Phase7_4Benchmarks({
      iterations: 1,
      now: () => {
        clock += 0.0001;
        return clock;
      },
    });

    await benchmarks.benchmarkCachePerformance();

    expect(benchmarks.getResults()).toMatchObject({
      phase: '7.4',
      total_benchmarks: 2,
      passed_benchmarks: 2,
    });
    expect(benchmarks.printSummary()).toContain('PHASE 7.4 BENCHMARK SUMMARY');
  });
});
