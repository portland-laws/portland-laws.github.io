import {
  analyze_neurosymbolic,
  analyze_neurosymbolic_api,
  analyze_neurosymbolic_graphrag,
  analyze_symbolic_neurosymbolic_graphrag,
  coordinate_reasoning,
  create_browser_native_neurosymbolic_api,
  create_browser_native_hybrid_confidence,
  create_browser_native_embedding_prover,
  create_browser_native_neurosymbolic_integration,
  create_browser_native_neurosymbolic_graphrag,
  create_browser_native_symbolic_neurosymbolic_graphrag,
  create_browser_native_reasoning_coordinator,
  prove_embedding,
  query_neurosymbolic_api,
  query_neurosymbolic_graphrag,
  query_symbolic_neurosymbolic_graphrag,
  reason_neurosymbolic,
  score_hybrid_confidence,
} from './neurosymbolic';

describe('browser-native neurosymbolic integration parity', () => {
  it('projects local neural signals into symbolic facts', () => {
    const integration = create_browser_native_neurosymbolic_integration();
    const result = integration.analyze(
      'The tenant must pay rent. The landlord may inspect after notice. The owner shall not retaliate.',
    );

    expect(integration.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/neurosymbolic.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      neuralRuntime: 'deterministic-local-adapter',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      proofStatus: 'not_applicable',
      metadata: { sourcePythonModule: 'logic/integration/neurosymbolic.py' },
    });
    expect(result.neuralSignals.map((signal) => signal.intent)).toEqual([
      'obligation',
      'permission',
      'prohibition',
    ]);
    expect(result.symbolicFacts).toEqual([
      'O(the_tenant_must_pay_rent)',
      'P(the_landlord_may_inspect_after_notice)',
      'F(the_owner_shall_not_retaliate)',
    ]);
  });

  it('reasons over local facts and rules without Python or server fallback', () => {
    const result = reason_neurosymbolic('The tenant must pay rent.', 'Protected(Tenant)', {
      rules: ['O(the_tenant_must_pay_rent) => Protected(Tenant)'],
    });

    expect(result).toMatchObject({
      status: 'success',
      proofStatus: 'proved',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      inferredFacts: ['Protected(Tenant)'],
    });
    expect(result.reasoningSteps.map((step) => step.kind)).toContain('rule_match');
    expect(result.confidence).toBeGreaterThan(0.8);
  });

  it('fails closed on invalid input and exposes Python-compatible aliases', () => {
    expect(analyze_neurosymbolic('')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: { sourcePythonModule: 'logic/integration/neurosymbolic.py' },
    });
    expect(analyze_neurosymbolic('Plain background context.').issues).toContain(
      'no local neural-symbolic signals matched',
    );
  });
});

describe('browser-native neurosymbolic API parity', () => {
  it('coordinates symbolic, GraphRAG, embedding, and confidence evidence locally', () => {
    const api = create_browser_native_neurosymbolic_api();
    const result = api.analyze({
      text: 'The agency shall publish the rule.',
      query: 'Protected(Agency)',
      documents: [
        {
          id: 'agency-rule',
          text: 'The agency shall publish the rule before enforcement.',
        },
      ],
      rules: ['O(the_agency_shall_publish_the_rule_before_enforcement) => Protected(Agency)'],
      embedding: { threshold: 0.4 },
    });

    expect(api.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic/neurosymbolic_api.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      apiRuntime: 'deterministic-local-neurosymbolic-api',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      selectedMode: 'graphrag',
      proofStatus: 'proved',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic_api.py',
      },
    });
    expect(result.answerFacts).toContain('Protected(Agency)');
    expect(result.graphrag?.retrievedDocuments[0]?.id).toBe('agency-rule');
  });

  it('exposes Python-compatible aliases and fails closed without runtime fallbacks', () => {
    const proved = analyze_neurosymbolic_api({
      text: 'The tenant must pay rent.',
      query: 'O(the_tenant_must_pay_rent)',
    });
    const closed = query_neurosymbolic_api({ text: '', query: 'Any(Query)' });

    expect(proved).toMatchObject({
      status: 'success',
      selectedMode: 'coordinator',
      proofStatus: 'proved',
    });
    expect(closed).toMatchObject({
      status: 'validation_failed',
      success: false,
      selectedMode: 'none',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      issues: expect.arrayContaining(['no local neurosymbolic api evidence is available']),
    });
  });
});

