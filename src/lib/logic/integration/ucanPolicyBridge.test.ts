import {
  BrowserNativeUcanPolicyBridge,
  compile_ucan_policy_bridge,
  create_unsigned_ucan_policy_token,
} from './ucanPolicyBridge';

describe('BrowserNativeUcanPolicyBridge', () => {
  it('ports ucan_policy_bridge.py as an unsigned browser-native policy token bridge', () => {
    const result = compile_ucan_policy_bridge('The tenant shall maintain smoke alarms.', {
      issuer: 'did:key:issuer',
      audience: 'did:key:audience',
      expiration: 1893456000,
      proofs: ['bafyproof'],
    });
    expect(result).toMatchObject({
      ok: true,
      metadata: {
        sourcePythonModule: 'logic/integration/ucan_policy_bridge.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
      delegation: { iss: 'did:key:issuer', aud: 'did:key:audience', signed: false },
    });
    expect(result.token).toMatch(/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.$/);
    expect(result.capabilities[0]).toMatchObject({
      with: 'urn:policy:tenant',
      can: 'policy/maintain_smoke_alarms',
      effect: 'must',
    });
  });

  it('fails closed for invalid local bridge identity and validates standalone payloads', () => {
    expect(
      new BrowserNativeUcanPolicyBridge().compile('The tenant shall maintain smoke alarms.', {
        issuer: 'issuer',
        audience: 'did:key:audience',
      }),
    ).toMatchObject({
      ok: false,
      capabilities: [],
      fail_closed_reason: 'ucan_policy_bridge_invalid_options',
      errors: ['issuer must be a local DID string.'],
    });
    expect(
      create_unsigned_ucan_policy_token({
        iss: 'did:key:i',
        aud: 'did:key:a',
        att: [],
        signed: false,
      }),
    ).toMatchObject({
      ok: false,
      errors: ['delegation must include at least one capability.'],
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
  });
});
