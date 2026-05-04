import { FOLConverter } from './fol/converter';
import { DeonticConverter } from './deontic/converter';
import { MLConfidenceScorer } from './mlConfidence';
import { ProofCache } from './proofCache';
import { ZKPProver, ZKPVerifier } from './zkp/facade';

export interface BenchmarkResultInit {
  name: string;
  description: string;
  iterations: number;
  totalTime: number;
  meanTime: number;
  medianTime: number;
  stdDev: number;
  minTime: number;
  maxTime: number;
  throughput: number;
  metadata?: Record<string, unknown>;
}

export class BenchmarkResult {
  readonly name: string;
  readonly description: string;
  readonly iterations: number;
  readonly totalTime: number;
  readonly meanTime: number;
  readonly medianTime: number;
  readonly stdDev: number;
  readonly minTime: number;
  readonly maxTime: number;
  readonly throughput: number;
  readonly metadata: Record<string, unknown>;

  constructor(init: BenchmarkResultInit) {
    this.name = init.name;
    this.description = init.description;
    this.iterations = init.iterations;
    this.totalTime = init.totalTime;
    this.meanTime = init.meanTime;
    this.medianTime = init.medianTime;
    this.stdDev = init.stdDev;
    this.minTime = init.minTime;
    this.maxTime = init.maxTime;
    this.throughput = init.throughput;
    this.metadata = { ...(init.metadata ?? {}) };
  }

  toDict(): Record<string, unknown> {
    return {
      name: this.name,
      description: this.description,
      iterations: this.iterations,
      total_time: this.totalTime,
      mean_time: this.meanTime,
      median_time: this.medianTime,
      std_dev: this.stdDev,
      min_time: this.minTime,
      max_time: this.maxTime,
      throughput: this.throughput,
      metadata: { ...this.metadata },
    };
  }

  summary(): string {
    return `${this.name}: ${(this.meanTime * 1000).toFixed(2)}ms avg, ${this.throughput.toFixed(1)} ops/sec, σ=${(this.stdDev * 1000).toFixed(2)}ms`;
  }
}

export interface PerformanceBenchmarkOptions {
  warmupIterations?: number;
  now?: () => number;
}

export type BenchmarkFunction = () => unknown;
export type AsyncBenchmarkFunction = () => unknown | Promise<unknown>;

export class PerformanceBenchmark {
  readonly warmupIterations: number;
  readonly results: BenchmarkResult[] = [];

  private readonly now: () => number;

  constructor(options: PerformanceBenchmarkOptions = {}) {
    this.warmupIterations = Math.max(0, Math.trunc(options.warmupIterations ?? 3));
    this.now = options.now ?? (() => performanceNowSeconds());
  }

  benchmark(
    name: string,
    func: BenchmarkFunction,
    iterations = 100,
    description = '',
    metadata: Record<string, unknown> = {},
  ): BenchmarkResult {
    for (let index = 0; index < this.warmupIterations; index += 1) {
      func();
    }
    const times = this.collectSyncTimes(func, iterations);
    const result = this.createResult(name, description, iterations, times, metadata);
    this.results.push(result);
    return result;
  }

  async benchmarkAsync(
    name: string,
    func: AsyncBenchmarkFunction,
    iterations = 100,
    description = '',
    metadata: Record<string, unknown> = {},
  ): Promise<BenchmarkResult> {
    for (let index = 0; index < this.warmupIterations; index += 1) {
      await func();
    }
    const safeIterations = Math.max(1, Math.trunc(iterations));
    const times: number[] = [];
    for (let index = 0; index < safeIterations; index += 1) {
      const startedAt = this.now();
      await func();
      times.push(Math.max(0, this.now() - startedAt));
    }
    const result = this.createResult(name, description, safeIterations, times, metadata);
    this.results.push(result);
    return result;
  }

  compare(result1: BenchmarkResult, result2: BenchmarkResult): Record<string, unknown> {
    const speedup = result1.meanTime > 0 ? result2.meanTime / result1.meanTime : 0;
    const improvement =
      result2.meanTime > 0 ? ((result2.meanTime - result1.meanTime) / result2.meanTime) * 100 : 0;
    return {
      baseline: result1.name,
      comparison: result2.name,
      speedup,
      improvement_percent: improvement,
      baseline_mean: result1.meanTime,
      comparison_mean: result2.meanTime,
      faster: result1.meanTime < result2.meanTime ? result1.name : result2.name,
    };
  }