describe('browser-native neurosymbolic GraphRAG parity', () => {
  it('builds a deterministic local graph and retrieves symbolic evidence', () => {
    const graphrag = create_browser_native_neurosymbolic_graphrag();
    const result = graphrag.query('unused corpus', 'Protected(Tenant)', {
      documents: [
        {
          id: 'lease',
          title: 'Lease duties',
          text: 'The tenant must pay rent. The landlord may inspect after notice.',
        },
        {
          id: 'retaliation',
          title: 'Retaliation rule',
          text: 'The owner shall not retaliate against the tenant.',
        },
      ],
      rules: ['O(the_tenant_must_pay_rent) => Protected(Tenant)'],
      topK: 1,
    });

    expect(graphrag.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/neurosymbolic_graphrag.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      graphRuntime: 'deterministic-local-graph-rag-adapter',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      proofStatus: 'proved',
      inferredFacts: ['Protected(Tenant)'],
      metadata: { sourcePythonModule: 'logic/integration/neurosymbolic_graphrag.py' },
    });
    expect(result.retrievedDocuments.map((document) => document.id)).toEqual(['lease']);
    expect(result.graphNodes.map((node) => node.kind)).toEqual(
      expect.arrayContaining(['document', 'fact', 'entity']),
    );
    expect(result.graphEdges.map((edge) => edge.relation)).toEqual(
      expect.arrayContaining(['contains', 'mentions', 'supports']),
    );
    expect(result.reasoningSteps.map((step) => step.kind)).toContain('query_match');
  });

  it('uses corpus sentences as documents and fails closed without runtime fallbacks', () => {
    const result = analyze_neurosymbolic_graphrag(
      'The agency shall publish the rule. Contractors may appeal.',
      {
        query: 'P(contractors_may_appeal)',
        topK: 1,
      },
    );

    expect(result.retrievedDocuments).toHaveLength(1);
    expect(result.symbolicFacts).toContain('P(contractors_may_appeal)');
    expect(query_neurosymbolic_graphrag('', 'Any(Query)')).toMatchObject({
      status: 'validation_failed',
      success: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: { sourcePythonModule: 'logic/integration/neurosymbolic_graphrag.py' },
    });
  });
});

describe('browser-native symbolic neurosymbolic GraphRAG parity', () => {
  it('ports the symbolic module facade to local deterministic graph retrieval', () => {
    const graphrag = create_browser_native_symbolic_neurosymbolic_graphrag();
    const result = graphrag.query('ignored corpus', 'Compliant(Agency)', {
      documents: [
        {
          id: 'rule-publication',
          title: 'Publication duty',
          text: 'The agency shall publish the final rule before enforcement.',
        },
        {
          id: 'appeal-window',
          text: 'Contractors may appeal within thirty days.',
        },
      ],
      rules: ['O(the_agency_shall_publish_the_final_rule_before_enforcement) => Compliant(Agency)'],
      topK: 1,
    });

    expect(graphrag.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic/neurosymbolic_graphrag.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      graphRuntime: 'deterministic-local-symbolic-graph-rag-adapter',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      proofStatus: 'proved',
      inferredFacts: ['Compliant(Agency)'],
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic_graphrag.py',
      },
    });
    expect(result.retrievedDocuments.map((document) => document.id)).toEqual(['rule-publication']);
    expect(result.retrievalTrace.map((step) => step.detail)).toContain(
      'symbolic_graphrag:Compliant(Agency)',
    );
  });

  it('exposes Python-compatible symbolic aliases and fails closed locally', () => {
    const result = analyze_symbolic_neurosymbolic_graphrag(
      'The court shall dismiss the claim. The clerk may issue notice.',
      {
        query: 'P(the_clerk_may_issue_notice)',
        topK: 1,
      },
    );
    const closed = query_symbolic_neurosymbolic_graphrag('', 'Any(Query)');

    expect(result.symbolicFacts).toContain('P(the_clerk_may_issue_notice)');
    expect(result.metadata.sourcePythonModule).toBe(
      'logic/integration/symbolic/neurosymbolic_graphrag.py',
    );
    expect(closed).toMatchObject({
      status: 'validation_failed',
      success: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic_graphrag.py',
      },
    });
  });
});

