import {
  buildCecBrowserPerformanceTimeline,
  buildCecFlamegraph,
  createCecProfilerBottleneckReport,
} from './profilerTimeline';
import {
  CecPerformanceProfiler,
  getStandardCecBenchmarks,
  profileCecFunction,
} from './performanceProfiler';
import {
  measure_cec_profile,
  normalizeCecProfilerSamples,
  summarizeCecProfiling,
} from './profilingUtils';

describe('CecPerformanceProfiler', () => {
  it('profiles repeated function execution and stores history', () => {
    const profiler = new CecPerformanceProfiler();
    const stats = profiler.profileFunction('quickCecOp', () => 1 + 1, 3);

    expect(stats).toMatchObject({
      functionName: 'quickCecOp',
      runs: 3,
      callsPerRun: 1,
      meetsThreshold: true,
    });
    expect(stats.meanTimeMs).toBeGreaterThanOrEqual(0);
    expect(profiler.history).toHaveLength(1);
  });

  it('identifies CEC bottlenecks with severity and recommendations', () => {
    const profiler = new CecPerformanceProfiler();
    const bottlenecks = profiler.identifyBottlenecks([
      { function: 'proveCecGoal', timeMs: 1200, calls: 1 },
      { function: 'minorRule', timeMs: 20, calls: 2 },
      { function: 'nestedRuleLoop', timeMs: 2, calls: 2001 },
      { function: 'strategySelector', timeMs: 200, calls: 1 },
    ]);

    expect(bottlenecks.find((b) => b.function === 'nestedRuleLoop')).toMatchObject({
      function: 'nestedRuleLoop',
      severity: 'critical',
      complexityEstimate: 'O(n^3)',
    });
    expect(bottlenecks.find((b) => b.function === 'strategySelector')?.recommendation).toContain(
      'strategy costs',
    );
    expect(bottlenecks.map((b) => b.severity)).toContain('medium');
  });

  it('builds browser-native timelines, flamegraphs, and richer bottleneck reports', () => {
    const samples = [
      {
        name: 'parseCec',
        durationMs: 10,
        startTimeMs: 0,
        category: 'parse',
        stack: ['prove'],
        metadata: { expressionType: 'deontic' },
      },
      { name: 'strategySelector', durationMs: 210, startTimeMs: 10, calls: 1, stack: ['prove'] },
      {
        name: 'nestedRuleLoop',
        durationMs: 5,
        startTimeMs: 220,
        calls: 2500,
        stack: ['prove', 'rules'],
      },
    ];

    const timeline = buildCecBrowserPerformanceTimeline(samples);
    expect(timeline).toMatchObject({
      source: 'browser-performance-timeline',
      totalDurationMs: 225,
      events: [
        { name: 'parseCec', category: 'parse', startTimeMs: 0, endTimeMs: 10, durationMs: 10 },
        { name: 'strategySelector', startTimeMs: 10, endTimeMs: 220, durationMs: 210 },
        { name: 'nestedRuleLoop', startTimeMs: 220, endTimeMs: 225, durationMs: 5, calls: 2500 },
      ],
    });
    expect(timeline.marks.map((mark) => mark.name)).toContain('strategySelector:end');

    const flamegraph = buildCecFlamegraph(samples);
    expect(flamegraph.children[0]).toMatchObject({ name: 'prove', valueMs: 225, calls: 2502 });
    expect(
      flamegraph.children[0].children.find((frame) => frame.name === 'strategySelector'),
    ).toMatchObject({ selfMs: 210 });

    const report = createCecProfilerBottleneckReport(samples);
    expect(report).toMatchObject({ totalDurationMs: 225, analyzedEvents: 3 });
    expect(
      report.bottlenecks.find((finding) => finding.function === 'nestedRuleLoop'),
    ).toMatchObject({
      severity: 'critical',
      calls: 2500,
    });
    expect(report.recommendations.join('\n')).toContain('strategy costs');
  });

  it('profiles browser memory snapshots without requiring Python memory tooling', () => {
    const profiler = new CecPerformanceProfiler();
    const memory = profiler.memoryProfile('allocate', () =>
      Array.from({ length: 10 }, (_, index) => index),
    );

    expect(memory).toMatchObject({
      functionName: 'allocate',
      allocations: 0,
      deallocations: 0,
      netAllocations: 0,
    });
    expect(memory.peakMb).toBeGreaterThanOrEqual(0);
  });

  it('runs standard and custom benchmark suites with baseline regression accounting', () => {
    const profiler = new CecPerformanceProfiler({ baseline: { custom: 0.000001 } });
    const results = profiler.runBenchmarkSuite([
      { name: 'custom', expression: '(subject_to agent code)', thresholdMs: 100, run: () => true },
      {
        name: 'failure',
        expression: '(bad expression)',
        thresholdMs: 100,
        run: () => {
          throw new Error('boom');
        },
      },
    ]);

    expect(getStandardCecBenchmarks().length).toBeGreaterThan(0);
    expect(results.benchmarks.some((benchmark) => benchmark.name === 'custom')).toBe(true);
    expect(results.failed).toBe(1);
    expect(results.passRate).toBeGreaterThan(0);
  });

  it('generates text, JSON, and HTML report strings', () => {
    const profiler = new CecPerformanceProfiler();
    profiler.profileFunction('reportMe', () => true, 1);

    expect(profiler.generateReport('text')).toContain('CEC Performance Profiling Report');
    expect(JSON.parse(profiler.generateReport('json')).history).toHaveLength(1);
    expect(profiler.generateReport('html')).toContain('');
  });

  it('exposes a convenience profiling helper', () => {
    expect(profileCecFunction('helper', () => true, 1)).toMatchObject({
      functionName: 'helper',
      runs: 1,
    });
  });

  it('ports profiling_utils.py helpers with browser-native metadata and deterministic summaries', () => {
    let clock = 10;
    const measured = measure_cec_profile(
      'proof-step',
      () => 'ok',
      () => {
        clock += 7;
        return clock;
      },
    );

    expect(measured).toMatchObject({
      name: 'proof-step',
      result: 'ok',
      durationMs: 7,
      metadata: {
        sourcePythonModule: 'logic/CEC/optimization/profiling_utils.py',
        browserNative: true,
        pythonRuntime: false,
        serverRuntime: false,
      },
    });

    const normalized = normalizeCecProfilerSamples([
      { name: '  ', durationMs: -3, calls: 0 },
      { name: 'proveGoal', durationMs: 1200, calls: 2, metadata: { phase: 'prove' } },
      { name: 'ruleLoop', durationMs: 8, calls: 2500 },
    ]);
    expect(normalized[0]).toMatchObject({ name: 'sample_0', durationMs: 0, calls: 1 });
    expect(normalized[1]).toMatchObject({ category: 'cec-proof', metadata: { phase: 'prove' } });

    const summary = summarizeCecProfiling(normalized, { topN: 2 });
    expect(summary).toMatchObject({
      metadata: {
        sourcePythonModule: 'logic/CEC/optimization/profiling_utils.py',
        runtime: 'browser-native-typescript',
      },
      sampleCount: 3,
      stats: { count: 3, max: 1200 },
    });
    expect(summary.slowest.map((sample) => sample.name)).toEqual(['proveGoal', 'ruleLoop']);
    expect(summary.bottlenecks.bottlenecks.map((finding) => finding.function)).toContain(
      'ruleLoop',
    );
  });
});