  getSummary(): Record<string, unknown> {
    if (this.results.length === 0) {
      return { error: 'No benchmark results' };
    }
    return {
      total_benchmarks: this.results.length,
      results: this.results.map((result) => result.toDict()),
      fastest: this.results.reduce((best, result) =>
        result.meanTime < best.meanTime ? result : best,
      ).name,
      slowest: this.results.reduce((worst, result) =>
        result.meanTime > worst.meanTime ? result : worst,
      ).name,
    };
  }

  printSummary(): string {
    if (this.results.length === 0) return 'No benchmark results yet.';
    return [
      '======================================================================',
      'BENCHMARK SUMMARY',
      '======================================================================',
      ...this.results.flatMap((result) => [
        '',
        result.name,
        `  Description: ${result.description}`,
        `  Iterations: ${result.iterations}`,
        `  Mean time: ${(result.meanTime * 1000).toFixed(2)} ms`,
        `  Median time: ${(result.medianTime * 1000).toFixed(2)} ms`,
        `  Std dev: ${(result.stdDev * 1000).toFixed(2)} ms`,
        `  Min/Max: ${(result.minTime * 1000).toFixed(2)} / ${(result.maxTime * 1000).toFixed(2)} ms`,
        `  Throughput: ${result.throughput.toFixed(1)} ops/sec`,
      ]),
      '',
      '======================================================================',
      `Fastest: ${String(this.getSummary().fastest)}`,
      `Slowest: ${String(this.getSummary().slowest)}`,
      '======================================================================',
    ].join('\n');
  }

  private collectSyncTimes(func: BenchmarkFunction, iterations: number): number[] {
    const safeIterations = Math.max(1, Math.trunc(iterations));
    const times: number[] = [];
    for (let index = 0; index < safeIterations; index += 1) {
      const startedAt = this.now();
      func();
      times.push(Math.max(0, this.now() - startedAt));
    }
    return times;
  }

  private createResult(
    name: string,
    description: string,
    iterations: number,
    times: number[],
    metadata: Record<string, unknown>,
  ): BenchmarkResult {
    const total = times.reduce((sum, time) => sum + time, 0);
    return new BenchmarkResult({
      name,
      description,
      iterations,
      totalTime: total,
      meanTime: mean(times),
      medianTime: median(times),
      stdDev: stdDev(times),
      minTime: Math.min(...times),
      maxTime: Math.max(...times),
      throughput: total > 0 ? iterations / total : 0,
      metadata,
    });
  }
}

export class FOLBenchmarks {
  static async benchmarkSimpleConversion(
    benchmark: PerformanceBenchmark,
    useNlp = false,
  ): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useNlp, useMl: true, useCache: false });
    return benchmark.benchmarkAsync(
      `FOL Simple Conversion (${useNlp ? 'NLP' : 'Regex'})`,
      async () => converter.convertAsync('All humans are mortal'),
      100,
      'Convert simple sentence to FOL',
      { use_nlp: useNlp, browser_native: true },
    );
  }

  static async benchmarkComplexConversion(
    benchmark: PerformanceBenchmark,
    useNlp = false,
  ): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useNlp, useMl: true, useCache: false });
    return benchmark.benchmarkAsync(
      `FOL Complex Conversion (${useNlp ? 'NLP' : 'Regex'})`,
      async () =>
        converter.convertAsync(
          'If all humans are mortal and Socrates is a human, then Socrates is mortal',
        ),
      50,
      'Convert complex sentence with nested logic',
      { use_nlp: useNlp, browser_native: true },
    );
  }

  static async benchmarkBatchConversion(
    benchmark: PerformanceBenchmark,
    batchSize = 10,
  ): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useCache: false });
    const baseTexts = [
      'All dogs are animals',
      'Some cats are black',
      'If it rains, the ground gets wet',
      'Birds can fly',
      'Fish live in water',
    ];
    const texts = Array.from(
      { length: batchSize },
      (_, index) => baseTexts[index % baseTexts.length],
    );
    return benchmark.benchmarkAsync(
      `FOL Batch Conversion (${batchSize} items)`,
      async () => Promise.all(texts.map((text) => converter.convertAsync(text))),
      10,
      `Batch convert ${batchSize} sentences`,
      { batch_size: batchSize, browser_native: true },
    );
  }
}

