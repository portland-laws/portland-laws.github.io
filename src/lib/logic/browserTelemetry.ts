export type BrowserTelemetryMetricKind = 'counter' | 'gauge' | 'timing';

export interface BrowserTelemetryTags {
  readonly [key: string]: string;
}

export interface BrowserTelemetryEvent {
  readonly name: string;
  readonly kind: BrowserTelemetryMetricKind;
  readonly value: number;
  readonly timestampMs: number;
  readonly tags: BrowserTelemetryTags;
}

export interface BrowserTelemetryMetricSnapshot {
  readonly name: string;
  readonly kind: BrowserTelemetryMetricKind;
  readonly count: number;
  readonly total: number;
  readonly min: number;
  readonly max: number;
  readonly latest: number;
  readonly average: number;
  readonly tags: BrowserTelemetryTags;
}

export interface BrowserTelemetrySnapshot {
  readonly generatedAtMs: number;
  readonly metrics: BrowserTelemetryMetricSnapshot[];
  readonly recentEvents: BrowserTelemetryEvent[];
}

export interface BrowserDeveloperPanelSummary {
  readonly generatedAtMs: number;
  readonly metricCount: number;
  readonly eventCount: number;
  readonly counters: BrowserTelemetryMetricSnapshot[];
  readonly gauges: BrowserTelemetryMetricSnapshot[];
  readonly timings: BrowserTelemetryMetricSnapshot[];
  readonly warnings: string[];
}

export interface BrowserTelemetryOptions {
  readonly maxEvents?: number;
  readonly now?: () => number;
}

interface BrowserTelemetryBucket {
  name: string;
  kind: BrowserTelemetryMetricKind;
  count: number;
  total: number;
  min: number;
  max: number;
  latest: number;
  tags: BrowserTelemetryTags;
}

interface BrowserTelemetryBucketMap {
  [key: string]: BrowserTelemetryBucket;
}

const DEFAULT_MAX_EVENTS = 100;

function stableTags(tags?: BrowserTelemetryTags): BrowserTelemetryTags {
  const stable: { [key: string]: string } = {};
  if (!tags) {
    return stable;
  }
  for (const key of Object.keys(tags).sort()) {
    const value = tags[key];
    if (typeof value === 'string' && value.length > 0) {
      stable[key] = value;
    }
  }
  return stable;
}

function metricKey(
  name: string,
  kind: BrowserTelemetryMetricKind,
  tags: BrowserTelemetryTags,
): string {
  const encodedTags = Object.keys(tags)
    .map((key) => key + '=' + tags[key])
    .join(',');
  return kind + ':' + name + ':' + encodedTags;
}

function assertMetricInput(name: string, value: number): void {
  if (typeof name !== 'string' || name.trim().length === 0) {
    throw new Error('Telemetry metric name must be a non-empty string.');
  }
  if (!Number.isFinite(value)) {
    throw new Error('Telemetry metric value must be finite.');
  }
}

function cloneTags(tags: BrowserTelemetryTags): BrowserTelemetryTags {
  return { ...tags };
}

function snapshotBucket(bucket: BrowserTelemetryBucket): BrowserTelemetryMetricSnapshot {
  return {
    name: bucket.name,
    kind: bucket.kind,
    count: bucket.count,
    total: bucket.total,
    min: bucket.min,
    max: bucket.max,
    latest: bucket.latest,
    average: bucket.count === 0 ? 0 : bucket.total / bucket.count,
    tags: cloneTags(bucket.tags),
  };
}

export class BrowserTelemetryCollector {
  private readonly maxEvents: number;
  private readonly now: () => number;
  private readonly buckets: BrowserTelemetryBucketMap = {};
  private readonly events: BrowserTelemetryEvent[] = [];

  constructor(options: BrowserTelemetryOptions = {}) {
    this.maxEvents = Math.max(0, Math.floor(options.maxEvents ?? DEFAULT_MAX_EVENTS));
    this.now = options.now ?? (() => Date.now());
  }

  increment(name: string, value = 1, tags?: BrowserTelemetryTags): void {
    this.record(name, 'counter', value, tags);
  }

  gauge(name: string, value: number, tags?: BrowserTelemetryTags): void {
    this.record(name, 'gauge', value, tags);
  }

  timing(name: string, durationMs: number, tags?: BrowserTelemetryTags): void {
    this.record(name, 'timing', durationMs, tags);
  }

  record(
    name: string,
    kind: BrowserTelemetryMetricKind,
    value: number,
    tags?: BrowserTelemetryTags,
  ): void {
    const metricName = name.trim();
    assertMetricInput(metricName, value);
    const stable = stableTags(tags);
    const key = metricKey(metricName, kind, stable);
    const existing = this.buckets[key];
    if (existing) {
      existing.count += 1;
      existing.total += value;
      existing.min = Math.min(existing.min, value);
      existing.max = Math.max(existing.max, value);
      existing.latest = value;
    } else {
      this.buckets[key] = {
        name: metricName,
        kind,
        count: 1,
        total: value,
        min: value,
        max: value,
        latest: value,
        tags: stable,
      };
    }
    this.pushEvent({
      name: metricName,
      kind,
      value,
      timestampMs: this.now(),
      tags: cloneTags(stable),
    });
  }

  snapshot(): BrowserTelemetrySnapshot {
    return {
      generatedAtMs: this.now(),
      metrics: Object.keys(this.buckets)
        .sort()
        .map((key) => snapshotBucket(this.buckets[key])),
      recentEvents: this.events.map((event) => ({ ...event, tags: cloneTags(event.tags) })),
    };
  }

  developerPanelSummary(): BrowserDeveloperPanelSummary {
    const snapshot = this.snapshot();
    const warnings: string[] = [];
    for (const metric of snapshot.metrics) {
      if (metric.kind === 'timing' && metric.max > 1000) {
        warnings.push(metric.name + ' exceeded 1000ms');
      }
    }
    return {
      generatedAtMs: snapshot.generatedAtMs,
      metricCount: snapshot.metrics.length,
      eventCount: snapshot.recentEvents.length,
      counters: snapshot.metrics.filter((metric) => metric.kind === 'counter'),
      gauges: snapshot.metrics.filter((metric) => metric.kind === 'gauge'),
      timings: snapshot.metrics.filter((metric) => metric.kind === 'timing'),
      warnings,
    };
  }

  reset(): void {
    for (const key of Object.keys(this.buckets)) {
      delete this.buckets[key];
    }
    this.events.length = 0;
  }

  private pushEvent(event: BrowserTelemetryEvent): void {
    if (this.maxEvents === 0) {
      return;
    }
    this.events.push(event);
    while (this.events.length > this.maxEvents) {
      this.events.shift();
    }
  }
}

export function createBrowserTelemetryCollector(
  options?: BrowserTelemetryOptions,
): BrowserTelemetryCollector {
  return new BrowserTelemetryCollector(options);
}
