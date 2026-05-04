import {
  BrowserNativeLogicVerification,
  LogicVerifier,
  get_logic_verifier_backends,
  select_logic_verifier_backend,
  verify_logic_formula,
} from './logicVerification';
import {
  assert_logic_verification_result,
  check_logic_verification_type,
  is_logic_verification_type,
} from './logicVerificationTypes';
import {
  detect_logic_verification_runtime_bridge,
  normalize_logic_verification_formula,
  summarize_logic_verification_results,
} from './logicVerificationUtils';

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
      checks: expect.arrayContaining(['balanced_delimiters', 'backend:cec', 'cec_syntax']),
      backend: {
        name: 'cec',
        available: true,
        sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
      },
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

  it('ports reasoning logic verifier backend mixin selection without runtime bridges', () => {
    const verifier = new BrowserNativeLogicVerification();
    const backends = get_logic_verifier_backends();

    expect(verifier.backendsMetadata).toMatchObject({
      sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      runtimeDependencies: [],
    });
    expect(backends.map((backend) => backend.name)).toEqual(
      expect.arrayContaining(['local', 'fol', 'tdfol', 'cec', 'dcec', 'z3', 'cvc5', 'lean']),
    );
    expect(select_logic_verifier_backend('tdfol')).toMatchObject({
      name: 'tdfol',
      available: true,
      runtimeDependencies: [],
    });
    expect(verifier.verify('Tenant(x)', { format: 'fol', backend: 'z3' })).toMatchObject({
      status: 'unsupported',
      success: false,
      backend: {
        name: 'z3',
        available: false,
        failureMode: 'fail_closed',
        runtimeDependencies: [],
      },
      issues: expect.arrayContaining([
        expect.objectContaining({ field: 'backend', severity: 'error' }),
      ]),
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

  it('ports logic_verification_utils.py as deterministic browser-native utilities', () => {
    const verifier = new BrowserNativeLogicVerification();
    const verified = verifier.verify('(forall x (implies (Resident x) (Comply x)))', {
      format: 'cec',
    });
    const blocked = verifier.verify('python subprocess fetch("https://example.test")', {
      requirePredicate: false,
    });
    const summary = summarize_logic_verification_results([verified, blocked]);

    expect(normalize_logic_verification_formula('  ∀ x   (A(x) → B(x)) ')).toBe(
      'forall x (A(x) implies B(x))',
    );
    expect(detect_logic_verification_runtime_bridge(blocked.normalizedFormula)).toMatchObject({
      safe: false,
      markers: expect.arrayContaining(['python', 'subprocess', 'http', 'fetch']),
      metadata: { sourcePythonModule: 'logic/integration/logic_verification_utils.py' },
    });
    expect(summary).toMatchObject({
      total: 2,
      verified: 1,
      invalid: 1,
      unsupported: 0,
      failedClosed: true,
      metadata: { sourcePythonModule: 'logic/integration/logic_verification_utils.py' },
    });
    expect(summary.issues).toEqual(
      expect.arrayContaining([expect.objectContaining({ resultIndex: 1, field: 'formula' })]),
    );
  });
});