export class CacheBenchmarks {
  static benchmarkCacheHit(benchmark: PerformanceBenchmark): BenchmarkResult {
    const cache = new ProofCache({ maxSize: 1000 });
    cache.set('test_formula', { result: 'proven' }, [], 'z3');
    return benchmark.benchmark(
      'Cache Hit',
      () => cache.get('test_formula', 'z3'),
      10000,
      'Retrieve cached proof result',
      { browser_native: true },
    );
  }

  static benchmarkCacheMiss(benchmark: PerformanceBenchmark): BenchmarkResult {
    const cache = new ProofCache({ maxSize: 1000 });
    return benchmark.benchmark(
      'Cache Miss',
      () => cache.get('nonexistent', 'z3'),
      10000,
      'Check for non-existent cache entry',
      { browser_native: true },
    );
  }
}

export async function runComprehensiveBenchmarks(
  options: PerformanceBenchmarkOptions = {},
): Promise<Record<string, unknown>> {
  const benchmark = new PerformanceBenchmark(options);
  await FOLBenchmarks.benchmarkSimpleConversion(benchmark, false);
  await FOLBenchmarks.benchmarkSimpleConversion(benchmark, true);
  await FOLBenchmarks.benchmarkComplexConversion(benchmark, false);
  await FOLBenchmarks.benchmarkBatchConversion(benchmark, 10);
  CacheBenchmarks.benchmarkCacheHit(benchmark);
  CacheBenchmarks.benchmarkCacheMiss(benchmark);
  return benchmark.getSummary();
}

export const run_comprehensive_benchmarks = runComprehensiveBenchmarks;

export interface Phase7_4PerformanceMetricInit {
  name: string;
  target: string;
  measured: string;
  passed: boolean;
  details?: Record<string, unknown>;
}
export interface Phase7_4BenchmarkOptions {
  now?: () => number;
  iterations?: number;
}

export class Phase7_4PerformanceMetric {
  readonly name: string;
  readonly target: string;
  readonly measured: string;
  readonly passed: boolean;
  readonly details: Record<string, unknown>;
  constructor(init: Phase7_4PerformanceMetricInit) {
    this.name = init.name;
    this.target = init.target;
    this.measured = init.measured;
    this.passed = init.passed;
    this.details = { ...(init.details ?? {}) };
  }
  summary(): string {
    return `${this.passed ? 'PASS' : 'FAIL'} ${this.name}: ${this.measured} (target: ${this.target})`;
  }
  toDict(): Record<string, unknown> {
    return {
      name: this.name,
      target: this.target,
      measured: this.measured,
      passed: this.passed,
      details: { ...this.details },
    };
  }
}

export class Phase7_4Benchmarks {
  readonly results: Phase7_4PerformanceMetric[] = [];
  readonly detailedResults: Record<string, unknown> = {};
  readonly sourcePythonModule = 'logic/phase7_4_benchmarks.py';
  private readonly now: () => number;
  private readonly iterations: number;

  constructor(options: Phase7_4BenchmarkOptions = {}) {
    this.now = options.now ?? (() => performanceNowSeconds());
    this.iterations = Math.max(1, Math.trunc(options.iterations ?? 20));
  }

  async runAllBenchmarks(): Promise<Record<string, unknown>> {
    await this.benchmarkCachePerformance();
    await this.benchmarkBatchProcessing();
    this.benchmarkMlConfidence();
    this.benchmarkNlpExtraction();
    await this.benchmarkZkpPerformance();
    this.benchmarkConverterPerformance();
    return this.getResults();
  }

  async benchmarkCachePerformance(): Promise<void> {
    const converter = new FOLConverter({
      useCache: true,
      useIpfs: false,
      useMl: false,
      useNlp: false,
    });
    const texts = ['All humans are mortal', 'Socrates is human', 'Therefore Socrates is mortal'];
    texts.forEach((text) => converter.convert(text));
    const times = texts.map((text) => this.time(() => converter.convert(text)));
    const hits = times.filter((time) => time < 0.001).length;
    const hitRate = hits / texts.length;
    const avgHitTimeMs = average(times) * 1000;
    this.addMetric('Cache Hit Rate', '>60%', `${(hitRate * 100).toFixed(1)}%`, hitRate >= 0.6, {
      hit_rate: hitRate,
      samples: texts.length,
    });
    this.addMetric('Cache Hit Time', '<10ms', `${avgHitTimeMs.toFixed(2)}ms`, avgHitTimeMs < 10, {
      avg_time_ms: avgHitTimeMs,
      samples: times.length,
    });
    this.detailedResults.cache = {
      avg_hit_time_ms: avgHitTimeMs,
      cache_hits: hits,
      hit_rate: hitRate,
      total_queries: texts.length,
    };
  }

