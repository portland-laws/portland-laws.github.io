import type { ProofResult } from '../types';
import {
  createTdfolPerformanceDashboardDemo,
  createTdfolProofMetrics,
  TDFOL_PERFORMANCE_DASHBOARD_METADATA,
  TdfolPerformanceDashboard,
} from './performanceDashboard';

describe('TdfolPerformanceDashboard', () => {
  it('creates proof metrics with complexity and formula type classification', () => {
    const metric = createTdfolProofMetrics({
      formula: 'always(Pred(x)) -> Pred(x)',
      proofTimeMs: 12,
      success: true,
      strategy: 'modal',
      cacheHit: true,
      memoryUsageMb: 4,
      numSteps: 3,
    });

    expect(metric).toMatchObject({
      formula: 'always(Pred(x)) -> Pred(x)',
      complexity: 2,
      formulaType: 'temporal',
      proofTimeMs: 12,
      success: true,
      strategy: 'modal',
      cacheHit: true,
      memoryMb: 4,
      numSteps: 3,
    });
  });

  it('records proof metrics and custom time-series metrics', () => {
    const dashboard = new TdfolPerformanceDashboard();
    dashboard.recordProof({
      formula: 'Pred(x)',
      proofTimeMs: 2,
      success: true,
      strategy: 'forward',
      cacheHit: true,
    });
    dashboard.recordProof({
      formula: 'O(Comply(x))',
      proofTimeMs: 10,
      success: false,
      strategy: 'modal',
      memoryUsageMb: 12,
    });
    dashboard.recordMetric('memory_usage_mb', 12, { source: 'test' });

    expect(dashboard.proofMetrics).toHaveLength(2);
    expect(dashboard.timeseriesMetrics.map((metric) => metric.metric)).toEqual([
      'proof_time_ms',
      'cache_hit',
      'proof_time_ms',
      'cache_miss',
      'memory_usage_mb',
    ]);
  });

  it('aggregates statistics across proofs', () => {
    const dashboard = new TdfolPerformanceDashboard();
    dashboard.recordProof({
      formula: 'Pred(x)',
      proofTimeMs: 1,
      success: true,
      strategy: 'forward',
      cacheHit: true,
      numSteps: 1,
    });
    dashboard.recordProof({
      formula: 'Goal(x)',
      proofTimeMs: 9,
      success: false,
      strategy: 'forward',
      cacheHit: false,
      numSteps: 3,
    });
    dashboard.recordProof({
      formula: 'always(Pred(x))',
      proofTimeMs: 5,
      success: true,
      strategy: 'modal',
      cacheHit: false,
      numSteps: 2,
    });

    expect(dashboard.getStatistics()).toMatchObject({
      totalProofs: 3,
      successfulProofs: 2,
      failedProofs: 1,
      successRate: 2 / 3,
      cacheHits: 1,
      cacheMisses: 2,
      cacheHitRate: 1 / 3,
      timing: {
        totalMs: 15,
        minMs: 1,
        maxMs: 9,
        avgMs: 5,
        medianMs: 5,
        p95Ms: 9,
      },
      formulas: {
        avgSteps: 2,
      },
      strategies: {
        counts: { forward: 2, modal: 1 },
        successRates: { forward: 0.5, modal: 1 },
      },
      formulaTypes: {
        counts: { propositional: 2, temporal: 1 },
      },
    });
  });

  it('compares strategies and exports JSON/HTML strings without external dependencies', () => {
    const dashboard = new TdfolPerformanceDashboard();
    dashboard.recordProof({
      formula: 'Pred(x)',
      proofTimeMs: 2,
      success: true,
      strategy: 'forward',
      cacheHit: true,
    });
    dashboard.recordProof({
      formula: 'always(Pred(x))',
      proofTimeMs: 8,
      success: true,
      strategy: 'modal',
    });

    expect(dashboard.compareStrategies()).toMatchObject({
      strategies: {
        forward: { count: 1, successRate: 1, cacheHitRate: 1, avgTimeMs: 2 },
        modal: { count: 1, successRate: 1, cacheHitRate: 0, avgTimeMs: 8 },
      },
    });
    expect(dashboard.exportJson()).toHaveProperty('statistics.totalProofs', 2);
    expect(dashboard.toHtmlString()).toContain(
      '<script type="application/json" id="tdfol-dashboard-data">',
    );
  });

  it('exposes Python-compatible dashboard aliases and browser-native export metadata', () => {
    let tick = 0;
    const dashboard = new TdfolPerformanceDashboard({
      now: () => Date.UTC(2026, 0, 2, 0, 0, tick++),
    });

    dashboard.record_proof({
      formula: 'Pred(x)',
      proofTimeMs: 2,
      success: true,
      strategy: 'forward',
      cacheHit: true,
    });
    dashboard.record_metric('memory_usage_mb', 7, { source: 'alias-test' });
    dashboard.record_metric('memory_usage_mb', 11, { source: 'alias-test' });

    expect(TDFOL_PERFORMANCE_DASHBOARD_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/performance_dashboard.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeRequired: false,
    });
    expect(dashboard.get_statistics().totalProofs).toBe(1);
    expect(dashboard.compare_strategies().strategies.forward.avgTimeMs).toBe(2);
    expect(dashboard.get_timeseries_summary('memory_usage_mb')).toEqual({
      memory_usage_mb: {
        count: 2,
        total: 18,
        min: 7,
        max: 11,
        avg: 9,
        latestValue: 11,
        latestTimestamp: Date.UTC(2026, 0, 2, 0, 0, 4),
      },
    });

    const json = dashboard.export_json();
    expect(json).toHaveProperty(
      'metadata.sourcePythonModule',
      'logic/TDFOL/performance_dashboard.py',
    );
    expect(json).toHaveProperty('timeseriesSummary.memory_usage_mb.avg', 9);
    expect(dashboard.to_html_string()).toContain('tdfol-dashboard-data');

    const pythonJson = dashboard.export_python_compatible_json();
    expect(pythonJson).toHaveProperty(
      'metadata.source_python_module',
      'logic/TDFOL/performance_dashboard.py',
    );
    expect(pythonJson).toHaveProperty('metadata.server_calls_allowed', false);
    expect(pythonJson).toHaveProperty('strategy_comparison.strategies.forward.count', 1);
    expect(pythonJson).toHaveProperty('timeseries_summary.memory_usage_mb.latestValue', 11);

    dashboard.clear_metrics();
    expect(dashboard.get_statistics().totalProofs).toBe(0);
  });

  it('records ProofResult objects and clears dashboard state', () => {
    const dashboard = new TdfolPerformanceDashboard();
    const result: ProofResult = {
      status: 'proved',
      theorem: 'Pred(x)',
      steps: [{ id: 's1', rule: 'Axiom', premises: [], conclusion: 'Pred(x)' }],
      method: 'test',
      timeMs: 3,
    };

    dashboard.recordProof(result, { strategy: 'direct', cacheHit: false });
    expect(dashboard.getStatistics()).toMatchObject({
      totalProofs: 1,
      successfulProofs: 1,
      strategies: { counts: { direct: 1 } },
    });

    dashboard.clear();
    expect(dashboard.getStatistics().totalProofs).toBe(0);
    expect(dashboard.proofMetrics).toHaveLength(0);
    expect(dashboard.timeseriesMetrics).toHaveLength(0);
  });

  it('builds a deterministic browser-native performance dashboard demo', () => {
    const demo = createTdfolPerformanceDashboardDemo({
      formats: ['summary', 'snapshot', 'json', 'html'],
    });

    expect(demo.id).toBe('tdfol-performance-dashboard-demo');
    expect(demo.statistics).toMatchObject({
      totalProofs: 3,
      successfulProofs: 2,
      failedProofs: 1,
      successRate: 2 / 3,
      cacheHits: 1,
      cacheMisses: 2,
      timing: { totalMs: 33, avgMs: 11, medianMs: 11, p95Ms: 18 },
      strategies: { counts: { 'temporal-deontic': 1, direct: 1, modal: 1 } },
      formulaTypes: { counts: { temporal_deontic: 1, deontic: 1, modal: 1 } },
    });
    expect(demo.strategyComparison.strategies.direct).toMatchObject({
      count: 1,
      cacheHitRate: 1,
      avgTimeMs: 4,
    });

    const snapshot = JSON.parse(demo.rendered.snapshot ?? '{}');
    expect(snapshot).toEqual({
      total_proofs: 3,
      success_rate: 2 / 3,
      cache_hit_rate: 1 / 3,
      avg_time_ms: 11,
      strategies: ['direct', 'modal', 'temporal-deontic'],
      formula_types: ['deontic', 'modal', 'temporal_deontic'],
    });
    expect(demo.rendered.summary).toContain('proofs=3');
    expect(demo.rendered.json).toContain('"dashboardStartDatetime": "2026-01-01T12:00:00.000Z"');
    expect(demo.rendered.html).toContain(
      '<script type="application/json" id="tdfol-dashboard-data">',
    );
  });
});
