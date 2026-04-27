import {
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

  it('supports timers, function timing, memory, counters, gauges, and histograms', () => {
    const collector = new TdfolMetricsCollector();

    collector.startTimer('parse');
    expect(collector.stopTimer('parse')).toEqual(expect.any(Number));
    expect(collector.time('sync', () => 42)).toBe(42);
    collector.recordMemory('load', 1, 2, 0.5);
    collector.incrementCounter('proofs', 2);
    collector.setGauge('queue', 7);
    collector.recordHistogram('depth', 2);
    collector.recordHistogram('depth', 4);

    expect(collector.getMemoryStats('load', 'deltaMb')).toMatchObject({ count: 1, mean: 0.5 });
    expect(collector.getHistogramStats('depth')).toMatchObject({ count: 2, mean: 3 });
    expect(collector.getStatistics()).toMatchObject({
      counters: { proofs: 2 },
      gauges: { queue: 7 },
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