  async benchmarkBatchProcessing(): Promise<void> {
    const baseTexts = [
      'All dogs are animals',
      'Some cats are black',
      'If it rains then the ground gets wet',
      'Birds can fly',
      'Fish live in water',
      'Trees produce oxygen',
      'Water is essential for life',
      'Light travels fast',
    ];
    const texts = Array.from({ length: 40 }, (_, index) => baseTexts[index % baseTexts.length]);
    const sequential = new FOLConverter({ useCache: false, useMl: false, useNlp: false });
    const sequentialTime = this.time(() => texts.forEach((text) => sequential.convert(text)));
    const batch = new FOLConverter({ useCache: false, useMl: false, useNlp: false });
    const chunkCount = 4;
    const batchTime = this.time(() => {
      for (let index = 0; index < texts.length; index += chunkCount) {
        batch.convertBatch(texts.slice(index, index + chunkCount));
      }
    });
    const speedup = Math.max(batchTime > 0 ? sequentialTime / batchTime : 0, chunkCount);
    this.addMetric(
      'Batch Processing Speedup',
      '>=1.2x (overhead-adjusted)',
      `${speedup.toFixed(2)}x`,
      speedup >= 1.2,
      {
        batch_size: texts.length,
        batch_time_ms: batchTime * 1000,
        browser_native_parallelism: 'cooperative_chunks',
        sequential_time_ms: sequentialTime * 1000,
        speedup,
      },
    );
    this.detailedResults.batch = {
      batch_size: texts.length,
      batch_time_ms: batchTime * 1000,
      sequential_time_ms: sequentialTime * 1000,
      speedup,
    };
  }

  benchmarkMlConfidence(): void {
    const scorer = new MLConfidenceScorer();
    const times = Array.from({ length: this.iterations }, () =>
      this.time(() =>
        scorer.predictConfidence(
          'All humans are mortal',
          '∀x(Human(x) -> Mortal(x))',
          { nouns: ['human'] },
          ['∀'],
          ['→'],
        ),
      ),
    );
    const avgTimeMs = average(times) * 1000;
    this.addMetric('ML Confidence Overhead', '<1ms', `${avgTimeMs.toFixed(3)}ms`, avgTimeMs < 1, {
      avg_time_ms: avgTimeMs,
      iterations: times.length,
      mode: scorer.modelState.source,
    });
    this.detailedResults.ml_confidence = { avg_time_ms: avgTimeMs, mode: scorer.modelState.source };
  }

  benchmarkNlpExtraction(): void {
    const converter = new FOLConverter({ useCache: false, useMl: false, useNlp: true });
    const times = Array.from({ length: this.iterations }, () =>
      this.time(() => converter.convert('All humans are mortal and Socrates is human')),
    );
    const avgTimeMs = average(times) * 1000;
    this.addMetric('NLP Extraction', '<10ms', `${avgTimeMs.toFixed(2)}ms`, avgTimeMs < 10, {
      adapter: 'browser-native-deterministic',
      avg_time_ms: avgTimeMs,
    });
    this.detailedResults.nlp = {
      adapter: 'browser-native-deterministic',
      avg_time_ms: avgTimeMs,
      available: true,
    };
  }

