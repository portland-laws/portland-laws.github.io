import type { ProofResult } from '../types';
import { CecPerformanceDashboard, createCecProofMetrics } from './performanceDashboard';

describe('CecPerformanceDashboard', () => {
  it('creates proof metrics with complexity and CEC expression type classification', () => {
    const metric = createCecProofMetrics({
      theorem: '(forall agent (O (always (comply_with agent code))))',
      proofTimeMs: 12,
      success: true,
      strategy: 'cached',
      cacheHit: true,
      memoryUsageMb: 4,
      numSteps: 3,
    });

    expect(metric).toMatchObject({
      theorem: '(forall agent (O (always (comply_with agent code))))',
      expressionType: 'mixed',
      proofTimeMs: 12,
      success: true,
      strategy: 'cached',
      cacheHit: true,
      memoryMb: 4,
      numSteps: 3,
    });
    expect(metric.complexity).toBeGreaterThanOrEqual(4);
  });

  it('records proof metrics and custom time-series metrics', () => {
    const dashboard = new CecPerformanceDashboard();
    dashboard.recordProof({ theorem: '(subject_to agent code)', proofTimeMs: 2, success: true, strategy: 'forward', cacheHit: true });
    dashboard.recordProof({ theorem: '(O (comply_with agent code))', proofTimeMs: 10, success: false, strategy: 'cached', memoryUsageMb: 12 });
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

  it('aggregates statistics across CEC proofs', () => {
    const dashboard = new CecPerformanceDashboard();
    dashboard.recordProof({ theorem: '(subject_to agent code)', proofTimeMs: 1, success: true, strategy: 'forward', cacheHit: true, numSteps: 1 });
    dashboard.recordProof({ theorem: '(comply_with agent code)', proofTimeMs: 9, success: false, strategy: 'forward', cacheHit: false, numSteps: 3 });
    dashboard.recordProof({ theorem: '(always (comply_with agent code))', proofTimeMs: 5, success: true, strategy: 'cached', cacheHit: false, numSteps: 2 });

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
      expressions: {
        avgSteps: 2,
      },
      strategies: {
        counts: { forward: 2, cached: 1 },
        successRates: { forward: 0.5, cached: 1 },
      },
      expressionTypes: {
        counts: { propositional: 2, temporal: 1 },
      },
    });
  });

  it('compares strategies and exports JSON/HTML strings without external dependencies', () => {
    const dashboard = new CecPerformanceDashboard();
    dashboard.recordProof({ theorem: '(subject_to agent code)', proofTimeMs: 2, success: true, strategy: 'forward', cacheHit: true });
    dashboard.recordProof({ theorem: '(always (comply_with agent code))', proofTimeMs: 8, success: true, strategy: 'cached' });

    expect(dashboard.compareStrategies()).toMatchObject({
      strategies: {
        forward: { count: 1, successRate: 1, cacheHitRate: 1, avgTimeMs: 2 },
        cached: { count: 1, successRate: 1, cacheHitRate: 0, avgTimeMs: 8 },
      },
    });
    expect(dashboard.exportJson()).toHaveProperty('statistics.totalProofs', 2);
    expect(dashboard.toHtmlString()).toContain('<script type="application/json" id="cec-dashboard-data">');
  });

  it('records ProofResult objects and clears dashboard state', () => {
    const dashboard = new CecPerformanceDashboard();
    const result: ProofResult = {
      status: 'proved',
      theorem: '(subject_to agent code)',
      steps: [{ id: 's1', rule: 'Axiom', premises: [], conclusion: '(subject_to agent code)' }],
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
