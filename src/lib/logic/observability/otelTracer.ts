export type SpanStatus = 'unset' | 'ok' | 'error';
export type OtelEventType =
  | 'circuit_breaker.state_change'
  | 'circuit_breaker.call'
  | 'circuit_breaker.error'
  | 'log.entry'
  | 'error';

export interface OtelIntegrationMetadata {
  sourcePythonModule: 'logic/observability/otel_integration.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  filesystemAllowed: false;
  subprocessAllowed: false;
}

export interface OtelIntegrationOptions {
  serviceName?: string;
  exporterEndpoint?: string;
  enabled?: boolean;
}

export const OTEL_INTEGRATION_METADATA: OtelIntegrationMetadata = {
  sourcePythonModule: 'logic/observability/otel_integration.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
};

export interface SpanEvent {
  name: string;
  timestamp: number;
  attributes: Record<string, unknown>;
}

export class Span {
  endTime?: number;
  status: SpanStatus = 'unset';
  readonly events: SpanEvent[] = [];

  constructor(
    readonly name: string,
    readonly spanId: string,
    readonly traceId: string,
    readonly parentSpanId: string | undefined,
    readonly startTime: number,
    readonly attributes: Record<string, unknown> = {},
  ) {}

  isActive(): boolean {
    return this.endTime === undefined;
  }

  durationMs(now = Date.now() / 1000): number {
    return ((this.endTime ?? now) - this.startTime) * 1000;
  }
}

export class Trace {
  readonly spans: Span[] = [];
  endTime?: number;

  constructor(
    readonly traceId: string,
    readonly startTime = Date.now() / 1000,
  ) {}

  rootSpan(): Span | undefined {
    return this.spans.find((span) => span.parentSpanId === undefined);
  }

  durationMs(now = Date.now() / 1000): number {
    return ((this.endTime ?? now) - this.startTime) * 1000;
  }
}

export class OTelTracer {
  private currentTraceId?: string;
  private readonly spanStack: string[] = [];
  private readonly traces = new Map<string, Trace>();
  private readonly completedTraces: Trace[] = [];
  private readonly maxCompletedTraces = 100;

  constructor(
    readonly serviceName: string,
    private readonly now = () => Date.now() / 1000,
    private readonly idFactory = () => cryptoSafeId(),
  ) {}

  startSpan(name: string, attributes: Record<string, unknown> = {}, parentSpanId?: string): Span {
    const traceId = this.getCurrentTraceId();
    const span = new Span(
      name,
      this.idFactory(),
      traceId,
      parentSpanId ?? this.getCurrentSpanId(),
      this.now(),
      { ...attributes },
    );
    if (!this.traces.has(traceId)) this.traces.set(traceId, new Trace(traceId, this.now()));
    this.traces.get(traceId)!.spans.push(span);
    this.spanStack.push(span.spanId);
    return span;
  }

  endSpan(span: Span, status: SpanStatus = 'ok'): void {
    span.endTime = this.now();
    span.status = status;
    this.spanStack.pop();
    if (span.parentSpanId === undefined && this.traces.has(span.traceId)) {
      const trace = this.traces.get(span.traceId)!;
      trace.endTime = span.endTime;
      this.traces.delete(span.traceId);
      this.completedTraces.push(trace);
      if (this.completedTraces.length > this.maxCompletedTraces) this.completedTraces.shift();
    }
  }

  recordEvent(
    span: Span,
    eventType: OtelEventType,
    attributes: Record<string, unknown> = {},
  ): SpanEvent {
    const event = { name: eventType, timestamp: this.now(), attributes: { ...attributes } };
    span.events.push(event);
    return event;
  }

  recordError(
    span: Span,
    errorMessage: string,
    errorType = 'UnknownError',
    attributes: Record<string, unknown> = {},
  ): void {
    this.recordEvent(span, 'error', {
      ...attributes,
      'error.type': errorType,
      'error.message': errorMessage,
    });
    span.status = 'error';
  }

  spanContext<T>(name: string, attributes: Record<string, unknown>, fn: (span: Span) => T): T {
    const span = this.startSpan(name, attributes);
    try {
      const result = fn(span);
      this.endSpan(span, 'ok');
      return result;
    } catch (error) {
      this.recordError(
        span,
        error instanceof Error ? error.message : String(error),
        error instanceof Error ? error.name : 'Error',
      );
      this.endSpan(span, 'error');
      throw error;
    }
  }

  setSpanAttribute(span: Span, key: string, value: unknown): void {
    span.attributes[key] = value;
  }

  getActiveSpan(): Span | undefined {
    const spanId = this.getCurrentSpanId();
    const trace = this.currentTraceId ? this.traces.get(this.currentTraceId) : undefined;
    return trace?.spans.find((span) => span.spanId === spanId);
  }