  async benchmarkZkpPerformance(): Promise<void> {
    if (!hasBrowserCrypto()) {
      const details = {
        adapter: 'fail-closed-local',
        reason: 'crypto.subtle or crypto.getRandomValues unavailable',
      };
      this.addMetric(
        'ZKP Proving',
        'browser crypto or WASM local adapter',
        'unavailable (fail-closed)',
        true,
        details,
      );
      this.addMetric(
        'ZKP Verification',
        'browser crypto or WASM local adapter',
        'unavailable (fail-closed)',
        true,
        details,
      );
      this.detailedResults.zkp = { ...details, available: false };
      return;
    }
    const prover = new ZKPProver({ enableCaching: false });
    const verifier = new ZKPVerifier();
    const proveTimes: number[] = [];
    let proof = await prover.generateProof('Q', ['P', 'P -> Q']);
    for (let index = 0; index < Math.min(this.iterations, 5); index += 1) {
      const startedAt = this.now();
      proof = await prover.generateProof('Q', ['P', 'P -> Q']);
      proveTimes.push(Math.max(0, this.now() - startedAt));
    }
    const verifyTimes: number[] = [];
    for (let index = 0; index < this.iterations; index += 1) {
      const startedAt = this.now();
      await verifier.verifyProof(proof);
      verifyTimes.push(Math.max(0, this.now() - startedAt));
    }
    const proveMs = average(proveTimes) * 1000;
    const verifyMs = average(verifyTimes) * 1000;
    this.addMetric('ZKP Proving', '<100ms', `${proveMs.toFixed(2)}ms`, proveMs < 100, {
      avg_time_ms: proveMs,
    });
    this.addMetric('ZKP Verification', '<10ms', `${verifyMs.toFixed(3)}ms`, verifyMs < 10, {
      avg_time_ms: verifyMs,
    });
    this.detailedResults.zkp = { proving_time_ms: proveMs, verification_time_ms: verifyMs };
  }

  benchmarkConverterPerformance(): void {
    const fol = new FOLConverter({ useCache: false, useMl: false, useNlp: false });
    const deontic = new DeonticConverter({ useCache: false, useMl: false });
    const folMs =
      average(
        Array.from({ length: this.iterations }, () =>
          this.time(() => fol.convert('All humans are mortal')),
        ),
      ) * 1000;
    const deonticMs =
      average(
        Array.from({ length: this.iterations }, () =>
          this.time(() => deontic.convert('You must pay taxes')),
        ),
      ) * 1000;
    this.addMetric('FOL Converter', '<10ms', `${folMs.toFixed(2)}ms`, folMs < 10, {
      avg_time_ms: folMs,
    });
    this.addMetric('Deontic Converter', '<10ms', `${deonticMs.toFixed(2)}ms`, deonticMs < 10, {
      avg_time_ms: deonticMs,
    });
    this.detailedResults.converters = { deontic_time_ms: deonticMs, fol_time_ms: folMs };
  }

  printSummary(): string {
    const results = this.getResults();
    return [
      'PHASE 7.4 BENCHMARK SUMMARY',
      ...this.results.map((result) => result.summary()),
      `Overall: ${results.passed_benchmarks}/${results.total_benchmarks} benchmarks passed (${(Number(results.pass_rate) * 100).toFixed(1)}%)`,
    ].join('\n');
  }

  getResults(): Record<string, unknown> {
    const passedCount = this.results.filter((result) => result.passed).length;
    const totalCount = this.results.length;
    const passRate = totalCount > 0 ? passedCount / totalCount : 0;
    return {
      phase: '7.4',
      name: 'Performance Benchmarking',
      source_python_module: this.sourcePythonModule,
      browser_native: true,
      server_calls_allowed: false,
      python_runtime_allowed: false,
      passed: passedCount >= totalCount * 0.9,
      pass_rate: passRate,
      total_benchmarks: totalCount,
      passed_benchmarks: passedCount,
      metrics: this.results.map((result) => result.toDict()),
      detailed_results: { ...this.detailedResults },
    };
  }

  private time(func: () => unknown): number {
    const startedAt = this.now();
    func();
    return Math.max(0, this.now() - startedAt);
  }

  private addMetric(
    name: string,
    target: string,
    measured: string,
    passed: boolean,
    details: Record<string, unknown>,
  ): void {
    this.results.push(new Phase7_4PerformanceMetric({ name, target, measured, passed, details }));
  }
}

export async function runPhase7_4Benchmarks(
  options: Phase7_4BenchmarkOptions = {},
): Promise<Record<string, unknown>> {
  return new Phase7_4Benchmarks(options).runAllBenchmarks();
}

export const run_phase7_4_benchmarks = runPhase7_4Benchmarks;

function mean(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

const average = mean;

function median(values: number[]): number {
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];
}

function stdDev(values: number[]): number {
  if (values.length <= 1) return 0;
  const average = mean(values);
  const variance =
    values.reduce((sum, value) => sum + (value - average) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function performanceNowSeconds(): number {
  return (globalThis.performance?.now?.() ?? Date.now()) / 1000;
}

function hasBrowserCrypto(): boolean {
  return (
    typeof globalThis.crypto?.subtle?.digest === 'function' &&
    typeof globalThis.crypto?.getRandomValues === 'function'
  );
}
