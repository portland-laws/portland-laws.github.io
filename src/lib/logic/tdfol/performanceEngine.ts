import type { ProofResult } from '../types';
import { parseTdfolFormula } from './parser';
import type { TdfolKnowledgeBase } from './prover';
import {
  calculateStats,
  getGlobalTdfolMetricsCollector,
  type TdfolMetricsCollector,
  type TdfolStatisticalSummary,
} from './performanceMetrics';
import {
  TdfolForwardChainingStrategy,
  TdfolModalTableauxStrategy,
  TdfolStrategySelector,
  type TdfolProverStrategy,
} from './strategies';

export type TdfolPerformanceStrategyName = 'auto' | 'forward' | 'modal';
export type TdfolStatisticsFormat = 'json' | 'prometheus';

export const TDFOL_PERFORMANCE_ENGINE_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_performance_engine.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
  parity: [
    'metrics_aggregation',
    'profile_operation',
    'dashboard_html_export',
    'statistics_export',
    'strategy_comparison',
    'regression_checks',
    'reset',
  ],
} as const;

export interface TdfolProfileOperationOptions {
  formula: string;
  kbFormulas?: string[];
  runs?: number;
  strategy?: TdfolPerformanceStrategyName;
}

export interface TdfolProfileResult {
  formula: string;
  runs: number;
  strategy: string;
  kbSize: number;
  timing: {
    meanTimeMs: number;
    medianTimeMs: number;
    minTimeMs: number;
    maxTimeMs: number;
    stdDevMs: number;
    totalTimeMs: number;
  };
  performance: {
    provedRuns: number;
    unknownRuns: number;
    errorRuns: number;
    meetsThreshold: boolean;
    bottlenecks: TdfolPerformanceBottleneck[];
  };
  metadata: {
    operation: string;
    latestStatus?: ProofResult['status'];
  };
}

export interface TdfolPerformanceBottleneck {
  operation: string;
  timeMs: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
}

export interface TdfolPerformanceEngineMetrics {
  dashboardStats: ReturnType<TdfolPerformanceEngine['getDashboardStatistics']>;
  collectorStats: Record<string, unknown>;
  collectorSummary: {
    timingOperations: number;
    memoryOperations: number;
    counters: number;
    gauges: number;
    histograms: number;
  };
  metadata: {
    dashboardProofsRecorded: number;
    dashboardUptimeSeconds: number;
    collectorUptimeSeconds: number;
  };
}

export interface TdfolProofMetric {
  formula: string;
  strategy: string;
  status: ProofResult['status'];
  timeMs: number;
  timestamp: number;
}

export class TdfolPerformanceEngine {
  readonly proofMetrics: TdfolProofMetric[] = [];
  readonly profilingHistory: TdfolProfileResult[] = [];
  private readonly startedAt = Date.now();
  private readonly collector: TdfolMetricsCollector;

  constructor(collector: TdfolMetricsCollector = getGlobalTdfolMetricsCollector()) {
    this.collector = collector;
  }

  getMetrics(): TdfolPerformanceEngineMetrics {
    const collectorStats = this.collector.getStatistics();
    return {
      dashboardStats: this.getDashboardStatistics(),
      collectorStats,
      collectorSummary: {
        timingOperations: Object.keys((collectorStats.timing as Record<string, unknown>) ?? {})
          .length,
        memoryOperations: Object.keys((collectorStats.memory as Record<string, unknown>) ?? {})
          .length,
        counters: Object.keys((collectorStats.counters as Record<string, unknown>) ?? {}).length,
        gauges: Object.keys((collectorStats.gauges as Record<string, unknown>) ?? {}).length,
        histograms: Object.keys((collectorStats.histograms as Record<string, unknown>) ?? {})
          .length,
      },
      metadata: {
        dashboardProofsRecorded: this.proofMetrics.length,
        dashboardUptimeSeconds: this.getUptime(),
        collectorUptimeSeconds: this.getUptime(),
      },
    };
  }

  get_metrics(): TdfolPerformanceEngineMetrics {
    return this.getMetrics();
  }

