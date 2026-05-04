import {
  buildCecBrowserPerformanceTimeline,
  createCecProfilerBottleneckReport,
  type CecProfilerSample,
} from './profilerTimeline';
import { calculateCecStats, type CecStatisticalSummary } from './performanceMetrics';

export interface CecProfilingUtilsMetadata {
  readonly sourcePythonModule: 'logic/CEC/optimization/profiling_utils.py';
  readonly runtime: 'browser-native-typescript';
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
}

export interface CecProfileMeasurement<T> {
  readonly name: string;
  readonly result: T;
  readonly durationMs: number;
  readonly startedAtMs: number;
  readonly endedAtMs: number;
  readonly metadata: CecProfilingUtilsMetadata;
}

export interface CecProfileSummary {
  readonly metadata: CecProfilingUtilsMetadata;
  readonly totalDurationMs: number;
  readonly sampleCount: number;
  readonly stats: CecStatisticalSummary;
  readonly slowest: readonly CecProfilerSample[];
  readonly bottlenecks: ReturnType<typeof createCecProfilerBottleneckReport>;
}

export const CEC_PROFILING_UTILS_METADATA: CecProfilingUtilsMetadata = {
  sourcePythonModule: 'logic/CEC/optimization/profiling_utils.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
};

export function measureCecProfile<T>(
  name: string,
  fn: () => T,
  now: () => number = nowMs,
): CecProfileMeasurement<T> {
  const startedAtMs = now();
  const result = fn();
  const endedAtMs = now();
  return {
    name,
    result,
    durationMs: Math.max(0, endedAtMs - startedAtMs),
    startedAtMs,
    endedAtMs,
    metadata: CEC_PROFILING_UTILS_METADATA,
  };
}

export function normalizeCecProfilerSamples(
  samples: readonly CecProfilerSample[],
): CecProfilerSample[] {
  return samples.map((sample, index) => ({
    name: sample.name.trim() || `sample_${index}`,
    durationMs: Math.max(0, sample.durationMs),
    startTimeMs: sample.startTimeMs === undefined ? undefined : Math.max(0, sample.startTimeMs),
    calls: Math.max(1, Math.floor(sample.calls ?? 1)),
    category: sample.category ?? 'cec-proof',
    stack: sample.stack ? [...sample.stack] : undefined,
    metadata: sample.metadata ?? {},
  }));
}

export function summarizeCecProfiling(
  samples: readonly CecProfilerSample[],
  options: { topN?: number } = {},
): CecProfileSummary {
  const normalized = normalizeCecProfilerSamples(samples);
  const timeline = buildCecBrowserPerformanceTimeline(normalized);
  const stats = calculateCecStats(normalized.map((sample) => sample.durationMs));
  const topN = Math.max(1, Math.floor(options.topN ?? 5));
  return {
    metadata: CEC_PROFILING_UTILS_METADATA,
    totalDurationMs: timeline.totalDurationMs,
    sampleCount: normalized.length,
    stats,
    slowest: [...normalized]
      .sort((left, right) => right.durationMs - left.durationMs)
      .slice(0, topN),
    bottlenecks: createCecProfilerBottleneckReport(normalized),
  };
}

export const measure_cec_profile = measureCecProfile;
export const normalize_cec_profiler_samples = normalizeCecProfilerSamples;
export const summarize_cec_profiling = summarizeCecProfiling;

function nowMs(): number {
  return typeof globalThis.performance?.now === 'function'
    ? globalThis.performance.now()
    : Date.now();
}
