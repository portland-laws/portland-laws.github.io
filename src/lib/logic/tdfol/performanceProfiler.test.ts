import {
  getStandardBenchmarks,
  profileTdfolFunction,
  runTdfolPerformanceProfiler,
  runTdfolPerformanceProfilerExample,
  TDFOL_PERFORMANCE_PROFILER_METADATA,
  TdfolPerformanceProfiler,
} from './performanceProfiler';

describe('TdfolPerformanceProfiler', () => {
  it('profiles repeated function execution and stores history', () => {
    const profiler = new TdfolPerformanceProfiler();
    const stats = profiler.profileFunction('quickOp', () => 1 + 1, 3);

    expect(stats).toMatchObject({
      functionName: 'quickOp',
      runs: 3,
      callsPerRun: 1,
      meetsThreshold: true,
    });
    expect(stats.meanTimeMs).toBeGreaterThanOrEqual(0);
    expect(profiler.history).toHaveLength(1);
  });

  it('identifies bottlenecks with severity and recommendations', () => {
    const profiler = new TdfolPerformanceProfiler();
    const bottlenecks = profiler.identifyBottlenecks([
      { function: 'proveGoal', timeMs: 1200, calls: 1 },
      { function: 'minor', timeMs: 20, calls: 2 },
      { function: 'nestedLoop', timeMs: 2, calls: 2001 },
    ]);

    expect(bottlenecks.find((b) => b.function === 'nestedLoop')).toMatchObject({
      function: 'nestedLoop',
      severity: 'critical',
      complexityEstimate: 'O(n^3)',
    });
    expect(bottlenecks.map((b) => b.severity)).toContain('medium');
  });

  it('profiles browser memory snapshots without requiring Python tracemalloc', () => {
    const profiler = new TdfolPerformanceProfiler();
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
    const profiler = new TdfolPerformanceProfiler({ baseline: { custom: 0.000001 } });
    const results = profiler.runBenchmarkSuite([
      { name: 'custom', formula: 'Pred(x)', thresholdMs: 100, run: () => true },
      {
        name: 'failure',
        formula: 'Bad(x)',
        thresholdMs: 100,
        run: () => {
          throw new Error('boom');
        },
      },
    ]);

    expect(getStandardBenchmarks().length).toBeGreaterThan(0);
    expect(results.benchmarks.some((benchmark) => benchmark.name === 'custom')).toBe(true);
    expect(results.failed).toBe(1);
    expect(results.passRate).toBeGreaterThan(0);
  });

  it('generates text, JSON, and HTML report strings', () => {
    const profiler = new TdfolPerformanceProfiler();
    profiler.profileFunction('reportMe', () => true, 1);

    expect(profiler.generateReport('text')).toContain('TDFOL Performance Profiling Report');
    const jsonReport = JSON.parse(profiler.generateReport('json'));
    expect(jsonReport.history).toHaveLength(1);
    expect(jsonReport.metadata).toMatchObject(TDFOL_PERFORMANCE_PROFILER_METADATA);
    expect(profiler.generateReport('html')).toContain(
      '<script type="application/json" id="tdfol-profiler-data">',
    );
  });

  it('exposes a convenience profiling helper', () => {
    expect(profileTdfolFunction('helper', () => true, 1)).toMatchObject({
      functionName: 'helper',
      runs: 1,
    });
  });

  it('ports performance_profiler.py as a browser-native module contract', () => {
    const run = runTdfolPerformanceProfiler({
      functionName: 'module_profile',
      formula: 'forall permittee. O(permit(permittee))',
      runs: 2,
      baseline: { simple_propositional: 100 },
      customBenchmarks: [
        {
          name: 'module_custom',
          formula: 'O(P)',
          thresholdMs: 100,
          run: () => true,
        },
      ],
    });

    expect(run.metadata).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/performance_profiler.py',
      browserNative: true,
      pythonRuntimeRequired: false,
      serverCallsAllowed: false,
    });
    expect(run.profile).toMatchObject({ functionName: 'module_profile', runs: 2 });
    expect(run.memory.functionName).toBe('module_profile_memory');
    expect(run.benchmarks.benchmarks.some((benchmark) => benchmark.name === 'module_custom')).toBe(
      true,
    );
    expect(JSON.parse(run.reports.json).metadata.sourcePythonModule).toBe(
      'logic/TDFOL/performance_profiler.py',
    );
    expect(run.reports.html).toContain('logic/TDFOL/performance_profiler.py');
  });

  it('ports example_performance_profiler.py as a browser-native example runner', () => {
    const example = runTdfolPerformanceProfilerExample({ runs: 2 });

    expect(example).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/example_performance_profiler.py',
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      profile: {
        functionName: 'example_quantified_profile',
        runs: 2,
      },
      summary: {
        profiledFunction: 'example_quantified_profile',
      },
    });
    expect(
      example.bottlenecks.some((bottleneck) => bottleneck.function === 'tdfol_rule_loop'),
    ).toBe(true);
    expect(
      example.benchmarks.benchmarks.some(
        (benchmark) => benchmark.name === 'example_quantified_profile',
      ),
    ).toBe(true);
    expect(example.memory.functionName).toBe('example_memory_snapshot');
    expect(example.reports.text).toContain('TDFOL Performance Profiling Report');
    expect(JSON.parse(example.reports.json).history.length).toBeGreaterThanOrEqual(1);
    expect(example.reports.html).toContain('tdfol-profiler-data');
  });
});
