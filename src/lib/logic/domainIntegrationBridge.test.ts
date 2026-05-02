import {
  createDomainIntegrationBridge,
  createParityFixtureMetadata,
  validateWorkflowAction,
} from './domainIntegrationBridge';

describe('domain integration bridge parity contract', () => {
  it('creates browser-native integration metadata for interactive workflows', () => {
    const fixture = createParityFixtureMetadata('residential-policy-workflow-v1', [
      'domain_bridge',
      'interactive_workflow',
      'parity_fixture_metadata',
    ]);
    const bridge = createDomainIntegrationBridge({
      bridgeId: 'permit-policy-bridge',
      domain: 'permit-policy',
      runtime: 'browser-native',
      capabilities: ['interactive-workflow-validation'],
      fixture,
      workflows: [
        {
          id: 'review-application',
          label: 'Review application facts',
          requiredFacts: ['parcel_id', 'permit_type'],
          allowedActions: ['validate', 'explain'],
          guardrails: ['no_external_submission', 'no_unredacted_pii'],
        },
      ],
      metadata: {
        source_module: 'ipfs_datasets_py.logic.integration',
      },
    });

    expect(bridge.accepted).toBe(true);
    expect(bridge.runtime).toBe('browser-native');
    expect(bridge.browserNative).toBe(true);
    expect(bridge.wasmCompatible).toBe(true);
    expect(bridge.serverCallsAllowed).toBe(false);
    expect(bridge.pythonServiceAllowed).toBe(false);
    expect(bridge.validationIssues).toEqual([]);
    expect(bridge.capabilities).toEqual(
      expect.arrayContaining([
        'domain-policy-normalization',
        'interactive-workflow-validation',
        'parity-fixture-metadata',
      ]),
    );
    expect(bridge.fixture).toMatchObject({
      fixtureId: 'residential-policy-workflow-v1',
      sourceLogic: 'ipfs_datasets_py.logic',
      capturedWith: 'typescript-contract',
      deterministic: true,
    });
  });

  it('validates workflow actions without calling server or Python fallbacks', () => {
    const bridge = createDomainIntegrationBridge({
      bridgeId: 'permit-policy-bridge',
      domain: 'permit-policy',
      runtime: 'wasm-compatible',
      workflows: [
        {
          id: 'review-application',
          label: 'Review application facts',
          requiredFacts: ['parcel_id', 'permit_type'],
          allowedActions: ['validate'],
          guardrails: ['no_external_submission'],
        },
      ],
    });

    expect(
      validateWorkflowAction(bridge, {
        workflowId: 'review-application',
        actionId: 'validate',
        suppliedFacts: ['parcel_id'],
        acknowledgedGuardrails: ['no_external_submission'],
      }),
    ).toMatchObject({
      accepted: false,
      reason: 'missing_facts',
      missingFacts: ['permit_type'],
    });

    expect(
      validateWorkflowAction(bridge, {
        workflowId: 'review-application',
        actionId: 'validate',
        suppliedFacts: ['parcel_id', 'permit_type'],
      }),
    ).toMatchObject({
      accepted: false,
      reason: 'unacknowledged_guardrails',
      unacknowledgedGuardrails: ['no_external_submission'],
    });

    expect(
      validateWorkflowAction(bridge, {
        workflowId: 'review-application',
        actionId: 'validate',
        suppliedFacts: ['parcel_id', 'permit_type'],
        acknowledgedGuardrails: ['no_external_submission'],
      }),
    ).toEqual({
      accepted: true,
      reason: 'accepted',
      missingFacts: [],
      unacknowledgedGuardrails: [],
    });
  });

  it('fails closed for forbidden integration runtimes', () => {
    const bridge = createDomainIntegrationBridge({
      bridgeId: 'legacy-python-bridge',
      domain: 'permit-policy',
      runtime: 'python-service',
      workflows: [
        {
          id: 'review-application',
          label: 'Review application facts',
          requiredFacts: [],
          allowedActions: ['validate'],
          guardrails: ['no_external_submission'],
        },
      ],
    });

    expect(bridge.accepted).toBe(false);
    expect(bridge.runtime).toBe('fail-closed');
    expect(bridge.serverCallsAllowed).toBe(false);
    expect(bridge.pythonServiceAllowed).toBe(false);
    expect(bridge.capabilities).toContain('fail-closed-adapter');
    expect(bridge.validationIssues).toEqual([
      'forbidden runtime: python-service',
      'unsupported runtime: python-service',
    ]);
  });
});
