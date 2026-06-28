import { BrowserNativeLogicBridge, type LogicBridgeFormat } from '../bridge';

export type LogicTranslationCoreStatus = 'success' | 'partial' | 'failed' | 'unsupported';

export interface LogicTranslationCoreOptions {
  sourceFormat?: LogicBridgeFormat | string;
  targetFormat?: LogicBridgeFormat | string;
}

export interface LogicTranslationCoreResult {
  status: LogicTranslationCoreStatus;
  success: boolean;
  sourceFormula: string;
  targetFormula: string;
  sourceFormat: LogicBridgeFormat;
  targetFormat: LogicBridgeFormat;
  confidence: number;
  warnings: string[];
  errors: string[];
  metadata: Record<string, unknown>;
}

export const LOGIC_TRANSLATION_CORE_METADATA = {
  sourcePythonModule: 'logic/integration/converters/logic_translation_core.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: [
    'deterministic_logic_format_routing',
    'python_style_translation_facade',
    'batch_translation',
    'local_fail_closed_validation',
  ],
} as const;

const FORMAT_ALIASES: Record<string, LogicBridgeFormat> = {
  nl: 'natural_language',
  text: 'natural_language',
  natural: 'natural_language',
  natural_language: 'natural_language',
  legal: 'legal_text',
  legal_text: 'legal_text',
  fol: 'fol',
  first_order: 'fol',
  first_order_logic: 'fol',
  deontic: 'deontic',
  tdfol: 'tdfol',
  temporal_deontic_fol: 'tdfol',
  cec: 'cec',
  dcec: 'dcec',
  prolog: 'prolog',
  tptp: 'tptp',
  json: 'json',
  defeasible: 'defeasible',
};

export class BrowserNativeLogicTranslationCore {
  readonly metadata = LOGIC_TRANSLATION_CORE_METADATA;
  private readonly bridge: BrowserNativeLogicBridge;
  private readonly sourceFormat: LogicBridgeFormat;
  private readonly targetFormat: LogicBridgeFormat;

  constructor(options: LogicTranslationCoreOptions = {}) {
    this.bridge = new BrowserNativeLogicBridge();
    this.sourceFormat = normalizeLogicTranslationFormat(options.sourceFormat ?? 'fol');
    this.targetFormat = normalizeLogicTranslationFormat(options.targetFormat ?? 'tptp');
  }

  translate(
    formula: string,
    options: LogicTranslationCoreOptions = {},
  ): LogicTranslationCoreResult {
    const sourceFormat = normalizeLogicTranslationFormat(options.sourceFormat ?? this.sourceFormat);
    const targetFormat = normalizeLogicTranslationFormat(options.targetFormat ?? this.targetFormat);
    if (formula.trim().length === 0) {
      return failTranslation(
        formula,
        sourceFormat,
        targetFormat,
        'Formula must be a non-empty string.',
      );
    }
    const result = this.bridge.convert({
      source: formula,
      sourceFormat,
      targetFormat,
      metadata: { source_python_module: LOGIC_TRANSLATION_CORE_METADATA.sourcePythonModule },
    });
    return {
      status: result.status,
      success: result.status === 'success' || result.status === 'partial',
      sourceFormula: result.sourceFormula,
      targetFormula: result.targetFormula,
      sourceFormat,
      targetFormat,
      confidence: result.confidence,
      warnings: [...result.warnings],
      errors:
        result.status === 'failed' || result.status === 'unsupported' ? [...result.warnings] : [],
      metadata: {
        ...LOGIC_TRANSLATION_CORE_METADATA,
        ...result.metadata,
        source_format: sourceFormat,
        target_format: targetFormat,
        routed_to: 'BrowserNativeLogicBridge',
      },
    };
  }

  convert(
    formula: string,
    sourceFormat?: LogicBridgeFormat | string,
    targetFormat?: LogicBridgeFormat | string,
  ): string {
    return this.translate(formula, { sourceFormat, targetFormat }).targetFormula;
  }

  translateBatch(
    formulas: string[],
    options: LogicTranslationCoreOptions = {},
  ): LogicTranslationCoreResult[] {
    return formulas.map((formula) => this.translate(formula, options));
  }
}

export function normalizeLogicTranslationFormat(
  format: LogicBridgeFormat | string,
): LogicBridgeFormat {
  const normalized = format
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');
  const mapped = FORMAT_ALIASES[normalized];
  if (!mapped) throw new Error(`Unsupported browser-native logic translation format: ${format}`);
  return mapped;
}

export function createBrowserNativeLogicTranslationCore(options: LogicTranslationCoreOptions = {}) {
  return new BrowserNativeLogicTranslationCore(options);
}

export const create_logic_translation_core = createBrowserNativeLogicTranslationCore;

export function translateLogicCore(
  formula: string,
  sourceFormat: LogicBridgeFormat | string = 'fol',
  targetFormat: LogicBridgeFormat | string = 'tptp',
): LogicTranslationCoreResult {
  return new BrowserNativeLogicTranslationCore().translate(formula, { sourceFormat, targetFormat });
}

export const translate_logic_core = translateLogicCore;

function failTranslation(
  formula: string,
  sourceFormat: LogicBridgeFormat,
  targetFormat: LogicBridgeFormat,
  error: string,
): LogicTranslationCoreResult {
  return {
    status: 'failed',
    success: false,
    sourceFormula: formula,
    targetFormula: '',
    sourceFormat,
    targetFormat,
    confidence: 0,
    warnings: [],
    errors: [error],
    metadata: {
      ...LOGIC_TRANSLATION_CORE_METADATA,
      source_format: sourceFormat,
      target_format: targetFormat,
    },
  };
}
