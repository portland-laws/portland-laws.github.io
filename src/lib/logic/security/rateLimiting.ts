export const RATE_LIMITING_METADATA = {
  sourcePythonModule: 'logic/security/rate_limiting.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  algorithm: 'sliding_window',
  defaultCalls: 100,
  defaultPeriodSeconds: 60,
} as const;

export interface RateLimiterOptions {
  calls?: number;
  period?: number;
  now?: () => number;
}

export class RateLimitExceeded extends Error {
  constructor(
    message: string,
    readonly userId = 'default',
    readonly waitTimeSeconds = 0,
  ) {
    super(message);
    this.name = 'RateLimitExceeded';
  }
}

export class RateLimiter {
  readonly calls: number;
  readonly period: number;
  readonly metadata = RATE_LIMITING_METADATA;

  private readonly cache = new Map<string, number[]>();
  private readonly now: () => number;

  constructor(
    callsOrOptions: number | RateLimiterOptions = RATE_LIMITING_METADATA.defaultCalls,
    period: number = RATE_LIMITING_METADATA.defaultPeriodSeconds,
    now: () => number = () => Date.now() / 1000,
  ) {
    if (typeof callsOrOptions === 'number') {
      this.calls = callsOrOptions;
      this.period = period;
      this.now = now;
    } else {
      this.calls = callsOrOptions.calls ?? RATE_LIMITING_METADATA.defaultCalls;
      this.period = callsOrOptions.period ?? RATE_LIMITING_METADATA.defaultPeriodSeconds;
      this.now = callsOrOptions.now ?? now;
    }

    if (!Number.isFinite(this.calls) || this.calls < 1) {
      throw new RangeError("'calls' must be a positive finite number.");
    }
    if (!Number.isFinite(this.period) || this.period <= 0) {
      throw new RangeError("'period' must be a positive finite number of seconds.");
    }
  }

  checkRateLimit(userId = 'default'): void {
    const current = this.now();
    const window = this.prune(userId, current);
    if (window.length >= this.calls) {
      const oldest = window[0] ?? current;
      const waitTime = Math.max(0, this.period - (current - oldest));
      throw new RateLimitExceeded(
        `Rate limit exceeded: ${this.calls} calls per ${this.period}s. Try again in ${waitTime.toFixed(1)}s`,
        userId,
        waitTime,
      );
    }
    window.push(current);
    this.cache.set(userId, window);
  }

  check_rate_limit(userId = 'default'): void {
    this.checkRateLimit(userId);
  }

  wrap<TArgs extends Array<unknown>, TResult>(
    fn: (...args: TArgs) => TResult,
    userIdSelector?: (...args: TArgs) => string | undefined,
  ): (...args: TArgs) => TResult {
    return (...args: TArgs) => {
      this.checkRateLimit(userIdSelector?.(...args) ?? extractUserId(args));
      return fn(...args);
    };
  }

  reset(userId?: string): void {
    if (userId === undefined) {
      this.cache.clear();
    } else {
      this.cache.delete(userId);
    }
  }

  getRemaining(userId = 'default'): number {
    return Math.max(0, this.calls - this.prune(userId, this.now()).length);
  }

  get_remaining(userId = 'default'): number {
    return this.getRemaining(userId);
  }

  snapshot(): Record<string, Array<number>> {
    return Object.fromEntries([...this.cache.entries()].map(([key, values]) => [key, [...values]]));
  }

  private prune(userId: string, current: number): number[] {
    const window = (this.cache.get(userId) ?? []).filter(
      (timestamp) => current - timestamp < this.period,
    );
    this.cache.set(userId, window);
    return window;
  }
}

let globalRateLimiter: RateLimiter | undefined;

export function getRateLimiter(): RateLimiter {
  globalRateLimiter ??= new RateLimiter();
  return globalRateLimiter;
}

export function setRateLimiter(rateLimiter: RateLimiter | undefined): void {
  globalRateLimiter = rateLimiter;
}

export function get_rate_limiter(): RateLimiter {
  return getRateLimiter();
}

export function set_rate_limiter(rateLimiter: RateLimiter | undefined): void {
  setRateLimiter(rateLimiter);
}

export function rateLimit<TArgs extends Array<unknown>, TResult>(
  fn: (...args: TArgs) => TResult,
): (...args: TArgs) => TResult {
  return (...args: TArgs) => {
    getRateLimiter().checkRateLimit(extractUserId(args));
    return fn(...args);
  };
}

export const rate_limit = rateLimit;

function extractUserId(args: Array<unknown>): string {
  for (const arg of args) {
    if (isUserIdCarrier(arg)) {
      return arg.user_id ?? arg.userId ?? 'default';
    }
  }
  return 'default';
}

function isUserIdCarrier(value: unknown): value is { user_id?: string; userId?: string } {
  if (value === null || typeof value !== 'object') {
    return false;
  }
  const record = value as Record<string, unknown>;
  return typeof record.user_id === 'string' || typeof record.userId === 'string';
}