  profileOperation(options: TdfolProfileOperationOptions): TdfolProfileResult {
    const runs = Math.max(1, options.runs ?? 10);
    const strategyName = options.strategy ?? 'auto';
    const formula = parseTdfolFormula(options.formula);
    const kb: TdfolKnowledgeBase = { axioms: (options.kbFormulas ?? []).map(parseTdfolFormula) };
    const selector = new TdfolStrategySelector({ strategies: this.createStrategies(strategyName) });
    const durations: number[] = [];
    const statuses: ProofResult['status'][] = [];

    for (let index = 0; index < runs; index += 1) {
      const startedAt = nowMs();
      const result = selector.proveWithSelectedStrategy(formula, kb);
      const durationMs = nowMs() - startedAt;
      durations.push(durationMs);
      statuses.push(result.status);
      this.collector.recordTiming(`tdfol.profile.${strategyName}`, durationMs, {
        formula: options.formula,
        run: index + 1,
      });
      this.proofMetrics.push({
        formula: options.formula,
        strategy: strategyName,
        status: result.status,
        timeMs: durationMs,
        timestamp: Date.now(),
      });
    }

    const stats = calculateStats(durations);
    const profile: TdfolProfileResult = {
      formula: options.formula,
      runs,
      strategy: strategyName,
      kbSize: options.kbFormulas?.length ?? 0,
      timing: {
        meanTimeMs: stats.mean,
        medianTimeMs: stats.median,
        minTimeMs: stats.min,
        maxTimeMs: stats.max,
        stdDevMs: stats.stdDev,
        totalTimeMs: stats.sum,
      },
      performance: {
        provedRuns: statuses.filter((status) => status === 'proved').length,
        unknownRuns: statuses.filter((status) => status === 'unknown').length,
        errorRuns: statuses.filter((status) => status === 'error').length,
        meetsThreshold: stats.mean < 100,
        bottlenecks: identifyTimingBottlenecks(`tdfol.profile.${strategyName}`, stats),
      },
      metadata: {
        operation: 'profile_operation',
        latestStatus: statuses.at(-1),
      },
    };
    this.profilingHistory.push(profile);
    return profile;
  }

  profile_operation(options: TdfolProfileOperationOptions): TdfolProfileResult {
    return this.profileOperation(options);
  }

  generateDashboard(options: { includeProfiling?: boolean } = {}): {
    success: true;
    htmlString: string;
    metricsCount: number;
    summary: ReturnType<TdfolPerformanceEngine['getDashboardStatistics']>;
    profilingHistory?: TdfolProfileResult[];
  } {
    const summary = this.getDashboardStatistics();
    return {
      success: true,
      htmlString: this.toHtmlString(
        summary,
        options.includeProfiling ? this.profilingHistory.slice(-10) : [],
      ),
      metricsCount: this.proofMetrics.length,
      summary,
      profilingHistory: options.includeProfiling ? this.profilingHistory.slice(-10) : undefined,
    };
  }

  generate_dashboard(options: { includeProfiling?: boolean } = {}): {
    success: true;
    htmlString: string;
    metricsCount: number;
    summary: ReturnType<TdfolPerformanceEngine['getDashboardStatistics']>;
    profilingHistory?: TdfolProfileResult[];
  } {
    return this.generateDashboard(options);
  }

  exportStatistics(
    format: TdfolStatisticsFormat = 'json',
    includeRawData = false,
  ): Record<string, unknown> {
    const exportData: Record<string, unknown> = {
      metadata: TDFOL_PERFORMANCE_ENGINE_METADATA,
      timestamp: this.startedAt,
      uptime_seconds: this.getUptime(),
      dashboard_stats: this.getDashboardStatistics(),
      collector_stats: this.collector.exportDict(),
      format,
    };
    if (includeRawData) {
      exportData.raw_proof_metrics = this.proofMetrics.slice(-100);
    }
    if (format === 'json') {
      exportData.json_string = JSON.stringify(exportData, null, 2);
    } else {
      exportData.prometheus_metrics = this.toPrometheus(
        exportData.dashboard_stats as Record<string, unknown>,
      );
    }
    return exportData;
  }

