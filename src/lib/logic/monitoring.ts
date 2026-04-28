export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary';

export const MetricTypes = {
  COUNTER: 'counter',
  GAUGE: 'gauge',
  HISTOGRAM: 'histogram',
  SUMMARY: 'summary',
} as const satisfies Record<string, MetricType>;

export interface OperationMetricsInit {
  totalCount?: number;
  successCount?: number;
  failureCount?: number;
  totalTime?: number;
  minTime?: number;
  maxTime?: number;
  windowSize?: number;
  recentTimes?: number[];
}

export class OperationMetrics {
  totalCount: number;
  successCount: number;
  failureCount: number;
  totalTime: number;
  minTime: number;
  maxTime: number;
  readonly windowSize: number;
  readonly recentTimes: number[];

  constructor(init: OperationMetricsInit = {}) {
    this.totalCount = init.totalCount ?? 0;
    this.successCount = init.successCount ?? 0;
    this.failureCount = init.failureCount ?? 0;
    this.totalTime = init.totalTime ?? 0;
    this.minTime = init.minTime ?? Number.POSITIVE_INFINITY;
    this.maxTime = init.maxTime ?? 0;
    this.windowSize = Math.max(1, Math.trunc(init.windowSize ?? 100));
    this.recentTimes = [...(init.recentTimes ?? [])].slice(-this.windowSize);
  }

  record(success: boolean, duration: number): void {
    this.totalCount += 1;
    if (success) {
      this.successCount += 1;
    } else {
      this.failureCount += 1;
    }
    this.totalTime += duration;
    this.minTime = Math.min(this.minTime, duration);
    this.maxTime = Math.max(this.maxTime, duration);
    this.recentTimes.push(duration);
    while (this.recentTimes.length > this.windowSize) {
      this.recentTimes.shift();
    }
  }

  get successRate(): number {
    return this.totalCount === 0 ? 0 : this.successCount / this.totalCount;
  }

  get avgTime(): number {
    return this.totalCount === 0 ? 0 : this.totalTime / this.totalCount;
  }

  get recentAvgTime(): number {
    return this.recentTimes.length === 0
      ? 0
      : this.recentTimes.reduce((total, value) => total + value, 0) / this.recentTimes.length;
  }

  toDict(): Record<string, unknown> {
    return {
      total_count: this.totalCount,
      success_count: this.successCount,
      failure_count: this.failureCount,
      success_rate: this.successRate,
      avg_time: this.avgTime,
      recent_avg_time: this.recentAvgTime,
      min_time: Number.isFinite(this.minTime) ? this.minTime : 0,
      max_time: this.maxTime,
    };
  }
}

export interface LogicMonitorOptions {
  windowSize?: number;
  enablePrometheus?: boolean;
  now?: () => number;
}

export interface TrackingContext {
  success: boolean;
}

export interface HealthCheckResult {
  status: 'unknown' | 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  success_rate?: number;
  error_count?: number;
  warning_count?: number;
  timestamp: number;
}

export class LogicMonitor {
  readonly windowSize: number;
  readonly enablePrometheus: boolean;

  private readonly now: () => number;
  private readonly operations = new Map<string, OperationMetrics>();
  private readonly errors = new Map<string, number>();
  private readonly warnings = new Map<string, number>();
  private startTime: number;
  private lastHealthCheck: number;

  constructor(options: LogicMonitorOptions = {}) {
    this.windowSize = Math.max(1, Math.trunc(options.windowSize ?? 100));
    this.enablePrometheus = options.enablePrometheus ?? false;
    this.now = options.now ?? (() => performanceNowSeconds());
    this.startTime = this.now();
    this.lastHealthCheck = this.startTime;
  }

  async trackOperation<Result>(
    operation: string,
    callback: (context: TrackingContext) => Result | Promise<Result>,
  ): Promise<Result> {
    const startedAt = this.now();
    const context: TrackingContext = { success: true };
    try {
      return await callback(context);
    } catch (error) {
      context.success = false;
      this.recordError(operation, error instanceof Error ? error.message : String(error));
      throw error;
    } finally {
      this.recordOperation(operation, context.success, Math.max(0, this.now() - startedAt));
    }
  }

  beginOperation(operation: string): TrackingContext & { finish: () => void } {
    const startedAt = this.now();
    const context: TrackingContext & { finish: () => void } = {
      success: true,
      finish: () => {
        this.recordOperation(operation, context.success, Math.max(0, this.now() - startedAt));
      },
    };
    return context;
  }

  recordOperation(operation: string, success: boolean, duration: number): void {
    this.getOperationMetrics(operation).record(success, duration);
  }

  recordError(category: string, message: string): void {
    const key = `${category}: ${message.slice(0, 50)}`;
    this.errors.set(key, (this.errors.get(key) ?? 0) + 1);
  }

  recordWarning(category: string, message: string): void {
    const key = `${category}: ${message.slice(0, 50)}`;
    this.warnings.set(key, (this.warnings.get(key) ?? 0) + 1);
  }

  getMetrics(): Record<string, unknown> {
    return {
      system: this.getSystemMetrics(),
      operations: Object.fromEntries([...this.operations.entries()].map(([name, metrics]) => [name, metrics.toDict()])),
      errors: Object.fromEntries(this.errors),
      warnings: Object.fromEntries(this.warnings),
      health: this.healthCheck(),
    };
  }