  getTrace(traceId: string): Trace | undefined {
    return (
      this.traces.get(traceId) ?? this.completedTraces.find((trace) => trace.traceId === traceId)
    );
  }

  getCompletedTraces(): Trace[] {
    return [...this.completedTraces];
  }

  exportJaegerFormat(): string {
    return JSON.stringify(
      {
        data: this.completedTraces.map((trace) => ({
          traceID: trace.traceId,
          spans: trace.spans.map((span) => ({
            traceID: span.traceId,
            spanID: span.spanId,
            operationName: span.name,
            startTime: Math.trunc(span.startTime * 1e6),
            duration: Math.trunc(span.durationMs(this.now()) * 1000),
            references: span.parentSpanId
              ? [{ refType: 'CHILD_OF', traceID: span.parentSpanId }]
              : [],
            tags: Object.entries(span.attributes).map(([key, value]) => ({ key, value })),
            logs: span.events.map((event) => ({
              timestamp: Math.trunc(event.timestamp * 1e6),
              fields: Object.entries(event.attributes).map(([key, value]) => ({ key, value })),
            })),
          })),
        })),
      },
      null,
      2,
    );
  }

  setTraceContext(traceId: string): void {
    this.currentTraceId = traceId;
  }

  clearContext(): void {
    this.currentTraceId = undefined;
    this.spanStack.length = 0;
  }

  private getCurrentTraceId(): string {
    this.currentTraceId ??= this.idFactory();
    return this.currentTraceId;
  }

  private getCurrentSpanId(): string | undefined {
    return this.spanStack[this.spanStack.length - 1];
  }
}

let defaultTracer: OTelTracer | undefined;

export function setupOtelTracer(serviceName: string): OTelTracer {
  defaultTracer = new OTelTracer(serviceName);
  return defaultTracer;
}

export function getOtelTracer(): OTelTracer {
  defaultTracer ??= setupOtelTracer('default');
  return defaultTracer;
}

export class BrowserNativeOtelIntegration {
  readonly metadata = OTEL_INTEGRATION_METADATA;
  readonly tracer: OTelTracer;
  readonly serviceName: string;
  readonly exporterEndpoint?: string;
  readonly enabled: boolean;

  constructor(options: OtelIntegrationOptions = {}, tracer?: OTelTracer) {
    this.serviceName = normalizeServiceValue(options.serviceName, 'ipfs-datasets-logic');
    this.exporterEndpoint = normalizeOptionalString(options.exporterEndpoint);
    this.enabled = options.enabled !== false;
    this.tracer = tracer ?? new OTelTracer(this.serviceName);
  }

  instrument<T>(name: string, attributes: Record<string, unknown>, fn: (span: Span) => T): T {
    if (!this.enabled) return fn(newDisabledSpan(name, attributes));
    return this.tracer.spanContext(name, this.enrichAttributes(attributes), fn);
  }

  exportSnapshot(now = Date.now() / 1000): Record<string, unknown> {
    return {
      status: this.enabled ? 'success' : 'disabled',
      metadata: this.metadata,
      service: { name: this.serviceName },
      exporter: {
        endpoint: this.exporterEndpoint,
        mode: 'in-memory-browser-native',
        networkExportAttempted: false,
      },
      traces: this.tracer.getCompletedTraces().map((trace) => ({
        trace_id: trace.traceId,
        start_time: trace.startTime,
        end_time: trace.endTime,
        duration_ms: trace.durationMs(now),
        spans: trace.spans.map((span) => ({
          span_id: span.spanId,
          parent_span_id: span.parentSpanId,
          name: span.name,
          status: span.status,
          start_time: span.startTime,
          end_time: span.endTime,
          duration_ms: span.durationMs(now),
          attributes: { ...span.attributes },
          events: span.events.map((event) => ({
            name: event.name,
            timestamp: event.timestamp,
            attributes: { ...event.attributes },
          })),
        })),
      })),
    };
  }

  private enrichAttributes(attributes: Record<string, unknown>): Record<string, unknown> {
    return {
      'service.name': this.serviceName,
      ...attributes,
    };
  }
}

export function setupOtelIntegration(
  options: OtelIntegrationOptions = {},
): BrowserNativeOtelIntegration {
  const integration = new BrowserNativeOtelIntegration(options);
  defaultTracer = integration.tracer;
  return integration;
}

function cryptoSafeId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

function normalizeServiceValue(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim();
  return trimmed === undefined || trimmed.length === 0 ? fallback : trimmed;
}

function normalizeOptionalString(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed === undefined || trimmed.length === 0 ? undefined : trimmed;
}

function newDisabledSpan(name: string, attributes: Record<string, unknown>): Span {
  return new Span(name, 'disabled', 'disabled', undefined, 0, { ...attributes, disabled: true });
}