  export_statistics(
    format: TdfolStatisticsFormat = 'json',
    includeRawData = false,
  ): Record<string, unknown> {
    return this.exportStatistics(format, includeRawData);
  }

  getProfilerReport(): {
    warning?: string;
    suggestion?: string;
    latestRun?: TdfolProfileResult;
    historyCount: number;
  } {
    if (this.profilingHistory.length === 0) {
      return {
        warning: 'No profiling data available',
        suggestion: 'Run profileOperation first',
        historyCount: 0,
      };
    }
    return {
      latestRun: this.profilingHistory[this.profilingHistory.length - 1],
      historyCount: this.profilingHistory.length,
    };
  }

  get_profiler_report(): {
    warning?: string;
    suggestion?: string;
    latestRun?: TdfolProfileResult;
    historyCount: number;
  } {
    return this.getProfilerReport();
  }

  compareStrategies(
    options: Omit<TdfolProfileOperationOptions, 'strategy'> & {
      strategies?: TdfolPerformanceStrategyName[];
      runsPerStrategy?: number;
    },
  ): Record<string, unknown> {
    const strategies = options.strategies ?? ['forward', 'modal'];
    const results: Record<string, TdfolProfileResult['timing']> = {};
    for (const strategy of strategies) {
      results[strategy] = this.profileOperation({
        formula: options.formula,
        kbFormulas: options.kbFormulas,
        runs: options.runsPerStrategy ?? options.runs ?? 10,
        strategy,
      }).timing;
    }

    const entries = Object.entries(results);
    const best = entries.reduce((currentBest, candidate) =>
      candidate[1].meanTimeMs < currentBest[1].meanTimeMs ? candidate : currentBest,
    );
    const worst = entries.reduce((currentWorst, candidate) =>
      candidate[1].meanTimeMs > currentWorst[1].meanTimeMs ? candidate : currentWorst,
    );
    const speedup =
      worst[1].meanTimeMs === 0
        ? 1
        : worst[1].meanTimeMs / Math.max(best[1].meanTimeMs, Number.EPSILON);
    return {
      formula: options.formula,
      strategiesCompared: entries.length,
      runsPerStrategy: options.runsPerStrategy ?? options.runs ?? 10,
      results,
      bestStrategy: { name: best[0], ...best[1] },
      worstStrategy: { name: worst[0], ...worst[1] },
      speedup,
      recommendation: `Use '${best[0]}' strategy (${speedup.toFixed(1)}x faster than '${worst[0]}')`,
    };
  }

  compare_strategies(
    options: Omit<TdfolProfileOperationOptions, 'strategy'> & {
      strategies?: TdfolPerformanceStrategyName[];
      runsPerStrategy?: number;
    },
  ): Record<string, unknown> {
    return this.compareStrategies(options);
  }

  checkRegression(
    baseline: Record<string, number>,
    thresholdPercent = 10,
  ): Record<string, unknown> {
    const currentStats = this.collector.getStatistics();
    const timings = currentStats.timing as Record<string, TdfolStatisticalSummary | undefined>;
    const regressions = Object.entries(baseline).flatMap(([metric, baselineValue]) => {
      const currentValue = timings[metric]?.mean;
      if (
        currentValue === undefined ||
        currentValue <= baselineValue * (1 + thresholdPercent / 100)
      )
        return [];
      const regressionPercent = ((currentValue - baselineValue) / baselineValue) * 100;
      return [
        {
          metric,
          baseline: baselineValue,
          current: currentValue,
          regressionPercent,
          thresholdPercent,
          severity: regressionPercent > 20 ? 'critical' : 'warning',
        },
      ];
    });
    return {
      regressionsFound: regressions.length > 0,
      regressionCount: regressions.length,
      thresholdPercent,
      regressions,
      baselineMetrics: Object.keys(baseline).length,
      currentMetrics: Object.keys(timings).length,
      status: regressions.length === 0 ? 'All metrics within baseline threshold' : undefined,
    };
  }

