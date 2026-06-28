import {
  BrowserNativeIntegrationModalLogicExtension,
  INTEGRATION_MODAL_LOGIC_EXTENSION_METADATA,
  convert_integration_modal_logic_extension,
} from './modalLogicExtension';

describe('BrowserNativeIntegrationModalLogicExtension', () => {
  it('ports root modal_logic_extension.py as a browser-native facade over local modal projection', () => {
    const extension = new BrowserNativeIntegrationModalLogicExtension({
      outputFormat: 'json',
      runTableaux: true,
    });
    const result = extension.convert(
      'The tenant must pay rent. The landlord may enter after notice.',
    );

    expect(extension.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/modal_logic_extension.py',
      rootFacadeOf: 'logic/integration/converters/modal_logic_extension.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      formulas: ['box(Tenant_PayRent)', 'diamond(Landlord_EnterAfterNotice)'],
      metadata: {
        sourcePythonModule: 'logic/integration/modal_logic_extension.py',
        converterSourcePythonModule: 'logic/integration/converters/modal_logic_extension.py',
        clause_count: 2,
        tableaux_checked: true,
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
      tableaux: { metadata: { browserNative: true, pythonFallback: false } },
    });
  });

  it('supports root aliases, batch conversion, and fail-closed local validation', () => {
    expect(INTEGRATION_MODAL_LOGIC_EXTENSION_METADATA.parity).toContain(
      'root_module_compatibility_facade',
    );
    const extension = new BrowserNativeIntegrationModalLogicExtension();

    expect(extension.extend('Users may appeal decisions.', { outputFormat: 'prolog' }).output).toBe(
      'modal_clause(1, "diamond(Users_AppealDecisions)").',
    );
    expect(extension.convertBatch(['Auditors must inspect logs.'])).toEqual([
      expect.objectContaining({
        success: true,
        formulas: ['box(Auditors_InspectLogs)'],
        metadata: expect.objectContaining({
          sourcePythonModule: 'logic/integration/modal_logic_extension.py',
        }),
      }),
    ]);
    expect(convert_integration_modal_logic_extension('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: {
        sourcePythonModule: 'logic/integration/modal_logic_extension.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
  });
});
