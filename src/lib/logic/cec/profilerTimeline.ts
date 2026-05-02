export type CecProfilerSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface CecProfilerSample {
  name: string;
  durationMs: number;
  startTimeMs?: number;
  calls?: number;
  category?: string;
  stack?: string[];
  metadata?: { [key: string]: unknown };
}

export interface CecTimelineEvent {
  name: string;
  category: string;
  startTimeMs: number;
  endTimeMs: number;
  durationMs: number;
  calls: number;
  metadata: { [key: string]: unknown };
}

export interface CecBrowserPerformanceTimeline {
  source: 'browser-performance-timeline';
  totalDurationMs: number;
  events: CecTimelineEvent[];
  marks: { name: string; timeMs: number }[];
}

export interface CecFlamegraphFrame {
  name: string;
  valueMs: number;
  selfMs: number;
  calls: number;
  children: CecFlamegraphFrame[];
}

export interface CecProfilerBottleneckFinding {
  function: string;
  severity: CecProfilerSeverity;
  durationMs: number;
  calls: number;
  timelineShare: number;
  recommendation: string;
}

export interface CecProfilerBottleneckReport {
  totalDurationMs: number;
  analyzedEvents: number;
  bottlenecks: CecProfilerBottleneckFinding[];
  recommendations: string[];
}

const round = (value: number): number => Math.round(value * 1000) / 1000;
const nonNegative = (value: number | undefined): number => Math.max(0, value ?? 0);

export function buildCecBrowserPerformanceTimeline(
  samples: CecProfilerSample[],
): CecBrowserPerformanceTimeline {
  let cursorMs = 0;
  const events = samples
    .map((sample) => {
      const durationMs = round(nonNegative(sample.durationMs));
      const startTimeMs = round(sample.startTimeMs ?? cursorMs);
      const event: CecTimelineEvent = {
        name: sample.name,
        category: sample.category ?? 'cec-proof',
        startTimeMs,
        endTimeMs: round(startTimeMs + durationMs),
        durationMs,
        calls: Math.max(1, Math.floor(sample.calls ?? 1)),
        metadata: sample.metadata ?? {},
      };
      cursorMs = event.endTimeMs;
      return event;
    })
    .sort(
      (left, right) => left.startTimeMs - right.startTimeMs || left.name.localeCompare(right.name),
    );

  const totalDurationMs = events.reduce((maxEnd, event) => Math.max(maxEnd, event.endTimeMs), 0);
  return {
    source: 'browser-performance-timeline',
    totalDurationMs: round(totalDurationMs),
    events,
    marks: events.flatMap((event) => [
      { name: `${event.name}:start`, timeMs: event.startTimeMs },
      { name: `${event.name}:end`, timeMs: event.endTimeMs },
    ]),
  };
}

export function buildCecFlamegraph(samples: CecProfilerSample[]): CecFlamegraphFrame {
  const root: CecFlamegraphFrame = { name: 'root', valueMs: 0, selfMs: 0, calls: 0, children: [] };

  for (const sample of samples) {
    const durationMs = round(nonNegative(sample.durationMs));
    const calls = Math.max(1, Math.floor(sample.calls ?? 1));
    const stack = sample.stack && sample.stack.length > 0 ? [...sample.stack] : [];
    if (stack[stack.length - 1] !== sample.name) stack.push(sample.name);

    root.valueMs = round(root.valueMs + durationMs);
    root.calls += calls;
    let frame = root;
    for (const name of stack) {
      let child = frame.children.find((candidate) => candidate.name === name);
      if (!child) {
        child = { name, valueMs: 0, selfMs: 0, calls: 0, children: [] };
        frame.children.push(child);
      }
      child.valueMs = round(child.valueMs + durationMs);
      child.calls += calls;
      frame = child;
    }
    frame.selfMs = round(frame.selfMs + durationMs);
  }

  sortFlamegraph(root);
  return root;
}

export function createCecProfilerBottleneckReport(
  samples: CecProfilerSample[],
): CecProfilerBottleneckReport {
  const timeline = buildCecBrowserPerformanceTimeline(samples);
  const totalDurationMs = timeline.totalDurationMs || 1;
  const bottlenecks = timeline.events
    .map((event) => {
      const timelineShare = round(event.durationMs / totalDurationMs);
      const severity = classifySeverity(event.durationMs, event.calls, timelineShare);
      return {
        function: event.name,
        severity,
        durationMs: event.durationMs,
        calls: event.calls,
        timelineShare,
        recommendation: recommendationFor(event.name, severity, event.calls, timelineShare),
      };
    })
    .filter((finding) => finding.severity !== 'low')
    .sort((left, right) => right.durationMs - left.durationMs || right.calls - left.calls);

  return {
    totalDurationMs: timeline.totalDurationMs,
    analyzedEvents: timeline.events.length,
    bottlenecks,
    recommendations: bottlenecks.map((finding) => finding.recommendation),
  };
}

function sortFlamegraph(frame: CecFlamegraphFrame): void {
  frame.children.sort(
    (left, right) => right.valueMs - left.valueMs || left.name.localeCompare(right.name),
  );
  frame.children.forEach(sortFlamegraph);
}

function classifySeverity(durationMs: number, calls: number, share: number): CecProfilerSeverity {
  if (durationMs >= 1000 || calls >= 2000 || share >= 0.6) return 'critical';
  if (durationMs >= 500 || calls >= 1000 || share >= 0.35) return 'high';
  if (durationMs >= 100 || calls >= 100 || share >= 0.15) return 'medium';
  return 'low';
}

function recommendationFor(
  name: string,
  severity: CecProfilerSeverity,
  calls: number,
  share: number,
): string {
  if (calls >= 1000) return `Reduce repeated ${name} calls with memoization or rule batching.`;
  if (share >= 0.35) return `Inspect ${name} strategy costs and add cheaper early-exit checks.`;
  if (severity === 'medium')
    return `Track ${name} in the browser timeline and compare against proof-size growth.`;
  return `No immediate action required for ${name}.`;
}
