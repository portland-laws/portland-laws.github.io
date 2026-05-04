import {
  BrowserNativeIntegrationDeonticLogicConverter,
  convert_deontic_logic,
} from './deonticLogicConverter';

describe('BrowserNativeIntegrationDeonticLogicConverter', () => {
  it('converts legal text to structured obligations, permissions, and prohibitions', () => {
    const converter = new BrowserNativeIntegrationDeonticLogicConverter({ outputFormat: 'json' });
    expect(converter.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/converters/deontic_logic_converter.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    const result = converter.convert(
      'The tenant must pay rent unless the unit is uninhabitable. The landlord may enter after notice. The employer shall not retaliate.',
    );

    expect(result).toMatchObject({
      status: 'success',
      success: true,
      outputFormat: 'json',
      metadata: {
        sourcePythonModule: 'logic/integration/converters/deontic_logic_converter.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        norm_counts: { obligation: 1, permission: 1, prohibition: 1 },
      },
    });
    expect(result.formulas).toEqual([
      expect.stringContaining('O('),
      expect.stringContaining('P('),
      expect.stringContaining('F('),
    ]);
    expect(result.norms.map((norm) => norm.exceptions).flat()).toContain(
      'the unit is uninhabitable',
    );
    expect(result.output).toMatchObject({
      norm_counts: { obligation: 1, permission: 1, prohibition: 1 },
    });
  });

  it('projects deterministic local formats and fails closed on invalid input', () => {
    const converter = new BrowserNativeIntegrationDeonticLogicConverter();

    expect(
      converter.convert('The tenant must pay rent.', { outputFormat: 'defeasible' }).output,
    ).toContain('obligatory(');
    expect(
      converter.convert('The tenant must pay rent.', { outputFormat: 'prolog' }).output,
    ).toContain('deontic_norm(1');
    expect(
      converter.convert('The tenant must pay rent.', { outputFormat: 'tptp' }).output,
    ).toContain('fof(deontic_norm_1');
    expect(convert_deontic_logic('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: {
        sourcePythonModule: 'logic/integration/converters/deontic_logic_converter.py',
        serverCallsAllowed: false,
      },
    });
  });
});
