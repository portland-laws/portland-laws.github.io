import { formatCecExpression } from '../cec/formatter';
import { parseCecExpression } from '../cec/parser';
import { proveCec } from '../cec/prover';
import type { CecProverOptions } from '../cec/prover';
import { DeonticConverter, type DeonticConverterOptions } from '../deontic/converter';
import { FOLConverter, type FolConverterOptions } from '../fol/converter';
import { formatDeontic, formatFol, type FormattedDeontic, type FormattedFol, type LogicOutputFormat } from '../fol/formatter';
import { LogicBridgeError } from '../errors';
import { parseTdfolFormula } from '../tdfol/parser';
import { convertTdfolFormula, type TdfolConversionTarget } from '../tdfol/converter';
import { proveTdfol, type TdfolProverOptions } from '../tdfol/prover';
import {
  BRIDGE_CAPABILITIES,
  BridgeMetadata,
  LogicBridgeConversionResult,
  type ProofResult,
} from '../types';

export type LogicBridgeFormat =
  | 'natural_language'
  | 'legal_text'
  | 'fol'
  | 'deontic'
  | 'tdfol'
  | 'cec'
  | 'dcec'
  | 'prolog'
  | 'tptp'
  | 'json'
  | 'defeasible';

export interface BrowserNativeLogicBridgeOptions {
  fol?: FolConverterOptions;
  deontic?: DeonticConverterOptions;
  tdfol?: TdfolProverOptions;
  cec?: CecProverOptions;
}

export interface BridgeConversionRequest {
  source: string;
  sourceFormat: LogicBridgeFormat;
  targetFormat: LogicBridgeFormat;
  metadata?: Record<string, unknown>;
}

export interface BridgeProofRequest {
  logic: 'tdfol' | 'cec' | 'dcec';
  theorem: string;
  axioms: string[];
  theorems?: string[];
  maxSteps?: number;
  maxDerivedFormulas?: number;
}

interface ConversionRoute {
  readonly sourceFormat: LogicBridgeFormat;
  readonly targetFormat: LogicBridgeFormat;
  readonly description: string;
}

const ROUTES: ConversionRoute[] = [
  { sourceFormat: 'natural_language', targetFormat: 'fol', description: 'regex/ML-assisted FOL extraction' },
  { sourceFormat: 'legal_text', targetFormat: 'fol', description: 'legal text to FOL extraction' },
  { sourceFormat: 'natural_language', targetFormat: 'deontic', description: 'norm extraction' },
  { sourceFormat: 'legal_text', targetFormat: 'deontic', description: 'legal norm extraction' },
  { sourceFormat: 'fol', targetFormat: 'prolog', description: 'FOL formatter projection' },
  { sourceFormat: 'fol', targetFormat: 'tptp', description: 'FOL formatter projection' },
  { sourceFormat: 'fol', targetFormat: 'json', description: 'FOL structured formatter projection' },
  { sourceFormat: 'deontic', targetFormat: 'json', description: 'deontic structured formatter projection' },
  { sourceFormat: 'deontic', targetFormat: 'defeasible', description: 'deontic defeasible projection' },
  { sourceFormat: 'tdfol', targetFormat: 'tdfol', description: 'TDFOL parser and stable formatter' },
  { sourceFormat: 'tdfol', targetFormat: 'fol', description: 'TDFOL to FOL projection' },
  { sourceFormat: 'tdfol', targetFormat: 'cec', description: 'TDFOL to CEC expression projection' },
  { sourceFormat: 'tdfol', targetFormat: 'dcec', description: 'TDFOL to DCEC expression projection' },
  { sourceFormat: 'tdfol', targetFormat: 'tptp', description: 'TDFOL to TPTP projection' },
  { sourceFormat: 'tdfol', targetFormat: 'json', description: 'TDFOL structured projection' },
  { sourceFormat: 'cec', targetFormat: 'cec', description: 'CEC parser and stable formatter' },
  { sourceFormat: 'cec', targetFormat: 'json', description: 'CEC AST JSON projection' },
  { sourceFormat: 'dcec', targetFormat: 'cec', description: 'DCEC/CEC stable formatter' },
  { sourceFormat: 'dcec', targetFormat: 'json', description: 'DCEC/CEC AST JSON projection' },
];

export class BrowserNativeLogicBridge {
  readonly metadata = new BridgeMetadata(
    'browser-native-logic-bridge',
    '0.1.0-ts',
    'typescript-wasm-browser',
    [
      BRIDGE_CAPABILITIES.BIDIRECTIONAL_CONVERSION,
      BRIDGE_CAPABILITIES.RULE_EXTRACTION,
      BRIDGE_CAPABILITIES.OPTIMIZATION,
    ],
    false,
    'Routes logic conversion and proof requests to local TypeScript/WASM-compatible cores without server calls.',
  );

