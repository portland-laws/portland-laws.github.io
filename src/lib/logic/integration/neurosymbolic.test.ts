import {
  analyze_neurosymbolic,
  analyze_neurosymbolic_graphrag,
  create_browser_native_neurosymbolic_integration,
  create_browser_native_neurosymbolic_graphrag,
  query_neurosymbolic_graphrag,
  reason_neurosymbolic,
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