describe('browser-native neurosymbolic embedding prover parity', () => {
  it('proves by deterministic local embedding similarity without runtime fallbacks', () => {
    const prover = create_browser_native_embedding_prover();
    const result = prover.prove(
      [
        { id: 'rent-duty', text: 'The tenant must pay rent before the first day of each month.' },
        'The landlord may enter the unit after notice to inspect repairs.',
      ],
      'Tenant rent must be paid monthly.',
      { threshold: 0.5, topK: 2 },
    );

    expect(prover.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/embedding_prover.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      embeddingRuntime: 'deterministic-local-token-vector',
    });
    expect(result).toMatchObject({
      status: 'proved',
      success: true,
      runtime: 'browser-native',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/embedding_prover.py',
      },
    });
    expect(result.matchedPremises[0].premiseId).toBe('rent-duty');
    expect(result.bestSimilarity).toBeGreaterThanOrEqual(0.5);
  });

  it('fails closed for missing inputs and reports below-threshold matches', () => {
    expect(prove_embedding([], 'Tenant pays rent.')).toMatchObject({
      status: 'validation_failed',
      success: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });

    const result = prove_embedding(
      ['The agency shall publish permit rules.'],
      'Tenant pays rent.',
      {
        threshold: 0.95,
      },
    );

    expect(result).toMatchObject({ status: 'not_proved', success: false });
    expect(result.issues).toContain('embedding similarity did not meet proof threshold');
    expect(result.matchedPremises).toHaveLength(1);
  });
});

describe('browser-native hybrid confidence parity', () => {
  it('fuses local signals and fails closed without runtime fallbacks', () => {
    const scorer = create_browser_native_hybrid_confidence();
    const result = scorer.score({
      signals: [{ intent: 'obligation', evidence: 'The tenant must pay rent.', confidence: 0.82 }],
      symbolicConfidence: 0.88,
      retrievalScore: 0.7,
      proofStatus: 'proved',
      evidenceCount: 3,
    });

    expect(scorer.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/hybrid_confidence.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      confidenceRuntime: 'deterministic-local-hybrid-scorer',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      passedThreshold: true,
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/hybrid_confidence.py',
      },
    });
    expect(result.confidence).toBeGreaterThan(0.8);
    expect(result.components.neural).toBe(0.82);
    expect(result.components.evidence).toBe(0.06);
    expect(score_hybrid_confidence({})).toMatchObject({
      status: 'validation_failed',
      success: false,
      confidence: 0,
      issues: ['at least one confidence signal is required'],
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/hybrid_confidence.py',
      },
    });
  });
});

describe('browser-native reasoning coordinator parity', () => {
  it('orchestrates symbolic, embedding, and confidence reasoning locally', () => {
    const coordinator = create_browser_native_reasoning_coordinator();
    const result = coordinator.coordinate('The tenant must pay rent.', 'Protected(Tenant)', {
      rules: ['O(the_tenant_must_pay_rent) => Protected(Tenant)'],
      premises: ['Tenant rent payment creates protected tenancy evidence.'],
      embedding: { threshold: 0.4 },
    });

    expect(coordinator.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/reasoning_coordinator.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      coordinatorRuntime: 'deterministic-local-reasoning-orchestrator',
    });
    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      selectedProof: 'symbolic',
      proofStatus: 'proved',
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/reasoning_coordinator.py',
      },
    });
    expect(result.symbolic.inferredFacts).toEqual(['Protected(Tenant)']);
    expect(result.embedding?.runtime).toBe('browser-native');
    expect(result.confidence.passedThreshold).toBe(true);
    expect(result.reasoningSteps.map((step) => step.kind)).toContain('query_match');
  });

  it('fails closed without local symbolic text or embedding evidence', () => {
    expect(coordinate_reasoning('', 'Protected(Tenant)', { premises: [] })).toMatchObject({
      status: 'validation_failed',
      success: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      selectedProof: 'none',
      issues: expect.arrayContaining(['no local reasoning evidence is available']),
    });
  });
});
