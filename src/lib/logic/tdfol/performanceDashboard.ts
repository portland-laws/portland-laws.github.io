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

export interface TdfolPerformanceDashboardOptions {
  now?: () => number;
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

export interface TdfolTimeSeriesSummary {
  count: number;
  total: number;
  min: number;
  max: number;
  avg: number;
  latestValue: number;
  latestTimestamp: number;
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

export type TdfolPerformanceDashboardDemoFormat = 'summary' | 'json' | 'html' | 'snapshot';

export interface TdfolPerformanceDashboardDemoOptions {
  formats?: TdfolPerformanceDashboardDemoFormat[];
}

export interface TdfolPerformanceDashboardDemo {
  id: string;
  title: string;
  description: string;
  dashboard: Record<string, unknown>;
  statistics: TdfolAggregatedDashboardStats;
  strategyComparison: { strategies: Record<string, Record<string, number>> };
  rendered: Partial<Record<TdfolPerformanceDashboardDemoFormat, string>>;
}

export const TDFOL_PERFORMANCE_DASHBOARD_METADATA = {
  sourcePythonModule: 'logic/TDFOL/performance_dashboard.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
} as const;

export class TdfolPerformanceDashboard {
  readonly proofMetrics: TdfolProofMetrics[] = [];
  readonly timeseriesMetrics: TdfolTimeSeriesMetric[] = [];
  private readonly now: () => number;
  private startedAt: number;
  private statsCache?: TdfolAggregatedDashboardStats;

  constructor(options: TdfolPerformanceDashboardOptions = {}) {
    this.now = options.now ?? Date.now;
    this.startedAt = this.now();
  }

  recordProof(
    input: TdfolProofMetricsInput | ProofResult,
    metadata: Record<string, unknown> = {},
  ): void {
    const metric = isProofResult(input)
      ? proofResultToMetric(input, metadata)
      : inputToMetric(input);
    this.proofMetrics.push(metric);
    this.statsCache = undefined;
    this.recordMetric('proof_time_ms', metric.proofTimeMs, {
      strategy: metric.strategy,
      success: String(metric.success),
    });
    this.recordMetric(metric.cacheHit ? 'cache_hit' : 'cache_miss', 1, {
      strategy: metric.strategy,
    });
  }

  record_proof(
    input: TdfolProofMetricsInput | ProofResult,
    metadata: Record<string, unknown> = {},
  ): void {
    this.recordProof(input, metadata);
  }

  recordMetric(metricName: string, value: number, tags: Record<string, string> = {}): void {
    const timestamp = this.now();
    this.timeseriesMetrics.push({
      timestamp,
      datetime: new Date(timestamp).toISOString(),
      metric: metricName,
      value,
      tags,
    });
  }

  record_metric(metricName: string, value: number, tags: Record<string, string> = {}): void {
    this.recordMetric(metricName, value, tags);
  }

  getStatistics(): TdfolAggregatedDashboardStats {
    this.statsCache ??= this.calculateStatistics();
    return this.statsCache;
  }

  get_statistics(): TdfolAggregatedDashboardStats {
    return this.getStatistics();
  }

  getTimeSeriesSummary(metricName?: string): Record<string, TdfolTimeSeriesSummary> {
    const metrics =
      metricName === undefined
        ? this.timeseriesMetrics
        : this.timeseriesMetrics.filter((metric) => metric.metric === metricName);
    const grouped = groupBy(metrics, (metric) => metric.metric);
    return Object.fromEntries(
      Object.entries(grouped).map(([name, values]) => {
        const metricValues = values.map((metric) => metric.value);
        const latest = values.reduce((current, next) =>
          next.timestamp >= current.timestamp ? next : current,
        );
        return [
          name,
          {
            count: values.length,
            total: sum(metricValues),
            min: metricValues.length ? Math.min(...metricValues) : 0,
            max: metricValues.length ? Math.max(...metricValues) : 0,
            avg: mean(metricValues),
            latestValue: latest.value,
            latestTimestamp: latest.timestamp,
          },
        ];
      }),
    );
  }

