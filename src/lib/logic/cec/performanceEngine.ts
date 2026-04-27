import type { ProofResult } from '../types';
import { analyzeCecExpression } from './analyzer';
import { parseCecExpression } from './parser';
import type { CecKnowledgeBase } from './prover';
import { calculateCecStats, getGlobalCecMetricsCollector, type CecMetricsCollector, type CecStatisticalSummary } from './performanceMetrics';
import { CecCachedForwardStrategy, CecForwardChainingStrategy, CecStrategySelector, type CecProverStrategy } from './strategies';

export type CecPerformanceStrategyName = 'auto' | 'forward' | 'cached';
export type CecStatisticsFormat = 'json' | 'prometheus';

export interface CecProfileOperationOptions {
  theorem: string;
  kbExpressions?: string[];
  runs?: number;
  strategy?: CecPerformanceStrategyName;
}

export interface CecProfileResult {
  theorem: string;
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
    bottlenecks: CecPerformanceBottleneck[];
  };
  metadata: {
    operation: string;
    latestStatus?: ProofResult['status'];
    theoremComplexity: number;
  };
}

export interface CecPerformanceBottleneck {
  operation: string;
  timeMs: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
}

export interface CecProofMetric {
  theorem: string;
  strategy: string;
  status: ProofResult['status'];
  timeMs: number;
  timestamp: number;
  stepCount: number;
  complexity: number;
}

export class CecPerformanceEngine {
  readonly proofMetrics: CecProofMetric[] = [];
  readonly profilingHistory: CecProfileResult[] = [];
  private readonly startedAt = Date.now();
  private readonly collector: CecMetricsCollector;

  constructor(collector: CecMetricsCollector = getGlobalCecMetricsCollector()) {
    this.collector = collector;
  }

