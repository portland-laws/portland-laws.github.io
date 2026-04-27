import { calculateCecStats } from './performanceMetrics';

export type CecProfilerReportFormat = 'text' | 'json' | 'html';
export type CecBottleneckSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface CecProfilingStats {
  functionName: string;
  totalTimeMs: number;
  meanTimeMs: number;
  medianTimeMs: number;
  minTimeMs: number;
  maxTimeMs: number;
  stdDevMs: number;
  runs: number;
  callsPerRun: number;
  meetsThreshold: boolean;
}

export interface CecBottleneck {
  function: string;
  timeMs: number;
  calls: number;
  timePerCallMs: number;
  severity: CecBottleneckSeverity;
  recommendation: string;
  complexityEstimate?: string;
}

export interface CecMemoryStats {
  functionName: string;
  peakMb: number;
  startMb: number;
  endMb: number;
  growthMb: number;
  allocations: number;
  deallocations: number;
  netAllocations: number;
  topAllocators: Array<[string, number]>;
  hasLeak: boolean;
}

export interface CecBenchmarkConfig {
  name: string;
  expression: string;
  thresholdMs?: number;
  run?: () => unknown;
}

export interface CecBenchmarkResult {
  name: string;
  expression: string;
  timeMs: number;
  memoryMb: number;
  passed: boolean;
  baselineTimeMs?: number;
  regressionPct?: number;
  metadata: Record<string, unknown>;
}

export interface CecBenchmarkResults {
  benchmarks: CecBenchmarkResult[];
  totalTimeMs: number;
  passed: number;
  failed: number;
  regressions: number;
  timestamp: string;
  passRate: number;
}

export class CecPerformanceProfiler {
  readonly history: Array<{ function: string; timestamp: string; stats: CecProfilingStats }> = [];
  readonly baseline: Record<string, number>;

  constructor(options: { baseline?: Record<string, number> } = {}) {
    this.baseline = options.baseline ?? {};
  }

  profileFunction<T>(functionName: string, fn: () => T, runs = 10): CecProfilingStats {
    const safeRuns = Math.max(1, runs);
    const durations: number[] = [];
    for (let index = 0; index < safeRuns; index += 1) {
      const startedAt = nowMs();
      fn();
      durations.push(nowMs() - startedAt);
    }
    const stats = calculateCecStats(durations);
    const profile: CecProfilingStats = {
      functionName,
      totalTimeMs: stats.sum,
      meanTimeMs: stats.mean,
      medianTimeMs: stats.median,
      minTimeMs: stats.min,
      maxTimeMs: stats.max,
      stdDevMs: stats.stdDev,
      runs: safeRuns,
      callsPerRun: 1,
      meetsThreshold: stats.mean < 100,
    };
    this.history.push({ function: functionName, timestamp: new Date().toISOString(), stats: profile });
    return profile;
  }

  identifyBottlenecks(samples: Array<{ function: string; timeMs: number; calls?: number }>, topN = 20, minTimeMs = 1): CecBottleneck[] {
    return samples
      .filter((sample) => sample.timeMs >= minTimeMs)
      .map((sample) => {
        const calls = sample.calls ?? 1;
        const analyzed = analyzeBottleneck(sample.function, sample.timeMs, calls);
        return {
          function: sample.function,
          timeMs: sample.timeMs,
          calls,
          timePerCallMs: calls > 0 ? sample.timeMs / calls : 0,
          ...analyzed,
        };
      })
      .sort((left, right) => severityOrder(left.severity) - severityOrder(right.severity) || right.timeMs - left.timeMs)
      .slice(0, topN);
  }

  memoryProfile<T>(functionName: string, fn: () => T): CecMemoryStats {
    const startMb = getJsHeapMb();
    fn();
    const endMb = getJsHeapMb();
    const growthMb = endMb - startMb;
    return {
      functionName,
      peakMb: Math.max(startMb, endMb),
      startMb,
      endMb,
      growthMb,
      allocations: 0,
      deallocations: 0,
      netAllocations: 0,
      topAllocators: [],
      hasLeak: growthMb > 5,
    };
  }

  runBenchmarkSuite(customBenchmarks: CecBenchmarkConfig[] = []): CecBenchmarkResults {
    const benchmarks = [...getStandardCecBenchmarks(), ...customBenchmarks];
    const results: CecBenchmarkResult[] = [];
    let totalTimeMs = 0;
    let regressions = 0;

    for (const benchmark of benchmarks) {
      const startedAt = nowMs();
      const memoryBefore = getJsHeapMb();
      try {
        benchmark.run?.();
        const timeMs = nowMs() - startedAt;
        const memoryMb = Math.max(0, getJsHeapMb() - memoryBefore);
        const baselineTimeMs = this.baseline[benchmark.name];
        const regressionPct = baselineTimeMs ? ((timeMs - baselineTimeMs) / baselineTimeMs) * 100 : undefined;
        if (regressionPct !== undefined && regressionPct > 10) regressions += 1;
        results.push({
          name: benchmark.name,
          expression: benchmark.expression,
          timeMs,
          memoryMb,
          passed: timeMs <= (benchmark.thresholdMs ?? 100),
          baselineTimeMs,
          regressionPct,
          metadata: {},
        });
        totalTimeMs += timeMs;
      } catch (error) {
        results.push({
          name: benchmark.name,
          expression: benchmark.expression,
          timeMs: 0,
          memoryMb: 0,
          passed: false,
          metadata: { error: error instanceof Error ? error.message : String(error) },
        });
      }
    }

    const passed = results.filter((result) => result.passed).length;
    const failed = results.length - passed;
    return {
      benchmarks: results,
      totalTimeMs,
      passed,
      failed,
      regressions,
      timestamp: new Date().toISOString(),
      passRate: results.length ? passed / results.length : 0,
    };
  }

