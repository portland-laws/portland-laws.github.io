import { BrowserNativeDomainDeonticQueryEngine, query_deontic_text } from './deonticQueryEngine';

describe('domain deontic query engine browser-native parity', () => {
  const text =
    'The tenant must pay rent within 30 days unless repairs are incomplete. The landlord may inspect the unit after notice. Staff shall not disclose sealed records.';

  it('queries typed deontic criteria against local extracted norms', () => {
    const engine = new BrowserNativeDomainDeonticQueryEngine();
    const result = engine.query(text, {
      normType: 'obligation',
      action: 'pay rent',
      temporal: '30 days',
    });

    expect(engine.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/domain/deontic_query_engine.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      metadata: { match_count: 1, serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
    expect(result.matches[0].matchedFields).toEqual(['normType', 'action', 'temporal']);
    expect(result.matches[0].formula).toContain('O(');
    expect(result.answer).toContain('pay rent');
  });

  it('supports Python-style query aliases and fails closed locally', () => {
    const parsed = query_deontic_text(text, 'which permissions inspect unit');
    const engine = new BrowserNativeDomainDeonticQueryEngine();

    expect(parsed.query).toMatchObject({ normType: 'permission', contains: 'inspect unit' });
    expect(parsed.matches[0].norm.normType).toBe('permission');
    expect(parsed.matches[0].formula).toContain('P(');
    expect(engine.query('', { normType: 'obligation' })).toMatchObject({
      status: 'validation_failed',
      success: false,
      errors: ['source text is required'],
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false, match_count: 0 },
    });
    expect(engine.query(text, {})).toMatchObject({
      status: 'validation_failed',
      errors: ['query must include at least one local criterion'],
    });
  });
});
