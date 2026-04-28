export type CircuitBreakerMetricState = 'closed' | 'open' | 'half_open';

export interface CallMetrics {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  latencies: number[];
  stateTransitions: Array<[number, string]>;
  lastFailureTime?: number;
  currentState: CircuitBreakerMetricState;
}

export class PrometheusMetricsCollector {
  private readonly metrics = new Map<string, CallMetrics>();
  private readonly logMetrics = new Map<string, Record<string, number>>();

  constructor(readonly maxLatencySamples = 1000) {}

  recordCircuitBreakerCall(component: string, latency: number, success: boolean, timestamp = Date.now() / 1000): void {
    const metrics = this.getCallMetrics(component);
    metrics.totalCalls += 1;
    if (success) {
      metrics.successfulCalls += 1;
    } else {
      metrics.failedCalls += 1;
      metrics.lastFailureTime = timestamp;
    }
    if (metrics.latencies.length >= this.maxLatencySamples) metrics.latencies.shift();
    metrics.latencies.push(latency);
  }

  recordCircuitBreakerState(component: string, state: CircuitBreakerMetricState, timestamp = Date.now() / 1000): void {
    const metrics = this.getCallMetrics(component);
    metrics.currentState = state;
    metrics.stateTransitions.push([timestamp, state]);
    if (metrics.stateTransitions.length > 100) metrics.stateTransitions.shift();
  }

  recordLogEntry(component: string, level = 'info'): void {
    const metrics = this.getLogMetrics(component);
    metrics.total_entries += 1;
    const key = `${level.toLowerCase()}_entries`;
    if (key in metrics) metrics[key] += 1;
  }

  getLatencyPercentiles(component: string, percentiles = [50, 95, 99]): Record<string, number> {
    const latencies = [...this.getCallMetrics(component).latencies].sort((a, b) => a - b);
    if (latencies.length === 0) return Object.fromEntries(percentiles.map((p) => [`p${p}`, 0]));
    return Object.fromEntries(percentiles.map((p) => [`p${p}`, percentile(latencies, p)]));
  }

  getFailureRate(component: string): number {
    const metrics = this.getCallMetrics(component);
    return metrics.totalCalls === 0 ? 0 : (metrics.failedCalls / metrics.totalCalls) * 100;
  }

  getSuccessRate(component: string): number {
    return 100 - this.getFailureRate(component);
  }

  getMetricsSummary(component: string): Record<string, unknown> {
    const metrics = this.getCallMetrics(component);
    return {
      component,
      total_calls: metrics.totalCalls,
      successful_calls: metrics.successfulCalls,
      failed_calls: metrics.failedCalls,
      success_rate: this.getSuccessRate(component),
      failure_rate: this.getFailureRate(component),
      avg_latency: average(metrics.latencies),
      min_latency: metrics.latencies.length ? Math.min(...metrics.latencies) : 0,
      max_latency: metrics.latencies.length ? Math.max(...metrics.latencies) : 0,
      current_state: metrics.currentState,
      last_failure_time: metrics.lastFailureTime,
      latency_percentiles: this.getLatencyPercentiles(component),
    };
  }

  exportPrometheusFormat(): string {
    const lines: string[] = [
      '# HELP circuit_breaker_calls_total Total calls to circuit breaker',
      '# TYPE circuit_breaker_calls_total counter',
    ];
    for (const [component, metrics] of this.metrics) lines.push(`circuit_breaker_calls_total{component="${component}"} ${metrics.totalCalls}`);
    lines.push('', '# HELP circuit_breaker_calls_success Successful calls to circuit breaker', '# TYPE circuit_breaker_calls_success counter');
    for (const [component, metrics] of this.metrics) lines.push(`circuit_breaker_calls_success{component="${component}"} ${metrics.successfulCalls}`);
    lines.push('', '# HELP circuit_breaker_calls_failed Failed calls to circuit breaker', '# TYPE circuit_breaker_calls_failed counter');
    for (const [component, metrics] of this.metrics) lines.push(`circuit_breaker_calls_failed{component="${component}"} ${metrics.failedCalls}`);
    lines.push('', '# HELP circuit_breaker_failure_rate Failure rate percentage', '# TYPE circuit_breaker_failure_rate gauge');
    for (const component of this.metrics.keys()) lines.push(`circuit_breaker_failure_rate{component="${component}"} ${this.getFailureRate(component).toFixed(2)}`);
    lines.push('', '# HELP circuit_breaker_latency_seconds Call latency in seconds', '# TYPE circuit_breaker_latency_seconds histogram');
    for (const [component, metrics] of this.metrics) {
      if (metrics.latencies.length) {
        lines.push(`circuit_breaker_latency_seconds_sum{component="${component}"} ${sum(metrics.latencies).toFixed(4)}`);
        lines.push(`circuit_breaker_latency_seconds_count{component="${component}"} ${metrics.latencies.length}`);
        lines.push(`circuit_breaker_latency_seconds_avg{component="${component}"} ${average(metrics.latencies).toFixed(4)}`);
      }
    }
    lines.push('', '# HELP circuit_breaker_state Current circuit breaker state', '# TYPE circuit_breaker_state gauge');
    const stateMap: Record<string, number> = { closed: 0, open: 1, half_open: 2 };
    for (const [component, metrics] of this.metrics) lines.push(`circuit_breaker_state{component="${component}",state="${metrics.currentState}"} ${stateMap[metrics.currentState] ?? 0}`);
    lines.push('', '# HELP log_entries_total Total log entries recorded', '# TYPE log_entries_total counter');
    for (const [component, metrics] of this.logMetrics) lines.push(`log_entries_total{component="${component}"} ${metrics.total_entries}`);
    lines.push('', '# HELP log_entries_by_level Log entries by level', '# TYPE log_entries_by_level counter');
    for (const [component, metrics] of this.logMetrics) {
      for (const level of ['debug', 'info', 'warning', 'error']) lines.push(`log_entries_by_level{component="${component}",level="${level}"} ${metrics[`${level}_entries`] ?? 0}`);
    }
    return lines.join('\n');
  }

  getComponents(): Set<string> {
    return new Set(this.metrics.keys());
  }

  resetComponent(component: string): void {
    this.metrics.delete(component);
    this.logMetrics.delete(component);
  }

  resetAll(): void {
    this.metrics.clear();
    this.logMetrics.clear();
  }

  private getCallMetrics(component: string): CallMetrics {
    if (!this.metrics.has(component)) {
      this.metrics.set(component, { totalCalls: 0, successfulCalls: 0, failedCalls: 0, latencies: [], stateTransitions: [], currentState: 'closed' });
    }
    return this.metrics.get(component)!;
  }

  private getLogMetrics(component: string): Record<string, number> {
    if (!this.logMetrics.has(component)) {
      this.logMetrics.set(component, { total_entries: 0, error_entries: 0, warning_entries: 0, info_entries: 0, debug_entries: 0 });
    }
    return this.logMetrics.get(component)!;
  }
}

let defaultCollector: PrometheusMetricsCollector | undefined;

export function getPrometheusCollector(): PrometheusMetricsCollector {
  defaultCollector ??= new PrometheusMetricsCollector();
  return defaultCollector;
}

function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function average(values: number[]): number {
  return values.length ? sum(values) / values.length : 0;
}

function percentile(sortedValues: number[], p: number): number {
  if (sortedValues.length === 1) return sortedValues[0];
  const index = Math.min(sortedValues.length - 1, Math.max(0, Math.ceil((p / 100) * sortedValues.length) - 1));
  return sortedValues[index];
}
