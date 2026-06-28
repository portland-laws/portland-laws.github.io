export interface TdfolTimingResult {
  name: string;
  durationMs: number;
  timestamp: number;
  metadata: Record<string, unknown>;
}

export interface TdfolMemoryResult {
  name: string;
  currentMb: number;
  peakMb: number;
  deltaMb: number;
  timestamp: number;
  metadata: Record<string, unknown>;
}

export interface TdfolStatisticalSummary {
  count: number;
  sum: number;
  mean: number;
  median: number;
  stdDev: number;
  min: number;
  max: number;
  p50: number;
  p95: number;
  p99: number;
  p999: number;
}

export interface TdfolMemorySample {
  currentMb: number;
  peakMb?: number;
}

export interface TdfolMetricsCollectorOptions {
  maxLength?: number;
  now?: () => number;
  wallClock?: () => number;
  memorySampler?: () => TdfolMemorySample | undefined;
}

export const TDFOL_PERFORMANCE_METRICS_METADATA = {
  sourcePythonModule: 'logic/TDFOL/performance_metrics.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
} as const;

export class TdfolMetricsCollector {
  readonly timings = new Map<string, number[]>();
  readonly timingResults: TdfolTimingResult[] = [];
  readonly memorySnapshots = new Map<
    string,
    Array<{ currentMb: number; peakMb: number; deltaMb: number }>
  >();
  readonly memoryResults: TdfolMemoryResult[] = [];
  readonly counters = new Map<string, number>();
  readonly gauges = new Map<string, number>();
  readonly histograms = new Map<string, number[]>();

  private readonly timerStarts = new Map<string, number>();
  private readonly now: () => number;
  private readonly wallClock: () => number;
  private readonly memorySampler?: () => TdfolMemorySample | undefined;
  readonly maxLength: number;

  constructor(options: number | TdfolMetricsCollectorOptions = {}) {
    const normalized = typeof options === 'number' ? { maxLength: options } : options;
    this.maxLength = normalized.maxLength ?? 10000;
    this.now = normalized.now ?? nowMs;
    this.wallClock = normalized.wallClock ?? Date.now;
    this.memorySampler = normalized.memorySampler;
  }

  startTimer(name: string): void {
    this.timerStarts.set(name, this.now());
  }

  stopTimer(name: string, metadata: Record<string, unknown> = {}): number {
    const startedAt = this.timerStarts.get(name);
    if (startedAt === undefined) throw new Error(`Timer '${name}' was not started`);
    this.timerStarts.delete(name);
    const durationMs = this.now() - startedAt;
    this.recordTiming(name, durationMs, metadata);
    return durationMs;
  }

  time<T>(name: string, fn: () => T, metadata: Record<string, unknown> = {}): T {
    const startedAt = this.now();
    try {
      return fn();
    } finally {
      this.recordTiming(name, this.now() - startedAt, metadata);
    }
  }

  async timeAsync<T>(
    name: string,
    fn: () => Promise<T>,
    metadata: Record<string, unknown> = {},
  ): Promise<T> {
    const startedAt = this.now();
    try {
      return await fn();
    } finally {
      this.recordTiming(name, this.now() - startedAt, metadata);
    }
  }

  recordTiming(name: string, durationMs: number, metadata: Record<string, unknown> = {}): void {
    pushBounded(this.timings, name, durationMs, this.maxLength);
    this.timingResults.push({ name, durationMs, timestamp: this.wallClock(), metadata });
  }

  recordMemory(
    name: string,
    currentMb: number,
    peakMb: number,
    deltaMb: number,
    metadata: Record<string, unknown> = {},
  ): void {
    pushBounded(this.memorySnapshots, name, { currentMb, peakMb, deltaMb }, this.maxLength);
    this.memoryResults.push({
      name,
      currentMb,
      peakMb,
      deltaMb,
      timestamp: this.wallClock(),
      metadata,
    });
  }

  sampleMemory(
    name: string,
    metadata: Record<string, unknown> = {},
  ): TdfolMemoryResult | undefined {
    const sample = this.memorySampler?.();
    if (sample === undefined) return undefined;
    const previous = this.memorySnapshots.get(name)?.at(-1);
    const peakMb = sample.peakMb ?? Math.max(sample.currentMb, previous?.peakMb ?? 0);
    const deltaMb = previous === undefined ? 0 : sample.currentMb - previous.currentMb;
    this.recordMemory(name, sample.currentMb, peakMb, deltaMb, metadata);
    return this.memoryResults[this.memoryResults.length - 1];
  }

  incrementCounter(name: string, value = 1): void {
    this.counters.set(name, (this.counters.get(name) ?? 0) + value);
  }

  setGauge(name: string, value: number): void {
    this.gauges.set(name, value);
  }

  recordHistogram(name: string, value: number): void {
    pushBounded(this.histograms, name, value, this.maxLength);
  }

  getTimingStats(name: string): TdfolStatisticalSummary | undefined {
    const values = this.timings.get(name);
    return values?.length ? calculateStats(values) : undefined;
  }

