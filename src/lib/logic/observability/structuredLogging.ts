export const LOG_SCHEMA_VERSION = '1.0.0';

export interface StructuredLoggingMetadata {
  sourcePythonModule: 'logic/observability/structured_logging.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  sink: 'in-memory';
}

export interface ParsedJsonLogLines {
  records: Array<LogRecord>;
  rejected_lines: Array<{ line: string; reason: string }>;
}

export const STRUCTURED_LOGGING_METADATA: StructuredLoggingMetadata = {
  sourcePythonModule: 'logic/observability/structured_logging.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  sink: 'in-memory',
};

export const LogField = {
  TIMESTAMP: 'timestamp',
  SCHEMA_VERSION: 'schema_version',
  LEVEL: 'level',
  LOGGER_NAME: 'logger',
  REQUEST_ID: 'request_id',
  SESSION_ID: 'session_id',
  USER_ID: 'user_id',
  COMPONENT: 'component',
  FUNCTION: 'function',
  EVENT_TYPE: 'event_type',
  MESSAGE: 'message',
  ERROR_TYPE: 'error_type',
  ERROR_MESSAGE: 'error_message',
  ERROR_STACK: 'error_stack',
  ERROR_CODE: 'error_code',
  DURATION_MS: 'duration_ms',
  CPU_TIME_MS: 'cpu_time_ms',
  MEMORY_MB: 'memory_mb',
  TOOL_NAME: 'tool_name',
  INTENT_CID: 'intent_cid',
  DECISION_CID: 'decision_cid',
  RECEIPT_CID: 'receipt_cid',
  POLICY_NAME: 'policy_name',
  COMPLIANCE_STATUS: 'compliance_status',
} as const;

export const EventType = {
  SYSTEM_START: 'system.start',
  SYSTEM_STOP: 'system.stop',
  COMPONENT_INIT: 'component.init',
  COMPONENT_SHUTDOWN: 'component.shutdown',
  TOOL_INVOKED: 'mcp.tool.invoked',
  TOOL_COMPLETED: 'mcp.tool.completed',
  TOOL_FAILED: 'mcp.tool.failed',
  POLICY_EVALUATED: 'mcp.policy.evaluated',
  COMPLIANCE_CHECKED: 'mcp.compliance.checked',
  ENTITY_EXTRACTED: 'graphrag.entity.extracted',
  ENTITY_DEDUPLICATED: 'graphrag.entity.deduplicated',
  GRAPH_TRAVERSED: 'graphrag.graph.traversed',
  QUERY_EXECUTED: 'graphrag.query.executed',
  ERROR_OCCURRED: 'error.occurred',
  ERROR_RECOVERED: 'error.recovered',
  CIRCUIT_BREAKER_OPENED: 'circuit_breaker.opened',
  CIRCUIT_BREAKER_CLOSED: 'circuit_breaker.closed',
  CUSTOM: 'custom',
} as const;

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
export type LogRecord = Record<string, unknown>;
export type StructuredLogSink = (record: LogRecord) => void;

let currentContext: Record<string, unknown> = {};

export class LogContext {
  private previousContext: Record<string, unknown> = {};

  constructor(readonly context: Record<string, unknown> = {}) {}

  enter(): this {
    this.previousContext = { ...currentContext };
    currentContext = { ...currentContext, ...this.context };
    return this;
  }

  exit(): void {
    currentContext = { ...this.previousContext };
  }

  run<T>(fn: () => T): T {
    this.enter();
    try {
      return fn();
    } finally {
      this.exit();
    }
  }
}

export function getCurrentContext(): Record<string, unknown> {
  return { ...currentContext };
}

export function setContext(context: Record<string, unknown>): void {
  currentContext = { ...currentContext, ...context };
}

export function clearContext(): void {
  currentContext = {};
}

export function getStructuredLoggingMetadata(): StructuredLoggingMetadata {
  return { ...STRUCTURED_LOGGING_METADATA };
}

export function normalizeLogLevel(level: string): LogLevel {
  const normalized = level.trim().toUpperCase();
  if (normalized === 'WARN') return 'WARNING';
  if (
    normalized === 'DEBUG' ||
    normalized === 'INFO' ||
    normalized === 'WARNING' ||
    normalized === 'ERROR'
  ) {
    return normalized;
  }
  return 'INFO';
}

export function serializeJsonLogLine(record: LogRecord): string {
  return JSON.stringify(record);
}

export class StructuredLogger {
  readonly records: LogRecord[] = [];

  constructor(
    readonly name: string,
    private readonly now = () => new Date().toISOString(),
    private readonly sink?: StructuredLogSink,
  ) {}

