import {
  BrowserNativeIntegrationDeonticLogicCore,
  INTEGRATION_DEONTIC_LOGIC_CORE_METADATA,
  type IntegrationDeonticConversionOptions,
  type IntegrationDeonticConverterOptions,
} from './converters/deonticLogicConverter';

export const INTEGRATION_ROOT_DEONTIC_LOGIC_CORE_METADATA = {
  ...INTEGRATION_DEONTIC_LOGIC_CORE_METADATA,
  sourcePythonModule: 'logic/integration/deontic_logic_core.py',
  parity: [
    'integration_root_deontic_core',
    'core_norm_extraction',
    'core_formula_projection',
    'norm_type_partitioning',
    'local_fail_closed_validation',
  ],
} as const;

export class BrowserNativeIntegrationRootDeonticLogicCore {
  readonly metadata = INTEGRATION_ROOT_DEONTIC_LOGIC_CORE_METADATA;
  private readonly core: BrowserNativeIntegrationDeonticLogicCore;

  constructor(options: IntegrationDeonticConverterOptions = {}) {
    this.core = new BrowserNativeIntegrationDeonticLogicCore(options);
  }

  analyze(text: string, options: IntegrationDeonticConversionOptions = {}) {
    const result = this.core.analyze(text, options);
    return {
      ...result,
      metadata: {
        ...result.metadata,
        ...INTEGRATION_ROOT_DEONTIC_LOGIC_CORE_METADATA,
        core: 'browser-native-integration-root-deontic-logic-core',
        norm_counts: result.metadata.norm_counts,
        output_format: result.metadata.output_format,
      },
    };
  }

  convert(text: string, options: IntegrationDeonticConversionOptions = {}) {
    return this.analyze(text, options);
  }

  analyzeBatch(texts: string[], options: IntegrationDeonticConversionOptions = {}) {
    return texts.map((text) => this.analyze(text, options));
  }

  convertBatch(texts: string[], options: IntegrationDeonticConversionOptions = {}) {
    return this.analyzeBatch(texts, options);
  }
}

export const BrowserNativeIntegrationDeonticLogicCoreFacade =
  BrowserNativeIntegrationRootDeonticLogicCore;

export function createBrowserNativeIntegrationRootDeonticLogicCore(
  options: IntegrationDeonticConverterOptions = {},
) {
  return new BrowserNativeIntegrationRootDeonticLogicCore(options);
}

export const create_integration_deontic_logic_core =
  createBrowserNativeIntegrationRootDeonticLogicCore;

export function analyzeIntegrationDeonticLogicCore(
  text: string,
  options: IntegrationDeonticConversionOptions = {},
) {
  return new BrowserNativeIntegrationRootDeonticLogicCore({
    outputFormat: options.outputFormat,
  }).analyze(text, options);
}

export const analyze_integration_deontic_logic_core = analyzeIntegrationDeonticLogicCore;

export function convertIntegrationDeonticLogicCore(
  text: string,
  options: IntegrationDeonticConversionOptions = {},
) {
  return analyzeIntegrationDeonticLogicCore(text, options);
}

export const convert_integration_deontic_logic_core = convertIntegrationDeonticLogicCore;
