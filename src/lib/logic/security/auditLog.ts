export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface AuditLogMetadata {
  sourcePythonModule: 'logic/security/audit_log.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  storage: 'memory';
}

export interface AuditEvent {
  timestamp: string;
  event_type: string;
  user_id: string;
  success: boolean;
  details?: Record<string, unknown>;
  [key: string]: unknown;
}

export type AuditEventListener = (event: AuditEvent) => void;

export interface AuditLoggerOptions {
  now?: () => string;
  maxEvents?: number;
  listeners?: Array<AuditEventListener>;
}

export const AUDIT_LOG_METADATA: AuditLogMetadata = {
  sourcePythonModule: 'logic/security/audit_log.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  storage: 'memory',
};

export class AuditLogger {
  readonly metadata = AUDIT_LOG_METADATA;
  readonly events: AuditEvent[] = [];
  private readonly listeners: Array<AuditEventListener>;
  private readonly maxEvents: number;
  private readonly now: () => string;

  constructor(nowOrOptions: (() => string) | AuditLoggerOptions = () => new Date().toISOString()) {
    const options: AuditLoggerOptions =
      typeof nowOrOptions === 'function' ? { now: nowOrOptions } : nowOrOptions;
    this.now = options.now ?? (() => new Date().toISOString());
    this.maxEvents = Math.max(0, Math.floor(options.maxEvents ?? Number.POSITIVE_INFINITY));
    this.listeners = [...(options.listeners ?? [])];
  }

  addEventListener(listener: AuditEventListener): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index >= 0) {
        this.listeners.splice(index, 1);
      }
    };
  }

  logEvent(
    eventType: string,
    userId: string,
    success: boolean,
    details?: Record<string, unknown>,
    extra: Record<string, unknown> = {},
  ): AuditEvent {
    const event: AuditEvent = {
      timestamp: this.now(),
      event_type: eventType,
      user_id: userId,
      success,
      ...extra,
    };
    if (details) event.details = { ...details };
    this.events.push(event);
    if (this.events.length > this.maxEvents) {
      this.events.splice(0, this.events.length - this.maxEvents);
    }
    for (const listener of this.listeners) {
      listener({ ...event, details: event.details ? { ...event.details } : undefined });
    }
    return event;
  }

  logProofAttempt(
    userId: string,
    formula: string,
    prover: string,
    success: boolean,
    durationMs: number,
    options: { cached?: boolean; error?: string } = {},
  ): AuditEvent {
    const details: Record<string, unknown> = {
      formula: formula.slice(0, 100),
      prover,
      duration_ms: durationMs,
      cached: options.cached ?? false,
    };
    if (options.error) details.error = options.error;
    return this.logEvent('proof_attempt', userId, success, details);
  }

  logSecurityEvent(
    userId: string,
    eventType: string,
    severity: AuditSeverity,
    message: string,
    details: Record<string, unknown> = {},
  ): AuditEvent {
    return this.logEvent(`security.${eventType}`, userId, false, {
      severity,
      message,
      ...details,
    });
  }

  logRateLimitExceeded(userId: string, calls: number, period: number): AuditEvent {
    return this.logSecurityEvent(
      userId,
      'rate_limit_exceeded',
      'medium',
      `User exceeded rate limit of ${calls} calls per ${period}s`,
      { limit_calls: calls, limit_period: period },
    );
  }

  logValidationError(userId: string, validationType: string, errorMessage: string): AuditEvent {
    return this.logSecurityEvent(
      userId,
      'validation_error',
      'low',
      `Input validation failed: ${validationType}`,
      {
        validation_type: validationType,
        error: errorMessage,
      },
    );
  }

  toJsonLines(): string {
    return this.events.map((event) => JSON.stringify(event)).join('\n');
  }

  toJson(): string {
    return JSON.stringify(this.events);
  }

  getEvents(
    options: { eventType?: string; userId?: string; limit?: number } = {},
  ): Array<AuditEvent> {
    const filtered = this.events.filter((event) => {
      if (options.eventType !== undefined && event.event_type !== options.eventType) {
        return false;
      }
      if (options.userId !== undefined && event.user_id !== options.userId) {
        return false;
      }
      return true;
    });
    const limit =
      options.limit === undefined ? filtered.length : Math.max(0, Math.floor(options.limit));
    return filtered.slice(Math.max(0, filtered.length - limit)).map((event) => ({
      ...event,
      details: event.details ? { ...event.details } : undefined,
    }));
  }

  clear(): void {
    this.events.length = 0;
  }
}

let globalAuditLogger: AuditLogger | undefined;

export function getAuditLogger(): AuditLogger {
  globalAuditLogger ??= new AuditLogger();
  return globalAuditLogger;
}

export function setAuditLogger(logger: AuditLogger | undefined): void {
  globalAuditLogger = logger;
}

export function logProofAttempt(
  userId: string,
  formula: string,
  prover: string,
  success: boolean,
  durationMs: number,
  cached = false,
  error?: string,
): AuditEvent {
  return getAuditLogger().logProofAttempt(userId, formula, prover, success, durationMs, {
    cached,
    error,
  });
}

export function logSecurityEvent(
  userId: string,
  eventType: string,
  severity: AuditSeverity,
  message: string,
  details: Record<string, unknown> = {},
): AuditEvent {
  return getAuditLogger().logSecurityEvent(userId, eventType, severity, message, details);
}
