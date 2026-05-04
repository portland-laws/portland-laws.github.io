import {
  BrowserNativeLogicVerification,
  BrowserNativeReasoningLogicVerification,
  LogicVerifier,
  ReasoningLogicVerification,
  get_logic_verifier_backends,
  select_logic_verifier_backend,
  verify_logic_formula,
  verify_reasoning_theorem,
} from './logicVerification';
import {
  assert_logic_verification_result,
  assert_reasoning_logic_verification_summary,
  check_logic_verification_type,
  check_reasoning_logic_verification_type,
  is_logic_verification_type,
} from './logicVerificationTypes';
import {
  detect_logic_verification_runtime_bridge,
  normalize_logic_verification_formula,
  summarize_logic_verification_results,
} from './logicVerificationUtils';
import {
  build_reasoning_logic_theorem_formula,
  normalize_reasoning_logic_assumptions,
  summarize_reasoning_logic_verification_results,
  validate_reasoning_logic_verification_inputs,
} from './reasoningLogicVerificationUtils';
import {
  ProofExecutionEngine,
  assert_proof_execution_result,
  check_consistency,
  check_proof_execution_type,
  is_proof_execution_type,
} from './proofExecutionEngine';

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

  it('ports reasoning logic_verification.py as a browser-native theorem facade', () => {
    const verifier = new BrowserNativeReasoningLogicVerification();
    const result = verifier.verifyTheorem('(forall x (implies (Resident x) (O (Comply x))))', [], {
      format: 'cec',
    });
    const summary = verifier.verifyBatch(['Tenant(x)', 'fetch("https://example.test/prove")'], {
      format: 'fol',
      requirePredicate: false,
    });

    expect(verifier.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/reasoning/logic_verification.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      runtimeDependencies: [],
    });
    expect(result).toMatchObject({
      status: 'verified',
      success: true,
      checks: expect.arrayContaining(['cec_syntax', 'reasoning_theorem_formula']),
    });
    expect(summary).toMatchObject({
      total: 2,
      verified: 1,
      invalid: 1,
      unsupported: 0,
      success: false,
      failedClosed: true,
      metadata: {
        sourcePythonModule: 'logic/integration/reasoning/logic_verification.py',
      },
    });
    expect(summary.results[1].issues).toEqual(
      expect.arrayContaining([expect.objectContaining({ field: 'formula', severity: 'error' })]),
    );
    expect(assert_reasoning_logic_verification_summary(summary)).toBe(summary);
    expect(check_reasoning_logic_verification_type('batch_summary', summary)).toMatchObject({
      ok: true,
      typeName: 'batch_summary',
      metadata: {
        sourcePythonModule: 'logic/integration/reasoning/logic_verification_types.py',
      },
    });
    expect(
      check_reasoning_logic_verification_type('batch_summary', {
        total: -1,
        verified: 0,
        invalid: 0,
        unsupported: 0,
        success: 'yes',
        failedClosed: false,
        results: [{ status: 'proved' }],
        metadata: { sourcePythonModule: 'logic/integration/reasoning/logic_verification_types.py' },
      }),
    ).toMatchObject({
      ok: false,
      issues: expect.arrayContaining([
        expect.objectContaining({ path: '$.total', message: 'expected_non_negative_integer' }),
        expect.objectContaining({ path: '$.success', message: 'expected_boolean' }),
        expect.objectContaining({ path: '$.metadata.sourcePythonModule' }),
      ]),
    });
    expect(
      verify_reasoning_theorem('(forall x (implies (Resident x) (O (Comply x))))', [], {
        format: 'cec',
      }),
    ).toMatchObject({ status: 'verified' });
    expect(new ReasoningLogicVerification().metadata.sourcePythonModule).toBe(
      'logic/integration/reasoning/logic_verification.py',
    );
  });

  it('ports reasoning logic_verification_utils.py as local theorem utilities', () => {
    const formula = build_reasoning_logic_theorem_formula('  ∀ x  (Comply(x)) ', [
      ' Resident(x) ',
      'Resident(x)',
      '',
    ]);
    const result = verify_logic_formula('Tenant(x)', { format: 'fol' });
    const blocked = validate_reasoning_logic_verification_inputs('Comply(x)', [
      'fetch("https://example.test/prove")',
    ]);
    const summary = summarize_reasoning_logic_verification_results([
      result,
      verify_logic_formula('fetch("https://example.test/prove")', { requirePredicate: false }),
    ]);

    expect(normalize_reasoning_logic_assumptions([' A(x) ', 'A(x)', null, 'B(x)'])).toEqual([
      'A(x)',
      'B(x)',
    ]);
    expect(formula).toBe('(forall x (implies (and Resident(x)) forall x (Comply(x))))');
    expect(blocked).toMatchObject({
      valid: false,
      metadata: {
        sourcePythonModule: 'logic/integration/reasoning/logic_verification_utils.py',
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
    expect(blocked.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: 'assumptions.0', severity: 'error' }),
      ]),
    );
    expect(summary).toMatchObject({
      total: 2,
      verified: 1,
      invalid: 1,
      unsupported: 0,
      success: false,
      failedClosed: true,
      metadata: {
        sourcePythonModule: 'logic/integration/reasoning/logic_verification_utils.py',
      },
    });
  });

  it('ports proof_execution_engine.py as a browser-native proof facade', () => {
    const engine = new ProofExecutionEngine({ enableRateLimiting: false });
    const first = engine.prove_deontic_formula('Tenant(x)', 'local');
    const cached = engine.prove('Tenant(x)');
    const blocked = engine.prove('fetch("https://example.test/prove")', 'z3');
    const consistency = check_consistency({ formulas: ['Tenant(x)', 'Resident(x)'] });

    expect(engine.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/reasoning/proof_execution_engine.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      subprocessAllowed: false,
      runtimeDependencies: [],
    });
    expect(first).toMatchObject({ prover: 'local', status: 'success' });
    expect(cached.metadata).toMatchObject({ cacheHit: true });
    expect(blocked).toMatchObject({
      prover: 'z3',
      status: 'unsupported',
    });
    expect(consistency).toMatchObject({ status: 'success', metadata: { checkedFormulas: 2 } });
    expect(engine.get_prover_status()).toMatchObject({
      availableProvers: { local: true, z3: false },
    });
  });

  it('ports proof_execution_engine_types.py as browser-native runtime contracts', () => {
    const engine = new ProofExecutionEngine({ timeout: 12, cacheSize: 2 });
    const result = engine.prove('Tenant(x)');
    const invalid = check_proof_execution_type('result', {
      ...result,
      status: 'pending',
      metadata: { ...result.metadata, pythonRuntimeAllowed: true },
    });

    expect(
      check_proof_execution_type('options', {
        timeout: 12,
        cacheSize: 2,
        defaultProver: 'local',
        enableCaching: true,
      }),
    ).toMatchObject({
      ok: true,
      metadata: {
        sourcePythonModule: 'logic/integration/reasoning/proof_execution_engine_types.py',
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
    expect(is_proof_execution_type('result', result)).toBe(true);
    expect(assert_proof_execution_result(result)).toBe(result);
    expect(check_proof_execution_type('metadata', result.metadata)).toMatchObject({ ok: true });
    expect(invalid).toMatchObject({
      ok: false,
      issues: expect.arrayContaining([
        expect.objectContaining({ path: '$.status', message: 'expected_status' }),
        expect.objectContaining({
          path: '$.metadata.pythonRuntimeAllowed',
          message: 'expected_false',
        }),
      ]),
    });
  });
});
