import {
  BrowserNativeIntegrationLogicTranslationCore,
  INTEGRATION_LOGIC_TRANSLATION_CORE_METADATA,
  LogicTranslationCore,
  LogicTranslator,
  translate_integration_logic_core,
} from './logicTranslationCore';

describe('BrowserNativeIntegrationLogicTranslationCore', () => {
  it('ports root logic_translation_core.py as a browser-native compatibility facade', () => {
    const core = new BrowserNativeIntegrationLogicTranslationCore({
      sourceFormat: 'first order logic',
      targetFormat: 'tptp',
    });
    const result = core.translate('forall x. Resident(x) -> Tenant(x)');

    expect(core.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/logic_translation_core.py',
      rootFacadeOf: 'logic/integration/converters/logic_translation_core.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      sourceFormat: 'fol',
      targetFormat: 'tptp',
      metadata: {
        sourcePythonModule: 'logic/integration/logic_translation_core.py',
        converterSourcePythonModule: 'logic/integration/converters/logic_translation_core.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
    expect(result.targetFormula).toContain('fof(formula, axiom');
    expect(result.errors).toEqual([]);
  });

  it('keeps Python import-surface aliases local and fail closed', () => {
    expect(INTEGRATION_LOGIC_TRANSLATION_CORE_METADATA.parity).toContain(
      'root_module_compatibility_reexport',
    );
    expect(LogicTranslationCore).toBe(BrowserNativeIntegrationLogicTranslationCore);
    expect(LogicTranslator).toBe(BrowserNativeIntegrationLogicTranslationCore);

    const core = new LogicTranslator();
    expect(core.convert('forall x. Resident(x) -> O(Comply(x))', 'tdfol', 'fol')).toBe(
      '∀x ((Resident(x)) → (Comply(x)))',
    );
    expect(
      core.translateBatch(['Resident(Alice)', 'Tenant(Bob)'], { targetFormat: 'prolog' }),
    ).toEqual([
      expect.objectContaining({ success: true, targetFormat: 'prolog' }),
      expect.objectContaining({ success: true, targetFormat: 'prolog' }),
    ]);
    expect(translate_integration_logic_core('', 'fol', 'tptp')).toMatchObject({
      status: 'failed',
      success: false,
      errors: ['Formula must be a non-empty string.'],
      metadata: {
        sourcePythonModule: 'logic/integration/logic_translation_core.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
  });
});