  check_regression(
    baseline: Record<string, number>,
    thresholdPercent = 10,
  ): Record<string, unknown> {
    return this.checkRegression(baseline, thresholdPercent);
  }

  resetMetrics(): { success: true; clearedProofMetrics: number; clearedProfilingRuns: number } {
    const clearedProofMetrics = this.proofMetrics.length;
    const clearedProfilingRuns = this.profilingHistory.length;
    this.proofMetrics.length = 0;
    this.profilingHistory.length = 0;
    this.collector.reset();
    return { success: true, clearedProofMetrics, clearedProfilingRuns };
  }

  reset_metrics(): { success: true; clearedProofMetrics: number; clearedProfilingRuns: number } {
    return this.resetMetrics();
  }

  getDashboardStatistics(): {
    totalProofs: number;
    successRate: number;
    avgProofTimeMs: number;
    cacheHitRate: number;
    statusCounts: Record<string, number>;
  } {
    const totalProofs = this.proofMetrics.length;
    const statusCounts = this.proofMetrics.reduce<Record<string, number>>((counts, metric) => {
      counts[metric.status] = (counts[metric.status] ?? 0) + 1;
      return counts;
    }, {});
    const totalTime = this.proofMetrics.reduce((sum, metric) => sum + metric.timeMs, 0);
    return {
      totalProofs,
      successRate: totalProofs > 0 ? (statusCounts.proved ?? 0) / totalProofs : 0,
      avgProofTimeMs: totalProofs > 0 ? totalTime / totalProofs : 0,
      cacheHitRate: 0,
      statusCounts,
    };
  }

  get_dashboard_statistics(): ReturnType<TdfolPerformanceEngine['getDashboardStatistics']> {
    return this.getDashboardStatistics();
  }

  private createStrategies(
    strategy: TdfolPerformanceStrategyName,
  ): TdfolProverStrategy[] | undefined {
    if (strategy === 'forward') return [new TdfolForwardChainingStrategy()];
    if (strategy === 'modal') return [new TdfolModalTableauxStrategy()];
    return undefined;
  }

  private getUptime(): number {
    return (Date.now() - this.startedAt) / 1000;
  }

  private toHtmlString(
    summary: ReturnType<TdfolPerformanceEngine['getDashboardStatistics']>,
    history: TdfolProfileResult[],
  ): string {
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>TDFOL Performance</title></head><body><h1>TDFOL Performance</h1><script type="application/json" id="tdfol-performance-data">${escapeHtml(JSON.stringify({ summary, history }))}</script><p>Total proofs: ${summary.totalProofs}</p><p>Success rate: ${(summary.successRate * 100).toFixed(1)}%</p><p>Average time: ${summary.avgProofTimeMs.toFixed(3)}ms</p></body></html>`;
  }

  private toPrometheus(stats: Record<string, unknown>): string {
    return [
      `tdfol_total_proofs ${Number(stats.totalProofs ?? 0)}`,
      `tdfol_success_rate ${Number(stats.successRate ?? 0)}`,
      `tdfol_avg_proof_time_ms ${Number(stats.avgProofTimeMs ?? 0)}`,
      `tdfol_cache_hit_rate ${Number(stats.cacheHitRate ?? 0)}`,
    ].join('\n');
  }
}

export function createTdfolPerformanceEngine(
  collector?: TdfolMetricsCollector,
): TdfolPerformanceEngine {
  return new TdfolPerformanceEngine(collector);
}

function identifyTimingBottlenecks(
  operation: string,
  stats: TdfolStatisticalSummary,
): TdfolPerformanceBottleneck[] {
  if (stats.mean <= 1) return [];
  const severity =
    stats.mean > 1000 ? 'critical' : stats.mean > 100 ? 'high' : stats.mean > 10 ? 'medium' : 'low';
  return [
    {
      operation,
      timeMs: stats.mean,
      severity,
      recommendation:
        severity === 'low'
          ? 'Monitor if this appears in hot paths'
          : 'Inspect formula complexity, cacheability, and strategy selection',
    },
  ];
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
