import { TdfolMetricsCollector } from './performanceMetrics';
import {
  createTdfolPerformanceEngine,
  TDFOL_PERFORMANCE_ENGINE_METADATA,
  TdfolPerformanceEngine,
} from './performanceEngine';

describe('TdfolPerformanceEngine', () => {
  it('profiles proving operations and records dashboard metrics', () => {
    const engine = createTdfolPerformanceEngine(new TdfolMetricsCollector());
    const profile = engine.profileOperation({
      formula: 'Pred(x) -> Pred(x)',
      runs: 3,
      strategy: 'forward',
      kbFormulas: ['Pred(x)'],
    });

    expect(profile).toMatchObject({
      formula: 'Pred(x) -> Pred(x)',
      runs: 3,
      strategy: 'forward',
      kbSize: 1,
    });
    expect(profile.timing.meanTimeMs).toBeGreaterThanOrEqual(0);
    expect(engine.getMetrics().metadata.dashboardProofsRecorded).toBe(3);
    expect(engine.getMetrics().collectorSummary.timingOperations).toBe(1);
  });

  it('generates self-contained dashboard HTML and statistics exports', () => {
    const engine = new TdfolPerformanceEngine(new TdfolMetricsCollector());
    engine.profileOperation({ formula: 'always(Pred(x)) -> Pred(x)', runs: 1, strategy: 'modal' });

    const dashboard = engine.generateDashboard({ includeProfiling: true });
    const jsonExport = engine.exportStatistics('json', true);
    const prometheusExport = engine.exportStatistics('prometheus');

    expect(dashboard.success).toBe(true);
    expect(dashboard.htmlString).toContain(
      '<script type="application/json" id="tdfol-performance-data">',
    );
    expect(dashboard.summary.totalProofs).toBe(1);
    expect(String(jsonExport.json_string)).toContain('"dashboard_stats"');
    expect(String(prometheusExport.prometheus_metrics)).toContain('tdfol_total_proofs 1');
  });

  it('compares strategies and reports the best observed timing', () => {
    const engine = new TdfolPerformanceEngine(new TdfolMetricsCollector());
    const comparison = engine.compareStrategies({
      formula: 'Pred(x) -> Pred(x)',
      strategies: ['forward', 'modal'],
      runsPerStrategy: 1,
    });

    expect(comparison).toMatchObject({
      formula: 'Pred(x) -> Pred(x)',
      strategiesCompared: 2,
      runsPerStrategy: 1,
    });
    expect(comparison).toHaveProperty('bestStrategy.name');
    expect(String(comparison.recommendation)).toContain('Use');
  });

  it('checks regressions against collector timing means', () => {
    const collector = new TdfolMetricsCollector();
    collector.recordTiming('tdfol.profile.forward', 20);
    const engine = new TdfolPerformanceEngine(collector);

    expect(engine.checkRegression({ 'tdfol.profile.forward': 10 }, 10)).toMatchObject({
      regressionsFound: true,
      regressionCount: 1,
      regressions: [{ metric: 'tdfol.profile.forward', severity: 'critical' }],
    });
    expect(engine.checkRegression({ 'tdfol.profile.forward': 25 }, 10)).toMatchObject({
      regressionsFound: false,
      status: 'All metrics within baseline threshold',
    });
  });

  it('reports profiler history and resets metrics', () => {
    const engine = new TdfolPerformanceEngine(new TdfolMetricsCollector());

    expect(engine.getProfilerReport()).toMatchObject({
      warning: 'No profiling data available',
      historyCount: 0,
    });

    engine.profileOperation({ formula: 'Pred(x) -> Pred(x)', runs: 1, strategy: 'forward' });
    expect(engine.getProfilerReport()).toMatchObject({ historyCount: 1 });
    expect(engine.resetMetrics()).toEqual({
      success: true,
      clearedProofMetrics: 1,
      clearedProfilingRuns: 1,
    });
    expect(engine.getMetrics().metadata.dashboardProofsRecorded).toBe(0);
  });

  it('exposes tdfol_performance_engine.py metadata and Python-compatible aliases', () => {
    const engine = new TdfolPerformanceEngine(new TdfolMetricsCollector());
    const profile = engine.profile_operation({
      formula: 'Pred(x) -> Pred(x)',
      runs: 1,
      strategy: 'forward',
      kbFormulas: ['Pred(x)'],
    });
    const dashboard = engine.generate_dashboard({ includeProfiling: true });
    const statistics = engine.export_statistics('json', true);

    expect(TDFOL_PERFORMANCE_ENGINE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/tdfol_performance_engine.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeRequired: false,
    });
    expect(TDFOL_PERFORMANCE_ENGINE_METADATA.parity).toContain('regression_checks');
    expect(profile.metadata.latestStatus).toBeDefined();
    expect(engine.get_metrics().metadata.dashboardProofsRecorded).toBe(1);
    expect(engine.get_dashboard_statistics().totalProofs).toBe(1);
    expect(dashboard.profilingHistory).toHaveLength(1);
    expect(statistics.metadata).toBe(TDFOL_PERFORMANCE_ENGINE_METADATA);
    expect(engine.get_profiler_report()).toMatchObject({ historyCount: 1 });
    expect(engine.check_regression({ 'tdfol.profile.forward': 1000 })).toMatchObject({
      regressionsFound: false,
    });
    expect(
      engine.compare_strategies({
        formula: 'Pred(x) -> Pred(x)',
        strategies: ['forward'],
        runsPerStrategy: 1,
      }),
    ).toMatchObject({ strategiesCompared: 1 });
    expect(engine.reset_metrics()).toMatchObject({ success: true });
  });
});
