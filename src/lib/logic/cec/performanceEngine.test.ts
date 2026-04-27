import { CecMetricsCollector } from './performanceMetrics';
import { CecPerformanceEngine, createCecPerformanceEngine } from './performanceEngine';

describe('CecPerformanceEngine', () => {
  it('profiles CEC proving operations and records metrics', () => {
    const engine = createCecPerformanceEngine(new CecMetricsCollector());
    const profile = engine.profileOperation({
      theorem: '(comply_with agent code)',
      runs: 3,
      strategy: 'forward',
      kbExpressions: [
        '(subject_to agent code)',
        '(implies (subject_to agent code) (comply_with agent code))',
      ],
    });

    expect(profile).toMatchObject({
      theorem: '(comply_with agent code)',
      runs: 3,
      strategy: 'forward',
      kbSize: 2,
    });
    expect(profile.performance.provedRuns).toBe(3);
    expect(profile.timing.meanTimeMs).toBeGreaterThanOrEqual(0);
    expect(engine.getDashboardStatistics()).toMatchObject({ totalProofs: 3, successRate: 1 });
    expect(engine.getMetrics()).toMatchObject({
      metadata: { proofsRecorded: 3 },
      collectorSummary: { timingOperations: 1, histograms: 1 },
    });
  });

  it('generates self-contained dashboard HTML and statistics exports', () => {
    const engine = new CecPerformanceEngine(new CecMetricsCollector());
    engine.profileOperation({
      theorem: '(P (comply_with agent code))',
      runs: 1,
      strategy: 'forward',
      kbExpressions: ['(O (comply_with agent code))'],
    });

    const dashboard = engine.generateDashboard({ includeProfiling: true });
    const jsonExport = engine.exportStatistics('json', true);
    const prometheusExport = engine.exportStatistics('prometheus');

    expect(dashboard.success).toBe(true);
    expect(dashboard.htmlString).toContain('<script type="application/json" id="cec-performance-data">');
    expect(dashboard.summary.totalProofs).toBe(1);
    expect(String(jsonExport.json_string)).toContain('"dashboard_stats"');
    expect(String(prometheusExport.prometheus_metrics)).toContain('cec_total_proofs 1');
  });

  it('compares strategies and reports the best observed timing', () => {
    const engine = new CecPerformanceEngine(new CecMetricsCollector());
    const comparison = engine.compareStrategies({
      theorem: '(comply_with agent code)',
      kbExpressions: [
        '(subject_to agent code)',
        '(implies (subject_to agent code) (comply_with agent code))',
      ],
      strategies: ['forward', 'cached'],
      runsPerStrategy: 1,
    });

    expect(comparison).toMatchObject({
      theorem: '(comply_with agent code)',
      strategiesCompared: 2,
      runsPerStrategy: 1,
    });
    expect(comparison).toHaveProperty('bestStrategy.name');
    expect(String(comparison.recommendation)).toContain('Use');
  });

  it('checks regressions against collector timing means', () => {
    const collector = new CecMetricsCollector();
    collector.recordTiming('cec.profile.forward', 20);
    const engine = new CecPerformanceEngine(collector);

    expect(engine.checkRegression({ 'cec.profile.forward': 10 }, 10)).toMatchObject({
      regressionsFound: true,
      regressionCount: 1,
      regressions: [{ metric: 'cec.profile.forward', severity: 'critical' }],
    });
    expect(engine.checkRegression({ 'cec.profile.forward': 25 }, 10)).toMatchObject({
      regressionsFound: false,
      status: 'All metrics within baseline threshold',
    });
  });

  it('reports profiler history and resets metrics', () => {
    const engine = new CecPerformanceEngine(new CecMetricsCollector());

    expect(engine.getProfilerReport()).toMatchObject({
      warning: 'No profiling data available',
      historyCount: 0,
    });

    engine.profileOperation({ theorem: '(known fact)', runs: 1, strategy: 'forward', kbExpressions: ['(known fact)'] });
    expect(engine.getProfilerReport()).toMatchObject({ historyCount: 1 });
    expect(engine.resetMetrics()).toEqual({ success: true, clearedProofMetrics: 1, clearedProfilingRuns: 1 });
    expect(engine.getDashboardStatistics().totalProofs).toBe(0);
  });
});
