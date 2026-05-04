import {
  BrowserNativeLogicVerification,
  LogicVerifier,
  verify_logic_formula,
} from './logicVerification';

describe('BrowserNativeLogicVerification', () => {
  it('ports logic_verification.py as local browser-native formula verification', () => {
    const verifier = new BrowserNativeLogicVerification();
    const result = verifier.verify('(forall x (implies (Resident x) (O (Comply x))))', {
      format: 'cec',
    });

    expect(verifier.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/logic_verification.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'verified',
      success: true,
      checks: expect.arrayContaining(['balanced_delimiters', 'cec_syntax']),
      metadata: { sourcePythonModule: 'logic/integration/logic_verification.py' },
    });
  });

  it('fails closed for invalid formulas, runtime bridges, and unsupported DCEC', () => {
    const verifier = new LogicVerifier();

    expect(verifier.verify('Tenant(x', { format: 'fol' })).toMatchObject({
      status: 'invalid',
      issues: expect.arrayContaining([
        expect.objectContaining({ message: 'Unbalanced delimiters.' }),
      ]),
    });
    expect(
      verify_logic_formula('fetch("https://example.test/prove")', { requirePredicate: false }),
    ).toMatchObject({ status: 'invalid' });
    expect(
      verifier.verify('forall x (Event(x) implies Happens(x))', { format: 'dcec' }),
    ).toMatchObject({
      status: 'unsupported',
      success: false,
    });
  });
});
