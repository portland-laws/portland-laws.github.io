import { createBrowserTelemetryCollector } from './browserTelemetry';

describe('browserTelemetry', () => {
  it('aggregates counters, gauges, and timings into deterministic snapshots', () => {
    let now = 1000;
    const telemetry = createBrowserTelemetryCollector({ now: () => now });

    telemetry.increment('proof.search.requests', 1, { engine: 'tdfol' });
    now += 5;
    telemetry.increment('proof.search.requests', 2, { engine: 'tdfol' });
    telemetry.gauge('cache.entries', 4);
    telemetry.timing('proof.search.ms', 12, { engine: 'tdfol' });
    telemetry.timing('proof.search.ms', 18, { engine: 'tdfol' });

    const snapshot = telemetry.snapshot();
    const counter = snapshot.metrics.find((metric) => metric.name === 'proof.search.requests');
    const timing = snapshot.metrics.find((metric) => metric.name === 'proof.search.ms');
    const gauge = snapshot.metrics.find((metric) => metric.name === 'cache.entries');

    expect(counter).toMatchObject({
      kind: 'counter',
      count: 2,
      total: 3,
      min: 1,
      max: 2,
      latest: 2,
      average: 1.5,
    });
    expect(timing).toMatchObject({
      kind: 'timing',
      count: 2,
      total: 30,
      min: 12,
      max: 18,
      latest: 18,
      average: 15,
    });
    expect(gauge).toMatchObject({ kind: 'gauge', count: 1, total: 4, latest: 4 });
    expect(snapshot.recentEvents).toHaveLength(5);
  });

  it('returns developer panel groups and browser-local warnings', () => {
    const telemetry = createBrowserTelemetryCollector({ now: () => 42 });

    telemetry.increment('logic.requests');
    telemetry.gauge('proof.queue.depth', 3);
    telemetry.timing('slow.proof.ms', 1201);

    const panel = telemetry.developerPanelSummary();

    expect(panel.generatedAtMs).toBe(42);
    expect(panel.metricCount).toBe(3);
    expect(panel.eventCount).toBe(3);
    expect(panel.counters.map((metric) => metric.name)).toEqual(['logic.requests']);
    expect(panel.gauges.map((metric) => metric.name)).toEqual(['proof.queue.depth']);
    expect(panel.timings.map((metric) => metric.name)).toEqual(['slow.proof.ms']);
    expect(panel.warnings).toEqual(['slow.proof.ms exceeded 1000ms']);
  });

  it('bounds recent events without dropping aggregate metrics', () => {
    const telemetry = createBrowserTelemetryCollector({ maxEvents: 2, now: () => 7 });

    telemetry.increment('requests', 1);
    telemetry.increment('requests', 1);
    telemetry.increment('requests', 1);

    const snapshot = telemetry.snapshot();

    expect(snapshot.recentEvents).toHaveLength(2);
    expect(snapshot.metrics[0]).toMatchObject({ name: 'requests', count: 3, total: 3 });
  });

  it('fails closed for invalid metric names and values', () => {
    const telemetry = createBrowserTelemetryCollector();

    expect(() => telemetry.increment('')).toThrow(
      'Telemetry metric name must be a non-empty string.',
    );
    expect(() => telemetry.gauge('cache.entries', Number.NaN)).toThrow(
      'Telemetry metric value must be finite.',
    );
    expect(telemetry.snapshot().metrics).toEqual([]);
  });
});
