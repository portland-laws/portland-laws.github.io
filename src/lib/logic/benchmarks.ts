import { FOLConverter } from './fol/converter';
import { ProofCache } from './proofCache';

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
    const improvement = result2.meanTime > 0 ? ((result2.meanTime - result1.meanTime) / result2.meanTime) * 100 : 0;
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
      fastest: this.results.reduce((best, result) => result.meanTime < best.meanTime ? result : best).name,
      slowest: this.results.reduce((worst, result) => result.meanTime > worst.meanTime ? result : worst).name,
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
  static async benchmarkSimpleConversion(benchmark: PerformanceBenchmark, useNlp = false): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useNlp, useMl: true, useCache: false });
    return benchmark.benchmarkAsync(
      `FOL Simple Conversion (${useNlp ? 'NLP' : 'Regex'})`,
      async () => converter.convertAsync('All humans are mortal'),
      100,
      'Convert simple sentence to FOL',
      { use_nlp: useNlp, browser_native: true },
    );
  }

  static async benchmarkComplexConversion(benchmark: PerformanceBenchmark, useNlp = false): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useNlp, useMl: true, useCache: false });
    return benchmark.benchmarkAsync(
      `FOL Complex Conversion (${useNlp ? 'NLP' : 'Regex'})`,
      async () => converter.convertAsync('If all humans are mortal and Socrates is a human, then Socrates is mortal'),
      50,
      'Convert complex sentence with nested logic',
      { use_nlp: useNlp, browser_native: true },
    );
  }

  static async benchmarkBatchConversion(benchmark: PerformanceBenchmark, batchSize = 10): Promise<BenchmarkResult> {
    const converter = new FOLConverter({ useCache: false });
    const baseTexts = [
      'All dogs are animals',
      'Some cats are black',
      'If it rains, the ground gets wet',
      'Birds can fly',
      'Fish live in water',
    ];
    const texts = Array.from({ length: batchSize }, (_, index) => baseTexts[index % baseTexts.length]);
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

function mean(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values: number[]): number {
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];
}

function stdDev(values: number[]): number {
  if (values.length <= 1) return 0;
  const average = mean(values);
  const variance = values.reduce((sum, value) => sum + (value - average) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function performanceNowSeconds(): number {
  return (globalThis.performance?.now?.() ?? Date.now()) / 1000;
}
