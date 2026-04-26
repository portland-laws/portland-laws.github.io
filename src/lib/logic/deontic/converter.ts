import {
  ConverterValidationResult,
  LogicConverter,
  type ConversionMetadata,
  type ConvertOptions,
} from '../converters';
import { getLogicRuntimeCapabilities } from '../runtimeCapabilities';
import {
  buildDeonticFormula,
  convertLegalTextToDeontic,
  type DeonticNormType,
  type DeonticOperator,
  type NormativeElement,
} from './parser';

export type DeonticOutputFormat = 'json' | 'formula' | 'prolog' | 'tptp';
export type DeonticJurisdiction = 'us' | 'eu' | 'uk' | 'international' | 'general';
export type DeonticDocumentType = 'statute' | 'regulation' | 'contract' | 'policy' | 'agreement' | 'general';

export interface DeonticFormula {
  operator: DeonticOperator;
  normType: DeonticNormType;
  proposition: string;
  formulas: string[];
  elements: NormativeElement[];
  confidence: number;
  sourceText: string;
  metadata: ConversionMetadata;
  toString(): string;
}

export interface DeonticConverterOptions {
  useCache?: boolean;
  useIpfs?: boolean;
  useMl?: boolean;
  enableMonitoring?: boolean;
  jurisdiction?: DeonticJurisdiction;
  documentType?: DeonticDocumentType;
  extractObligations?: boolean;
  includeExceptions?: boolean;
  confidenceThreshold?: number;
  outputFormat?: DeonticOutputFormat;
  cacheMaxSize?: number;
  cacheTtlMs?: number;
}

const JURISDICTIONS: DeonticJurisdiction[] = ['us', 'eu', 'uk', 'international', 'general'];
const DOCUMENT_TYPES: DeonticDocumentType[] = ['statute', 'regulation', 'contract', 'policy', 'agreement', 'general'];

export class DeonticConverter extends LogicConverter<string, DeonticFormula> {
  readonly useIpfs: boolean;
  readonly useMl: boolean;
  readonly enableMonitoring: boolean;
  readonly jurisdiction: DeonticJurisdiction;
  readonly documentType: DeonticDocumentType;
  readonly extractObligations: boolean;
  readonly includeExceptions: boolean;
  readonly confidenceThreshold: number;
  readonly outputFormat: DeonticOutputFormat;

  private conversions = 0;
  private successful = 0;
  private failed = 0;

  constructor(options: DeonticConverterOptions = {}) {
    super({
      enableCaching: options.useCache ?? true,
      enableValidation: true,
      cacheMaxSize: options.cacheMaxSize,
      cacheTtlMs: options.cacheTtlMs,
    });
    this.useIpfs = false;
    this.useMl = options.useMl ?? true;
    this.enableMonitoring = options.enableMonitoring ?? true;
    this.jurisdiction = normalizeOption(options.jurisdiction, JURISDICTIONS, 'general');
    this.documentType = normalizeOption(options.documentType, DOCUMENT_TYPES, 'general');
    this.extractObligations = options.extractObligations ?? true;
    this.includeExceptions = options.includeExceptions ?? true;
    this.confidenceThreshold = options.confidenceThreshold ?? 0.7;
    this.outputFormat = options.outputFormat ?? 'json';

    if (options.useIpfs) {
      this.useIpfs = false;
    }
  }

  override convert(text: string, options: ConvertOptions = {}) {
    this.conversions += 1;
    const result = super.convert(text, options);
    if (result.success) {
      this.successful += 1;
    } else {
      this.failed += 1;
    }
    return result;
  }

  validateInput(text: string): ConverterValidationResult {
    const result = new ConverterValidationResult();
    if (typeof text !== 'string' || text.length === 0) {
      result.addError('Input text must be a non-empty string');
      return result;
    }
    if (text.trim().length === 0) {
      result.addError('Input text cannot be empty or whitespace');
      return result;
    }
    if (text.trim().length < 3) {
      result.addError('Input text too short (minimum 3 characters)');
    }
    return result;
  }

  protected convertImpl(text: string, _options: ConvertOptions): DeonticFormula {
    const converted = convertLegalTextToDeontic(text);
    const firstElement = converted.elements[0];
    const proposition = firstElement ? buildDeonticFormula(firstElement) : '';
    return {
      operator: firstElement?.deonticOperator ?? 'O',
      normType: firstElement?.normType ?? 'obligation',
      proposition,
      formulas: converted.formulas,
      elements: converted.elements,
      confidence: converted.confidence,
      sourceText: text,
      metadata: {
        source_text: text,
        jurisdiction: this.jurisdiction,
        document_type: this.documentType,
        elements_count: converted.elements.length,
        output_format: this.outputFormat,
      },
      toString() {
        return proposition;
      },
    };
  }

  protected override getConfidence(output: DeonticFormula, _input: string, options: ConvertOptions): number {
    return typeof options.confidence === 'number' ? options.confidence : output.confidence;
  }

  protected override getWarnings(output: DeonticFormula): string[] {
    return [
      ...(output.elements.length > 0 ? [] : ['No normative indicators were detected']),
      ...(this.useMl && getLogicRuntimeCapabilities().deontic.mlUnavailable
        ? ['Browser-native ML confidence is not yet complete; heuristic confidence was used.']
        : []),
    ];
  }

  protected override getMetadata(output: DeonticFormula): ConversionMetadata {
    return {
      ...output.metadata,
      ipfs_enabled: this.useIpfs,
      browser_native_ml_confidence: getLogicRuntimeCapabilities().deontic.browserNativeMlConfidence,
    };
  }

  toDeontic(text: string): string {
    const result = this.convert(text);
    return result.output?.proposition ?? '';
  }

  getStats(): Record<string, number> {
    return {
      conversions: this.conversions,
      successful: this.successful,
      failed: this.failed,
    };
  }

  getMonitoringStats(): Record<string, unknown> {
    return {};
  }
}

function normalizeOption<T extends string>(value: T | undefined, allowed: T[], fallback: T): T {
  return value && allowed.includes(value) ? value : fallback;
}