  log(level: LogLevel, message: string, extra: Record<string, unknown> = {}): LogRecord {
    const record: LogRecord = {
      [LogField.TIMESTAMP]: this.now(),
      [LogField.SCHEMA_VERSION]: LOG_SCHEMA_VERSION,
      [LogField.LEVEL]: normalizeLogLevel(level),
      [LogField.LOGGER_NAME]: this.name,
      [LogField.MESSAGE]: message,
      ...getCurrentContext(),
      ...extra,
    };
    this.records.push(record);
    try {
      this.sink?.(record);
    } catch (error) {
      this.records.push({
        [LogField.TIMESTAMP]: this.now(),
        [LogField.SCHEMA_VERSION]: LOG_SCHEMA_VERSION,
        [LogField.LEVEL]: 'ERROR',
        [LogField.LOGGER_NAME]: this.name,
        [LogField.MESSAGE]: 'Structured log sink failed closed',
        [LogField.EVENT_TYPE]: EventType.ERROR_OCCURRED,
        [LogField.ERROR_TYPE]: error instanceof Error ? error.name : 'Error',
        [LogField.ERROR_MESSAGE]: error instanceof Error ? error.message : String(error),
      });
    }
    return record;
  }

  debug(message: string, extra: Record<string, unknown> = {}): LogRecord {
    return this.log('DEBUG', message, extra);
  }

  info(message: string, extra: Record<string, unknown> = {}): LogRecord {
    return this.log('INFO', message, extra);
  }

  warning(message: string, extra: Record<string, unknown> = {}): LogRecord {
    return this.log('WARNING', message, extra);
  }

  error(message: string, extra: Record<string, unknown> = {}): LogRecord {
    return this.log('ERROR', message, extra);
  }

  toJsonLines(): string {
    return this.records.map((record) => serializeJsonLogLine(record)).join('\n');
  }

  exportSnapshot(exportedAt: string | number = this.now()): Record<string, unknown> {
    return {
      exported_at: exportedAt,
      metadata: getStructuredLoggingMetadata(),
      logger: this.name,
      records: this.records.map((record) => ({ ...record })),
    };
  }
}

const loggers = new Map<string, StructuredLogger>();

export function getLogger(name: string): StructuredLogger {
  if (!loggers.has(name)) loggers.set(name, new StructuredLogger(name));
  return loggers.get(name)!;
}

export function logEvent(
  eventType: string,
  logger = getLogger('root'),
  level: LogLevel = 'INFO',
  extra: Record<string, unknown> = {},
): LogRecord {
  return logger.log(level, `Event: ${eventType}`, { ...extra, [LogField.EVENT_TYPE]: eventType });
}

export function logError(
  error: Error,
  logger = getLogger('root'),
  extra: Record<string, unknown> = {},
): LogRecord {
  return logger.error(`Error: ${error.name}: ${error.message}`, {
    ...extra,
    [LogField.EVENT_TYPE]: EventType.ERROR_OCCURRED,
    [LogField.ERROR_TYPE]: error.name,
    [LogField.ERROR_MESSAGE]: error.message,
    [LogField.ERROR_STACK]: error.stack,
  });
}

export function logPerformance(
  operation: string,
  durationMs: number,
  logger = getLogger('root'),
  extra: Record<string, unknown> = {},
): LogRecord {
  return logger.info(`Performance: ${operation} completed in ${durationMs.toFixed(2)}ms`, {
    ...extra,
    [LogField.EVENT_TYPE]: 'performance.measured',
    operation,
    [LogField.DURATION_MS]: durationMs,
  });
}

export function logMcpTool(
  toolName: string,
  status: 'invoked' | 'completed' | 'failed',
  options: { durationMs?: number; logger?: StructuredLogger; extra?: Record<string, unknown> } = {},
): LogRecord {
  const eventType =
    status === 'invoked'
      ? EventType.TOOL_INVOKED
      : status === 'completed'
        ? EventType.TOOL_COMPLETED
        : EventType.TOOL_FAILED;
  return (options.logger ?? getLogger('root')).info(`Tool ${toolName} ${status}`, {
    ...(options.extra ?? {}),
    [LogField.TOOL_NAME]: toolName,
    [LogField.EVENT_TYPE]: eventType,
    ...(options.durationMs === undefined ? {} : { [LogField.DURATION_MS]: options.durationMs }),
  });
}

export function filterLogs(
  records: LogRecord[],
  criteria: { level?: string; eventType?: string; component?: string; requestId?: string } = {},
): LogRecord[] {
  return records.filter((record) => {
    if (criteria.level && record[LogField.LEVEL] !== criteria.level) return false;
    if (criteria.eventType && record[LogField.EVENT_TYPE] !== criteria.eventType) return false;
    if (criteria.component && record[LogField.COMPONENT] !== criteria.component) return false;
    if (criteria.requestId && record[LogField.REQUEST_ID] !== criteria.requestId) return false;
    return true;
  });
}

export function parseJsonLogLines(text: string): LogRecord[] {
  return parseJsonLogLinesDetailed(text).records;
}

export function parseJsonLogLinesDetailed(text: string): ParsedJsonLogLines {
  const records: Array<LogRecord> = [];
  const rejected_lines: Array<{ line: string; reason: string }> = [];
  for (const line of text.split(/\r?\n/)) {
    if (line.length === 0) continue;
    try {
      const parsed = JSON.parse(line) as unknown;
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        records.push(parsed as LogRecord);
      } else {
        rejected_lines.push({ line, reason: 'not an object record' });
      }
    } catch (error) {
      rejected_lines.push({ line, reason: error instanceof Error ? error.message : String(error) });
    }
  }
  return { records, rejected_lines };
}
