import {
  BrowserNativeNlUcanPolicyCompiler,
  compile_nl_ucan_policy,
  compileNlUcanPolicy,
} from './nlUcanPolicyCompiler';

describe('BrowserNativeNlUcanPolicyCompiler', () => {
  it('ports nl_ucan_policy_compiler.py as browser-native NL policy capabilities', () => {
    const result = compileNlUcanPolicy(
      'The tenant shall maintain smoke alarms. The landlord may inspect alarms.',
      {
        issuer: 'did:key:issuer',
        audience: 'did:key:audience',
        expiration: 1893456000,
        proofs: ['bafyproof'],
      },
    );

    expect(result).toMatchObject({
      ok: true,
      success: true,
      metadata: {
        sourcePythonModule: 'logic/integration/nl_ucan_policy_compiler.py',
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
      delegation: {
        iss: 'did:key:issuer',
        aud: 'did:key:audience',
        exp: 1893456000,
        prf: ['bafyproof'],
        signed: false,
      },
    });
    expect(result.capabilities).toEqual([
      expect.objectContaining({
        with: 'urn:policy:tenant',
        can: 'policy/maintain_smoke_alarms',
        deonticOperator: 'O',
        effect: 'must',
        nb: expect.objectContaining({ requirement: 'OBLIGATION', subject: 'tenant' }),
      }),
      expect.objectContaining({
        with: 'urn:policy:landlord',
        can: 'policy/inspect_alarms',
        deonticOperator: 'P',
        effect: 'can',
      }),
    ]);
  });

  it('maps prohibitions to deny effects and preserves Python-compatible aliases', () => {
    const compiler = new BrowserNativeNlUcanPolicyCompiler();
    const result = compile_nl_ucan_policy('The landlord must not enter the unit.');

    expect(compiler.metadata.sourcePythonModule).toBe(
      'logic/integration/nl_ucan_policy_compiler.py',
    );
    expect(result.capabilities[0]).toMatchObject({
      can: 'policy/enter_the_unit',
      deonticOperator: 'F',
      effect: 'deny',
      nb: { requirement: 'PROHIBITION' },
    });
  });

  it('fails closed for unsupported local NLP input without server or Python fallback', () => {
    expect(compileNlUcanPolicy('El inquilino debe pagar la renta.')).toMatchObject({
      ok: false,
      success: false,
      capabilities: [],
      fail_closed_reason: 'ucan_capability_compile_failed',
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
  });
});
