import { LogicMonitor, OperationMetrics, getGlobalMonitor, resetGlobalMonitor } from './monitoring';

describe('logic monitoring browser-native parity helpers', () => {
  it('records operation metrics with Python-compatible summary fields', () => {
    const metrics = new OperationMetrics({ windowSize: 2 });

    metrics.record(true, 0.1);
    metrics.record(false, 0.3);
    metrics.record(true, 0.5);

    expect(metrics.recentTimes).toEqual([0.3, 0.5]);
    expect(metrics.toDict()).toEqual({
      total_count: 3,
      success_count: 2,
      failure_count: 1,
      success_rate: 2 / 3,
      avg_time: 0.3,
      recent_avg_time: 0.4,
      min_time: 0.1,
      max_time: 0.5,
    });
  });

  it('tracks async operations, failures, errors, warnings, and health', async () => {
    let now = 10;
    const monitor = new LogicMonitor({ windowSize: 3, now: () => now });

    await monitor.trackOperation('fol_conversion', async () => {
      now += 0.2;
      return 'ok';
    });
    await expect(
      monitor.trackOperation('fol_conversion', async () => {
        now += 0.4;
        throw new Error('conversion failed');
      }),
    ).rejects.toThrow('conversion failed');
    monitor.recordWarning('fol_conversion', 'regex fallback used');

    const summary = monitor.getOperationSummary('fol_conversion');
    const metrics = monitor.getMetrics();

    expect(summary).toMatchObject({
      total_count: 2,
      success_count: 1,
      failure_count: 1,
    });
    expect(summary?.avg_time).toBeCloseTo(0.3);
    expect(metrics.system).toMatchObject({
      total_operations: 2,
      total_successes: 1,
      total_failures: 1,
      total_errors: 1,
      total_warnings: 1,
    });
    expect(metrics.health).toMatchObject({
      status: 'unhealthy',
      success_rate: 0.5,
      error_count: 1,
      warning_count: 1,
    });
  });

  it('supports manual operation contexts and healthy/degraded health thresholds', () => {
    let now = 0;
    const monitor = new LogicMonitor({ now: () => now });

    for (let index = 0; index < 9; index += 1) {
      const context = monitor.beginOperation('proof');
      now += 0.01;
      context.finish();
    }
    monitor.recordOperation('proof', false, 0.2);

    expect(monitor.healthCheck()).toMatchObject({
      status: 'degraded',
      success_rate: 0.9,
      error_count: 0,
    });
  });

  it('exports Prometheus metrics only when enabled', () => {
    const disabled = new LogicMonitor();
    const enabled = new LogicMonitor({ enablePrometheus: true, now: () => 3 });

    enabled.recordOperation('fol-conversion.simple', true, 0.25);

    expect(disabled.getPrometheusMetrics()).toBe('');
    expect(enabled.getPrometheusMetrics()).toContain('logic_operations_total 1');
    expect(enabled.getPrometheusMetrics()).toContain('logic_operation_fol_conversion_simple_duration_seconds_sum 0.25');
  });

  it('resets metrics and exposes a global monitor facade', () => {
    resetGlobalMonitor();
    const first = getGlobalMonitor(7, true);
    const second = getGlobalMonitor();

    first.recordOperation('cache_hit', true, 0.001);
    expect(first).toBe(second);
    expect(first.getOperationSummary('cache_hit')).toMatchObject({ total_count: 1 });

    first.resetMetrics();
    expect(first.getOperationSummary('cache_hit')).toBeUndefined();
    expect(first.healthCheck()).toMatchObject({ status: 'unknown' });
  });
});
