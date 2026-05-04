import {
  BrowserNativeIntegrationDeonticLogicCore,
  BrowserNativeIntegrationDeonticLogicConverter,
  convert_deontic_logic_core,
  convert_deontic_logic,
} from './deonticLogicConverter';
import {
  BrowserNativeIntegrationRootDeonticLogicConverter,
  convert_integration_deontic_logic,
} from '../deonticLogicConverter';

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

describe('BrowserNativeIntegrationDeonticLogicCore', () => {
  it('ports deontic_logic_core.py as browser-native norm partitions', () => {
    const core = new BrowserNativeIntegrationDeonticLogicCore({ outputFormat: 'json' });
    const result = core.analyze(
      'The agency shall publish the rule within 30 days. Contractors may appeal. Officers must not disclose sealed records unless the court orders disclosure.',
    );

    expect(core.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/converters/deontic_logic_core.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      metadata: {
        sourcePythonModule: 'logic/integration/converters/deontic_logic_core.py',
        core: 'browser-native-deontic-logic-core',
        norm_counts: { obligation: 1, permission: 1, prohibition: 1 },
      },
    });
    expect(result.obligations).toHaveLength(1);
    expect(result.permissions).toHaveLength(1);
    expect(result.prohibitions).toHaveLength(1);
    expect(result.formulas).toEqual([
      expect.stringContaining('O('),
      expect.stringContaining('P('),
      expect.stringContaining('F('),
    ]);
    expect(result.prohibitions[0].exceptions).toContain('the court orders disclosure');
  });

  it('fails closed locally and supports batch conversion without Python bridges', () => {
    const core = new BrowserNativeIntegrationDeonticLogicCore();
    const batch = core.analyzeBatch(['Tenants must pay rent.', 'Owners may inspect units.']);

    expect(batch.map((entry) => entry.success)).toEqual([true, true]);
    expect(convert_deontic_logic_core('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: {
        sourcePythonModule: 'logic/integration/converters/deontic_logic_core.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
  });
});

describe('BrowserNativeIntegrationRootDeonticLogicConverter', () => {
  it('ports logic/integration/deontic_logic_converter.py as a browser-native facade', () => {
    const converter = new BrowserNativeIntegrationRootDeonticLogicConverter({
      outputFormat: 'json',
    });
    const result = converter.convert(
      'The processor shall delete records within 10 days unless litigation hold applies. The auditor may inspect logs.',
    );

    expect(converter.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/deontic_logic_converter.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      metadata: {
        sourcePythonModule: 'logic/integration/deontic_logic_converter.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        norm_counts: { obligation: 1, permission: 1, prohibition: 0 },
      },
    });
    expect(result.output).toMatchObject({
      norm_counts: { obligation: 1, permission: 1, prohibition: 0 },
    });
    expect(result.formulas).toEqual([expect.stringContaining('O('), expect.stringContaining('P(')]);
  });

  it('keeps Python-style root aliases local and fail-closed', () => {
    expect(
      convert_integration_deontic_logic('The custodian must preserve records.', {
        outputFormat: 'prolog',
      }).output,
    ).toContain('deontic_norm(1');
    expect(convert_integration_deontic_logic('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: {
        sourcePythonModule: 'logic/integration/deontic_logic_converter.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
  });
});