  private readonly folConverter: FOLConverter;
  private readonly deonticConverter: DeonticConverter;
  private readonly tdfolOptions: TdfolProverOptions;
  private readonly cecOptions: CecProverOptions;

  constructor(options: BrowserNativeLogicBridgeOptions = {}) {
    this.folConverter = new FOLConverter(options.fol);
    this.deonticConverter = new DeonticConverter(options.deontic);
    this.tdfolOptions = options.tdfol ?? {};
    this.cecOptions = options.cec ?? {};
  }

  listRoutes(): ConversionRoute[] {
    return ROUTES.map((route) => ({ ...route }));
  }

  supportsConversion(sourceFormat: LogicBridgeFormat, targetFormat: LogicBridgeFormat): boolean {
    return ROUTES.some((route) => route.sourceFormat === sourceFormat && route.targetFormat === targetFormat);
  }

  convert(source: string, sourceFormat: LogicBridgeFormat, targetFormat: LogicBridgeFormat): LogicBridgeConversionResult;
  convert(request: BridgeConversionRequest): LogicBridgeConversionResult;
  convert(
    requestOrSource: BridgeConversionRequest | string,
    sourceFormat?: LogicBridgeFormat,
    targetFormat?: LogicBridgeFormat,
  ): LogicBridgeConversionResult {
    const request =
      typeof requestOrSource === 'string'
        ? {
            source: requestOrSource,
            sourceFormat: sourceFormat ?? 'natural_language',
            targetFormat: targetFormat ?? 'fol',
          }
        : requestOrSource;

    if (!this.supportsConversion(request.sourceFormat, request.targetFormat)) {
      return new LogicBridgeConversionResult(
        'unsupported',
        request.source,
        '',
        request.sourceFormat,
        request.targetFormat,
        0,
        [`Unsupported browser-native conversion route: ${request.sourceFormat} -> ${request.targetFormat}`],
        { server_calls_allowed: false, ...(request.metadata ?? {}) },
      );
    }

    try {
      return this.convertSupported(request);
    } catch (error) {
      return new LogicBridgeConversionResult(
        'failed',
        request.source,
        '',
        request.sourceFormat,
        request.targetFormat,
        0,
        [error instanceof Error ? error.message : 'Unknown browser-native bridge conversion error'],
        { server_calls_allowed: false, ...(request.metadata ?? {}) },
      );
    }
  }

  prove(request: BridgeProofRequest): ProofResult {
    const startedAt = performance.now();
    if (request.logic === 'tdfol') {
      const theorem = parseTdfolFormula(request.theorem);
      const result = proveTdfol(
        theorem,
        {
          axioms: request.axioms.map(parseTdfolFormula),
          theorems: request.theorems?.map(parseTdfolFormula),
        },
        {
          ...this.tdfolOptions,
          maxSteps: request.maxSteps ?? this.tdfolOptions.maxSteps,
          maxDerivedFormulas: request.maxDerivedFormulas ?? this.tdfolOptions.maxDerivedFormulas,
        },
      );
      return { ...result, timeMs: performance.now() - startedAt, method: `bridge:${result.method ?? 'tdfol'}` };
    }

    if (request.logic === 'cec' || request.logic === 'dcec') {
      const theorem = parseCecExpression(request.theorem);
      const result = proveCec(
        theorem,
        {
          axioms: request.axioms.map(parseCecExpression),
          theorems: request.theorems?.map(parseCecExpression),
        },
        {
          ...this.cecOptions,
          maxSteps: request.maxSteps ?? this.cecOptions.maxSteps,
          maxDerivedExpressions: request.maxDerivedFormulas ?? this.cecOptions.maxDerivedExpressions,
        },
      );
      return { ...result, timeMs: performance.now() - startedAt, method: `bridge:${result.method ?? 'cec'}` };
    }

    throw new LogicBridgeError(`Unsupported browser-native proof logic: ${request.logic}`);
  }

