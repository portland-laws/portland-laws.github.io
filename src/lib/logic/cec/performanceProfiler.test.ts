import { CecPerformanceProfiler, getStandardCecBenchmarks, profileCecFunction } from './performanceProfiler';

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
    expect(bottlenecks.find((b) => b.function === 'strategySelector')?.recommendation).toContain('strategy costs');
    expect(bottlenecks.map((b) => b.severity)).toContain('medium');
  });

  it('profiles browser memory snapshots without requiring Python memory tooling', () => {
    const profiler = new CecPerformanceProfiler();
    const memory = profiler.memoryProfile('allocate', () => Array.from({ length: 10 }, (_, index) => index));

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
      { name: 'failure', expression: '(bad expression)', thresholdMs: 100, run: () => { throw new Error('boom'); } },
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
    expect(profiler.generateReport('html')).toContain('<script type="application/json" id="cec-profiler-data">');
  });

  it('exposes a convenience profiling helper', () => {
    expect(profileCecFunction('helper', () => true, 1)).toMatchObject({
      functionName: 'helper',
      runs: 1,
    });
  });
});
