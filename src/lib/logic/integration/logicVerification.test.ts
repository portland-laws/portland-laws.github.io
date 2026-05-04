import {
  BrowserNativeLogicVerification,
  LogicVerifier,
  verify_logic_formula,
} from './logicVerification';
import {
  assert_logic_verification_result,
  check_logic_verification_type,
  is_logic_verification_type,
} from './logicVerificationTypes';

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

  it('ports logic_verification_types.py as browser-native runtime type checks', () => {
    const verifier = new BrowserNativeLogicVerification();
    const result = verifier.verify('Tenant(x)', { format: 'fol' });

    expect(is_logic_verification_type('options', { format: 'cec', requirePredicate: true })).toBe(
      true,
    );
    expect(assert_logic_verification_result(result)).toBe(result);
    expect(check_logic_verification_type('result', result)).toMatchObject({
      ok: true,
      typeName: 'result',
      metadata: { sourcePythonModule: 'logic/integration/logic_verification_types.py' },
    });
    expect(
      check_logic_verification_type('result', {
        status: 'proved',
        success: true,
        formula: 'Tenant(x)',
        format: 'fol',
        normalizedFormula: 'Tenant(x)',
        checks: ['input_string'],
        issues: [{ severity: 'notice', message: '' }],
        metadata: {
          sourcePythonModule: 'logic/integration/logic_verification_types.py',
          browserNative: false,
          serverCallsAllowed: true,
          pythonRuntimeAllowed: true,
          runtimeDependencies: ['python'],
        },
      }),
    ).toMatchObject({
      ok: false,
      issues: expect.arrayContaining([
        expect.objectContaining({ path: '$.status', message: 'expected_status' }),
        expect.objectContaining({ path: '$.metadata.browserNative', message: 'expected_true' }),
        expect.objectContaining({ path: '$.metadata.runtimeDependencies' }),
      ]),
    });
  });
});
