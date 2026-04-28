import { DeonticGraph, DeonticGraphBuilder, modalitiesConflict, safeIdentifier } from './graph';

describe('DeonticGraph browser-native parity helpers', () => {
  it('stores nodes and rules, summarizes distributions, and assesses source gaps', () => {
    const graph = new DeonticGraph('2026-01-01T00:00:00.000Z');
    graph.addNode({ id: 'actor:tenant', node_type: 'actor', label: 'Tenant', active: true, confidence: 0.9, attributes: {} });
    graph.addNode({ id: 'condition:notice', node_type: 'condition', label: 'Notice served', active: false, confidence: 0.8, attributes: {} });
    graph.addNode({ id: 'action:pay', node_type: 'action', label: 'pay rent', active: false, confidence: 0.9, attributes: {} });
    graph.addRule({
      id: 'rule:pay',
      modality: 'obligation',
      source_ids: ['actor:tenant', 'condition:notice'],
      target_id: 'action:pay',
      predicate: 'pay rent',
      active: true,
      confidence: 0.92,
      authority_ids: ['code:1'],
      evidence_ids: ['context:1'],
      attributes: {},
    });

    expect(graph.summary()).toMatchObject({
      total_nodes: 3,
      total_rules: 1,
      active_rule_count: 1,
      node_types: { actor: 1, condition: 1, action: 1 },
      modalities: { obligation: 1 },
      governed_target_count: 1,
    });
    expect(graph.assessRules()[0]).toMatchObject({
      rule_id: 'rule:pay',
      satisfied_sources: ['actor:tenant'],
      missing_sources: ['condition:notice'],
    });
    expect(graph.sourceGapSummary()).toMatchObject({
      rule_count: 1,
      fully_supported_rule_count: 0,
    });
  });

  it('detects Python-compatible modality conflicts by target and predicate', () => {
    const graph = new DeonticGraph();
    graph.addNode({ id: 'action:enter', node_type: 'action', label: 'enter unit', active: false, confidence: 1, attributes: {} });
    for (const [id, modality] of [
      ['allow', 'entitlement'],
      ['deny', 'prohibition'],
    ] as const) {
      graph.addRule({
        id,
        modality,
        source_ids: [],
        target_id: 'action:enter',
        predicate: 'enter unit',
        active: true,
        confidence: 1,
        authority_ids: [],
        evidence_ids: [],
        attributes: {},
      });
    }

    expect(modalitiesConflict('obligation', 'prohibition')).toBe(true);
    expect(modalitiesConflict('permission', 'prohibition')).toBe(false);
    expect(graph.detectConflicts()).toEqual([
      {
        rule_id: 'allow',
        conflicting_rule_id: 'deny',
        target_id: 'action:enter',
        modalities: ['entitlement', 'prohibition'],
        reason: 'Rules govern the same target and predicate with incompatible modalities.',
      },
    ]);
  });

  it('round-trips dictionaries and builds from matrix rows', () => {
    const graph = new DeonticGraphBuilder().buildFromMatrix([
      {
        rule_id: 'rule_1',
        modality: 'permission',
        predicate: 'appeal',
        target_id: 'action:appeal',
        target_label: 'appeal',
        target_type: 'action',
        sources: [{ id: 'fact:denial', label: 'permit denied', node_type: 'fact', active: true }],
        authorities: [{ id: 'code:appeal', label: 'Appeal Code' }],
        evidence_ids: ['ev:1'],
        active: true,
        confidence: 0.8,
      },
    ]);

    const restored = DeonticGraph.fromDict(graph.toDict());
    expect(restored.rulesForSource('fact:denial')).toHaveLength(1);
    expect(restored.exportReasoningRows()[0]).toMatchObject({
      target_label: 'appeal',
      modality: 'permission',
      satisfied_sources: ['fact:denial'],
      authority_ids: ['code:appeal'],
    });
  });

  it('builds graph rows from analyzer-style statements', () => {
    const graph = new DeonticGraphBuilder().buildFromStatements([
      {
        id: 'stmt_1',
        entity: 'The Tenant',
        modality: 'obligation',
        action: 'pay rent',
        document_source: 'Portland Code',
        document_date: '2026-01-01',
        document_id: 7,
        context: 'The tenant must pay rent.',
        confidence: 0.91,
        conditions: ['lease is active'],
        exceptions: ['rent is waived'],
      },
    ]);

    expect(safeIdentifier('The Tenant')).toBe('the_tenant');
    expect(graph.summary()).toMatchObject({ total_rules: 1, total_nodes: 4 });
    expect(graph.rules.get('stmt_1')).toMatchObject({
      modality: 'obligation',
      evidence_ids: ['context_1'],
      authority_ids: ['authority_portland_code'],
    });
  });
});
