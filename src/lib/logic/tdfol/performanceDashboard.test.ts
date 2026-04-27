import type { ProofResult } from '../types';
import { createTdfolProofMetrics, TdfolPerformanceDashboard } from './performanceDashboard';

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
    dashboard.recordProof({ formula: 'Pred(x)', proofTimeMs: 2, success: true, strategy: 'forward', cacheHit: true });
    dashboard.recordProof({ formula: 'O(Comply(x))', proofTimeMs: 10, success: false, strategy: 'modal', memoryUsageMb: 12 });
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
    dashboard.recordProof({ formula: 'Pred(x)', proofTimeMs: 1, success: true, strategy: 'forward', cacheHit: true, numSteps: 1 });
    dashboard.recordProof({ formula: 'Goal(x)', proofTimeMs: 9, success: false, strategy: 'forward', cacheHit: false, numSteps: 3 });
    dashboard.recordProof({ formula: 'always(Pred(x))', proofTimeMs: 5, success: true, strategy: 'modal', cacheHit: false, numSteps: 2 });

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
    dashboard.recordProof({ formula: 'Pred(x)', proofTimeMs: 2, success: true, strategy: 'forward', cacheHit: true });
    dashboard.recordProof({ formula: 'always(Pred(x))', proofTimeMs: 8, success: true, strategy: 'modal' });

    expect(dashboard.compareStrategies()).toMatchObject({
      strategies: {
        forward: { count: 1, successRate: 1, cacheHitRate: 1, avgTimeMs: 2 },
        modal: { count: 1, successRate: 1, cacheHitRate: 0, avgTimeMs: 8 },
      },
    });
    expect(dashboard.exportJson()).toHaveProperty('statistics.totalProofs', 2);
    expect(dashboard.toHtmlString()).toContain('<script type="application/json" id="tdfol-dashboard-data">');
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
});