  generateReport(format: CecProfilerReportFormat = 'html'): string {
    if (format === 'json') {
      return JSON.stringify({ timestamp: new Date().toISOString(), history: this.history, baseline: this.baseline }, null, 2);
    }
    if (format === 'text') {
      return [
        'CEC Performance Profiling Report',
        `Generated: ${new Date().toISOString()}`,
        `Total profiles: ${this.history.length}`,
        ...this.history.slice(-5).flatMap((entry) => [
          `Function: ${entry.function}`,
          `Mean time: ${entry.stats.meanTimeMs.toFixed(3)}ms`,
          `Runs: ${entry.stats.runs}`,
        ]),
      ].join('\n');
    }
    const data = JSON.stringify({ history: this.history, baseline: this.baseline });
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>CEC Profiling Report</title></head><body><h1>CEC Performance Profiling Report</h1><script type="application/json" id="cec-profiler-data">${escapeHtml(data)}</script><p>Total profiles: ${this.history.length}</p></body></html>`;
  }
}

export function getStandardCecBenchmarks(): CecBenchmarkConfig[] {
  return [
    { name: 'simple_atom', expression: '(subject_to agent code)', thresholdMs: 10, run: () => true },
    { name: 'simple_implication', expression: '(implies (subject_to agent code) (comply_with agent code))', thresholdMs: 10, run: () => true },
    { name: 'quantified_simple', expression: '(forall agent (subject_to agent code))', thresholdMs: 20, run: () => true },
    { name: 'quantified_modus_ponens', expression: '(forall agent (implies (subject_to agent code) (comply_with agent code)))', thresholdMs: 100, run: () => true },
    { name: 'temporal_always', expression: '(always (comply_with agent code))', thresholdMs: 10, run: () => true },
    { name: 'temporal_eventually', expression: '(eventually (comply_with agent code))', thresholdMs: 10, run: () => true },
    { name: 'deontic_obligation', expression: '(O (comply_with agent code))', thresholdMs: 10, run: () => true },
    { name: 'mixed_temporal_deontic', expression: '(always (O (comply_with agent code)))', thresholdMs: 100, run: () => true },
  ];
}

export function profileCecFunction<T>(functionName: string, fn: () => T, runs = 10): CecProfilingStats {
  return new CecPerformanceProfiler().profileFunction(functionName, fn, runs);
}

function analyzeBottleneck(functionName: string, totalTimeMs: number, calls: number): Pick<CecBottleneck, 'severity' | 'recommendation' | 'complexityEstimate'> {
  const lower = functionName.toLowerCase();
  if (calls > 1000) return { severity: 'critical', recommendation: `Potential O(n^3) CEC operation with ${calls} calls. Consider indexing, caching, or WASM acceleration.`, complexityEstimate: 'O(n^3)' };
  if (totalTimeMs > 1000 && lower.includes('unify')) return { severity: 'critical', recommendation: 'CEC unification is slow. Consider indexed substitutions or constraint propagation.', complexityEstimate: 'O(n^2)' };
  if (totalTimeMs > 1000 && lower.includes('prove')) return { severity: 'critical', recommendation: 'CEC proving is slow. Enable proof caching, reduce generative rules, or switch strategies.' };
  if (totalTimeMs > 1000 && lower.includes('event')) return { severity: 'critical', recommendation: 'Event-calculus reasoning is slow. Index fluents by time and subject.' };
  if (totalTimeMs > 100 && lower.includes('strategy')) return { severity: 'high', recommendation: 'Strategy selection is expensive. Cache strategy costs by theorem and KB signature.' };
  if (totalTimeMs > 1000) return { severity: 'critical', recommendation: `Function takes ${(totalTimeMs / 1000).toFixed(2)}s. Profile and optimize.` };
  if (totalTimeMs > 100) return { severity: 'high', recommendation: `Function takes ${totalTimeMs.toFixed(1)}ms. Consider optimization.` };
  if (totalTimeMs > 10) return { severity: 'medium', recommendation: 'Minor CEC bottleneck. Optimize if called frequently.' };
  return { severity: 'low', recommendation: 'Performance acceptable.' };
}

function severityOrder(severity: CecBottleneckSeverity): number {
  return { critical: 0, high: 1, medium: 2, low: 3 }[severity];
}

function getJsHeapMb(): number {
  const memory = (globalThis.performance as (Performance & { memory?: { usedJSHeapSize?: number } }) | undefined)?.memory;
  return memory?.usedJSHeapSize ? memory.usedJSHeapSize / 1024 / 1024 : 0;
}

function nowMs(): number {
  return typeof globalThis.performance?.now === 'function' ? globalThis.performance.now() : Date.now();
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
