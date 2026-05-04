import {
  buildSignedDelegation,
  compileNlToPolicy,
  convertLegalTextToDeontic,
  convertLogic,
  convertTextToFol,
  createLogicApi,
  evaluateNlPolicy,
  handleLogicApiServerRequest,
  proveLogic,
  resetGlobalLogicApi,
} from './api';
import { LogicMonitor } from './monitoring';

describe('browser-native logic public API facade', () => {
  beforeEach(() => {
    resetGlobalLogicApi();
  });

  it('converts natural language through stable FOL and deontic API wrappers', () => {
    const fol = convertTextToFol('All tenants are residents', { useNlp: true, useMl: true });
    const deontic = convertLegalTextToDeontic('Tenants must maintain exits.', { useMl: true });

    expect(fol).toMatchObject({
      success: true,
      output: { formulaString: '∀x (Tenants(x) → Residents(x))' },
    });
    expect(fol.metadata).toMatchObject({ browser_native_ml_confidence: true });
    expect(deontic).toMatchObject({
      success: true,
      output: {
        formulas: expect.arrayContaining([expect.stringContaining('O(')]),
      },
    });
  });

  it('routes generic conversion and proof requests through local bridge cores', () => {
    const converted = convertLogic('forall x. O(Comply(x))', 'tdfol', 'cec');
    const proof = proveLogic({
      logic: 'cec',
      theorem: '(subject_to ada code)',
      axioms: ['(subject_to ada code)'],
    });

    expect(converted).toMatchObject({
      status: 'success',
      targetFormula: '(forall x (O (Comply x)))',
    });
    expect(converted.metadata).toMatchObject({ server_calls_allowed: false });
    expect(proof).toMatchObject({
      status: 'proved',
      method: 'bridge:cec-forward-chaining',
    });
  });

  it('exposes browser-native NL policy helpers without pretending UCAN signing exists', async () => {
    const compiled = compileNlToPolicy('Tenants may use the community room.');
    const evaluation = evaluateNlPolicy('Tenants may use the community room.', {
      tool: 'use-community-room',
      actor: 'did:example:tenant',
    });
    const signed = await buildSignedDelegation('Tenants may use the community room.', {
      audienceDid: 'did:example:audience',
    });

    expect(compiled).toMatchObject({
      success: true,
      capabilities: { serverCallsAllowed: false, ucanSigningAvailable: false },
    });
    expect(compiled.policyFormula).toContain('P[tenants:Agent]');
    expect(evaluation).toMatchObject({
      tool: 'use-community-room',
      actor: 'did:example:tenant',
      capabilities: { serverCallsAllowed: false },
    });
    expect(typeof evaluation.allowed).toBe('boolean');
    expect(signed).toEqual({
      success: false,
      status: 'unsupported',
      nlText: 'Tenants may use the community room.',
      audienceDid: 'did:example:audience',
      error: 'UCAN signing is not yet ported to browser-native crypto/WASM.',
      capabilities: { serverCallsAllowed: false, ucanSigningAvailable: false },
    });
  });

  it('records API operation metrics through the supplied monitor', () => {
    const api = createLogicApi({ monitor: new LogicMonitor() });

    api.convertTextToFol('All humans are mortal');
    api.convertLegalTextToDeontic('Employers shall not retaliate.');
    api.convertLogic('Resident(Ada)', 'tdfol', 'json');

    expect(api.monitor.getOperationSummary('api.convert_text_to_fol')).toMatchObject({
      total_count: 1,
    });
    expect(api.monitor.getOperationSummary('api.convert_legal_text_to_deontic')).toMatchObject({
      total_count: 1,
    });
    expect(api.monitor.getOperationSummary('api.convert_logic')).toMatchObject({ total_count: 1 });
  });

  it('handles api_server-style requests locally without HTTP, Python, or server fallbacks', async () => {
    const health = await handleLogicApiServerRequest({ method: 'GET', path: '/health' });
    const converted = await handleLogicApiServerRequest({
      method: 'POST',
      path: '/convert',
      body: {
        source: 'All tenants are residents',
        source_format: 'natural_language',
        target_format: 'fol',
      },
    });
    const proof = await handleLogicApiServerRequest({
      method: 'POST',
      path: '/prove',
      body: {
        logic: 'cec',
        theorem: '(subject_to ada code)',
        axioms: ['(subject_to ada code)'],
      },
    });
    const malformed = await handleLogicApiServerRequest({
      method: 'POST',
      path: '/convert',
      body: { source: 'All tenants are residents' },
    });

    expect(health.body).toMatchObject({
      status: 'ok',
      server_runtime: false,
      python_runtime: false,
      server_calls_allowed: false,
    });
    expect(health.headers).toMatchObject({ 'x-logic-runtime': 'browser-native-typescript-wasm' });
    expect(converted).toMatchObject({
      ok: true,
      status: 200,
      body: {
        status: 'partial',
        target_formula: '∀x (Tenants(x) → Residents(x))',
        browser_native_api_server: true,
      },
    });
    expect(proof).toMatchObject({
      ok: true,
      status: 200,
      body: {
        status: 'proved',
        method: 'bridge:cec-forward-chaining',
        browser_native_api_server: true,
        server_calls_allowed: false,
      },
    });
    expect(malformed).toMatchObject({
      ok: false,
      status: 400,
      body: { server_runtime: false, python_runtime: false },
    });
  });
});
