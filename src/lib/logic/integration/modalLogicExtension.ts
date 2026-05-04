import {
  BrowserNativeModalLogicExtension,
  MODAL_LOGIC_EXTENSION_METADATA,
  type ModalExtensionConversionOptions,
  type ModalExtensionOptions,
} from './converters/modalLogicExtension';

export {
  type ModalExtensionClause,
  type ModalExtensionConversionOptions,
  type ModalExtensionOperator,
  type ModalExtensionOptions,
  type ModalExtensionOutputFormat,
} from './converters/modalLogicExtension';

export type IntegrationModalLogicExtensionResult = Omit<
  ReturnType<BrowserNativeModalLogicExtension['convert']>,
  'metadata'
> & {
  metadata: Record<string, unknown>;
};

export const INTEGRATION_MODAL_LOGIC_EXTENSION_METADATA = {
  ...MODAL_LOGIC_EXTENSION_METADATA,
  sourcePythonModule: 'logic/integration/modal_logic_extension.py',
  rootFacadeOf: MODAL_LOGIC_EXTENSION_METADATA.sourcePythonModule,
  parity: [...MODAL_LOGIC_EXTENSION_METADATA.parity, 'root_module_compatibility_facade'],
} as const;

export class BrowserNativeIntegrationModalLogicExtension {
  readonly metadata = INTEGRATION_MODAL_LOGIC_EXTENSION_METADATA;
  private readonly extension: BrowserNativeModalLogicExtension;

  constructor(options: ModalExtensionOptions = {}) {
    this.extension = new BrowserNativeModalLogicExtension(options);
  }

  convert(
    text: string,
    options: ModalExtensionConversionOptions = {},
  ): IntegrationModalLogicExtensionResult {
    return withIntegrationModalMetadata(this.extension.convert(text, options));
  }

  extend(
    text: string,
    options: ModalExtensionConversionOptions = {},
  ): IntegrationModalLogicExtensionResult {
    return this.convert(text, options);
  }

  convertBatch(
    texts: Array<string>,
    options: ModalExtensionConversionOptions = {},
  ): Array<IntegrationModalLogicExtensionResult> {
    return texts.map((text) => this.convert(text, options));
  }
}

export const ModalLogicExtension = BrowserNativeIntegrationModalLogicExtension;

export function createBrowserNativeIntegrationModalLogicExtension(
  options: ModalExtensionOptions = {},
): BrowserNativeIntegrationModalLogicExtension {
  return new BrowserNativeIntegrationModalLogicExtension(options);
}

export const create_integration_modal_logic_extension =
  createBrowserNativeIntegrationModalLogicExtension;

export function convertIntegrationModalLogicExtension(
  text: string,
  options: ModalExtensionConversionOptions = {},
): IntegrationModalLogicExtensionResult {
  return new BrowserNativeIntegrationModalLogicExtension(options).convert(text, options);
}

export const convert_integration_modal_logic_extension = convertIntegrationModalLogicExtension;
export const extend_integration_modal_logic = convertIntegrationModalLogicExtension;

function withIntegrationModalMetadata(
  result: IntegrationModalLogicExtensionResult,
): IntegrationModalLogicExtensionResult {
  return {
    ...result,
    metadata: {
      ...result.metadata,
      ...INTEGRATION_MODAL_LOGIC_EXTENSION_METADATA,
      converterSourcePythonModule: MODAL_LOGIC_EXTENSION_METADATA.sourcePythonModule,
      output_format: result.outputFormat,
    },
  };
}