  getMemoryStats(
    name: string,
    field: 'currentMb' | 'peakMb' | 'deltaMb' = 'deltaMb',
  ): TdfolStatisticalSummary | undefined {
    const values = this.memorySnapshots.get(name)?.map((snapshot) => snapshot[field]);
    return values?.length ? calculateStats(values) : undefined;
  }

  getHistogramStats(name: string): TdfolStatisticalSummary | undefined {
    const values = this.histograms.get(name);
    return values?.length ? calculateStats(values) : undefined;
  }

  getStatistics(): Record<string, unknown> {
    return {
      timing: Object.fromEntries(
        [...this.timings.keys()].map((name) => [name, this.getTimingStats(name)]),
      ),
      memory: Object.fromEntries(
        [...this.memorySnapshots.keys()].map((name) => [
          name,
          {
            delta_mb: this.getMemoryStats(name, 'deltaMb'),
            peak_mb: this.getMemoryStats(name, 'peakMb'),
            current_mb: this.getMemoryStats(name, 'currentMb'),
          },
        ]),
      ),
      histograms: Object.fromEntries(
        [...this.histograms.keys()].map((name) => [name, this.getHistogramStats(name)]),
      ),
      counters: Object.fromEntries(this.counters),
      gauges: Object.fromEntries(this.gauges),
      metadata: {
        sourcePythonModule: TDFOL_PERFORMANCE_METRICS_METADATA.sourcePythonModule,
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntimeRequired: false,
        collector_maxlen: this.maxLength,
        total_timing_samples: [...this.timings.values()].reduce(
          (total, values) => total + values.length,
          0,
        ),
        total_memory_samples: [...this.memorySnapshots.values()].reduce(
          (total, values) => total + values.length,
          0,
        ),
        total_histogram_samples: [...this.histograms.values()].reduce(
          (total, values) => total + values.length,
          0,
        ),
        generated_at: new Date(this.wallClock()).toISOString(),
      },
    };
  }

  get_statistics(): Record<string, unknown> {
    return this.getStatistics();
  }

  exportDict(): Record<string, unknown> {
    return {
      metadata: TDFOL_PERFORMANCE_METRICS_METADATA,
      statistics: this.getStatistics(),
      timing_results: this.timingResults.slice(-1000),
      memory_results: this.memoryResults.slice(-1000),
    };
  }

  export_dict(): Record<string, unknown> {
    return this.exportDict();
  }

  exportPythonCompatibleDict(): Record<string, unknown> {
    const exported = this.exportDict();
    return {
      ...exported,
      metadata: {
        source_python_module: TDFOL_PERFORMANCE_METRICS_METADATA.sourcePythonModule,
        browser_native: true,
        server_calls_allowed: false,
        python_runtime_required: false,
      },
    };
  }

  export_python_compatible_dict(): Record<string, unknown> {
    return this.exportPythonCompatibleDict();
  }

  reset(): void {
    this.timings.clear();
    this.timingResults.length = 0;
    this.memorySnapshots.clear();
    this.memoryResults.length = 0;
    this.counters.clear();
    this.gauges.clear();
    this.histograms.clear();
    this.timerStarts.clear();
  }
}

let globalCollector: TdfolMetricsCollector | undefined;

export function getGlobalTdfolMetricsCollector(): TdfolMetricsCollector {
  globalCollector ??= new TdfolMetricsCollector();
  return globalCollector;
}

export function resetGlobalTdfolMetricsCollector(): void {
  globalCollector = undefined;
}

export function calculateStats(values: number[]): TdfolStatisticalSummary {
  if (values.length === 0) {
    return {
      count: 0,
      sum: 0,
      mean: 0,
      median: 0,
      stdDev: 0,
      min: 0,
      max: 0,
      p50: 0,
      p95: 0,
      p99: 0,
      p999: 0,
    };
  }
  const sorted = [...values].sort((left, right) => left - right);
  const sum = sorted.reduce((total, value) => total + value, 0);
  const mean = sum / sorted.length;
  const variance =
    sorted.length > 1
      ? sorted.reduce((total, value) => total + (value - mean) ** 2, 0) / (sorted.length - 1)
      : 0;
  return {
    count: sorted.length,
    sum,
    mean,
    median: percentile(sorted, 50),
    stdDev: Math.sqrt(variance),
    min: sorted[0],
    max: sorted[sorted.length - 1],
    p50: percentile(sorted, 50),
    p95: percentile(sorted, 95),
    p99: percentile(sorted, 99),
    p999: percentile(sorted, 99.9),
  };
}

function percentile(sortedValues: number[], percentileValue: number): number {
  if (sortedValues.length === 0) return 0;
  const k = ((sortedValues.length - 1) * percentileValue) / 100;
  const floor = Math.floor(k);
  const ceil = floor + 1;
  if (ceil >= sortedValues.length) return sortedValues[sortedValues.length - 1];
  return sortedValues[floor] * (ceil - k) + sortedValues[ceil] * (k - floor);
}

function pushBounded<T>(map: Map<string, T[]>, name: string, value: T, maxLength: number): void {
  const values = map.get(name) ?? [];
  values.push(value);
  if (values.length > maxLength) values.splice(0, values.length - maxLength);
  map.set(name, values);
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now();
}
