export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface AuditEvent {
  timestamp: string;
  event_type: string;
  user_id: string;
  success: boolean;
  details?: Record<string, unknown>;
  [key: string]: unknown;
}

export class AuditLogger {
  readonly events: AuditEvent[] = [];

  constructor(readonly now = () => new Date().toISOString()) {}

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
    return this.logSecurityEvent(userId, 'validation_error', 'low', `Input validation failed: ${validationType}`, {
      validation_type: validationType,
      error: errorMessage,
    });
  }

  toJsonLines(): string {
    return this.events.map((event) => JSON.stringify(event)).join('\n');
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
  return getAuditLogger().logProofAttempt(userId, formula, prover, success, durationMs, { cached, error });
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
