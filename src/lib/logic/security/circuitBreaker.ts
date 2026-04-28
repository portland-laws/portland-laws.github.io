export type CircuitState = 'closed' | 'open' | 'half_open';

export interface CircuitBreakerStats {
  name: string;
  state: CircuitState;
  thresholds: {
    failure_threshold: number;
    success_threshold: number;
    timeout_seconds: number;
  };
  metrics: {
    total_calls: number;
    successes: number;
    failures: number;
    failure_rate: number;
    consecutive_failures: number;
    consecutive_successes: number;
    state_transitions: number;
    average_latency_ms: number;
  };
  timing: {
    last_failure?: number;
    last_success?: number;
    last_state_change: number;
    seconds_since_state_change: number;
  };
}

export class CircuitBreakerMetrics {
  successCount = 0;
  failureCount = 0;
  totalCalls = 0;
  lastFailureTime?: number;
  lastSuccessTime?: number;
  consecutiveSuccesses = 0;
  consecutiveFailures = 0;
  stateTransitions = 0;
  latencies: number[] = [];

  recordSuccess(latencySeconds: number, now: number): void {
    this.successCount += 1;
    this.totalCalls += 1;
    this.consecutiveSuccesses += 1;
    this.consecutiveFailures = 0;
    this.lastSuccessTime = now;
    this.latencies.push(latencySeconds);
    if (this.latencies.length > 100) this.latencies.shift();
  }

  recordFailure(now: number): void {
    this.failureCount += 1;
    this.totalCalls += 1;
    this.consecutiveFailures += 1;
    this.consecutiveSuccesses = 0;
    this.lastFailureTime = now;
  }

  recordStateTransition(): void {
    this.stateTransitions += 1;
  }

  getFailureRate(): number {
    return this.totalCalls === 0 ? 0 : this.failureCount / this.totalCalls;
  }

  getAverageLatency(): number {
    return this.latencies.length === 0 ? 0 : this.latencies.reduce((total, value) => total + value, 0) / this.latencies.length;
  }

  clone(): CircuitBreakerMetrics {
    const copy = new CircuitBreakerMetrics();
    Object.assign(copy, this, { latencies: [...this.latencies] });
    return copy;
  }
}

export class CircuitBreakerOpenError extends Error {
  constructor(message = 'Circuit breaker is OPEN', readonly breaker?: LLMCircuitBreaker) {
    super(message);
    this.name = 'CircuitBreakerOpenError';
  }
}

export class LLMCircuitBreaker {
  readonly failureThreshold: number;
  readonly timeoutSeconds: number;
  readonly successThreshold: number;
  readonly name: string;
  readonly fallback?: () => unknown;
  private currentState: CircuitState = 'closed';
  private lastStateChange: number;
  private currentMetrics = new CircuitBreakerMetrics();

  constructor(options: {
    failureThreshold?: number;
    timeoutSeconds?: number;
    successThreshold?: number;
    fallback?: () => unknown;
    name?: string;
    now?: () => number;
  } = {}) {
    this.failureThreshold = options.failureThreshold ?? 5;
    this.timeoutSeconds = options.timeoutSeconds ?? 60;
    this.successThreshold = options.successThreshold ?? 2;
    this.fallback = options.fallback;
    this.name = options.name ?? 'llm_circuit_breaker';
    this.now = options.now ?? (() => Date.now() / 1000);
    if (this.failureThreshold < 1) throw new Error('failure_threshold must be >= 1');
    if (this.timeoutSeconds <= 0) throw new Error('timeout_seconds must be > 0');
    if (this.successThreshold < 1) throw new Error('success_threshold must be >= 1');
    this.lastStateChange = this.now();
  }

  private readonly now: () => number;

  get state(): CircuitState {
    return this.currentState;
  }

  get metrics(): CircuitBreakerMetrics {
    return this.currentMetrics.clone();
  }

