import {
  TDFOL_PERFORMANCE_METRICS_METADATA,
  TdfolMetricsCollector,
  calculateStats,
  getGlobalTdfolMetricsCollector,
  resetGlobalTdfolMetricsCollector,
} from './performanceMetrics';

describe('TdfolMetricsCollector', () => {
  it('records timing values and calculates summary statistics', () => {
    const collector = new TdfolMetricsCollector();

    collector.recordTiming('prove', 1);
    collector.recordTiming('prove', 3);
    collector.recordTiming('prove', 5);

    expect(collector.getTimingStats('prove')).toMatchObject({
      count: 3,
      sum: 9,
      mean: 3,
      median: 3,
      min: 1,
      max: 5,
    });
  });

  it('supports timers, function timing, memory, counters, gauges, and histograms', async () => {
    const ticks = [0, 4, 10, 13, 21, 34];
    const collector = new TdfolMetricsCollector({
      now: () => ticks.shift() ?? 34,
      wallClock: () => Date.UTC(2026, 0, 1, 0, 0, 0),
      memorySampler: (() => {
        const samples = [{ currentMb: 8 }, { currentMb: 11, peakMb: 12 }];
        return () => samples.shift();
      })(),
    });

    collector.startTimer('parse');
    expect(collector.stopTimer('parse')).toBe(4);
    expect(collector.time('sync', () => 42)).toBe(42);
    await expect(collector.timeAsync('async', async () => 'ok')).resolves.toBe('ok');
    collector.recordMemory('load', 1, 2, 0.5);
    expect(collector.sampleMemory('load')).toMatchObject({ currentMb: 8, peakMb: 8, deltaMb: 7 });
    expect(collector.sampleMemory('load')).toMatchObject({ currentMb: 11, peakMb: 12, deltaMb: 3 });
    collector.incrementCounter('proofs', 2);
    collector.setGauge('queue', 7);
    collector.recordHistogram('depth', 2);
    collector.recordHistogram('depth', 4);

    expect(collector.getMemoryStats('load', 'deltaMb')).toMatchObject({ count: 3, mean: 3.5 });
    expect(collector.getHistogramStats('depth')).toMatchObject({ count: 2, mean: 3 });
    expect(collector.getStatistics()).toMatchObject({
      counters: { proofs: 2 },
      gauges: { queue: 7 },
      metadata: { total_timing_samples: 3, total_memory_samples: 3 },
    });
  });

  it('exports and resets metrics', () => {
    const collector = new TdfolMetricsCollector(2);
    collector.recordTiming('a', 1);
    collector.recordTiming('a', 2);
    collector.recordTiming('a', 3);

    expect(collector.getTimingStats('a')).toMatchObject({ count: 2, min: 2 });
    expect(collector.exportDict()).toHaveProperty('statistics');
    collector.reset();
    expect(collector.getTimingStats('a')).toBeUndefined();
  });

  it('exposes Python-compatible metadata, aliases, and fail-closed local export contract', () => {
    const collector = new TdfolMetricsCollector({
      maxLength: 3,
      wallClock: () => Date.UTC(2026, 0, 2, 3, 4, 5),
    });
    collector.recordTiming('prove', 7, { strategy: 'forward' });
    collector.recordHistogram('branching_factor', 2);

    expect(TDFOL_PERFORMANCE_METRICS_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/performance_metrics.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeRequired: false,
    });
    expect(collector.get_statistics()).toHaveProperty('metadata.collector_maxlen', 3);
    expect(collector.export_dict()).toHaveProperty(
      'metadata.sourcePythonModule',
      'logic/TDFOL/performance_metrics.py',
    );
    expect(collector.export_python_compatible_dict()).toMatchObject({
      metadata: {
        source_python_module: 'logic/TDFOL/performance_metrics.py',
        server_calls_allowed: false,
        python_runtime_required: false,
      },
      statistics: { metadata: { generated_at: '2026-01-02T03:04:05.000Z' } },
      timing_results: [
        {
          name: 'prove',
          durationMs: 7,
          timestamp: Date.UTC(2026, 0, 2, 3, 4, 5),
          metadata: { strategy: 'forward' },
        },
      ],
    });
  });

  it('supports global collector helpers', () => {
    resetGlobalTdfolMetricsCollector();
    getGlobalTdfolMetricsCollector().incrementCounter('global');

    expect(getGlobalTdfolMetricsCollector().getStatistics()).toMatchObject({
      counters: { global: 1 },
    });
  });

  it('calculates percentiles and empty summaries', () => {
    expect(calculateStats([])).toMatchObject({ count: 0, p95: 0 });
    expect(calculateStats([1, 2, 3, 4, 5])).toMatchObject({
      p50: 3,
      p95: 4.8,
      p99: 4.96,
    });
  });
});
