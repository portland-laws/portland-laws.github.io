import {
  BrowserNativeTemporalDeonticApi,
  analyze_temporal_deontic_text,
} from './temporalDeonticApi';

describe('browser-native temporal deontic api', () => {
  const text =
    'The agency shall publish the rule within 30 days. The auditor may inspect records monthly. Officers must not disclose sealed records unless the court orders disclosure.';

  it('projects temporal deontic status without Python bridges', () => {
    const api = new BrowserNativeTemporalDeonticApi();
    const result = api.analyze(text, {
      effectiveDate: '2026-05-01T00:00:00.000Z',
      asOf: '2026-05-15T00:00:00.000Z',
    });

    expect(api.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/domain/temporal_deontic_api.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result.metadata).toMatchObject({ norm_count: 3, temporal_count: 2, active_count: 1 });
    expect(result.obligations[0]).toMatchObject({ temporalStatus: 'active' });
    expect(result.permissions[0]).toMatchObject({
      temporalStatus: 'recurring',
      interval: { recurring: 'monthly' },
    });
    expect(result.prohibitions[0].norm.exceptions).toContain('the court orders disclosure');
  });

  it('supports Python-style aliases and fails closed locally', () => {
    expect(
      analyze_temporal_deontic_text('The clerk shall file notice within 2 days.', {
        effectiveDate: '2026-05-01T00:00:00.000Z',
        asOf: '2026-05-10T00:00:00.000Z',
      }).norms[0],
    ).toMatchObject({ temporalStatus: 'expired' });
    expect(new BrowserNativeTemporalDeonticApi().analyze('', { asOf: 'bad-date' })).toMatchObject({
      status: 'validation_failed',
      success: false,
      errors: ['source text is required', 'asOf must be a valid date'],
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
  });
});
