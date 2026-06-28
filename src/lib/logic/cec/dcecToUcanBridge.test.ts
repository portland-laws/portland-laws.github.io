import {
  createUnsignedDcecUcanDelegation,
  dcecToUcan,
  dcec_to_ucan_capabilities,
} from './dcecToUcanBridge';

describe('DCEC to UCAN bridge', () => {
  it('maps permission formulas to browser-native UCAN capabilities', () => {
    const result = dcecToUcan('(P (always (comply_with agent portland_city_code_1_01_010)))');

    expect(result.ok).toBe(true);
    expect(result.metadata).toMatchObject({
      sourcePythonModule: 'logic/CEC/nl/dcec_to_ucan_bridge.py',
      pythonRuntime: false,
      serverRuntime: false,
    });
    expect(result.capabilities[0]).toMatchObject({
      with: 'urn:dcec:portland_city_code_1_01_010',
      can: 'dcec/comply_with',
      nb: {
        arguments: ['agent', 'portland_city_code_1_01_010'],
        predicate: 'comply_with',
        requirement: 'PERMISSION',
      },
      deonticOperator: 'P',
      effect: 'can',
    });
  });

  it('maps prohibitions to deny capabilities and preserves Python-compatible aliases', () => {
    const capabilities = dcec_to_ucan_capabilities('(F (block_exit tenant fire_exit))');

    expect(capabilities[0]).toMatchObject({
      with: 'urn:dcec:fire_exit',
      can: 'dcec/block_exit',
      deonticOperator: 'F',
      effect: 'deny',
      nb: { requirement: 'PROHIBITION' },
    });
  });

  it('creates unsigned local delegation tokens without signing or server fallbacks', () => {
    const result = createUnsignedDcecUcanDelegation(
      '(O (pay_rent tenant lease_123))',
      'did:key:issuer',
      'did:key:audience',
      { expiration: 1893456000, proofs: ['bafyproof'] },
    );

    expect(result.ok).toBe(true);
    expect(result.token).toMatch(/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.$/);
    expect(result.payload).toMatchObject({
      iss: 'did:key:issuer',
      aud: 'did:key:audience',
      exp: 1893456000,
      prf: ['bafyproof'],
      att: [{ with: 'urn:dcec:lease_123', can: 'dcec/pay_rent' }],
    });
  });

  it('fails closed for formulas that do not contain deontic capability operators', () => {
    expect(dcecToUcan('(and a b)')).toMatchObject({
      ok: false,
      capabilities: [],
      errors: ['No deontic O, P, or F capability formula was found.'],
    });
  });
});