  get_timeseries_summary(metricName?: string): Record<string, TdfolTimeSeriesSummary> {
    return this.getTimeSeriesSummary(metricName);
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

  compare_strategies(): { strategies: Record<string, Record<string, number>> } {
    return this.compareStrategies();
  }

  exportJson(): Record<string, unknown> {
    const exportTime = this.now();
    return {
      metadata: {
        sourcePythonModule: TDFOL_PERFORMANCE_DASHBOARD_METADATA.sourcePythonModule,
        browserNative: TDFOL_PERFORMANCE_DASHBOARD_METADATA.browserNative,
        serverCallsAllowed: TDFOL_PERFORMANCE_DASHBOARD_METADATA.serverCallsAllowed,
        pythonRuntimeRequired: TDFOL_PERFORMANCE_DASHBOARD_METADATA.pythonRuntimeRequired,
        dashboardStartTime: this.startedAt,
        dashboardStartDatetime: new Date(this.startedAt).toISOString(),
        exportTime,
        exportDatetime: new Date(exportTime).toISOString(),
        totalProofs: this.proofMetrics.length,
        totalMetrics: this.timeseriesMetrics.length,
      },
      statistics: this.getStatistics(),
      strategyComparison: this.compareStrategies(),
      timeseriesSummary: this.getTimeSeriesSummary(),
      proofMetrics: this.proofMetrics,
      timeseriesMetrics: this.timeseriesMetrics,
    };
  }

  export_json(): Record<string, unknown> {
    return this.exportJson();
  }

  exportPythonCompatibleJson(): Record<string, unknown> {
    const json = this.exportJson();
    return {
      metadata: {
        ...(json.metadata as Record<string, unknown>),
        source_python_module: TDFOL_PERFORMANCE_DASHBOARD_METADATA.sourcePythonModule,
        browser_native: true,
        server_calls_allowed: false,
        python_runtime_required: false,
      },
      statistics: json.statistics,
      strategy_comparison: json.strategyComparison,
      timeseries_summary: json.timeseriesSummary,
      proof_metrics: json.proofMetrics,
      timeseries_metrics: json.timeseriesMetrics,
    };
  }

  export_python_compatible_json(): Record<string, unknown> {
    return this.exportPythonCompatibleJson();
  }

  toHtmlString(): string {
    const data = this.exportJson();
    const stats = this.getStatistics();
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>TDFOL Performance Dashboard</title><style>body{font-family:system-ui,sans-serif;margin:24px;color:#222}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.card{border:1px solid #bbb;border-radius:8px;padding:12px}.value{font-size:1.6rem;font-weight:700}</style></head><body><h1>TDFOL Performance Dashboard</h1><script type="application/json" id="tdfol-dashboard-data">${escapeHtml(JSON.stringify(data))}</script><section class="grid"><div class="card"><div>Total proofs</div><div class="value">${stats.totalProofs}</div></div><div class="card"><div>Success rate</div><div class="value">${(stats.successRate * 100).toFixed(1)}%</div></div><div class="card"><div>Cache hit rate</div><div class="value">${(stats.cacheHitRate * 100).toFixed(1)}%</div></div><div class="card"><div>Avg proof time</div><div class="value">${stats.timing.avgMs.toFixed(3)}ms</div></div></section></body></html>`;
  }

  to_html_string(): string {
    return this.toHtmlString();
  }

  clear(): void {
    this.proofMetrics.length = 0;
    this.timeseriesMetrics.length = 0;
    this.startedAt = this.now();
    this.statsCache = undefined;
  }

  clear_metrics(): void {
    this.clear();
  }

  getUptime(): number {
    return (this.now() - this.startedAt) / 1000;
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
      avgSpeedupFromCache:
        cacheHits.length && cacheMisses.length
          ? mean(cacheMisses.map((m) => m.proofTimeMs)) /
            Math.max(mean(cacheHits.map((m) => m.proofTimeMs)), Number.EPSILON)
          : 0,
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

export function createTdfolPerformanceDashboardDemo(
  options: TdfolPerformanceDashboardDemoOptions = {},
): TdfolPerformanceDashboardDemo {
  const formats = options.formats ?? ['summary', 'json', 'html', 'snapshot'];
  const baseTime = Date.UTC(2026, 0, 1, 12, 0, 0);
  let tick = 0;
  const dashboard = new TdfolPerformanceDashboard({
    now: () => baseTime + tick++ * 1000,
  });

  for (const proof of buildDemoProofs(baseTime)) {
    dashboard.recordProof(proof);
  }
  dashboard.recordMetric('dashboard_render_ms', 1.25, { renderer: 'browser-html' });

  const dashboardJson = dashboard.exportJson();
  const statistics = dashboard.getStatistics();
  const strategyComparison = dashboard.compareStrategies();
  const rendered = Object.fromEntries(
    formats.map((format): [TdfolPerformanceDashboardDemoFormat, string] => [
      format,
      renderDemoFormat(format, dashboard, dashboardJson, statistics, strategyComparison),
    ]),
  ) as Partial<Record<TdfolPerformanceDashboardDemoFormat, string>>;

  return {
    id: 'tdfol-performance-dashboard-demo',
    title: 'TDFOL performance dashboard demo',
    description:
      'Deterministic browser-native port of the Python demonstration module using local proof metrics, aggregate statistics, strategy comparison, JSON export, and self-contained HTML.',
    dashboard: dashboardJson,
    statistics,
    strategyComparison,
    rendered,
  };
}

function buildDemoProofs(baseTime: number): TdfolProofMetricsInput[] {
  return [
    {
      formula: 'always(O(Comply(alice)) -> eventually(Audit(alice)))',
      proofTimeMs: 18,
      success: true,
      method: 'tableaux',
      strategy: 'temporal-deontic',
      cacheHit: false,
      memoryUsageMb: 7,
      numSteps: 6,
      formulaType: 'temporal_deontic',
      timestamp: baseTime + 100,
    },
    {
      formula: 'O(Comply(alice))',
      proofTimeMs: 4,
      success: true,
      method: 'direct',
      strategy: 'direct',
      cacheHit: true,
      memoryUsageMb: 3,
      numSteps: 2,
      timestamp: baseTime + 200,
    },
    {
      formula: 'Necessary(Permitted(bob))',
      proofTimeMs: 11,
      success: false,
      method: 'modal-tableaux',
      strategy: 'modal',
      cacheHit: false,
      memoryUsageMb: 5,
      numSteps: 5,
      formulaType: 'modal',
      timestamp: baseTime + 300,
    },
  ];
}

function renderDemoFormat(
  format: TdfolPerformanceDashboardDemoFormat,
  dashboard: TdfolPerformanceDashboard,
  dashboardJson: Record<string, unknown>,
  statistics: TdfolAggregatedDashboardStats,
  strategyComparison: { strategies: Record<string, Record<string, number>> },
): string {
  if (format === 'html') return dashboard.toHtmlString();
  if (format === 'json') return JSON.stringify(dashboardJson, null, 2);
  if (format === 'snapshot') {
    return JSON.stringify(
      {
        total_proofs: statistics.totalProofs,
        success_rate: statistics.successRate,
        cache_hit_rate: statistics.cacheHitRate,
        avg_time_ms: statistics.timing.avgMs,
        strategies: Object.keys(strategyComparison.strategies).sort(),
        formula_types: Object.keys(statistics.formulaTypes.counts).sort(),
      },
      null,
      2,
    );
  }
  return [
    'TDFOL Performance Dashboard Demo',
    `proofs=${statistics.totalProofs}`,
    `success_rate=${statistics.successRate.toFixed(3)}`,
    `cache_hit_rate=${statistics.cacheHitRate.toFixed(3)}`,
    `avg_time_ms=${statistics.timing.avgMs.toFixed(3)}`,
  ].join('\n');
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

function proofResultToMetric(
  result: ProofResult,
  metadata: Record<string, unknown>,
): TdfolProofMetrics {
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

function summarizeGroups(
  groups: Record<string, TdfolProofMetrics[]>,
): TdfolAggregatedDashboardStats['strategies'] {
  const counts = countGroups(groups);
  const success = successRates(groups);
  const avgTimesMs = Object.fromEntries(
    Object.entries(groups).map(([name, metrics]) => [
      name,
      mean(metrics.map((metric) => metric.proofTimeMs)),
    ]),
  );
  return { counts, successRates: success, avgTimesMs };
}

function countGroups(groups: Record<string, unknown[]>): Record<string, number> {
  return Object.fromEntries(Object.entries(groups).map(([name, values]) => [name, values.length]));
}

function successRates(groups: Record<string, TdfolProofMetrics[]>): Record<string, number> {
  return Object.fromEntries(
    Object.entries(groups).map(([name, metrics]) => [
      name,
      ratio(metrics.filter((metric) => metric.success).length, metrics.length),
    ]),
  );
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
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
