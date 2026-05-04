import {
  analyze_neurosymbolic,
  create_browser_native_neurosymbolic_integration,
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
