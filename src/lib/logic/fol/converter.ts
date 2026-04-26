import {
  ConverterValidationResult,
  LogicConverter,
  type ConversionMetadata,
  type ConvertOptions,
} from '../converters';
import { getLogicRuntimeCapabilities } from '../runtimeCapabilities';
import {
  parseFolOperators,
  parseFolQuantifiers,
  parseFolText,
  validateFolSyntax,
  type FolParseResult,
  type FolTokenMatch,
} from './parser';

export type FolOutputFormat = 'json' | 'formula' | 'prolog' | 'tptp';

export interface FolPredicate {
  name: string;
  arity: number;
}

export interface FolFormula {
  formulaString: string;
  predicates: FolPredicate[];
  quantifiers: FolTokenMatch[];
  operators: FolTokenMatch[];
  confidence: number;
  metadata: ConversionMetadata;
  toString(): string;
}

export interface FolConverterOptions {
  useCache?: boolean;
  useIpfs?: boolean;
  useMl?: boolean;
  useNlp?: boolean;
  enableMonitoring?: boolean;
  confidenceThreshold?: number;
  outputFormat?: FolOutputFormat;
  cacheMaxSize?: number;
  cacheTtlMs?: number;
}

export class FOLConverter extends LogicConverter<string, FolFormula> {
  readonly useIpfs: boolean;
  readonly useMl: boolean;
  readonly useNlp: boolean;
  readonly enableMonitoring: boolean;
  readonly confidenceThreshold: number;
  readonly outputFormat: FolOutputFormat;

  constructor(options: FolConverterOptions = {}) {
    super({
      enableCaching: options.useCache ?? true,
      enableValidation: true,
      cacheMaxSize: options.cacheMaxSize,
      cacheTtlMs: options.cacheTtlMs,
    });
    this.useIpfs = false;
    this.useMl = options.useMl ?? true;
    this.useNlp = options.useNlp ?? true;
    this.enableMonitoring = options.enableMonitoring ?? true;
    this.confidenceThreshold = options.confidenceThreshold ?? 0.7;
    this.outputFormat = options.outputFormat ?? 'json';

    if (options.useIpfs) {
      this.useIpfs = false;
    }
  }

  validateInput(text: string): ConverterValidationResult {
    const result = new ConverterValidationResult();
    if (typeof text !== 'string' || text.length === 0) {
      result.addError('Input text must be a non-empty string');
      return result;
    }
    if (text.trim().length === 0) {
      result.addError('Input text cannot be empty or whitespace only');
      return result;
    }
    if (text.trim().length > 10000) {
      result.addWarning('Input text is very long (>10000 chars), may take time to process');
    }
    return result;
  }

  protected convertImpl(text: string, _options: ConvertOptions): FolFormula {
    const parsed = parseFolText(text);
    if (!parsed.validation.valid) {
      throw new Error(parsed.validation.issues.map((issue) => issue.message).join('; '));
    }
    const confidence = this.calculateHeuristicConfidence(text, parsed);
    return {
      formulaString: parsed.formula,
      predicates: extractPredicateNames(parsed.formula).map((name) => ({ name, arity: 1 })),
      quantifiers: parsed.quantifiers,
      operators: parsed.operators,
      confidence,
      metadata: {
        source_text: text,
        validation: parsed.validation,
        predicates_count: extractPredicateNames(parsed.formula).length,
        quantifiers_count: parsed.quantifiers.length,
        output_format: this.outputFormat,
      },
      toString() {
        return parsed.formula;
      },
    };
  }

  protected override getConfidence(output: FolFormula, _input: string, options: ConvertOptions): number {
    return typeof options.confidence === 'number' ? options.confidence : output.confidence;
  }

  protected override getWarnings(_output: FolFormula, _input: string, _options: ConvertOptions): string[] {
    const capabilities = getLogicRuntimeCapabilities().fol;
    return [
      ...(this.useNlp && capabilities.nlpUnavailable
        ? ['Browser-native NLP extraction is not yet complete; regex extraction was used.']
        : []),
      ...(this.useMl && capabilities.mlUnavailable
        ? ['Browser-native ML confidence is not yet complete; heuristic confidence was used.']
        : []),
    ];
  }

  protected override getMetadata(output: FolFormula): ConversionMetadata {
    return {
      ...output.metadata,
      ipfs_enabled: this.useIpfs,
      browser_native_nlp: getLogicRuntimeCapabilities().fol.browserNativeNlp,
      browser_native_ml_confidence: getLogicRuntimeCapabilities().fol.browserNativeMlConfidence,
    };
  }

  toFol(text: string): string {
    const result = this.convert(text);
    return result.output?.formulaString ?? '';
  }

  toProlog(text: string): string {
    return convertFolFormulaToProlog(this.toFol(text));
  }

  toTptp(text: string): string {
    return convertFolFormulaToTptp(this.toFol(text));
  }

  getMonitoringStats(): Record<string, unknown> {
    return {};
  }

  private calculateHeuristicConfidence(text: string, parsed: FolParseResult): number {
    let confidence = 0.5;
    const predicates = extractPredicateNames(parsed.formula);
    if (predicates.length > 0) confidence += 0.2;
    if (parsed.quantifiers.length > 0) confidence += 0.15;
    if (parsed.formula.length > 10) confidence += 0.1;
    if (text.length > 10 && text.length < 500) confidence += 0.05;
    return Math.min(1, confidence);
  }
}

export function convertFolFormulaToProlog(formula: string): string {
  return formula
    .replace(/∀([a-z])\s*\((.+?)\s*→\s*(.+?)\)/g, 'forall($1, implies($2, $3))')
    .replace(/∃([a-z])\s*\((.+?)\s*∧\s*(.+?)\)/g, 'exists($1, and($2, $3))')
    .replace(/¬/g, 'not ')
    .replace(/∧/g, ',')
    .replace(/∨/g, ';')
    .replace(/→/g, ':-');
}

export function convertFolFormulaToTptp(formula: string, name = 'formula_1'): string {
  const body = formula
    .replace(/∀([a-z])\s*/g, '! [$1] : ')
    .replace(/∃([a-z])\s*/g, '? [$1] : ')
    .replace(/∧/g, ' & ')
    .replace(/∨/g, ' | ')
    .replace(/→/g, ' => ')
    .replace(/¬/g, '~');
  return `fof(${name}, axiom, ${body}).`;
}

export function validateFolFormulaText(formula: string): boolean {
  return validateFolSyntax(formula).valid;
}

export function extractFolQuantifiersAndOperators(text: string): {
  quantifiers: FolTokenMatch[];
  operators: FolTokenMatch[];
} {
  return {
    quantifiers: parseFolQuantifiers(text),
    operators: parseFolOperators(text),
  };
}

function extractPredicateNames(formula: string): string[] {
  return [...new Set([...formula.matchAll(/\b([A-Z][A-Za-z0-9_]*)\s*\(/g)].map((match) => match[1]))];
}
