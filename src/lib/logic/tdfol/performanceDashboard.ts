import type { ProofResult } from '../types';

export type TdfolDashboardMetricType =
  | 'proof_time'
  | 'cache_hit'
  | 'cache_miss'
  | 'memory_usage'
  | 'formula_complexity'
  | 'strategy_selection'
  | 'success'
  | 'failure'
  | 'zkp_verification';

export interface TdfolProofMetricsInput {
  formula: string;
  proofTimeMs: number;
  success: boolean;
  method?: string;
  strategy?: string;
  cacheHit?: boolean;
  memoryUsageMb?: number;
  numSteps?: number;
  formulaComplexity?: number;
  formulaType?: string;
  metadata?: Record<string, unknown>;
  timestamp?: number;
}

export interface TdfolProofMetrics {
  timestamp: number;
  datetime: string;
  formula: string;
  complexity: number;
  proofTimeMs: number;
  success: boolean;
  method: string;
  strategy: string;
  cacheHit: boolean;
  memoryMb: number;
  numSteps: number;
  formulaType: string;
  metadata: Record<string, unknown>;
}

export interface TdfolTimeSeriesMetric {
  timestamp: number;
  datetime: string;
  metric: string;
  value: number;
  tags: Record<string, string>;
}

export interface TdfolAggregatedDashboardStats {
  totalProofs: number;
  successfulProofs: number;
  failedProofs: number;
  successRate: number;
  cacheHits: number;
  cacheMisses: number;
  cacheHitRate: number;
  avgSpeedupFromCache: number;
  timing: {
    totalMs: number;
    minMs: number;
    maxMs: number;
    avgMs: number;
    medianMs: number;
    p95Ms: number;
    p99Ms: number;
  };
  formulas: {
    avgComplexity: number;
    avgSteps: number;
  };
  memory: {
    avgMb: number;
    maxMb: number;
  };
  strategies: {
    counts: Record<string, number>;
    successRates: Record<string, number>;
    avgTimesMs: Record<string, number>;
  };
  formulaTypes: {
    counts: Record<string, number>;
    successRates: Record<string, number>;
  };
}

export class TdfolPerformanceDashboard {
  readonly proofMetrics: TdfolProofMetrics[] = [];
  readonly timeseriesMetrics: TdfolTimeSeriesMetric[] = [];
  private startedAt = Date.now();
  private statsCache?: TdfolAggregatedDashboardStats;

  recordProof(input: TdfolProofMetricsInput | ProofResult, metadata: Record<string, unknown> = {}): void {
    const metric = isProofResult(input) ? proofResultToMetric(input, metadata) : inputToMetric(input);
    this.proofMetrics.push(metric);
    this.statsCache = undefined;
    this.recordMetric('proof_time_ms', metric.proofTimeMs, { strategy: metric.strategy, success: String(metric.success) });
    this.recordMetric(metric.cacheHit ? 'cache_hit' : 'cache_miss', 1, { strategy: metric.strategy });
  }

  recordMetric(metricName: string, value: number, tags: Record<string, string> = {}): void {
    const timestamp = Date.now();
    this.timeseriesMetrics.push({
      timestamp,
      datetime: new Date(timestamp).toISOString(),
      metric: metricName,
      value,
      tags,
    });
  }

  getStatistics(): TdfolAggregatedDashboardStats {
    this.statsCache ??= this.calculateStatistics();
    return this.statsCache;
  }

  compareStrategies(): { strategies: Record<string, Record<string, number>> } {
    const grouped = groupBy(this.proofMetrics, (metric) => metric.strategy);
    const strategies: Record<string, Record<string, number>> = {};
    for (const [strategy, metrics] of Object.entries(grouped)) {
      const times = metrics.map((metric) => metric.proofTimeMs);
      strategies[strategy] = {
        count: metrics.length,
        successRate: ratio(metrics.filter((metric) => metric.success).length, metrics.length),
        cacheHitRate: ratio(metrics.filter((metric) => metric.cacheHit).length, metrics.length),
        avgTimeMs: mean(times),
        medianTimeMs: median(times),
        minTimeMs: times.length ? Math.min(...times) : 0,
        maxTimeMs: times.length ? Math.max(...times) : 0,
        avgComplexity: mean(metrics.map((metric) => metric.complexity)),
      };
    }
    return { strategies };
  }

