import {
  BrowserNativeLogicTranslationCore,
  LOGIC_TRANSLATION_CORE_METADATA,
  normalizeLogicTranslationFormat,
  translate_logic_core,
} from './logicTranslationCore';

describe('BrowserNativeLogicTranslationCore', () => {
  it('ports logic_translation_core.py as local deterministic format translation', () => {
    const core = new BrowserNativeLogicTranslationCore({
      sourceFormat: 'first-order logic',
      targetFormat: 'tptp',
    });
    const result = core.translate('∀x (Resident(x) → Tenant(x))');

    expect(core.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/converters/logic_translation_core.py',
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
        sourcePythonModule: 'logic/integration/converters/logic_translation_core.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        routed_to: 'BrowserNativeLogicBridge',
      },
    });
    expect(result.targetFormula).toContain('fof(formula, axiom');
    expect(result.errors).toEqual([]);
  });

  it('supports Python-style aliases, batch translation, and fail-closed validation', () => {
    expect(LOGIC_TRANSLATION_CORE_METADATA.parity).toContain('batch_translation');
    expect(normalizeLogicTranslationFormat('first-order')).toBe('fol');
    expect(normalizeLogicTranslationFormat('temporal deontic fol')).toBe('tdfol');

    const core = new BrowserNativeLogicTranslationCore();
    expect(core.convert('forall x. Resident(x) -> O(Comply(x))', 'tdfol', 'fol')).toBe(
      '∀x ((Resident(x)) → (Comply(x)))',
    );
    expect(
      core.translateBatch(['Resident(Alice)', 'Tenant(Bob)'], { targetFormat: 'prolog' }),
    ).toEqual([
      expect.objectContaining({ success: true, targetFormat: 'prolog' }),
      expect.objectContaining({ success: true, targetFormat: 'prolog' }),
    ]);
    expect(core.translate('', { sourceFormat: 'fol', targetFormat: 'tptp' })).toMatchObject({
      status: 'failed',
      success: false,
      errors: ['Formula must be a non-empty string.'],
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
    expect(translate_logic_core('Resident(Alice)', 'fol', 'json')).toMatchObject({
      status: 'success',
      targetFormat: 'json',
    });
  });
});
