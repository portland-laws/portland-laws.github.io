export class RateLimitExceeded extends Error {
  constructor(
    message: string,
    readonly userId: string,
    readonly waitTimeSeconds: number,
  ) {
    super(message);
    this.name = 'RateLimitExceeded';
  }
}

export class RateLimiter {
  private readonly cache = new Map<string, number[]>();

  constructor(
    readonly calls = 100,
    readonly period = 60,
    private readonly now = () => Date.now() / 1000,
  ) {}

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

  wrap<TArgs extends unknown[], TResult>(fn: (...args: TArgs) => TResult, userIdSelector?: (...args: TArgs) => string | undefined): (...args: TArgs) => TResult {
    return (...args: TArgs) => {
      this.checkRateLimit(userIdSelector?.(...args) ?? 'default');
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

  snapshot(): Record<string, number[]> {
    return Object.fromEntries([...this.cache.entries()].map(([key, values]) => [key, [...values]]));
  }

  private prune(userId: string, current: number): number[] {
    const window = (this.cache.get(userId) ?? []).filter((timestamp) => current - timestamp < this.period);
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

export function rateLimit<TArgs extends unknown[], TResult>(fn: (...args: TArgs) => TResult): (...args: TArgs) => TResult {
  return (...args: TArgs) => {
    getRateLimiter().checkRateLimit('default');
    return fn(...args);
  };
}