  healthCheck(): HealthCheckResult {
    this.lastHealthCheck = this.now();
    const totalOps = [...this.operations.values()].reduce((total, metrics) => total + metrics.totalCount, 0);

    if (totalOps === 0) {
      return {
        status: 'unknown',
        message: 'No operations recorded yet',
        timestamp: this.lastHealthCheck,
      };
    }

    const successCount = [...this.operations.values()].reduce((total, metrics) => total + metrics.successCount, 0);
    const successRate = successCount / totalOps;
    const errorCount = sumMapValues(this.errors);
    const warningCount = sumMapValues(this.warnings);

    if (successRate >= 0.95 && errorCount < 10) {
      return {
        status: 'healthy',
        message: 'System operating normally',
        success_rate: successRate,
        error_count: errorCount,
        warning_count: warningCount,
        timestamp: this.lastHealthCheck,
      };
    }
    if (successRate >= 0.8) {
      return {
        status: 'degraded',
        message: `Success rate: ${(successRate * 100).toFixed(1)}%, may need attention`,
        success_rate: successRate,
        error_count: errorCount,
        warning_count: warningCount,
        timestamp: this.lastHealthCheck,
      };
    }
    return {
      status: 'unhealthy',
      message: `Success rate: ${(successRate * 100).toFixed(1)}%, immediate attention required`,
      success_rate: successRate,
      error_count: errorCount,
      warning_count: warningCount,
      timestamp: this.lastHealthCheck,
    };
  }

  getPrometheusMetrics(): string {
    if (!this.enablePrometheus) return '';
    const lines: string[] = [];
    const system = this.getSystemMetrics();

    lines.push('# HELP logic_uptime_seconds System uptime in seconds');
    lines.push('# TYPE logic_uptime_seconds gauge');
    lines.push(`logic_uptime_seconds ${system.uptime_seconds}`);
    lines.push('# HELP logic_operations_total Total operations');
    lines.push('# TYPE logic_operations_total counter');
    lines.push(`logic_operations_total ${system.total_operations}`);

    for (const [name, metrics] of this.operations.entries()) {
      const safeName = name.replace(/[-.]/g, '_');
      lines.push(`# HELP logic_operation_${safeName}_total Total count`);
      lines.push(`# TYPE logic_operation_${safeName}_total counter`);
      lines.push(`logic_operation_${safeName}_total ${metrics.totalCount}`);
      lines.push(`# HELP logic_operation_${safeName}_success Success count`);
      lines.push(`# TYPE logic_operation_${safeName}_success counter`);
      lines.push(`logic_operation_${safeName}_success ${metrics.successCount}`);
      lines.push(`# HELP logic_operation_${safeName}_duration_seconds Operation duration`);
      lines.push(`# TYPE logic_operation_${safeName}_duration_seconds summary`);
      lines.push(`logic_operation_${safeName}_duration_seconds_sum ${metrics.totalTime}`);
      lines.push(`logic_operation_${safeName}_duration_seconds_count ${metrics.totalCount}`);
    }

    return lines.join('\n');
  }

  resetMetrics(): void {
    this.operations.clear();
    this.errors.clear();
    this.warnings.clear();
    this.startTime = this.now();
    this.lastHealthCheck = this.startTime;
  }

  getOperationSummary(operation: string): Record<string, unknown> | undefined {
    return this.operations.get(operation)?.toDict();
  }

  private getOperationMetrics(operation: string): OperationMetrics {
    let metrics = this.operations.get(operation);
    if (!metrics) {
      metrics = new OperationMetrics({ windowSize: this.windowSize });
      this.operations.set(operation, metrics);
    }
    return metrics;
  }

  private getSystemMetrics(): Record<string, number> {
    const totalOperations = [...this.operations.values()].reduce((total, metrics) => total + metrics.totalCount, 0);
    const totalSuccesses = [...this.operations.values()].reduce((total, metrics) => total + metrics.successCount, 0);
    const totalFailures = [...this.operations.values()].reduce((total, metrics) => total + metrics.failureCount, 0);
    return {
      uptime_seconds: Math.max(0, this.now() - this.startTime),
      total_operations: totalOperations,
      total_successes: totalSuccesses,
      total_failures: totalFailures,
      overall_success_rate: totalOperations > 0 ? totalSuccesses / totalOperations : 0,
      total_errors: sumMapValues(this.errors),
      total_warnings: sumMapValues(this.warnings),
    };
  }
}

let globalMonitor: LogicMonitor | undefined;

export function getGlobalMonitor(windowSize = 100, enablePrometheus = false): LogicMonitor {
  globalMonitor ??= new LogicMonitor({ windowSize, enablePrometheus });
  return globalMonitor;
}

export function resetGlobalMonitor(): void {
  globalMonitor = undefined;
}

export const get_global_monitor = getGlobalMonitor;

function sumMapValues(map: Map<string, number>): number {
  return [...map.values()].reduce((total, value) => total + value, 0);
}

function performanceNowSeconds(): number {
  return (globalThis.performance?.now?.() ?? Date.now()) / 1000;
}