  exportJson(): Record<string, unknown> {
    return {
      metadata: {
        dashboardStartTime: this.startedAt,
        dashboardStartDatetime: new Date(this.startedAt).toISOString(),
        exportTime: Date.now(),
        exportDatetime: new Date().toISOString(),
        totalProofs: this.proofMetrics.length,
        totalMetrics: this.timeseriesMetrics.length,
      },
      statistics: this.getStatistics(),
      strategyComparison: this.compareStrategies(),
      proofMetrics: this.proofMetrics,
      timeseriesMetrics: this.timeseriesMetrics,
    };
  }

  toHtmlString(): string {
    const data = this.exportJson();
    const stats = this.getStatistics();
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>TDFOL Performance Dashboard</title><style>body{font-family:system-ui,sans-serif;margin:24px;color:#222}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.card{border:1px solid #bbb;border-radius:8px;padding:12px}.value{font-size:1.6rem;font-weight:700}</style></head><body><h1>TDFOL Performance Dashboard</h1><script type="application/json" id="tdfol-dashboard-data">${escapeHtml(JSON.stringify(data))}</script><section class="grid"><div class="card"><div>Total proofs</div><div class="value">${stats.totalProofs}</div></div><div class="card"><div>Success rate</div><div class="value">${(stats.successRate * 100).toFixed(1)}%</div></div><div class="card"><div>Cache hit rate</div><div class="value">${(stats.cacheHitRate * 100).toFixed(1)}%</div></div><div class="card"><div>Avg proof time</div><div class="value">${stats.timing.avgMs.toFixed(3)}ms</div></div></section></body></html>`;
  }

  clear(): void {
    this.proofMetrics.length = 0;
    this.timeseriesMetrics.length = 0;
    this.startedAt = Date.now();
    this.statsCache = undefined;
  }

  getUptime(): number {
    return (Date.now() - this.startedAt) / 1000;
  }

  calculateComplexity(formula: string): number {
    let depth = 0;
    let maxDepth = 0;
    for (const char of formula) {
      if (char === '(') {
        depth += 1;
        maxDepth = Math.max(maxDepth, depth);
      } else if (char === ')') {
        depth = Math.max(0, depth - 1);
      }
    }
    return maxDepth;
  }

  determineFormulaType(formula: string): string {
    if (/always|eventually|□|◊|next/i.test(formula)) return 'temporal';
    if (/(?:^|[^a-zA-Z])O\s*\(|Obligatory|Permitted|Forbidden/.test(formula)) return 'deontic';
    if (/Necessary|Possible/.test(formula)) return 'modal';
    return 'propositional';
  }

  private calculateStatistics(): TdfolAggregatedDashboardStats {
    const metrics = this.proofMetrics;
    const times = metrics.map((metric) => metric.proofTimeMs);
    const complexities = metrics.map((metric) => metric.complexity);
    const steps = metrics.map((metric) => metric.numSteps);
    const memory = metrics.map((metric) => metric.memoryMb);
    const cacheHits = metrics.filter((metric) => metric.cacheHit);
    const cacheMisses = metrics.filter((metric) => !metric.cacheHit);
    const strategyGroups = groupBy(metrics, (metric) => metric.strategy);
    const typeGroups = groupBy(metrics, (metric) => metric.formulaType);

    return {
      totalProofs: metrics.length,
      successfulProofs: metrics.filter((metric) => metric.success).length,
      failedProofs: metrics.filter((metric) => !metric.success).length,
      successRate: ratio(metrics.filter((metric) => metric.success).length, metrics.length),
      cacheHits: cacheHits.length,
      cacheMisses: cacheMisses.length,
      cacheHitRate: ratio(cacheHits.length, metrics.length),
      avgSpeedupFromCache: cacheHits.length && cacheMisses.length ? mean(cacheMisses.map((m) => m.proofTimeMs)) / Math.max(mean(cacheHits.map((m) => m.proofTimeMs)), Number.EPSILON) : 0,
      timing: {
        totalMs: sum(times),
        minMs: times.length ? Math.min(...times) : 0,
        maxMs: times.length ? Math.max(...times) : 0,
        avgMs: mean(times),
        medianMs: median(times),
        p95Ms: percentile(times, 95),
        p99Ms: percentile(times, 99),
      },
      formulas: {
        avgComplexity: mean(complexities),
        avgSteps: mean(steps),
      },
      memory: {
        avgMb: mean(memory),
        maxMb: memory.length ? Math.max(...memory) : 0,
      },
      strategies: summarizeGroups(strategyGroups),
      formulaTypes: {
        counts: countGroups(typeGroups),
        successRates: successRates(typeGroups),
      },
    };
  }
}

export function createTdfolProofMetrics(input: TdfolProofMetricsInput): TdfolProofMetrics {
  return inputToMetric(input);
}

function inputToMetric(input: TdfolProofMetricsInput): TdfolProofMetrics {
  const timestamp = input.timestamp ?? Date.now();
  const dashboard = new TdfolPerformanceDashboard();
  return {
    timestamp,
    datetime: new Date(timestamp).toISOString(),
    formula: input.formula,
    complexity: input.formulaComplexity ?? dashboard.calculateComplexity(input.formula),
    proofTimeMs: input.proofTimeMs,
    success: input.success,
    method: input.method ?? 'unknown',
    strategy: input.strategy ?? 'unknown',
    cacheHit: input.cacheHit ?? false,
    memoryMb: input.memoryUsageMb ?? 0,
    numSteps: input.numSteps ?? 0,
    formulaType: input.formulaType ?? dashboard.determineFormulaType(input.formula),
    metadata: input.metadata ?? {},
  };
}

function proofResultToMetric(result: ProofResult, metadata: Record<string, unknown>): TdfolProofMetrics {
  return inputToMetric({
    formula: result.theorem,
    proofTimeMs: result.timeMs ?? Number(metadata.proofTimeMs ?? 0),
    success: result.status === 'proved',
    method: result.method,
    strategy: String(metadata.strategy ?? result.method ?? 'unknown'),
    cacheHit: Boolean(metadata.cacheHit),
    memoryUsageMb: Number(metadata.memoryMb ?? 0),
    numSteps: result.steps.length,
    metadata,
  });
}

function isProofResult(value: TdfolProofMetricsInput | ProofResult): value is ProofResult {
  return 'theorem' in value && 'status' in value && 'steps' in value;
}

function groupBy<T>(values: T[], key: (value: T) => string): Record<string, T[]> {
  return values.reduce<Record<string, T[]>>((groups, value) => {
    const group = key(value);
    groups[group] = groups[group] ?? [];
    groups[group].push(value);
    return groups;
  }, {});
}

function summarizeGroups(groups: Record<string, TdfolProofMetrics[]>): TdfolAggregatedDashboardStats['strategies'] {
  const counts = countGroups(groups);
  const success = successRates(groups);
  const avgTimesMs = Object.fromEntries(Object.entries(groups).map(([name, metrics]) => [name, mean(metrics.map((metric) => metric.proofTimeMs))]));
  return { counts, successRates: success, avgTimesMs };
}

function countGroups(groups: Record<string, unknown[]>): Record<string, number> {
  return Object.fromEntries(Object.entries(groups).map(([name, values]) => [name, values.length]));
}

function successRates(groups: Record<string, TdfolProofMetrics[]>): Record<string, number> {
  return Object.fromEntries(Object.entries(groups).map(([name, metrics]) => [name, ratio(metrics.filter((metric) => metric.success).length, metrics.length)]));
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function mean(values: number[]): number {
  return values.length ? sum(values) / values.length : 0;
}

function median(values: number[]): number {
  return percentile(values, 50);
}

function percentile(values: number[], p: number): number {
  if (!values.length) return 0;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[index];
}

function ratio(numerator: number, denominator: number): number {
  return denominator > 0 ? numerator / denominator : 0;
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
