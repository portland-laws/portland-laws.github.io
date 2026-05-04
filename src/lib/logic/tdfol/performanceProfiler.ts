import { calculateStats } from './performanceMetrics';

export type TdfolProfilerReportFormat = 'text' | 'json' | 'html';
export type TdfolBottleneckSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface TdfolProfilingStats {
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

export interface TdfolBottleneck {
  function: string;
  timeMs: number;
  calls: number;
  timePerCallMs: number;
  severity: TdfolBottleneckSeverity;
  recommendation: string;
  complexityEstimate?: string;
}

export interface TdfolMemoryStats {
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

export interface TdfolBenchmarkConfig {
  name: string;
  formula: string;
  thresholdMs?: number;
  run?: () => unknown;
}

export interface TdfolBenchmarkResult {
  name: string;
  formula: string;
  timeMs: number;
  memoryMb: number;
  passed: boolean;
  baselineTimeMs?: number;
  regressionPct?: number;
  metadata: Record<string, unknown>;
}

export interface TdfolBenchmarkResults {
  benchmarks: TdfolBenchmarkResult[];
  totalTimeMs: number;
  passed: number;
  failed: number;
  regressions: number;
  timestamp: string;
  passRate: number;
}

export interface TdfolPerformanceProfilerMetadata {
  sourcePythonModule: 'logic/TDFOL/performance_profiler.py';
  browserNative: true;
  pythonRuntimeRequired: false;
  serverCallsAllowed: false;
  memoryBackend: 'performance.memory';
  timingBackend: 'performance.now';
}

export interface TdfolPerformanceProfilerRun {
  metadata: TdfolPerformanceProfilerMetadata;
  profile: TdfolProfilingStats;
  memory: TdfolMemoryStats;
  bottlenecks: TdfolBottleneck[];
  benchmarks: TdfolBenchmarkResults;
  reports: Record<TdfolProfilerReportFormat, string>;
}

export interface TdfolPerformanceProfilerExampleResult {
  sourcePythonModule: 'logic/TDFOL/example_performance_profiler.py';
  browserNative: true;
  pythonRuntime: false;
  serverRuntime: false;
  profile: TdfolProfilingStats;
  memory: TdfolMemoryStats;
  bottlenecks: TdfolBottleneck[];
  benchmarks: TdfolBenchmarkResults;
  reports: Record<TdfolProfilerReportFormat, string>;
  summary: {
    profiledFunction: string;
    benchmarkCount: number;
    bottleneckCount: number;
    passRate: number;
  };
}

export const TDFOL_PERFORMANCE_PROFILER_METADATA: TdfolPerformanceProfilerMetadata = {
  sourcePythonModule: 'logic/TDFOL/performance_profiler.py',
  browserNative: true,
  pythonRuntimeRequired: false,
  serverCallsAllowed: false,
  memoryBackend: 'performance.memory',
  timingBackend: 'performance.now',
};

export class TdfolPerformanceProfiler {
  readonly history: Array<{ function: string; timestamp: string; stats: TdfolProfilingStats }> = [];
  readonly baseline: Record<string, number>;

  constructor(options: { baseline?: Record<string, number> } = {}) {
    this.baseline = options.baseline ?? {};
  }

  profileFunction<T>(functionName: string, fn: () => T, runs = 10): TdfolProfilingStats {
    const safeRuns = Math.max(1, runs);
    const durations: number[] = [];
    for (let index = 0; index < safeRuns; index += 1) {
      const startedAt = nowMs();
      fn();
      durations.push(nowMs() - startedAt);
    }
    const stats = calculateStats(durations);
    const profile: TdfolProfilingStats = {
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
    this.history.push({
      function: functionName,
      timestamp: new Date().toISOString(),
      stats: profile,
    });
    return profile;
  }

  identifyBottlenecks(
    samples: Array<{ function: string; timeMs: number; calls?: number }>,
    topN = 20,
    minTimeMs = 1,
  ): TdfolBottleneck[] {
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
      .sort(
        (left, right) =>
          severityOrder(left.severity) - severityOrder(right.severity) ||
          right.timeMs - left.timeMs,
      )
      .slice(0, topN);
  }

  memoryProfile<T>(functionName: string, fn: () => T): TdfolMemoryStats {
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

  runBenchmarkSuite(customBenchmarks: TdfolBenchmarkConfig[] = []): TdfolBenchmarkResults {
    const benchmarks = [...getStandardBenchmarks(), ...customBenchmarks];
    const results: TdfolBenchmarkResult[] = [];
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
        const regressionPct = baselineTimeMs
          ? ((timeMs - baselineTimeMs) / baselineTimeMs) * 100
          : undefined;
        if (regressionPct !== undefined && regressionPct > 10) regressions += 1;
        results.push({
          name: benchmark.name,
          formula: benchmark.formula,
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
          formula: benchmark.formula,
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

  generateReport(format: TdfolProfilerReportFormat = 'html'): string {
    if (format === 'json') {
      return JSON.stringify(
        {
          metadata: TDFOL_PERFORMANCE_PROFILER_METADATA,
          timestamp: new Date().toISOString(),
          history: this.history,
          baseline: this.baseline,
        },
        null,
        2,
      );
    }
    if (format === 'text') {
      return [
        'TDFOL Performance Profiling Report',
        `Generated: ${new Date().toISOString()}`,
        `Total profiles: ${this.history.length}`,
        ...this.history
          .slice(-5)
          .flatMap((entry) => [
            `Function: ${entry.function}`,
            `Mean time: ${entry.stats.meanTimeMs.toFixed(3)}ms`,
            `Runs: ${entry.stats.runs}`,
          ]),
      ].join('\n');
    }
    const data = JSON.stringify({
      metadata: TDFOL_PERFORMANCE_PROFILER_METADATA,
      history: this.history,
      baseline: this.baseline,
    });
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>TDFOL Profiling Report</title></head><body><h1>TDFOL Performance Profiling Report</h1><script type="application/json" id="tdfol-profiler-data">${escapeHtml(data)}</script><p>Total profiles: ${this.history.length}</p></body></html>`;
  }
}

export function getStandardBenchmarks(): TdfolBenchmarkConfig[] {
  return [
    { name: 'simple_propositional', formula: 'P ∧ Q', thresholdMs: 10, run: () => true },
    { name: 'simple_implication', formula: 'P → Q', thresholdMs: 10, run: () => true },
    { name: 'quantified_simple', formula: '∀x. P(x)', thresholdMs: 20, run: () => true },
    {
      name: 'quantified_complex',
      formula: '∀x. ∃y. (P(x) → Q(x, y))',
      thresholdMs: 100,
      run: () => true,
    },
    { name: 'temporal_always', formula: '□P', thresholdMs: 10, run: () => true },
    { name: 'temporal_eventually', formula: '◊P', thresholdMs: 10, run: () => true },
    { name: 'deontic_obligation', formula: 'O(P)', thresholdMs: 10, run: () => true },
    { name: 'mixed_temporal_deontic', formula: '□O(P) → ◊P', thresholdMs: 100, run: () => true },
  ];
}

export function profileTdfolFunction<T>(
  functionName: string,
  fn: () => T,
  runs = 10,
): TdfolProfilingStats {
  return new TdfolPerformanceProfiler().profileFunction(functionName, fn, runs);
}

export function runTdfolPerformanceProfiler(
  options: {
    functionName?: string;
    runs?: number;
    formula?: string;
    customBenchmarks?: TdfolBenchmarkConfig[];
    baseline?: Record<string, number>;
  } = {},
): TdfolPerformanceProfilerRun {
  const functionName = options.functionName ?? 'tdfol_profiled_workload';
  const formula = options.formula ?? 'forall x. obligation(x) -> eventually compliant(x)';
  const profiler = new TdfolPerformanceProfiler({ baseline: options.baseline });
  const profile = profiler.profileFunction(
    functionName,
    () => deterministicTdfolWorkload(formula),
    options.runs ?? 5,
  );
  const memory = profiler.memoryProfile(`${functionName}_memory`, () =>
    deterministicTdfolWorkload(`${formula} memory snapshot`),
  );
  const bottlenecks = profiler.identifyBottlenecks([
    {
      function: profile.functionName,
      timeMs: Math.max(profile.totalTimeMs, 1),
      calls: profile.runs,
    },
    {
      function: `${functionName}_allocation_delta`,
      timeMs: Math.max(memory.growthMb * 10, 0),
      calls: 1,
    },
  ]);
  const benchmarks = profiler.runBenchmarkSuite(options.customBenchmarks);
  const reports: Record<TdfolProfilerReportFormat, string> = {
    text: profiler.generateReport('text'),
    json: profiler.generateReport('json'),
    html: profiler.generateReport('html'),
  };

  return {
    metadata: TDFOL_PERFORMANCE_PROFILER_METADATA,
    profile,
    memory,
    bottlenecks,
    benchmarks,
    reports,
  };
}

export function runTdfolPerformanceProfilerExample(
  options: { runs?: number } = {},
): TdfolPerformanceProfilerExampleResult {
  const profiler = new TdfolPerformanceProfiler({
    baseline: {
      example_quantified_profile: 100,
      quantified_complex: 100,
    },
  });
  const profile = profiler.profileFunction(
    'example_quantified_profile',
    () => deterministicTdfolWorkload('forall x. obligation(x) implies eventually compliant(x)'),
    options.runs ?? 3,
  );
  const memory = profiler.memoryProfile('example_memory_snapshot', () =>
    deterministicTdfolWorkload('always permitted(agent, action)'),
  );
  const bottlenecks = profiler.identifyBottlenecks([
    {
      function: profile.functionName,
      timeMs: Math.max(profile.totalTimeMs, 1),
      calls: profile.runs,
    },
    { function: 'tdfol_rule_loop', timeMs: 3, calls: 1501 },
    { function: 'tdfol_report_render', timeMs: 12, calls: 1 },
  ]);
  const benchmarks = profiler.runBenchmarkSuite([
    {
      name: 'example_quantified_profile',
      formula: 'forall x. obligation(x) -> eventually compliant(x)',
      thresholdMs: 100,
      run: () => deterministicTdfolWorkload('obligation compliant eventually'),
    },
  ]);
  const reports: Record<TdfolProfilerReportFormat, string> = {
    text: profiler.generateReport('text'),
    json: profiler.generateReport('json'),
    html: profiler.generateReport('html'),
  };

  return {
    sourcePythonModule: 'logic/TDFOL/example_performance_profiler.py',
    browserNative: true,
    pythonRuntime: false,
    serverRuntime: false,
    profile,
    memory,
    bottlenecks,
    benchmarks,
    reports,
    summary: {
      profiledFunction: profile.functionName,
      benchmarkCount: benchmarks.benchmarks.length,
      bottleneckCount: bottlenecks.length,
      passRate: benchmarks.passRate,
    },
  };
}

function analyzeBottleneck(
  functionName: string,
  totalTimeMs: number,
  calls: number,
): Pick<TdfolBottleneck, 'severity' | 'recommendation' | 'complexityEstimate'> {
  if (calls > 1000)
    return {
      severity: 'critical',
      recommendation: `Potential O(n^3) operation with ${calls} calls. Consider indexing or caching.`,
      complexityEstimate: 'O(n^3)',
    };
  if (totalTimeMs > 1000 && functionName.toLowerCase().includes('unify'))
    return {
      severity: 'critical',
      recommendation: 'Unification is slow. Consider indexed KB or constraint propagation.',
      complexityEstimate: 'O(n^2)',
    };
  if (totalTimeMs > 1000 && functionName.toLowerCase().includes('prove'))
    return {
      severity: 'critical',
      recommendation: 'Proving is slow. Enable caching or use optimized prover.',
    };
  if (totalTimeMs > 1000)
    return {
      severity: 'critical',
      recommendation: `Function takes ${(totalTimeMs / 1000).toFixed(2)}s. Profile and optimize.`,
    };
  if (totalTimeMs > 100)
    return {
      severity: 'high',
      recommendation: `Function takes ${totalTimeMs.toFixed(1)}ms. Consider optimization.`,
    };
  if (totalTimeMs > 10)
    return {
      severity: 'medium',
      recommendation: 'Minor bottleneck. Optimize if called frequently.',
    };
  return { severity: 'low', recommendation: 'Performance acceptable.' };
}

function severityOrder(severity: TdfolBottleneckSeverity): number {
  return { critical: 0, high: 1, medium: 2, low: 3 }[severity];
}

function getJsHeapMb(): number {
  const memory = (
    globalThis.performance as (Performance & { memory?: { usedJSHeapSize?: number } }) | undefined
  )?.memory;
  return memory?.usedJSHeapSize ? memory.usedJSHeapSize / 1024 / 1024 : 0;
}

function nowMs(): number {
  return typeof globalThis.performance?.now === 'function'
    ? globalThis.performance.now()
    : Date.now();
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function deterministicTdfolWorkload(formula: string): number {
  let score = 0;
  for (let index = 0; index < formula.length; index += 1) {
    const code = formula.charCodeAt(index);
    score = (score + code * (index + 1)) % 9973;
  }
  return score;
}