  profileOperation(options: CecProfileOperationOptions): CecProfileResult {
    const runs = Math.max(1, options.runs ?? 10);
    const strategyName = options.strategy ?? 'auto';
    const theorem = parseCecExpression(options.theorem);
    const kb: CecKnowledgeBase = { axioms: (options.kbExpressions ?? []).map(parseCecExpression) };
    const selector = new CecStrategySelector({ strategies: this.createStrategies(strategyName) });
    const durations: number[] = [];
    const statuses: ProofResult['status'][] = [];
    const theoremComplexity = analyzeCecExpression(theorem).nodeCount;

    for (let index = 0; index < runs; index += 1) {
      const startedAt = nowMs();
      const result = selector.proveWithSelectedStrategy(theorem, kb);
      const durationMs = nowMs() - startedAt;
      durations.push(durationMs);
      statuses.push(result.status);
      this.collector.recordTiming(`cec.profile.${strategyName}`, durationMs, { theorem: options.theorem, run: index + 1 });
      this.collector.recordHistogram('cec.profile.steps', result.steps.length);
      this.proofMetrics.push({
        theorem: options.theorem,
        strategy: strategyName,
        status: result.status,
        timeMs: durationMs,
        timestamp: Date.now(),
        stepCount: result.steps.length,
        complexity: theoremComplexity,
      });
    }

    const stats = calculateCecStats(durations);
    const profile: CecProfileResult = {
      theorem: options.theorem,
      runs,
      strategy: strategyName,
      kbSize: options.kbExpressions?.length ?? 0,
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
        bottlenecks: identifyTimingBottlenecks(`cec.profile.${strategyName}`, stats),
      },
      metadata: {
        operation: 'profile_operation',
        latestStatus: statuses.at(-1),
        theoremComplexity,
      },
    };
    this.profilingHistory.push(profile);
    return profile;
  }

  getMetrics(): Record<string, unknown> {
    const collectorStats = this.collector.getStatistics();
    return {
      dashboardStats: this.getDashboardStatistics(),
      collectorStats,
      collectorSummary: {
        timingOperations: Object.keys((collectorStats.timing as Record<string, unknown>) ?? {}).length,
        memoryOperations: Object.keys((collectorStats.memory as Record<string, unknown>) ?? {}).length,
        counters: Object.keys((collectorStats.counters as Record<string, unknown>) ?? {}).length,
        gauges: Object.keys((collectorStats.gauges as Record<string, unknown>) ?? {}).length,
        histograms: Object.keys((collectorStats.histograms as Record<string, unknown>) ?? {}).length,
      },
      metadata: {
        proofsRecorded: this.proofMetrics.length,
        uptimeSeconds: this.getUptime(),
      },
    };
  }

  getDashboardStatistics(): {
    totalProofs: number;
    successRate: number;
    avgProofTimeMs: number;
    avgStepCount: number;
    avgComplexity: number;
    statusCounts: Record<string, number>;
    strategyCounts: Record<string, number>;
  } {
    const totalProofs = this.proofMetrics.length;
    const statusCounts = this.proofMetrics.reduce<Record<string, number>>((counts, metric) => {
      counts[metric.status] = (counts[metric.status] ?? 0) + 1;
      return counts;
    }, {});
    const strategyCounts = this.proofMetrics.reduce<Record<string, number>>((counts, metric) => {
      counts[metric.strategy] = (counts[metric.strategy] ?? 0) + 1;
      return counts;
    }, {});
    const totalTime = this.proofMetrics.reduce((sum, metric) => sum + metric.timeMs, 0);
    const totalSteps = this.proofMetrics.reduce((sum, metric) => sum + metric.stepCount, 0);
    const totalComplexity = this.proofMetrics.reduce((sum, metric) => sum + metric.complexity, 0);
    return {
      totalProofs,
      successRate: totalProofs > 0 ? (statusCounts.proved ?? 0) / totalProofs : 0,
      avgProofTimeMs: totalProofs > 0 ? totalTime / totalProofs : 0,
      avgStepCount: totalProofs > 0 ? totalSteps / totalProofs : 0,
      avgComplexity: totalProofs > 0 ? totalComplexity / totalProofs : 0,
      statusCounts,
      strategyCounts,
    };
  }

  generateDashboard(options: { includeProfiling?: boolean } = {}): { success: true; htmlString: string; metricsCount: number; summary: ReturnType<CecPerformanceEngine['getDashboardStatistics']>; profilingHistory?: CecProfileResult[] } {
    const summary = this.getDashboardStatistics();
    return {
      success: true,
      htmlString: this.toHtmlString(summary, options.includeProfiling ? this.profilingHistory.slice(-10) : []),
      metricsCount: this.proofMetrics.length,
      summary,
      profilingHistory: options.includeProfiling ? this.profilingHistory.slice(-10) : undefined,
    };
  }

  exportStatistics(format: CecStatisticsFormat = 'json', includeRawData = false): Record<string, unknown> {
    const exportData: Record<string, unknown> = {
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
      exportData.prometheus_metrics = this.toPrometheus(exportData.dashboard_stats as Record<string, unknown>);
    }
    return exportData;
  }

  compareStrategies(options: Omit<CecProfileOperationOptions, 'strategy'> & { strategies?: CecPerformanceStrategyName[]; runsPerStrategy?: number }): Record<string, unknown> {
    const strategies = options.strategies ?? ['forward', 'cached'];
    const results: Record<string, CecProfileResult['timing']> = {};
    for (const strategy of strategies) {
      results[strategy] = this.profileOperation({
        theorem: options.theorem,
        kbExpressions: options.kbExpressions,
        runs: options.runsPerStrategy ?? options.runs ?? 10,
        strategy,
      }).timing;
    }

    const entries = Object.entries(results);
    const best = entries.reduce((currentBest, candidate) => candidate[1].meanTimeMs < currentBest[1].meanTimeMs ? candidate : currentBest);
    const worst = entries.reduce((currentWorst, candidate) => candidate[1].meanTimeMs > currentWorst[1].meanTimeMs ? candidate : currentWorst);
    const speedup = worst[1].meanTimeMs === 0 ? 1 : worst[1].meanTimeMs / Math.max(best[1].meanTimeMs, Number.EPSILON);
    return {
      theorem: options.theorem,
      strategiesCompared: entries.length,
      runsPerStrategy: options.runsPerStrategy ?? options.runs ?? 10,
      results,
      bestStrategy: { name: best[0], ...best[1] },
      worstStrategy: { name: worst[0], ...worst[1] },
      speedup,
      recommendation: `Use '${best[0]}' strategy (${speedup.toFixed(1)}x faster than '${worst[0]}')`,
    };
  }

  checkRegression(baseline: Record<string, number>, thresholdPercent = 10): Record<string, unknown> {
    const currentStats = this.collector.getStatistics();
    const timings = currentStats.timing as Record<string, CecStatisticalSummary | undefined>;
    const regressions = Object.entries(baseline).flatMap(([metric, baselineValue]) => {
      const currentValue = timings[metric]?.mean;
      if (currentValue === undefined || currentValue <= baselineValue * (1 + thresholdPercent / 100)) return [];
      const regressionPercent = ((currentValue - baselineValue) / baselineValue) * 100;
      return [{
        metric,
        baseline: baselineValue,
        current: currentValue,
        regressionPercent,
        thresholdPercent,
        severity: regressionPercent > 20 ? 'critical' : 'warning',
      }];
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

  getProfilerReport(): { warning?: string; suggestion?: string; latestRun?: CecProfileResult; historyCount: number } {
    if (this.profilingHistory.length === 0) {
      return { warning: 'No profiling data available', suggestion: 'Run profileOperation first', historyCount: 0 };
    }
    return {
      latestRun: this.profilingHistory[this.profilingHistory.length - 1],
      historyCount: this.profilingHistory.length,
    };
  }

  resetMetrics(): { success: true; clearedProofMetrics: number; clearedProfilingRuns: number } {
    const clearedProofMetrics = this.proofMetrics.length;
    const clearedProfilingRuns = this.profilingHistory.length;
    this.proofMetrics.length = 0;
    this.profilingHistory.length = 0;
    this.collector.reset();
    return { success: true, clearedProofMetrics, clearedProfilingRuns };
  }

  private createStrategies(strategy: CecPerformanceStrategyName): CecProverStrategy[] | undefined {
    if (strategy === 'forward') return [new CecForwardChainingStrategy()];
    if (strategy === 'cached') return [new CecCachedForwardStrategy()];
    return undefined;
  }

  private getUptime(): number {
    return (Date.now() - this.startedAt) / 1000;
  }

  private toHtmlString(summary: ReturnType<CecPerformanceEngine['getDashboardStatistics']>, history: CecProfileResult[]): string {
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>CEC Performance</title></head><body><h1>CEC Performance</h1><script type="application/json" id="cec-performance-data">${escapeHtml(JSON.stringify({ summary, history }))}</script><p>Total proofs: ${summary.totalProofs}</p><p>Success rate: ${(summary.successRate * 100).toFixed(1)}%</p><p>Average time: ${summary.avgProofTimeMs.toFixed(3)}ms</p></body></html>`;
  }

  private toPrometheus(stats: Record<string, unknown>): string {
    return [
      `cec_total_proofs ${Number(stats.totalProofs ?? 0)}`,
      `cec_success_rate ${Number(stats.successRate ?? 0)}`,
      `cec_avg_proof_time_ms ${Number(stats.avgProofTimeMs ?? 0)}`,
      `cec_avg_step_count ${Number(stats.avgStepCount ?? 0)}`,
    ].join('\n');
  }
}

export function createCecPerformanceEngine(collector?: CecMetricsCollector): CecPerformanceEngine {
  return new CecPerformanceEngine(collector);
}

function identifyTimingBottlenecks(operation: string, stats: CecStatisticalSummary): CecPerformanceBottleneck[] {
  if (stats.mean <= 1) return [];
  const severity = stats.mean > 1000 ? 'critical' : stats.mean > 100 ? 'high' : stats.mean > 10 ? 'medium' : 'low';
  return [{
    operation,
    timeMs: stats.mean,
    severity,
    recommendation: severity === 'low' ? 'Monitor if this appears in hot paths' : 'Inspect CEC expression complexity, cacheability, and strategy selection',
  }];
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function' ? performance.now() : Date.now();
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
