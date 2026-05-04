import { OTelTracer } from './otelTracer';
import { PrometheusMetricsCollector } from './prometheusMetrics';
import {
  clearContext,
  EventType,
  filterLogs,
  getCurrentContext,
  LogContext,
  logError,
  logEvent,
  logMcpTool,
  logPerformance,
  parseJsonLogLines,
  StructuredLogger,
} from './structuredLogging';

describe('logic observability browser-native parity helpers', () => {
  afterEach(() => clearContext());

  it('emits structured JSON logs with propagated context and filters records', () => {
    const logger = new StructuredLogger('component', () => '2026-01-01T00:00:00.000Z');
    new LogContext({ request_id: 'req-1', user_id: 'ada' }).run(() => {
      expect(getCurrentContext()).toMatchObject({ request_id: 'req-1' });
      logEvent(EventType.TOOL_INVOKED, logger, 'INFO', { tool_name: 'prove' });
      logPerformance('prove', 12.25, logger, { memory_mb: 4 });
      logMcpTool('prove', 'completed', { durationMs: 13, logger, extra: { receipt_cid: 'bafy' } });
    });
    logError(new TypeError('bad'), logger, { component: 'parser' });

    expect(logger.records).toHaveLength(4);
    expect(filterLogs(logger.records, { requestId: 'req-1' })).toHaveLength(3);
    expect(filterLogs(logger.records, { eventType: EventType.ERROR_OCCURRED })).toHaveLength(1);
    expect(parseJsonLogLines(`${logger.toJsonLines()}\nnot-json`)).toHaveLength(4);
  });

  it('collects circuit-breaker and log metrics in Prometheus text format', () => {
    const collector = new PrometheusMetricsCollector(2);
    collector.recordCircuitBreakerCall('llm"router', 0.1, true, 1);
    collector.recordCircuitBreakerCall('llm"router', 0.3, false, 2);
    collector.recordCircuitBreakerCall('llm"router', 0.5, true, 3);
    collector.recordCircuitBreakerState('llm"router', 'open', 4);
    collector.recordLogEntry('logic', 'info');
    collector.recordLogEntry('logic', 'error');
    collector.recordLogEntry('logic', 'warn');

    expect(collector.getFailureRate('llm"router')).toBeCloseTo(33.333, 2);
    expect(collector.getLatencyPercentiles('llm"router')).toMatchObject({ p50: 0.3, p95: 0.5 });
    expect(collector.getMetricsSummary('llm"router')).toMatchObject({
      total_calls: 3,
      successful_calls: 2,
      failed_calls: 1,
      current_state: 'open',
      state_transitions: [{ timestamp: 4, state: 'open' }],
    });
    expect(collector.getLogMetricsSummary('logic')).toMatchObject({
      total_entries: 3,
      warning_entries: 1,
    });
    expect(collector.exportJsonSnapshot(12)).toMatchObject({
      exported_at: 12,
      browser_native: true,
      server_calls_allowed: false,
    });
    expect(collector.exportPrometheusFormat()).toContain(
      'circuit_breaker_calls_total{component="llm\\"router"} 3',
    );
    expect(collector.exportPrometheusFormat()).toContain(
      'circuit_breaker_last_failure_timestamp_seconds{component="llm\\"router"} 2',
    );
    expect(collector.exportPrometheusFormat()).toContain(
      'log_entries_by_level{component="logic",level="warning"} 1',
    );
    collector.resetComponent('llm"router');
    expect(collector.getComponents().has('llm"router')).toBe(false);
  });

  it('records in-memory spans, errors, completed traces, and Jaeger-compatible exports', () => {
    let now = 10;
    let id = 0;
    const tracer = new OTelTracer(
      'logic',
      () => now,
      () => `id-${++id}`,
    );
    tracer.setTraceContext('trace-1');
    const root = tracer.startSpan('root', { component: 'logic' });
    now = 11;
    const child = tracer.startSpan('child');
    tracer.recordEvent(child, 'circuit_breaker.call', { component: 'llm' });
    tracer.recordError(child, 'failed', 'TypeError');
    tracer.endSpan(child, 'error');
    now = 12;
    tracer.setSpanAttribute(root, 'done', true);
    tracer.endSpan(root, 'ok');

    expect(tracer.getCompletedTraces()).toHaveLength(1);
    expect(tracer.getTrace('trace-1')?.rootSpan()?.name).toBe('root');
    const exported = JSON.parse(tracer.exportJaegerFormat());
    expect(exported.data[0].spans).toHaveLength(2);
    expect(exported.data[0].spans[1].logs[0].fields).toContainEqual({
      key: 'component',
      value: 'llm',
    });
  });
});
