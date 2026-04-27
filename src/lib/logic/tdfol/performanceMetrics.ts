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

export class TdfolMetricsCollector {
  readonly timings = new Map<string, number[]>();
  readonly timingResults: TdfolTimingResult[] = [];
  readonly memorySnapshots = new Map<string, Array<{ currentMb: number; peakMb: number; deltaMb: number }>>();
  readonly memoryResults: TdfolMemoryResult[] = [];
  readonly counters = new Map<string, number>();
  readonly gauges = new Map<string, number>();
  readonly histograms = new Map<string, number[]>();

  private readonly timerStarts = new Map<string, number>();

  constructor(readonly maxLength = 10000) {}

  startTimer(name: string): void {
    this.timerStarts.set(name, performance.now());
  }

  stopTimer(name: string, metadata: Record<string, unknown> = {}): number {
    const startedAt = this.timerStarts.get(name);
    if (startedAt === undefined) throw new Error(`Timer '${name}' was not started`);
    this.timerStarts.delete(name);
    const durationMs = performance.now() - startedAt;
    this.recordTiming(name, durationMs, metadata);
    return durationMs;
  }

  time<T>(name: string, fn: () => T, metadata: Record<string, unknown> = {}): T {
    const startedAt = performance.now();
    try {
      return fn();
    } finally {
      this.recordTiming(name, performance.now() - startedAt, metadata);
    }
  }

  recordTiming(name: string, durationMs: number, metadata: Record<string, unknown> = {}): void {
    pushBounded(this.timings, name, durationMs, this.maxLength);
    this.timingResults.push({ name, durationMs, timestamp: Date.now(), metadata });
  }

  recordMemory(name: string, currentMb: number, peakMb: number, deltaMb: number, metadata: Record<string, unknown> = {}): void {
    pushBounded(this.memorySnapshots, name, { currentMb, peakMb, deltaMb }, this.maxLength);
    this.memoryResults.push({ name, currentMb, peakMb, deltaMb, timestamp: Date.now(), metadata });
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

  getMemoryStats(name: string, field: 'currentMb' | 'peakMb' | 'deltaMb' = 'deltaMb'): TdfolStatisticalSummary | undefined {
    const values = this.memorySnapshots.get(name)?.map((snapshot) => snapshot[field]);
    return values?.length ? calculateStats(values) : undefined;
  }

  getHistogramStats(name: string): TdfolStatisticalSummary | undefined {
    const values = this.histograms.get(name);
    return values?.length ? calculateStats(values) : undefined;
  }

  getStatistics(): Record<string, unknown> {
    return {
      timing: Object.fromEntries([...this.timings.keys()].map((name) => [name, this.getTimingStats(name)])),
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
      histograms: Object.fromEntries([...this.histograms.keys()].map((name) => [name, this.getHistogramStats(name)])),
      counters: Object.fromEntries(this.counters),
      gauges: Object.fromEntries(this.gauges),
      metadata: {
        collector_maxlen: this.maxLength,
        total_timing_samples: [...this.timings.values()].reduce((total, values) => total + values.length, 0),
        total_memory_samples: [...this.memorySnapshots.values()].reduce((total, values) => total + values.length, 0),
        generated_at: new Date().toISOString(),
      },
    };
  }

  exportDict(): Record<string, unknown> {
    return {
      statistics: this.getStatistics(),
      timing_results: this.timingResults.slice(-1000),
      memory_results: this.memoryResults.slice(-1000),
    };
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
    return { count: 0, sum: 0, mean: 0, median: 0, stdDev: 0, min: 0, max: 0, p50: 0, p95: 0, p99: 0, p999: 0 };
  }
  const sorted = [...values].sort((left, right) => left - right);
  const sum = sorted.reduce((total, value) => total + value, 0);
  const mean = sum / sorted.length;
  const variance = sorted.length > 1 ? sorted.reduce((total, value) => total + (value - mean) ** 2, 0) / (sorted.length - 1) : 0;
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