  refreshState(): CircuitState {
    if (this.currentState === 'open' && this.shouldAttemptReset()) {
      this.transitionTo('half_open');
    }
    return this.currentState;
  }

  call<TResult>(fn: () => TResult): TResult {
    const state = this.refreshState();
    if (state === 'open') {
      if (this.fallback) return this.fallback() as TResult;
      throw new CircuitBreakerOpenError(`Circuit breaker '${this.name}' is OPEN`, this);
    }

    const start = this.now();
    try {
      const result = fn();
      this.recordSuccess(this.now() - start);
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }

  protected<TArgs extends unknown[], TResult>(fn: (...args: TArgs) => TResult): (...args: TArgs) => TResult {
    return (...args: TArgs) => this.call(() => fn(...args));
  }

  reset(): void {
    this.transitionTo('closed');
    this.currentMetrics = new CircuitBreakerMetrics();
  }

  forceOpen(): void {
    this.transitionTo('open');
  }

  getStats(): CircuitBreakerStats {
    const metrics = this.metrics;
    return {
      name: this.name,
      state: this.currentState,
      thresholds: {
        failure_threshold: this.failureThreshold,
        success_threshold: this.successThreshold,
        timeout_seconds: this.timeoutSeconds,
      },
      metrics: {
        total_calls: metrics.totalCalls,
        successes: metrics.successCount,
        failures: metrics.failureCount,
        failure_rate: metrics.getFailureRate(),
        consecutive_failures: metrics.consecutiveFailures,
        consecutive_successes: metrics.consecutiveSuccesses,
        state_transitions: metrics.stateTransitions,
        average_latency_ms: metrics.getAverageLatency() * 1000,
      },
      timing: {
        last_failure: metrics.lastFailureTime,
        last_success: metrics.lastSuccessTime,
        last_state_change: this.lastStateChange,
        seconds_since_state_change: this.now() - this.lastStateChange,
      },
    };
  }

  toString(): string {
    return `LLMCircuitBreaker(name=${JSON.stringify(this.name)}, state=${this.currentState}, failures=${this.currentMetrics.consecutiveFailures}/${this.failureThreshold})`;
  }

  private shouldAttemptReset(): boolean {
    return this.now() - this.lastStateChange >= this.timeoutSeconds;
  }

  private recordSuccess(latencySeconds: number): void {
    this.currentMetrics.recordSuccess(latencySeconds, this.now());
    if (this.currentState === 'half_open' && this.currentMetrics.consecutiveSuccesses >= this.successThreshold) {
      this.transitionTo('closed');
    }
  }

  private recordFailure(): void {
    this.currentMetrics.recordFailure(this.now());
    if (this.currentState === 'closed' && this.currentMetrics.consecutiveFailures >= this.failureThreshold) {
      this.transitionTo('open');
    } else if (this.currentState === 'half_open') {
      this.transitionTo('open');
    }
  }

  private transitionTo(newState: CircuitState): void {
    if (this.currentState !== newState) {
      this.currentState = newState;
      this.lastStateChange = this.now();
      this.currentMetrics.recordStateTransition();
    }
  }
}

const globalBreakers = new Map<string, LLMCircuitBreaker>();

export function getCircuitBreaker(name: string, options: ConstructorParameters<typeof LLMCircuitBreaker>[0] = {}): LLMCircuitBreaker {
  if (!globalBreakers.has(name)) {
    globalBreakers.set(name, new LLMCircuitBreaker({ ...options, name }));
  }
  return globalBreakers.get(name)!;
}

export function resetAllCircuitBreakers(): number {
  for (const breaker of globalBreakers.values()) breaker.reset();
  return globalBreakers.size;
}

export function getAllCircuitBreakerStats(): Record<string, CircuitBreakerStats> {
  return Object.fromEntries([...globalBreakers.entries()].map(([name, breaker]) => [name, breaker.getStats()]));
}
