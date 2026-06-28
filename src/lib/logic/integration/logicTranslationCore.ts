import {
  BrowserNativeLogicTranslationCore,
  LOGIC_TRANSLATION_CORE_METADATA,
  type LogicTranslationCoreOptions,
  type LogicTranslationCoreResult,
  type LogicTranslationCoreStatus,
  createBrowserNativeLogicTranslationCore,
  create_logic_translation_core,
  normalizeLogicTranslationFormat,
  translateLogicCore,
  translate_logic_core,
} from './converters/logicTranslationCore';
import type { LogicBridgeFormat } from './bridge';

export {
  LOGIC_TRANSLATION_CORE_METADATA,
  type LogicTranslationCoreOptions,
  type LogicTranslationCoreResult,
  type LogicTranslationCoreStatus,
  createBrowserNativeLogicTranslationCore,
  create_logic_translation_core,
  normalizeLogicTranslationFormat,
  translateLogicCore,
  translate_logic_core,
} from './converters/logicTranslationCore';

export const INTEGRATION_LOGIC_TRANSLATION_CORE_METADATA = {
  ...LOGIC_TRANSLATION_CORE_METADATA,
  sourcePythonModule: 'logic/integration/logic_translation_core.py',
  rootFacadeOf: LOGIC_TRANSLATION_CORE_METADATA.sourcePythonModule,
  parity: [...LOGIC_TRANSLATION_CORE_METADATA.parity, 'root_module_compatibility_reexport'],
} as const;

export class BrowserNativeIntegrationLogicTranslationCore {
  readonly metadata = INTEGRATION_LOGIC_TRANSLATION_CORE_METADATA;
  private readonly core: BrowserNativeLogicTranslationCore;

  constructor(options: LogicTranslationCoreOptions = {}) {
    this.core = new BrowserNativeLogicTranslationCore(options);
  }

  translate(
    formula: string,
    options: LogicTranslationCoreOptions = {},
  ): LogicTranslationCoreResult {
    return withRootMetadata(this.core.translate(formula, options));
  }

  convert(
    formula: string,
    sourceFormat?: LogicBridgeFormat | string,
    targetFormat?: LogicBridgeFormat | string,
  ): string {
    return this.translate(formula, { sourceFormat, targetFormat }).targetFormula;
  }

  translateBatch(
    formulas: Array<string>,
    options: LogicTranslationCoreOptions = {},
  ): Array<LogicTranslationCoreResult> {
    return formulas.map((formula) => this.translate(formula, options));
  }
}

export const LogicTranslationCore = BrowserNativeIntegrationLogicTranslationCore;
export const LogicTranslator = BrowserNativeIntegrationLogicTranslationCore;

export function createBrowserNativeIntegrationLogicTranslationCore(
  options: LogicTranslationCoreOptions = {},
): BrowserNativeIntegrationLogicTranslationCore {
  return new BrowserNativeIntegrationLogicTranslationCore(options);
}

export const create_integration_logic_translation_core =
  createBrowserNativeIntegrationLogicTranslationCore;

export function translateIntegrationLogicCore(
  formula: string,
  sourceFormat: LogicBridgeFormat | string = 'fol',
  targetFormat: LogicBridgeFormat | string = 'tptp',
): LogicTranslationCoreResult {
  const result = translateLogicCore(formula, sourceFormat, targetFormat);
  return withRootMetadata(result);
}

export const translate_integration_logic_core = translateIntegrationLogicCore;

function withRootMetadata(result: LogicTranslationCoreResult): LogicTranslationCoreResult {
  return {
    ...result,
    metadata: {
      ...result.metadata,
      ...INTEGRATION_LOGIC_TRANSLATION_CORE_METADATA,
      converterSourcePythonModule: LOGIC_TRANSLATION_CORE_METADATA.sourcePythonModule,
      source_format: result.sourceFormat,
      target_format: result.targetFormat,
    },
  };
}