  private convertSupported(request: BridgeConversionRequest): LogicBridgeConversionResult {
    if (request.targetFormat === 'fol' && isNaturalText(request.sourceFormat)) {
      const result = this.folConverter.convert(request.source);
      return new LogicBridgeConversionResult(
        result.success ? result.status === 'partial' ? 'partial' : 'success' : 'failed',
        request.source,
        result.output?.formulaString ?? '',
        request.sourceFormat,
        request.targetFormat,
        result.confidence,
        result.warnings.concat(result.errors),
        bridgeMetadata(request, {
          ...result.metadata,
          server_calls_allowed: false,
          routed_to: 'FOLConverter',
        }),
      );
    }

    if (request.targetFormat === 'deontic' && isNaturalText(request.sourceFormat)) {
      const result = this.deonticConverter.convert(request.source);
      return new LogicBridgeConversionResult(
        result.success ? result.status === 'partial' ? 'partial' : 'success' : 'failed',
        request.source,
        result.output?.formulas.join('\n') ?? '',
        request.sourceFormat,
        request.targetFormat,
        result.confidence,
        result.warnings.concat(result.errors),
        bridgeMetadata(request, {
          ...result.metadata,
          server_calls_allowed: false,
          routed_to: 'DeonticConverter',
        }),
      );
    }

    if (request.sourceFormat === 'fol') {
      const formatted = formatFol(request.source, toLogicOutputFormat(request.targetFormat));
      return new LogicBridgeConversionResult(
        'success',
        request.source,
        stringifyFormattedOutput(formatted),
        request.sourceFormat,
        request.targetFormat,
        1,
        [],
        bridgeMetadata(request, { formatter_metadata: formatted.metadata, server_calls_allowed: false }),
      );
    }

    if (request.sourceFormat === 'deontic') {
      const formatted = formatDeontic(request.source, 'obligation', toLogicOutputFormat(request.targetFormat));
      return new LogicBridgeConversionResult(
        'success',
        request.source,
        stringifyFormattedOutput(formatted),
        request.sourceFormat,
        request.targetFormat,
        1,
        [],
        bridgeMetadata(request, { formatter_metadata: formatted.metadata, server_calls_allowed: false }),
      );
    }

    if (request.sourceFormat === 'tdfol') {
      const target = toTdfolTarget(request.targetFormat);
      const result = convertTdfolFormula(request.source, target);
      return new LogicBridgeConversionResult(
        result.warnings.length > 0 ? 'partial' : 'success',
        result.source,
        typeof result.output === 'string' ? result.output : JSON.stringify(result.output),
        request.sourceFormat,
        request.targetFormat,
        result.warnings.length > 0 ? 0.85 : 1,
        result.warnings,
        bridgeMetadata(request, {
          ...result.metadata,
          server_calls_allowed: false,
          routed_to: 'convertTdfolFormula',
        }),
      );
    }

    if (request.sourceFormat === 'cec' || request.sourceFormat === 'dcec') {
      const expression = parseCecExpression(request.source);
      const targetFormula =
        request.targetFormat === 'json' ? JSON.stringify(expression) : formatCecExpression(expression);
      return new LogicBridgeConversionResult(
        'success',
        request.source,
        targetFormula,
        request.sourceFormat,
        request.targetFormat,
        1,
        [],
        bridgeMetadata(request, { server_calls_allowed: false, routed_to: 'parseCecExpression' }),
      );
    }

    throw new LogicBridgeError(`Unhandled browser-native bridge route: ${request.sourceFormat} -> ${request.targetFormat}`);
  }
}

export function createBrowserNativeLogicBridge(options: BrowserNativeLogicBridgeOptions = {}): BrowserNativeLogicBridge {
  return new BrowserNativeLogicBridge(options);
}

function isNaturalText(format: LogicBridgeFormat): boolean {
  return format === 'natural_language' || format === 'legal_text';
}

function toTdfolTarget(format: LogicBridgeFormat): TdfolConversionTarget {
  if (format === 'cec' || format === 'dcec') return 'dcec';
  if (format === 'tdfol' || format === 'fol' || format === 'tptp' || format === 'json') return format;
  throw new LogicBridgeError(`Unsupported TDFOL bridge target: ${format}`);
}

function toLogicOutputFormat(format: LogicBridgeFormat): LogicOutputFormat {
  if (format === 'fol') return 'symbolic';
  if (format === 'deontic') return 'symbolic';
  if (format === 'json' || format === 'prolog' || format === 'tptp' || format === 'defeasible') return format;
  throw new LogicBridgeError(`Unsupported formatter bridge target: ${format}`);
}

function stringifyFormattedOutput(output: FormattedFol | FormattedDeontic): string {
  if ('prolog_form' in output && typeof output.prolog_form === 'string') return output.prolog_form;
  if ('tptp_form' in output && typeof output.tptp_form === 'string') return output.tptp_form;
  if ('defeasible_form' in output && typeof output.defeasible_form === 'string') return output.defeasible_form;
  if ('fol_formula' in output && typeof output.fol_formula === 'string') return output.fol_formula;
  if ('deontic_formula' in output && typeof output.deontic_formula === 'string') return output.deontic_formula;
  return JSON.stringify(output);
}

function bridgeMetadata(
  request: BridgeConversionRequest,
  metadata: Record<string, unknown>,
): Record<string, unknown> {
  return {
    ...metadata,
    ...(request.metadata ?? {}),
    source_format: request.sourceFormat,
    target_format: request.targetFormat,
  };
}
