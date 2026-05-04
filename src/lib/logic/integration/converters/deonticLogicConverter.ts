import { DeonticConverter, type DeonticConverterOptions } from '../../deontic/converter';
import { formatDeontic } from '../../fol/formatter';
import type { DeonticNormType, NormativeElement } from '../../deontic/parser';

export type IntegrationDeonticOutputFormat = 'formula' | 'json' | 'defeasible' | 'prolog' | 'tptp';
export type IntegrationDeonticConverterOptions = Omit<DeonticConverterOptions, 'outputFormat'> & {
  outputFormat?: IntegrationDeonticOutputFormat;
};
export interface IntegrationDeonticConversionOptions {
  outputFormat?: IntegrationDeonticOutputFormat;
  confidence?: number;
}

export const INTEGRATION_DEONTIC_LOGIC_CONVERTER_METADATA = {
  sourcePythonModule: 'logic/integration/converters/deontic_logic_converter.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: ['legal_text_norm_extraction', 'multi_format_projection', 'local_fail_closed_validation'],
} as const;

export class BrowserNativeIntegrationDeonticLogicConverter {
  readonly metadata = INTEGRATION_DEONTIC_LOGIC_CONVERTER_METADATA;
  private readonly converter: DeonticConverter;
  private readonly outputFormat: IntegrationDeonticOutputFormat;

  constructor(options: IntegrationDeonticConverterOptions = {}) {
    this.outputFormat = options.outputFormat ?? 'formula';
    this.converter = new DeonticConverter({ ...options, outputFormat: 'json', useIpfs: false });
  }

  convert(text: string, options: IntegrationDeonticConversionOptions = {}) {
    const outputFormat = options.outputFormat ?? this.outputFormat;
    const result = this.converter.convert(text, {
      useCache: false,
      confidence: options.confidence,
      metadata: { integration_converter: 'browser-native-deontic-logic-converter' },
    });
    const formulas = result.output?.formulas ?? [];
    const norms = result.output?.elements ?? [];
    return {
      status: result.status,
      success: result.success,
      sourceText: text,
      outputFormat,
      output: result.success ? formatOutput(formulas, norms, outputFormat) : '',
      formulas,
      norms,
      confidence: result.confidence,
      warnings: result.warnings,
      errors: result.errors,
      metadata: {
        ...INTEGRATION_DEONTIC_LOGIC_CONVERTER_METADATA,
        ...result.metadata,
        norm_counts: countNorms(norms),
        output_format: outputFormat,
      },
    };
  }

  convertBatch(texts: string[], options: IntegrationDeonticConversionOptions = {}) {
    return texts.map((text) => this.convert(text, options));
  }
}

export function createBrowserNativeIntegrationDeonticLogicConverter(
  options: IntegrationDeonticConverterOptions = {},
) {
  return new BrowserNativeIntegrationDeonticLogicConverter(options);
}

export const create_deontic_logic_converter = createBrowserNativeIntegrationDeonticLogicConverter;

export function convertDeonticLogic(
  text: string,
  options: IntegrationDeonticConversionOptions = {},
) {
  return new BrowserNativeIntegrationDeonticLogicConverter({
    outputFormat: options.outputFormat,
  }).convert(text, options);
}

export const convert_deontic_logic = convertDeonticLogic;

function formatOutput(
  formulas: string[],
  norms: NormativeElement[],
  outputFormat: IntegrationDeonticOutputFormat,
): string | Record<string, unknown> {
  if (outputFormat === 'json')
    return { formulas, norms: norms.map(jsonNorm), norm_counts: countNorms(norms) };
  if (outputFormat === 'prolog')
    return formulas
      .map((formula, index) => `deontic_norm(${index + 1}, ${quote(formula)}).`)
      .join('\n');
  if (outputFormat === 'tptp')
    return formulas
      .map((formula, index) => `fof(deontic_norm_${index + 1}, axiom, ${quote(formula)}).`)
      .join('\n');
  if (outputFormat === 'defeasible') {
    return formulas
      .map(
        (formula, index) =>
          formatDeontic(formula, norms[index]?.normType ?? 'obligation', 'defeasible')
            .defeasible_form ?? formula,
      )
      .join('\n');
  }
  return formulas.join('\n');
}

function jsonNorm(norm: NormativeElement): Record<string, unknown> {
  return {
    text: norm.text,
    norm_type: norm.normType,
    deontic_operator: norm.deonticOperator,
    subjects: norm.subjects,
    actions: norm.actions,
    conditions: norm.conditions,
    exceptions: norm.exceptions,
    temporal_constraints: norm.temporalConstraints,
    confidence: norm.confidence,
  };
}

function countNorms(norms: NormativeElement[]): Record<DeonticNormType, number> {
  const counts: Record<DeonticNormType, number> = { obligation: 0, permission: 0, prohibition: 0 };
  for (const norm of norms) counts[norm.normType] += 1;
  return counts;
}

function quote(value: string): string {
  return JSON.stringify(value);
}
