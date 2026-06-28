import {
  BrowserNativeIntegrationDeonticLogicConverter,
  INTEGRATION_DEONTIC_LOGIC_CONVERTER_METADATA,
  type IntegrationDeonticConversionOptions,
  type IntegrationDeonticConverterOptions,
} from './converters/deonticLogicConverter';

export const INTEGRATION_ROOT_DEONTIC_LOGIC_CONVERTER_METADATA = {
  ...INTEGRATION_DEONTIC_LOGIC_CONVERTER_METADATA,
  sourcePythonModule: 'logic/integration/deontic_logic_converter.py',
  parity: [
    'integration_root_deontic_converter',
    'legal_text_norm_extraction',
    'multi_format_projection',
    'local_fail_closed_validation',
  ],
} as const;

export class BrowserNativeIntegrationRootDeonticLogicConverter {
  readonly metadata = INTEGRATION_ROOT_DEONTIC_LOGIC_CONVERTER_METADATA;
  private readonly converter: BrowserNativeIntegrationDeonticLogicConverter;

  constructor(options: IntegrationDeonticConverterOptions = {}) {
    this.converter = new BrowserNativeIntegrationDeonticLogicConverter(options);
  }

  convert(text: string, options: IntegrationDeonticConversionOptions = {}) {
    const result = this.converter.convert(text, options);
    return {
      ...result,
      metadata: {
        ...result.metadata,
        ...INTEGRATION_ROOT_DEONTIC_LOGIC_CONVERTER_METADATA,
        norm_counts: result.metadata.norm_counts,
        output_format: result.metadata.output_format,
      },
    };
  }

  convertBatch(texts: string[], options: IntegrationDeonticConversionOptions = {}) {
    return texts.map((text) => this.convert(text, options));
  }
}

export const BrowserNativeIntegrationDeonticLogicFacade =
  BrowserNativeIntegrationRootDeonticLogicConverter;

export function createBrowserNativeIntegrationRootDeonticLogicConverter(
  options: IntegrationDeonticConverterOptions = {},
) {
  return new BrowserNativeIntegrationRootDeonticLogicConverter(options);
}

export const create_integration_deontic_logic_converter =
  createBrowserNativeIntegrationRootDeonticLogicConverter;

export function convertIntegrationDeonticLogic(
  text: string,
  options: IntegrationDeonticConversionOptions = {},
) {
  return new BrowserNativeIntegrationRootDeonticLogicConverter({
    outputFormat: options.outputFormat,
  }).convert(text, options);
}

export const convert_integration_deontic_logic = convertIntegrationDeonticLogic;
